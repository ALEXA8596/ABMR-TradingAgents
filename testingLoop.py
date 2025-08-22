import argparse
from datetime import datetime, timedelta
from pathlib import Path

from tradingagents.graph.trading_graph import TradingAgentsGraph  # [`tradingagents.graph.trading_graph.TradingAgentsGraph`](tradingagents/graph/trading_graph.py)
from tradingagents.default_config import DEFAULT_CONFIG  # existing config module

def daterange(start: datetime, end: datetime):
    for n in range(int((end - start).days) + 1):
        yield start + timedelta(n)

def run_range(ticker: str, start_date: str, end_date: str, outdir: str = "results", debug: bool = False):
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    out_path = Path(outdir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Instantiate graph once
    graph = TradingAgentsGraph(debug=debug, config=DEFAULT_CONFIG.copy())

    for current in daterange(start_dt, end_dt):
        day_str = current.strftime("%Y-%m-%d")
        fname = f"{ticker.upper()}_{day_str}.txt"
        fpath = out_path / fname
        if fpath.exists():
            print(f"⏭️  Skip {day_str} (exists: {fpath})")
            continue

        print(f"🚀 Running agents for {ticker} on {day_str}")
        try:
            final_state, final_decision = graph.propagate(ticker, day_str)
        except Exception as e:
            print(f"❌ Error on {day_str}: {e}")
            continue

        # Fallback if decision not a simple string
        if not isinstance(final_decision, str):
            final_decision = str(final_decision)

        content = (
            f"TICKER: {ticker.upper()}\nDATE: {day_str}\n"
            f"DECISION: {final_decision}\n"
        )
        try:
            fpath.write_text(content, encoding="utf-8")
            print(f"✅ Saved decision -> {fpath}")
        except Exception as e:
            print(f"❌ Failed to write {fpath}: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Run trading agents over a date range and persist decisions as TICKER_DATE.txt files."
    )
    parser.add_argument("ticker", help="Ticker symbol (e.g. AAPL)")
    parser.add_argument("start_date", help="Start date YYYY-MM-DD")
    parser.add_argument("end_date", help="End date YYYY-MM-DD")
    parser.add_argument("--outdir", default="evalRes", help="Output directory (default: evalRes)")
    parser.add_argument("--debug", action="store_true", help="Enable graph debug mode")
    args = parser.parse_args()

    run_range(args.ticker, args.start_date, args.end_date, args.outdir, args.debug)

if __name__ == "__main__":
    main()