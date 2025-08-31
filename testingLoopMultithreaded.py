import argparse
import copy
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.agents.utils.agent_utils import Toolkit
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

    # Consolidated portfolio optimization based on decisions
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
    lines.append("\n## Suggested Weights (normalized from decisions)\n")
    for t, w in weights.items():
        lines.append(f"- {t}: {w}")
    lines.append("\n## Risk Parity Reference\n")
    lines.append("```json")
    lines.append(json.dumps(rp, indent=2))
    lines.append("```")
    (out_date_dir / "portfolio_optimizer_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ Saved -> {(out_date_dir / 'portfolio_optimizer_report.md').as_posix()}")


def main():
    parser = argparse.ArgumentParser(description="Run 5 tickers in parallel for a single date; write outputs under testing/YYYY-MM-DD/")
    parser.add_argument("date", help="Single date YYYY-MM-DD")
    parser.add_argument("--outdir", default="testing", help="Output directory (default: testing)")
    parser.add_argument("--debug", action="store_true", help="Enable graph debug mode")
    parser.add_argument("--shallow-config", action="store_true", help="Use shallow copy of DEFAULT_CONFIG")
    parser.add_argument("--fail-fast", action="store_true", help="Abort on first error")
    parser.add_argument("--trace", action="store_true", help="Show full tracebacks on errors")
    args = parser.parse_args()

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


