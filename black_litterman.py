import argparse
import json
import math
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf


# ============================
# Data classes and structures
# ============================


@dataclass
class BLSettings:
    window_years: int = 3
    price_interval: str = "1d"
    risk_free_rate: float = 0.02  # annualized
    shrinkage: float = 0.10  # to identity
    tau: float = 0.05
    delta: Optional[float] = None  # risk aversion; estimate if None
    long_only: bool = True
    min_weight: float = 0.0
    max_weight: float = 0.25
    use_market_caps: bool = True
    benchmark: Optional[str] = None  # if provided, used for delta estimation


@dataclass
class BLInputs:
    tickers: List[str]
    views: List[dict]
    settings: BLSettings


# ============================
# JSON loading and validation
# ============================


def load_config(path: str) -> BLInputs:
    with open(path, "r") as f:
        raw = json.load(f)

    if isinstance(raw, dict) and "tickers" not in raw:
        # Allow a bare list of tickers in the json
        if isinstance(raw, list):
            raw = {"tickers": raw}
        else:
            # Attempt to infer keys like {"assets": [..]}
            if "assets" in raw and isinstance(raw["assets"], list):
                raw["tickers"] = raw["assets"]

    tickers = raw.get("tickers") or raw.get("assets")
    if not tickers or not isinstance(tickers, list):
        raise ValueError("JSON must include a 'tickers' array or be a bare array of tickers.")

    views = raw.get("views", [])
    if not isinstance(views, list):
        raise ValueError("'views' must be a list if provided.")

    settings_dict = raw.get("settings", {})
    settings = BLSettings(
        window_years=int(settings_dict.get("window_years", 3)),
        price_interval=str(settings_dict.get("price_interval", "1d")),
        risk_free_rate=float(settings_dict.get("risk_free_rate", 0.02)),
        shrinkage=float(settings_dict.get("shrinkage", 0.10)),
        tau=float(settings_dict.get("tau", 0.05)),
        delta=(float(settings_dict["delta"]) if settings_dict.get("delta") is not None else None),
        long_only=bool(settings_dict.get("long_only", True)),
        min_weight=float(settings_dict.get("min_weight", 0.0)),
        max_weight=float(settings_dict.get("max_weight", 0.25)),
        use_market_caps=bool(settings_dict.get("use_market_caps", True)),
        benchmark=settings_dict.get("benchmark"),
    )

    # Normalize tickers
    tickers = [str(t).upper().strip() for t in tickers if str(t).strip()]

    return BLInputs(tickers=tickers, views=views, settings=settings)


# ============================
# Market data utilities
# ============================


def compute_date_range(years: int) -> Tuple[datetime, datetime]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=365 * years)
    # Normalize to naive dates for yfinance
    return start.replace(tzinfo=None), end.replace(tzinfo=None)


def fetch_prices(tickers: List[str], start: datetime, end: datetime, interval: str) -> pd.DataFrame:
    data = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        interval=interval,
        auto_adjust=True,
        progress=False,
    )
    if not isinstance(data, pd.DataFrame) or data.empty:
        raise ValueError("Failed to download price data from yfinance.")

    # With auto_adjust=True, yfinance uses 'Close' instead of 'Adj Close'.
    # Handle both MultiIndex (multiple tickers) and single-index (single ticker) cases.
    prices: pd.DataFrame
    if isinstance(data.columns, pd.MultiIndex):
        level0 = set(data.columns.get_level_values(0))
        col_key = "Close" if "Close" in level0 else ("Adj Close" if "Adj Close" in level0 else None)
        if col_key is None:
            # Fallback to the last price-like field
            for candidate in ["Close", "Adj Close", "Price"]:
                if candidate in level0:
                    col_key = candidate
                    break
        if col_key is None:
            raise ValueError("Downloaded data missing 'Close'/'Adj Close' columns.")
        # Extract the selected price level -> columns become tickers
        prices = data.xs(col_key, axis=1, level=0).copy()
    else:
        # Single ticker: columns are single-level
        if "Close" in data.columns:
            ser = data["Close"].copy()
        elif "Adj Close" in data.columns:
            ser = data["Adj Close"].copy()
        else:
            # Take the first numeric column as a last resort
            numeric_cols = [c for c in data.columns if pd.api.types.is_numeric_dtype(data[c])]
            if not numeric_cols:
                raise ValueError("No numeric price column found in downloaded data.")
            ser = data[numeric_cols[0]].copy()
        prices = ser.to_frame()
        # Name the single column after the single ticker
        prices.columns = [tickers[0]]

    prices = prices.dropna(how="all")
    # Ensure all requested tickers are in columns
    missing = [t for t in tickers if t not in prices.columns]
    if missing:
        raise ValueError(f"Missing price data for: {', '.join(missing)}")
    return prices


def compute_returns_cov(prices: pd.DataFrame) -> Tuple[pd.Series, pd.DataFrame]:
    log_returns = np.log(prices / prices.shift(1)).dropna()
    mu = log_returns.mean() * 252.0
    sigma = log_returns.cov() * 252.0
    return mu, sigma


def shrink_covariance(cov: pd.DataFrame, shrinkage: float) -> pd.DataFrame:
    if shrinkage <= 0.0:
        return cov
    cov_np = cov.values
    diag_avg = np.trace(cov_np) / cov_np.shape[0]
    identity = np.eye(cov_np.shape[0]) * diag_avg
    shrunk = shrinkage * identity + (1.0 - shrinkage) * cov_np
    return pd.DataFrame(shrunk, index=cov.index, columns=cov.columns)


def get_market_caps(tickers: List[str]) -> Dict[str, Optional[float]]:
    caps: Dict[str, Optional[float]] = {}
    for t in tickers:
        try:
            info = yf.Ticker(t).get_info()
            caps[t] = float(info.get("marketCap")) if info.get("marketCap") is not None else None
        except Exception:
            caps[t] = None
    return caps


def market_weights_from_caps(tickers: List[str], caps: Dict[str, Optional[float]]) -> np.ndarray:
    values = np.array([caps.get(t) or 0.0 for t in tickers], dtype=float)
    total = np.sum(values)
    if total <= 0:
        return np.ones(len(tickers), dtype=float) / len(tickers)
    return values / total


# ============================
# Black-Litterman core
# ============================


def estimate_risk_aversion(mu: pd.Series, cov: pd.DataFrame, rf: float, market_weights: np.ndarray) -> float:
    portfolio_return = float(np.dot(market_weights, mu.values))
    portfolio_var = float(market_weights @ cov.values @ market_weights)
    if portfolio_var <= 0:
        portfolio_var = float(np.mean(np.diag(cov.values)))
    # delta = (E[R] - Rf) / Var[R]
    return max(1e-6, (portfolio_return - rf) / portfolio_var)


def equilibrium_returns(delta: float, cov: pd.DataFrame, market_weights: np.ndarray) -> pd.Series:
    pi = delta * cov.values @ market_weights
    return pd.Series(pi, index=cov.columns)


def parse_views(views: List[dict], tickers: List[str]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    n = len(tickers)
    P_list: List[np.ndarray] = []
    Q_list: List[float] = []
    conf_list: List[float] = []

    for v in views:
        if not isinstance(v, dict):
            continue
        assets = v.get("assets")
        if isinstance(assets, list):
            # e.g., ["AAPL", "MSFT"], default equal weights
            weights = {str(a).upper(): 1.0 / len(assets) for a in assets}
        elif isinstance(assets, dict):
            weights = {str(k).upper(): float(val) for k, val in assets.items()}
        else:
            raise ValueError("Each view must have 'assets' as list or dict of weights.")

        p = np.zeros(n)
        for k, w in weights.items():
            if k not in tickers:
                raise ValueError(f"View references unknown asset: {k}")
            idx = tickers.index(k)
            p[idx] = float(w)

        q = float(v.get("view"))  # annualized expected excess return differential
        confidence = float(v.get("confidence", 0.5))
        confidence = min(max(confidence, 1e-6), 0.999999)

        P_list.append(p)
        Q_list.append(q)
        conf_list.append(confidence)

    if not P_list:
        return np.zeros((0, n)), np.zeros((0,)), np.zeros((0,))

    P = np.vstack(P_list)
    Q = np.array(Q_list)
    confidences = np.array(conf_list)
    return P, Q, confidences


def construct_omega(P: np.ndarray, tau: float, cov: pd.DataFrame, confidences: np.ndarray) -> np.ndarray:
    # Base omega from He-Litterman suggestion: diag(P * tau * Sigma * P^T)
    if P.shape[0] == 0:
        return np.zeros((0, 0))
    S = cov.values
    base = np.diag(np.diag(P @ (tau * S) @ P.T))
    # Scale by inverse of confidence: higher confidence -> smaller variance
    # Map c in (0,1) to scale = (1-c)/c so that c=0.5 -> 1, c=0.8 -> 0.25, c=0.2 -> 4
    scales = (1.0 - confidences) / confidences
    scales = np.clip(scales, 1e-6, 1e6)
    return base * scales[:, None]


def black_litterman_posterior(
    cov: pd.DataFrame,
    pi: pd.Series,
    P: np.ndarray,
    Q: np.ndarray,
    omega: np.ndarray,
    tau: float,
) -> Tuple[np.ndarray, np.ndarray]:
    S = cov.values
    n = S.shape[0]
    tauS_inv = np.linalg.inv(tau * S)
    if P.shape[0] == 0:
        # No views; posterior equals prior
        mu_post = pi.values
        Sigma_post = S.copy()
        return mu_post, Sigma_post

    omega_inv = np.linalg.inv(omega)
    A = tauS_inv + P.T @ omega_inv @ P
    A_inv = np.linalg.inv(A)
    b = tauS_inv @ pi.values + P.T @ omega_inv @ Q
    mu_post = A_inv @ b
    Sigma_post = S + A_inv
    return mu_post, Sigma_post


# ============================
# Optimization
# ============================


def mean_variance_optimal_weights(mu: np.ndarray, Sigma: np.ndarray, delta: float) -> np.ndarray:
    # Unconstrained: w* = (1/delta) * Sigma^{-1} mu
    # Add small ridge for stability
    n = Sigma.shape[0]
    ridge = 1e-6 * np.eye(n)
    inv = np.linalg.inv(Sigma + ridge)
    w = (1.0 / delta) * (inv @ mu)
    # Normalize to sum to 1 if all positive; otherwise allow negative weights (unconstrained)
    s = np.sum(w)
    if s != 0:
        w = w / s
    return w


def project_to_simplex_with_box_constraints(weights: np.ndarray, min_w: float, max_w: float) -> np.ndarray:
    # Clip and project to sum=1
    w = np.clip(weights, min_w, max_w)
    # Project to simplex sum=1 with lower bound min_w and upper bound max_w iteratively
    # Use a heuristic: repeatedly adjust violating weights and renormalize until convergence
    for _ in range(50):
        w = np.clip(w, min_w, max_w)
        total = w.sum()
        if total == 0:
            # distribute equally within bounds
            w = np.full_like(w, (1.0 / len(w)))
        else:
            w = w / total
        # If within bounds and sums to ~1, break
        if abs(w.sum() - 1.0) < 1e-6 and np.all(w >= min_w - 1e-8) and np.all(w <= max_w + 1e-8):
            break
    return w


def projected_gradient_descent(
    mu: np.ndarray,
    Sigma: np.ndarray,
    rf: float,
    min_w: float,
    max_w: float,
    max_iter: int = 2000,
    step: float = 0.01,
) -> np.ndarray:
    # Maximize Sharpe (mu^T w - rf) / sqrt(w^T S w) subject to sum w = 1 and box constraints
    # We optimize equivalent: maximize (mu_excess^T w - 0.5 * lambda * w^T S w)
    # Use adaptive lambda by alternate optimization: update lambda to match risk target (not specified) -> set by gradient step only
    n = len(mu)
    w = np.ones(n) / n
    mu_excess = mu - rf
    for i in range(max_iter):
        grad_num = mu_excess
        grad_den = (w @ Sigma @ w)
        if grad_den <= 1e-12:
            grad_den = 1e-12
        grad = grad_num - (Sigma @ w) * ((mu_excess @ w) / grad_den)
        w = w + step * grad
        w = project_to_simplex_with_box_constraints(w, min_w, max_w)
    return w


# ============================
# Reporting
# ============================


def summarize(weights: pd.Series, mu: pd.Series, Sigma: pd.DataFrame, rf: float) -> Dict[str, float]:
    w = weights.values
    exp_return = float(w @ mu.values)
    exp_vol = float(np.sqrt(w @ Sigma.values @ w))
    sharpe = float((exp_return - rf) / exp_vol) if exp_vol > 0 else float("nan")
    return {
        "expected_return": exp_return,
        "expected_volatility": exp_vol,
        "sharpe": sharpe,
    }


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def create_output_dir() -> str:
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = os.path.join("results", f"black_litterman_{ts}")
    ensure_dir(out_dir)
    return out_dir


def write_outputs(
    out_dir: str,
    tickers: List[str],
    weights_uncon: Optional[np.ndarray],
    weights_constrained: Optional[np.ndarray],
    mu_bl: np.ndarray,
    Sigma_bl: np.ndarray,
    rf: float,
    settings: BLSettings,
    pi: np.ndarray,
):
    report: Dict[str, object] = {
        "tickers": tickers,
        "risk_free_rate": rf,
        "settings": {
            "window_years": settings.window_years,
            "price_interval": settings.price_interval,
            "shrinkage": settings.shrinkage,
            "tau": settings.tau,
            "delta": settings.delta,
            "long_only": settings.long_only,
            "min_weight": settings.min_weight,
            "max_weight": settings.max_weight,
            "use_market_caps": settings.use_market_caps,
            "benchmark": settings.benchmark,
        },
    }

    mu_ser = pd.Series(mu_bl, index=tickers)
    Sigma_df = pd.DataFrame(Sigma_bl, index=tickers, columns=tickers)
    pi_ser = pd.Series(pi, index=tickers)

    if weights_uncon is not None:
        w_uncon_ser = pd.Series(weights_uncon, index=tickers)
        report["unconstrained"] = {
            "weights": w_uncon_ser.to_dict(),
            **summarize(w_uncon_ser, mu_ser, Sigma_df, rf),
        }
        w_uncon_ser.to_csv(os.path.join(out_dir, "weights_unconstrained.csv"))

    if weights_constrained is not None:
        w_con_ser = pd.Series(weights_constrained, index=tickers)
        report["long_only"] = {
            "weights": w_con_ser.to_dict(),
            **summarize(w_con_ser, mu_ser, Sigma_df, rf),
        }
        w_con_ser.to_csv(os.path.join(out_dir, "weights_long_only.csv"))

    report["posterior"] = {
        "mu": mu_ser.to_dict(),
        "covariance": Sigma_df.to_dict(),
        "equilibrium_pi": pi_ser.to_dict(),
    }

    with open(os.path.join(out_dir, "report.json"), "w") as f:
        json.dump(report, f, indent=2)

    # Text summary (implementation-first, concise)
    lines: List[str] = []
    lines.append("Implementation summary")
    if weights_constrained is not None:
        w_con_ser = pd.Series(weights_constrained, index=tickers)
        summ = summarize(w_con_ser, mu_ser, Sigma_df, rf)
        lines.append(f"Long-only weights: {', '.join([f'{t}: {w_con_ser[t]:.2%}' for t in tickers])}")
        lines.append(f"Expected return: {summ['expected_return']:.2%}")
        lines.append(f"Expected volatility: {summ['expected_volatility']:.2%}")
        lines.append(f"Sharpe: {summ['sharpe']:.2f}")
    if weights_uncon is not None:
        w_uncon_ser = pd.Series(weights_uncon, index=tickers)
        summ = summarize(w_uncon_ser, mu_ser, Sigma_df, rf)
        lines.append("")
        lines.append("Unconstrained MV weights")
        lines.append(f"Weights: {', '.join([f'{t}: {w_uncon_ser[t]:.2%}' for t in tickers])}")
        lines.append(f"Expected return: {summ['expected_return']:.2%}")
        lines.append(f"Expected volatility: {summ['expected_volatility']:.2%}")
        lines.append(f"Sharpe: {summ['sharpe']:.2f}")

    with open(os.path.join(out_dir, "summary.txt"), "w") as f:
        f.write("\n".join(lines))


# ============================
# Orchestration
# ============================


def run_black_litterman(config_path: str) -> str:
    inputs = load_config(config_path)
    tickers = inputs.tickers
    settings = inputs.settings

    start, end = compute_date_range(settings.window_years)
    prices = fetch_prices(tickers, start, end, settings.price_interval)
    mu_hist, cov_hist = compute_returns_cov(prices)
    cov = shrink_covariance(cov_hist, settings.shrinkage)

    if settings.use_market_caps:
        caps = get_market_caps(tickers)
        w_mkt = market_weights_from_caps(tickers, caps)
    else:
        w_mkt = np.ones(len(tickers)) / len(tickers)

    rf = settings.risk_free_rate
    delta = settings.delta or estimate_risk_aversion(mu_hist, cov, rf, w_mkt)
    pi = equilibrium_returns(delta, cov, w_mkt)

    P, Q, confidences = parse_views(inputs.views, tickers)
    omega = construct_omega(P, settings.tau, cov, confidences)
    mu_bl, Sigma_bl = black_litterman_posterior(cov, pi, P, Q, omega, settings.tau)

    # Optimize
    w_uncon: Optional[np.ndarray] = mean_variance_optimal_weights(mu_bl, Sigma_bl, delta)

    w_constrained: Optional[np.ndarray] = None
    if settings.long_only:
        w_constrained = projected_gradient_descent(
            mu_bl,
            Sigma_bl,
            rf,
            settings.min_weight,
            settings.max_weight,
            max_iter=2000,
            step=0.02,
        )

    out_dir = create_output_dir()
    write_outputs(out_dir, tickers, w_uncon, w_constrained, mu_bl, Sigma_bl, rf, settings, pi.values)
    return out_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Black-Litterman portfolio optimizer")
    parser.add_argument("--config", required=True, help="Path to JSON file. Minimal schema: {\"tickers\":[...]}. Optional 'views' and 'settings'.")
    args = parser.parse_args()

    out_dir = run_black_litterman(args.config)
    print(f"Black-Litterman optimization complete. Outputs saved to: {out_dir}")


if __name__ == "__main__":
    main()


