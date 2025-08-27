#!/usr/bin/env python3
"""
Test script to verify the conditional routing logic for multi-ticker portfolio optimization.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tradingagents'))

def test_portfolio_routing_logic():
    """Test the portfolio routing logic without requiring LLM initialization."""
    try:
        print("🧪 Testing Portfolio Routing Logic...")
        print("=" * 60)
        
        # Import the conditional logic module directly
        from tradingagents.graph.conditional_logic import ConditionalLogic
        
        # Create conditional logic instance
        conditional_logic = ConditionalLogic(max_debate_rounds=1, max_risk_discuss_rounds=1)
        
        # Test 1: Single ticker mode
        print("\n📋 Test 1: Single ticker mode")
        single_ticker_state = {
            "tickers": ["SPY"],
            "messages": [("human", "Analyze SPY")]
        }
        result = conditional_logic.should_continue_portfolio_flow(single_ticker_state)
        print(f"   Input: Single ticker (SPY)")
        print(f"   Expected: Portfolio Optimizer")
        print(f"   Result: {result}")
        print(f"   ✅ PASS" if result == "Portfolio Optimizer" else "   ❌ FAIL")
        
        # Test 2: Multi-ticker mode
        print("\n📋 Test 2: Multi-ticker mode")
        multi_ticker_state = {
            "tickers": ["SPY", "AAPL", "TSLA"],
            "messages": [("human", "Analyze portfolio: SPY, AAPL, TSLA")]
        }
        result = conditional_logic.should_continue_portfolio_flow(multi_ticker_state)
        print(f"   Input: Multi-ticker (SPY, AAPL, TSLA)")
        print(f"   Expected: Multi-Ticker Portfolio Optimizer")
        print(f"   Result: {result}")
        print(f"   ✅ PASS" if result == "Multi-Ticker Portfolio Optimizer" else "   ❌ FAIL")
        
        # Test 3: Empty tickers
        print("\n📋 Test 3: Empty tickers")
        empty_ticker_state = {
            "tickers": [],
            "messages": [("human", "No tickers specified")]
        }
        result = conditional_logic.should_continue_portfolio_flow(empty_ticker_state)
        print(f"   Input: Empty tickers list")
        print(f"   Expected: Portfolio Optimizer")
        print(f"   Result: {result}")
        print(f"   ✅ PASS" if result == "Portfolio Optimizer" else "   ❌ FAIL")
        
        # Test 4: No tickers key
        print("\n📋 Test 4: No tickers key")
        no_tickers_state = {
            "messages": [("human", "No tickers key in state")]
        }
        result = conditional_logic.should_continue_portfolio_flow(no_tickers_state)
        print(f"   Input: No tickers key")
        print(f"   Expected: Portfolio Optimizer")
        print(f"   Result: {result}")
        print(f"   ✅ PASS" if result == "Portfolio Optimizer" else "   ❌ FAIL")
        
        print("\n🎉 All routing logic tests completed!")
        
    except Exception as e:
        print(f"❌ Error testing routing logic: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_portfolio_routing_logic() 