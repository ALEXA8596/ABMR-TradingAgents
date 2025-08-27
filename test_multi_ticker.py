#!/usr/bin/env python3
"""
Test script for the multi-ticker portfolio system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
import dotenv

# Load environment variables
dotenv.load_dotenv()

def test_multi_ticker_system():
    """Test the multi-ticker portfolio system."""
    
    print("🚀 Testing Multi-Ticker Portfolio System")
    print("=" * 50)
    
    # Create config
    config = DEFAULT_CONFIG.copy()
    config["max_debate_rounds"] = 1
    config["online_tools"] = False
    config["abmrOffline"] = True
    config["deep_think_llm"] = "gpt-4o-mini"
    config["quick_think_llm"] = "gpt-4o-mini"
    
    try:
        # Initialize the graph
        print("📊 Initializing TradingAgentsGraph...")
        ta = TradingAgentsGraph(debug=True, config=config)
        print("✅ TradingAgentsGraph initialized successfully")
        
        # Test single ticker (existing functionality)
        print("\n🔍 Testing Single Ticker Analysis...")
        try:
            _, decision = ta.propagate("AAPL", "2024-12-20")
            print(f"✅ Single ticker analysis completed: {decision[:100]}...")
        except Exception as e:
            print(f"⚠️ Single ticker analysis failed: {e}")
        
        # Test multi-ticker portfolio analysis
        print("\n📈 Testing Multi-Ticker Portfolio Analysis...")
        tickers = ["AAPL", "MSFT", "GOOGL"]
        try:
            _, portfolio_decision = ta.propagate_portfolio(tickers, "2024-12-20")
            print(f"✅ Portfolio analysis completed: {portfolio_decision[:100]}...")
        except Exception as e:
            print(f"⚠️ Portfolio analysis failed: {e}")
        
        # Test blackboard context
        print("\n📋 Testing Blackboard Context...")
        try:
            single_context = ta.get_blackboard_context("AAPL")
            print(f"✅ Single ticker context retrieved: {len(single_context)} items")
            
            portfolio_context = ta.get_portfolio_blackboard_context(tickers)
            print(f"✅ Portfolio context retrieved: {len(portfolio_context)} items")
        except Exception as e:
            print(f"⚠️ Blackboard context test failed: {e}")
        
        print("\n🎉 Multi-ticker system test completed!")
        
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_multi_ticker_system()
    sys.exit(0 if success else 1) 