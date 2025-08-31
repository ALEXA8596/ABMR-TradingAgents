import argparse
import copy
import json
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Tuple, List
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import pandas as pd
try:
    import pandas_market_calendars as mcal
except Exception:
    mcal = None

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.agents.utils.agent_utils import Toolkit
from tradingagents.agents.managers.MVO_BLM.pipeline import size_positions
from tradingagents.dataflows import interface as data_interface
from langchain_openai import ChatOpenAI
import yfinance as yf
import dotenv
dotenv.load_dotenv()
GRAPH_INIT_LOCK = Lock()


def _extract_action_and_rationale(final_state, final_decision) -> Tuple[str, str]:
    try:
        action = None
        if isinstance(final_decision, str) and final_decision.upper() in {"BUY", "SELL", "HOLD"}:
            action = final_decision.upper()
        if not action and isinstance(final_state, dict):
            po = final_state.get("portfolio_optimization_state") or {}
            if isinstance(po, dict):
                exec_info = po.get("execution") or {}
                if isinstance(exec_info, dict) and exec_info.get("action"):
                    action = str(exec_info.get("action")).upper()
        if not action and isinstance(final_state, dict):
            plan = final_state.get("trader_investment_plan") or ""
            text = str(plan).upper()
            if "FINAL TRANSACTION PROPOSAL: **BUY**" in text:
                action = "BUY"
            elif "FINAL TRANSACTION PROPOSAL: **SELL**" in text:
                action = "SELL"
            elif "FINAL TRANSACTION PROPOSAL: **HOLD**" in text:
                action = "HOLD"
        if not action:
            action = "HOLD"
        rationale = ""
        if isinstance(final_state, dict):
            # Prefer explicit final rationale
            rationale = final_state.get("final_trade_rationale") or ""
            # Fallbacks: trader plan text, investment plan, or condensed analyst reports
            if not rationale:
                plan_txt = str(final_state.get("trader_investment_plan") or final_state.get("investment_plan") or "")
                if plan_txt.strip():
                    rationale = plan_txt.strip()
            if not rationale:
                parts = []
                for key, label in [("market_report", "Market"), ("news_report", "News"), ("fundamentals_report", "Fundamentals"), ("sentiment_report", "Sentiment")]:
                    txt = str(final_state.get(key) or "").strip()
                    if txt:
                        # Take first 300 chars per section to avoid blank rationales
                        parts.append(f"{label}: {txt[:300]}")
                if parts:
                    rationale = " \n".join(parts)
        # Harmonize action with any explicit final proposal text in rationale
        if isinstance(rationale, str) and rationale:
            up = rationale.upper()
            if "FINAL TRANSACTION PROPOSAL: **SELL**" in up:
                action = "SELL"
            elif "FINAL TRANSACTION PROPOSAL: **BUY**" in up:
                action = "BUY"
            elif "FINAL TRANSACTION PROPOSAL: **HOLD**" in up:
                action = "HOLD"
        return action, rationale
    except Exception:
        return str(final_decision), ""


def _weights_from_actions(actions: Dict[str, str]) -> Dict[str, float]:
    raw = {}
    for t, a in actions.items():
        a_up = (a or "").upper()
        score = 1.0
        if a_up == "BUY":
            score = 1.5
        elif a_up == "SELL":
            score = 0.2
        elif a_up == "HOLD":
            score = 1.0
        raw[t] = max(0.0, float(score))
    s = sum(raw.values()) or 1.0
    return {t: round(v / s, 4) for t, v in raw.items()}


def run_ticker(ticker: str, date_str: str, out_date_dir: Path, config: Dict, debug: bool, show_trace: bool) -> Tuple[str, str]:
    # Serialize graph init to avoid concurrent collection creation in memories
    # Provide unique memory suffix to avoid collection name clashes
    config = {**config, "memory_suffix": f"{ticker}_{date_str}"}
    try:
        with GRAPH_INIT_LOCK:
            graph = TradingAgentsGraph(debug=debug, config=config)
        print(f"🚀 {ticker} {date_str} starting")
        final_state, final_decision = graph.propagate(ticker, date_str)
        action, rationale = _extract_action_and_rationale(final_state, final_decision)
    except Exception as e:
        # Ensure a per-ticker file is still written even if the graph fails
        action = "HOLD"
        rationale = f"Error during analysis: {e}"
        if show_trace:
            traceback.print_exc()
    file_text = "\n".join([
        f"TICKER: {ticker}",
        f"DATE: {date_str}",
        f"DECISION: {action}",
        "RATIONALE:",
        rationale or "",
    ]) + "\n"
    (out_date_dir / f"{ticker}.txt").write_text(file_text, encoding="utf-8")
    print(f"✅ Saved -> {(out_date_dir / f'{ticker}.txt').as_posix()}")
    return ticker, action


def run_batch5_multithreaded(
    date_str: str,
    out_root: str = "testing",
    debug: bool = False,
    deep_copy_config: bool = True,
    fail_fast: bool = False,
    show_trace: bool = False,
    reset_portfolio: bool = True,
):
    tickers = ["AAPL", "AMZN", "GOOG", "META", "NVDA"]
    out_date_dir = Path(out_root) / date_str
    out_date_dir.mkdir(parents=True, exist_ok=True)

    base_config = copy.deepcopy(DEFAULT_CONFIG) if deep_copy_config else DEFAULT_CONFIG.copy()
    print(f"🟢 Starting multithreaded batch-5 run for {date_str}: {', '.join(tickers)} | outdir={out_date_dir}")
    t0 = time.time()

    # Reset portfolio only when requested (e.g., first day of a multi-day run)
    portfolio_path = (Path.cwd() / "testing" / "portfolio.json").resolve()
    portfolio_path.parent.mkdir(parents=True, exist_ok=True)
    if reset_portfolio or (not portfolio_path.exists()):
        with open(portfolio_path, 'w') as f:
            json.dump({"portfolio": {}, "liquid": 100000}, f, indent=2)
        # Keep config/portfolio.json in sync (in case tools write there)
        try:
            config_portfolio_path = (Path.cwd() / "config" / "portfolio.json").resolve()
            config_portfolio_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_portfolio_path, 'w') as cf:
                json.dump({"portfolio": {}, "liquid": 100000}, cf, indent=2)
        except Exception:
            pass

    decisions: Dict[str, str] = {}

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(run_ticker, t, date_str, out_date_dir, copy.deepcopy(base_config), debug, show_trace)
            for t in tickers
        ]
        for future in as_completed(futures):
            try:
                ticker, action = future.result()
                decisions[ticker] = action
            except Exception as e:
                print(f"❌ Thread error: {e}")
                if show_trace:
                    traceback.print_exc()
                if fail_fast:
                    raise

    # After threads finish: generate LLM-based views for BL (fallback to decisions mapping)
    def _generate_llm_views(cfg: Dict, syms: list[str], d: str) -> Dict[str, float]:
        try:
            model = cfg.get("quick_think_llm", "gpt-4o-mini")
            llm = ChatOpenAI(model=model)
            prompt = (
                "You are a portfolio strategist. For the given tickers, provide expected annualized excess returns "
                "(decimal, e.g., 0.03 for +3%) for the next period based on macro/sector/price action. "
                "Return only a compact JSON object with tickers as keys and decimals as values. "
                f"Tickers: {', '.join(syms)}. Date context: {d}."
            )
            resp = llm.invoke(prompt)  # type: ignore
            txt = getattr(resp, "content", "{}")
            try:
                data = json.loads(txt)
                if isinstance(data, dict):
                    # clamp to [-0.1, 0.1]
                    return {k: float(max(-0.1, min(0.1, v))) for k, v in data.items() if k in syms}
            except Exception:
                pass
        except Exception:
            pass
        # fallback: decision-based views
        v: Dict[str, float] = {}
        for t, a in decisions.items():
            a_up = (a or '').upper()
            v[t] = 0.02 if a_up == 'BUY' else (-0.02 if a_up == 'SELL' else 0.0)
        return v

    llm_views = _generate_llm_views(base_config, tickers, date_str)

    # Run MVO-BLM sizing for the day
    def _get_prices_for_date(tks, d):
        prices: Dict[str, float] = {}
        for t in tks:
            try:
                prices[t] = float(data_interface.get_price_from_csv(t, d))
            except Exception:
                try:
                    start = datetime.strptime(d, "%Y-%m-%d")
                    end = start + timedelta(days=1)
                    hist = yf.Ticker(t).history(start=start, end=end)
                    prices[t] = float(hist['Close'].iloc[-1]) if not hist.empty else 0.0
                except Exception:
                    prices[t] = 0.0
        return prices

    prices = _get_prices_for_date(tickers, date_str)
    portfolio_path = (Path.cwd() / "testing" / "portfolio.json").resolve()
    trades = size_positions(tickers, date_str, decisions, str(portfolio_path), prices, views=llm_views)

    # Resizing report
    rr_lines = [f"# Resizing Report ({date_str})\n", "## Trades\n"]
    for t in tickers:
        tr = trades.get(t)
        if tr:
            rr_lines.append(f"- {t}: delta={tr.get('delta_shares')}, target_qty={tr.get('target_qty')}, current_qty={tr.get('current_qty')}, price={tr.get('price')}")
        else:
            rr_lines.append(f"- {t}: no change")
    (out_date_dir / "resizingReport.md").write_text("\n".join(rr_lines), encoding="utf-8")
    print(f"✅ Saved -> {(out_date_dir / 'resizingReport.md').as_posix()}")

    # Execute aggregated trades and then snapshot
    try:
        with open(portfolio_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"portfolio": {}, "liquid": 100000}
    if "portfolio" not in data or not isinstance(data["portfolio"], dict):
        data["portfolio"] = {}
    if "liquid" not in data or not isinstance(data["liquid"], (int, float)):
        data["liquid"] = 100000
    # Enforce short exposure cap while executing aggregated trades
    MAX_SHORT_NOTIONAL = 200000.0
    def _compute_short_notional(portfolio_dict: Dict[str, Dict[str, float]]) -> float:
        total_short = 0.0
        for _sym, _h in portfolio_dict.items():
            qty = float(_h.get("totalAmount", 0) or 0)
            px = float(_h.get("last_price", 0) or 0)
            if qty < 0 and px > 0:
                total_short += abs(qty) * px
        return total_short

    for sym, tr in (trades or {}).items():
        price = float(tr.get("price", 0.0) or 0.0)
        if price <= 0:
            continue
        holdings = data["portfolio"].get(sym, {"totalAmount": 0})
        current_qty = int(holdings.get("totalAmount", 0))
        # Enforce pipeline direction: SELL -> short (negative), BUY -> long (positive), HOLD -> no change
        decision_dir = (decisions.get(sym, "HOLD") or "HOLD").upper()
        proposed_delta = int(tr.get("delta_shares", 0))
        proposed_target = int(tr.get("target_qty", current_qty + proposed_delta))
        magnitude = abs(proposed_target)
        if decision_dir == "HOLD":
            desired_target_qty = current_qty
        elif decision_dir == "SELL":
            desired_target_qty = -magnitude
        elif decision_dir == "BUY":
            desired_target_qty = magnitude
        else:
            desired_target_qty = current_qty
        delta = desired_target_qty - current_qty
        if delta > 0:
            max_affordable = int((float(data.get("liquid", 0.0)) // price))
            buy_qty = min(delta, max_affordable)
            if buy_qty > 0:
                cost = buy_qty * price
                prev_qty = int(holdings.get("totalAmount", 0))
                new_qty = prev_qty + buy_qty
                holdings["totalAmount"] = new_qty
                holdings["last_price"] = price
                # Entry price: weighted average for adds; reset on side flip
                prev_entry = float(holdings.get("entry_price", 0.0) or 0.0)
                if prev_qty >= 0 and new_qty > 0:
                    if prev_qty > 0 and prev_entry > 0:
                        holdings["entry_price"] = ((prev_entry * prev_qty) + (price * buy_qty)) / max(new_qty, 1)
                    else:
                        holdings["entry_price"] = price
                else:
                    # Crossing from short to long in same tick: treat as new long entry
                    holdings["entry_price"] = price
                data["liquid"] = float(data.get("liquid", 0.0)) - cost
        elif delta < 0:
            sell_qty = abs(delta)
            current_qty = int(holdings.get("totalAmount", 0))
            # Enforce short capacity if this action would create/increase a short
            current_short_notional = _compute_short_notional(data["portfolio"])  # uses last prices
            remaining_short_capacity = max(0.0, MAX_SHORT_NOTIONAL - current_short_notional)
            if price > 0 and remaining_short_capacity <= 0 and (current_qty <= 0 or sell_qty > current_qty):
                # No capacity to add any new short exposure; limit sells to not cross into more short
                sell_qty = max(0, min(sell_qty, max(0, current_qty)))
            else:
                if current_qty < 0:
                    # Already short; adding more short
                    max_additional_short_shares = int(remaining_short_capacity // price)
                    sell_qty = min(sell_qty, max_additional_short_shares)
                elif current_qty >= 0:
                    # Selling from long; may cross to short
                    would_be_new_qty = current_qty - sell_qty
                    if would_be_new_qty < 0:
                        # Shares that would become short beyond flat
                        cross_short_shares = abs(would_be_new_qty)
                        max_additional_short_shares = int(remaining_short_capacity // price)
                        allowed_cross_short = max(0, min(cross_short_shares, max_additional_short_shares))
                        # total sell allowed = shares to flat + allowed cross short
                        sell_qty = min(sell_qty, current_qty + allowed_cross_short)

            new_qty = current_qty - sell_qty
            holdings["totalAmount"] = new_qty
            proceeds = sell_qty * price
            holdings["last_price"] = price
            prev_entry = float(holdings.get("entry_price", 0.0) or 0.0)
            # If selling increases short (current >=0 to <0, or already <0 and more negative)
            if current_qty >= 0 and new_qty < 0:
                # New short entry
                holdings["entry_price"] = price
            elif current_qty < 0 and new_qty < 0:
                # Adding to existing short -> weighted average based on absolute shares
                prev_abs = abs(current_qty)
                new_abs = abs(new_qty)
                add_abs = abs(delta)
                if prev_abs > 0 and prev_entry > 0:
                    holdings["entry_price"] = ((prev_entry * prev_abs) + (price * add_abs)) / max(new_abs, 1)
                else:
                    holdings["entry_price"] = price
            elif new_qty > 0:
                # Crossed from short to long within a day due to over-covering: new long entry
                holdings["entry_price"] = price
            elif new_qty == 0:
                # Flat
                holdings["entry_price"] = 0.0
            data["liquid"] = float(data.get("liquid", 0.0)) + proceeds
        else:
            # HOLD: update last_price only
            holdings["last_price"] = price
        data["portfolio"][sym] = holdings
    with open(portfolio_path, 'w') as f:
        json.dump(data, f, indent=2)

    # Snapshot now from persisted portfolio file but revalue positions with date-specific prices
    try:
        persisted = json.loads(portfolio_path.read_text(encoding="utf-8"))
    except Exception:
        persisted = data
    # Revalue last_price for each holding using the date's close
    for sym, info in list(persisted.get("portfolio", {}).items()):
        try:
            px = float(data_interface.get_price_from_csv(sym, date_str))
        except Exception:
            try:
                start = datetime.strptime(date_str, "%Y-%m-%d")
                end = start + timedelta(days=1)
                hist = yf.Ticker(sym).history(start=start, end=end)
                px = float(hist['Close'].iloc[-1]) if not hist.empty else float(info.get('last_price', 0.0) or 0.0)
            except Exception:
                px = float(info.get('last_price', 0.0) or 0.0)
        info["last_price"] = px
        persisted["portfolio"][sym] = info
    # Compute net liquidation and buying power with short cap
    liquid_cash = float(persisted.get("liquid", 0.0) or 0.0)
    net_liq = liquid_cash
    total_short_notional = 0.0
    for sym, info in persisted.get("portfolio", {}).items():
        qty = float(info.get("totalAmount", 0) or 0)
        px = float(info.get("last_price", 0.0) or 0.0)
        net_liq += qty * px
        if qty < 0 and px > 0:
            total_short_notional += abs(qty) * px
    short_capacity_remaining = max(0.0, MAX_SHORT_NOTIONAL - total_short_notional)
    # Buying power: do not equate to liquid; combine long capacity proxy (net_liq positive) and remaining short capacity
    buying_power = max(0.0, net_liq) + short_capacity_remaining
    snap_path = out_date_dir / f"portfolio_snapshot_{date_str}.json"
    with open(snap_path, 'w') as f:
        # enrich snapshot with value metrics
        enriched = dict(persisted)
        enriched["net_liquidation"] = net_liq
        # maintain legacy fields for compatibility
        enriched["portfolio_value"] = net_liq
        enriched["cash"] = liquid_cash
        enriched["buying_power"] = buying_power
        json.dump(enriched, f, indent=2)
    print(f"📸 Portfolio snapshot saved -> {snap_path.as_posix()}")

    # Consolidated portfolio optimization based on decisions (summary)
    # Ensure execution aligns with per-ticker decisions: SELL->increase short/cover long; BUY->increase long/cover short; HOLD->no change
    # (Already enforced above via size_positions and execution block.)
    weights = _weights_from_actions(decisions)
    toolkit = Toolkit(config=base_config)
    try:
        rp = toolkit.get_portfolio_risk_parity.invoke({})
    except Exception:
        rp = {"error": "risk parity unavailable"}
    runtime_s = round(time.time() - t0, 2)
    runtime_hms = f"{int(runtime_s//3600):02d}:{int((runtime_s%3600)//60):02d}:{int(runtime_s%60):02d}"

    lines = []
    lines.append(f"# Multithreaded Batch Portfolio Report ({date_str})\n")
    lines.append(f"- Runtime: {runtime_hms} ({runtime_s}s)\n")
    lines.append("## Decisions\n")
    for t in tickers:
        if t in decisions:
            lines.append(f"- {t}: {decisions[t]}")
    lines.append("\n## LLM Views (bounded)\n")
    for t in tickers:
        if t in llm_views:
            lines.append(f"- {t}: {llm_views[t]}")
    lines.append("\n## Resizing Summary\n")
    lines.extend(rr_lines[1:])
    lines.append("\n## Risk Parity Reference\n")
    lines.append("```json")
    lines.append(json.dumps(rp, indent=2))
    lines.append("```")
    (out_date_dir / "portfolio_optimizer_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ Saved -> {(out_date_dir / 'portfolio_optimizer_report.md').as_posix()}")


def main():
    parser = argparse.ArgumentParser(description="Run 5 tickers in parallel; single date or sequential date range. Outputs under testing/YYYY-MM-DD/")
    parser.add_argument("date", help="Start date YYYY-MM-DD")
    parser.add_argument("end_date", nargs='?', default=None, help="Optional end date YYYY-MM-DD for sequential runs")
    parser.add_argument("--outdir", default="testing", help="Output directory (default: testing)")
    parser.add_argument("--debug", action="store_true", help="Enable graph debug mode")
    parser.add_argument("--shallow-config", action="store_true", help="Use shallow copy of DEFAULT_CONFIG")
    parser.add_argument("--fail-fast", action="store_true", help="Abort on first error")
    parser.add_argument("--trace", action="store_true", help="Show full tracebacks on errors")
    args = parser.parse_args()

    if args.end_date:
        start_dt = datetime.strptime(args.date, "%Y-%m-%d")
        end_dt = datetime.strptime(args.end_date, "%Y-%m-%d")
        cur = start_dt
        # Build NYSE market calendar and precompute valid trading days
        valid_days = []
        if mcal is not None:
            nyse = mcal.get_calendar('XNYS')
            schedule = nyse.schedule(start_date=start_dt.strftime('%Y-%m-%d'), end_date=end_dt.strftime('%Y-%m-%d'))
            valid_days = [d.strftime('%Y-%m-%d') for d in schedule.index]
        else:
            # Fallback: skip weekends only
            d = start_dt
            while d <= end_dt:
                if d.weekday() < 5:
                    valid_days.append(d.strftime('%Y-%m-%d'))
                d += timedelta(days=1)
        for day in valid_days:
            run_batch5_multithreaded(
                date_str=day,
                out_root=args.outdir,
                debug=args.debug,
                deep_copy_config=not args.shallow_config,
                fail_fast=args.fail_fast,
                show_trace=args.trace,
                reset_portfolio=(day == valid_days[0]),
            )
        # Compute backtest statistics over the range
        compute_backtest_statistics(
            start_date=start_dt.strftime("%Y-%m-%d"),
            end_date=end_dt.strftime("%Y-%m-%d"),
            out_root=args.outdir,
            model_name=DEFAULT_CONFIG.get("quick_think_llm", "unknown-model"),
        )
    else:
        run_batch5_multithreaded(
            date_str=args.date,
            out_root=args.outdir,
            debug=args.debug,
            deep_copy_config=not args.shallow_config,
            fail_fast=args.fail_fast,
            show_trace=args.trace,
        )


def compute_backtest_statistics(start_date: str, end_date: str, out_root: str, model_name: str = "unknown-model") -> None:
    """Compute per-day and rolling performance metrics from daily snapshots.

    Metrics per day:
    - daily_return
    - cumulative_return (from first day)
    - drawdown (relative to running peak)
    - sharpe_per_day (standalone)
    - sortino_per_day (standalone)
    - calmar_per_day (standalone: daily_return / max(drawdown, eps))

    Rolling (from start to that day):
    - rolling_sharpe
    - rolling_sortino
    - rolling_calmar (cum_return / max_drawdown_so_far)

    Output file: testing/[model][start]-[end]-statistics.json
    """
    def daterange(d0: datetime, d1: datetime) -> List[str]:
        days = (d1 - d0).days
        return [(d0 + timedelta(n)).strftime("%Y-%m-%d") for n in range(days + 1)]

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    days = daterange(start_dt, end_dt)

    # Load daily portfolio values from snapshots
    values: Dict[str, float] = {}
    for d in days:
        snap_path = Path(out_root) / d / f"portfolio_snapshot_{d}.json"
        if not snap_path.exists():
            continue
        try:
            data = json.loads(snap_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        portfolio = data.get("portfolio", {}) if isinstance(data.get("portfolio"), dict) else {}
        liquid = float(data.get("liquid", 0.0) or 0.0)
        total = liquid
        for t, info in portfolio.items():
            qty = float(info.get("totalAmount", 0.0) or 0.0)
            px = float(info.get("last_price", 0.0) or 0.0)
            total += qty * px
        values[d] = total

    # Compute daily returns
    ordered_days = [d for d in days if d in values]
    if not ordered_days:
        return
    ordered_days.sort()
    first_val = values[ordered_days[0]]
    eps = 1e-9
    daily_returns: Dict[str, float] = {}
    cumulative_returns: Dict[str, float] = {}
    running_peak = -float("inf")
    drawdowns: Dict[str, float] = {}

    prev_val = None
    for d in ordered_days:
        val = values[d]
        if prev_val is None or prev_val == 0:
            r = 0.0
        else:
            r = (val - prev_val) / (prev_val + eps)
        daily_returns[d] = r
        cum = (val - first_val) / (first_val + eps)
        cumulative_returns[d] = cum
        running_peak = max(running_peak, val)
        dd = 0.0 if running_peak <= 0 else (val - running_peak) / (running_peak + eps)
        drawdowns[d] = dd
        prev_val = val

    # Rolling metrics
    rolling_sharpe: Dict[str, float] = {}
    rolling_sortino: Dict[str, float] = {}
    rolling_calmar: Dict[str, float] = {}

    series: List[float] = []
    for i, d in enumerate(ordered_days):
        r = daily_returns[d]
        series.append(r)
        mean_r = sum(series) / max(len(series), 1)
        var_r = sum((x - mean_r) ** 2 for x in series) / max(len(series) - 1, 1)
        std_r = (var_r ** 0.5) if var_r > 0 else 0.0
        negs = [min(x, 0.0) for x in series]
        if any(negs):
            mean_down = sum((x) ** 2 for x in negs) / max(len([x for x in negs if x < 0]), 1)
            down_dev = (abs(mean_down) ** 0.5)
        else:
            down_dev = 0.0

        rolling_sharpe[d] = mean_r / (std_r + eps)
        rolling_sortino[d] = mean_r / (down_dev + eps)
        # Rolling calmar uses cumulative return and max drawdown so far
        max_dd_so_far = min(drawdowns[x] for x in ordered_days[: i + 1]) if i >= 0 else 0.0
        rolling_calmar[d] = cumulative_returns[d] / (abs(max_dd_so_far) + eps)

        # Update each day's snapshot with rolling metrics
        try:
            snap_path = Path(out_root) / d / f"portfolio_snapshot_{d}.json"
            if snap_path.exists():
                snap = json.loads(snap_path.read_text(encoding="utf-8"))
                # Compute portfolio value and add metrics
                portfolio = snap.get("portfolio", {}) if isinstance(snap.get("portfolio"), dict) else {}
                liquid = float(snap.get("liquid", 0.0) or 0.0)
                total_val = liquid
                for t, info in portfolio.items():
                    qty = float(info.get("totalAmount", 0.0) or 0.0)
                    px = float(info.get("last_price", 0.0) or 0.0)
                    total_val += qty * px
                prev_val_local = values.get(ordered_days[i-1]) if i > 0 else None
                day_ret = 0.0 if not prev_val_local or prev_val_local == 0 else (total_val - prev_val_local) / (prev_val_local + eps)
                snap["portfolio_value"] = total_val
                snap["cash"] = liquid
                snap["buying_power"] = liquid
                snap["daily_return"] = day_ret
                snap["cumulative_return"] = cumulative_returns[d]
                snap["drawdown"] = drawdowns[d]
                snap["rolling_sharpe"] = rolling_sharpe[d]
                snap["rolling_sortino"] = rolling_sortino[d]
                snap["rolling_calmar"] = rolling_calmar[d]
                snap_path.write_text(json.dumps(snap, indent=2), encoding="utf-8")
        except Exception:
            pass

    # Summary
    total_return = cumulative_returns[ordered_days[-1]]
    max_drawdown = min(drawdowns.values()) if drawdowns else 0.0
    summary = {
        "start_date": ordered_days[0],
        "end_date": ordered_days[-1],
        "total_return": total_return,
        "max_drawdown": max_drawdown,
        "final_rolling_sharpe": rolling_sharpe[ordered_days[-1]],
        "final_rolling_sortino": rolling_sortino[ordered_days[-1]],
        "final_rolling_calmar": rolling_calmar[ordered_days[-1]],
    }

    # Update top-level portfolio.json with rolling summary
    try:
        portfolio_json = Path("testing/portfolio.json").resolve()
        if portfolio_json.exists():
            port = json.loads(portfolio_json.read_text(encoding="utf-8"))
            port["metrics"] = {
                "as_of": ordered_days[-1],
                "total_return": total_return,
                "max_drawdown": max_drawdown,
                "rolling_sharpe": rolling_sharpe[ordered_days[-1]],
                "rolling_sortino": rolling_sortino[ordered_days[-1]],
                "rolling_calmar": rolling_calmar[ordered_days[-1]],
            }
            portfolio_json.write_text(json.dumps(port, indent=2), encoding="utf-8")
    except Exception:
        pass

    stats = {
        "model": model_name,
        "summary": summary,
    }

    stats_name = f"{model_name}[{ordered_days[0]}]-[{ordered_days[-1]}]-statistics.json"
    stats_path = Path(out_root) / stats_name
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"✅ Backtest statistics saved -> {stats_path.as_posix()}")


if __name__ == "__main__":
    main()


