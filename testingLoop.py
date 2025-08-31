import argparse
import copy
import traceback
from datetime import datetime, timedelta
from pathlib import Path

from tradingagents.graph.trading_graph import TradingAgentsGraph  # [`tradingagents.graph.trading_graph.TradingAgentsGraph`](tradingagents/graph/trading_graph.py)
from tradingagents.default_config import DEFAULT_CONFIG  # [`DEFAULT_CONFIG`](tradingagents/default_config.py)
import dotenv

dotenv.load_dotenv()

def daterange(start: datetime, end: datetime):
    days = (end - start).days
    for n in range(days + 1):
        yield start + timedelta(n)


def run_range(
    ticker: str,
    start_date: str,
    end_date: str,
    outdir: str = "testing",
    debug: bool = False,
    deep_copy_config: bool = True,
    fail_fast: bool = False,
    show_trace: bool = False,
):
    # Validate dates
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Invalid date format: {e} (expected YYYY-MM-DD)") from e
    if end_dt < start_dt:
        raise ValueError("end_date must be >= start_date")

    out_path = Path(outdir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Start banner
    print(f"🟢 Starting testing run: {ticker.upper()} {start_date} -> {end_date} | outdir={outdir}")

    base_config = copy.deepcopy(DEFAULT_CONFIG) if deep_copy_config else DEFAULT_CONFIG.copy()
    graph = TradingAgentsGraph(debug=debug, config=base_config)

    for current in daterange(start_dt, end_dt):
        day_str = current.strftime("%Y-%m-%d")
        fname = f"{ticker.upper()}_{day_str}.txt"
        fpath = out_path / fname
        if fpath.exists():
            print(f"⏭️  Skip {day_str} (exists)")
            continue

        print(f"🚀 {ticker.upper()} {day_str} starting")
        try:
            final_state, final_decision = graph.propagate(ticker, day_str)
        except KeyboardInterrupt:
            print("🛑 Interrupted by user.")
            break
        except Exception as e:
            print(f"❌ Error {day_str}: {e}")
            if show_trace:
                traceback.print_exc()
            if fail_fast:
                raise
            continue

        decision_str = final_decision if isinstance(final_decision, str) else str(final_decision)

        # Optional: pull rationale and optimizer excerpt if present
        rationale = ""
        optimizer_excerpt = ""
        if isinstance(final_state, dict):
            rationale = final_state.get("final_trade_rationale") or ""
            po = final_state.get("portfolio_optimization_state") or {}
            if isinstance(po, dict):
                exec_info = po.get("execution") or {}
                if exec_info:
                    optimizer_excerpt = f"Optimizer Execution: {exec_info}"

        content_lines = [
            f"TICKER: {ticker.upper()}",
            f"DATE: {day_str}",
            f"DECISION: {decision_str}",
        ]
        if rationale or optimizer_excerpt:
            content_lines.append("RATIONALE:")
            if rationale:
                content_lines.append(rationale)
            if optimizer_excerpt:
                content_lines.append(optimizer_excerpt)
        file_text = "\n".join(content_lines) + "\n"

        try:
            fpath.write_text(file_text, encoding="utf-8")
            print(f"✅ Saved -> {fpath}")
        except Exception as e:
            print(f"❌ Write failed {fpath}: {e}")

        # Optional: reset per-day mutable internal state if API exposed
        reset_fn = getattr(graph, "reset_daily_state", None)
        if callable(reset_fn):
            reset_fn()

    print("🏁 Completed range.")


def main():
    parser = argparse.ArgumentParser(
        description="Run trading agents over a date range; persist decisions as TICKER_DATE.txt."
    )
    parser.add_argument("ticker", help="Ticker symbol (e.g. AAPL)")
    parser.add_argument("start_date", help="Start date YYYY-MM-DD")
    parser.add_argument("end_date", nargs='?', default=None, help="End date YYYY-MM-DD (optional; defaults to start_date)")
    parser.add_argument("--outdir", default="testing", help="Output directory (default: testing)")
    parser.add_argument("--debug", action="store_true", help="Enable graph debug mode")
    parser.add_argument("--shallow-config", action="store_true", help="Use shallow copy of DEFAULT_CONFIG")
    parser.add_argument("--fail-fast", action="store_true", help="Abort on first error")
    parser.add_argument("--trace", action="store_true", help="Show full tracebacks on errors")
    parser.add_argument("--single-day", action="store_true", help="Run for a single day (end_date = start_date)")
    args = parser.parse_args()

    resolved_end_date = args.start_date if (args.single_day or not args.end_date) else args.end_date

    run_range(
        args.ticker,
        args.start_date,
        resolved_end_date,
        args.outdir,
        args.debug,
        deep_copy_config=not args.shallow_config,
        fail_fast=args.fail_fast,
        show_trace=args.trace,
    )


if __name__ == "__main__":
    main()