#!/usr/bin/env python3
"""
Basic test script for the multi-ticker portfolio system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_basic_imports():
    """Test basic imports to ensure no syntax errors."""
    try:
        from tradingagents.blackboard.schema import (
            PORTFOLIO_ANALYSIS, CROSS_TICKER_CORRELATION, 
            PORTFOLIO_BALANCE, SECTOR_ANALYSIS
        )
        print("✅ Blackboard schema imports successful")
        
        from tradingagents.blackboard.utils import create_agent_blackboard
        print("✅ Blackboard utils imports successful")
        
        from tradingagents.agents.managers.multi_ticker_portfolio_optimizer import create_multi_ticker_portfolio_optimizer
        print("✅ Multi-ticker portfolio optimizer imports successful")
        
        from tradingagents.graph.propagation import Propagator
        print("✅ Propagator imports successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_portfolio_state_creation():
    """Test portfolio state creation."""
    try:
        from tradingagents.graph.propagation import Propagator
        
        propagator = Propagator()
        tickers = ["AAPL", "MSFT", "GOOGL"]
        portfolio_state = propagator.create_portfolio_state(tickers, "2024-12-20")
        
        # Check if required keys exist
        required_keys = ["tickers", "trade_date", "individual_reports", "portfolio_analysis_state"]
        for key in required_keys:
            if key not in portfolio_state:
                print(f"❌ Missing key in portfolio state: {key}")
                return False
        
        # Check if individual reports are created for each ticker
        for ticker in tickers:
            if ticker not in portfolio_state["individual_reports"]:
                print(f"❌ Missing individual report for ticker: {ticker}")
                return False
        
        print("✅ Portfolio state creation successful")
        return True
        
    except Exception as e:
        print(f"❌ Portfolio state creation failed: {e}")
        return False

def test_blackboard_agent_creation():
    """Test blackboard agent creation and basic methods."""
    try:
        from tradingagents.blackboard.utils import create_agent_blackboard
        
        agent = create_agent_blackboard("test", "TestAgent")
        
        # Test basic posting methods
        message_id = agent.post_portfolio_analysis(
            tickers=["AAPL", "MSFT"],
            analysis={"test": "data"},
            confidence="High"
        )
        
        if not message_id:
            print("❌ Failed to post portfolio analysis")
            return False
        
        print("✅ Blackboard agent creation and basic methods successful")
        return True
        
    except Exception as e:
        print(f"❌ Blackboard agent test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Running Basic Multi-Ticker System Tests")
    print("=" * 50)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Portfolio State Creation", test_portfolio_state_creation),
        ("Blackboard Agent Creation", test_blackboard_agent_creation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} passed")
        else:
            print(f"❌ {test_name} failed")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Multi-ticker system is working at basic level.")
        return True
    else:
        print("⚠️ Some tests failed. Check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 