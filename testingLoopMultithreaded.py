import argparse
import copy
import json
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Tuple
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

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
            rationale = final_state.get("final_trade_rationale") or ""
            po = final_state.get("portfolio_optimization_state") or {}
            if isinstance(po, dict):
                exec_info = po.get("execution") or {}
                if exec_info:
                    rationale = (rationale + "\n" if rationale else "") + f"Optimizer Execution: {exec_info}"
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
    with GRAPH_INIT_LOCK:
        graph = TradingAgentsGraph(debug=debug, config=config)
    print(f"🚀 {ticker} {date_str} starting")
    final_state, final_decision = graph.propagate(ticker, date_str)
    action, rationale = _extract_action_and_rationale(final_state, final_decision)
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
):
    tickers = ["AAPL", "AMZN", "GOOG", "META", "NVDA"]
    out_date_dir = Path(out_root) / date_str
    out_date_dir.mkdir(parents=True, exist_ok=True)

    base_config = copy.deepcopy(DEFAULT_CONFIG) if deep_copy_config else DEFAULT_CONFIG.copy()
    print(f"🟢 Starting multithreaded batch-5 run for {date_str}: {', '.join(tickers)} | outdir={out_date_dir}")
    t0 = time.time()

    # Reset portfolio for this run (positions-only schema)
    portfolio_path = (Path.cwd() / "testing" / "portfolio.json").resolve()
    portfolio_path.parent.mkdir(parents=True, exist_ok=True)
    with open(portfolio_path, 'w') as f:
        json.dump({"portfolio": {}, "liquid": 100000}, f, indent=2)

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
                    hist = yf.Ticker(t).history(period="1d")
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
    for sym, tr in (trades or {}).items():
        price = float(tr.get("price", 0.0) or 0.0)
        if price <= 0:
            continue
        delta = int(tr.get("delta_shares", 0))
        holdings = data["portfolio"].get(sym, {"totalAmount": 0})
        if delta > 0:
            max_affordable = int((float(data.get("liquid", 0.0)) // price))
            buy_qty = min(delta, max_affordable)
            if buy_qty > 0:
                cost = buy_qty * price
                holdings["totalAmount"] = int(holdings.get("totalAmount", 0)) + buy_qty
                holdings["last_price"] = price
                data["liquid"] = float(data.get("liquid", 0.0)) - cost
        elif delta < 0:
            sell_qty = abs(delta)
            current_qty = int(holdings.get("totalAmount", 0))
            holdings["totalAmount"] = current_qty - sell_qty
            proceeds = sell_qty * price
            holdings["last_price"] = price
            data["liquid"] = float(data.get("liquid", 0.0)) + proceeds
        else:
            # HOLD: update last_price only
            holdings["last_price"] = price
        data["portfolio"][sym] = holdings
    with open(portfolio_path, 'w') as f:
        json.dump(data, f, indent=2)

    # Snapshot now
    snap_path = out_date_dir / f"portfolio_snapshot_{date_str}.json"
    with open(snap_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"📸 Portfolio snapshot saved -> {snap_path.as_posix()}")

    # Consolidated portfolio optimization based on decisions (summary)
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
        while cur <= end_dt:
            day = cur.strftime("%Y-%m-%d")
            run_batch5_multithreaded(
                date_str=day,
                out_root=args.outdir,
                debug=args.debug,
                deep_copy_config=not args.shallow_config,
                fail_fast=args.fail_fast,
                show_trace=args.trace,
            )
            cur += timedelta(days=1)
    else:
        run_batch5_multithreaded(
            date_str=args.date,
            out_root=args.outdir,
            debug=args.debug,
            deep_copy_config=not args.shallow_config,
            fail_fast=args.fail_fast,
            show_trace=args.trace,
        )


if __name__ == "__main__":
    main()


