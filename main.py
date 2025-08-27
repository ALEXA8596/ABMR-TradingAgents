from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
import os
import dotenv

# Load environment variables from a .env file
dotenv.load_dotenv()

# Create a custom config
config = DEFAULT_CONFIG.copy()
config["max_debate_rounds"] = 1  # Increase debate rounds
config["online_tools"] = False
config["abmrOffline"] = True
config["deep_think_llm"] = "gpt-4.1-nano"
config["quick_think_llm"] = "gpt-4o-mini" 

# Initialize with custom config
ta = TradingAgentsGraph(debug=True, config=config)

# Example 1: Single ticker analysis (existing functionality)
print("=== Single Ticker Analysis ===")
_, decision = ta.propagate("AAPL", "2025-07-10")
print(f"Single ticker decision: {decision}")

# Example 2: Multi-ticker portfolio analysis (new functionality)
print("\n=== Multi-Ticker Portfolio Analysis ===")
tickers = ["AAPL", "MSFT", "GOOGL"]
_, portfolio_decision = ta.propagate_portfolio(tickers, "2025-07-10")
print(f"Portfolio decision for {', '.join(tickers)}: {portfolio_decision}")

# Example 3: Larger portfolio analysis
print("\n=== Larger Portfolio Analysis ===")
larger_portfolio = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"]
_, larger_portfolio_decision = ta.propagate_portfolio(larger_portfolio, "2025-07-10")
print(f"Larger portfolio decision: {larger_portfolio_decision}")

# Memorize mistakes and reflect
# ta.reflect_and_remember(1000) # parameter is the position returns
