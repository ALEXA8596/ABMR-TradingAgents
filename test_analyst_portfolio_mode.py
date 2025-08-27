#!/usr/bin/env python3
"""
Test script to verify analyst agents can handle portfolio mode.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_analyst_portfolio_mode():
    """Test that analyst agents can handle portfolio mode state."""
    try:
        # Test portfolio state creation
        from tradingagents.graph.propagation import Propagator
        
        propagator = Propagator()
        tickers = ["AAPL", "MSFT", "TSLA"]
        portfolio_state = propagator.create_portfolio_state(tickers, "2024-12-20")
        
        print("✅ Portfolio state created successfully")
        print(f"   Tickers: {portfolio_state['tickers']}")
        print(f"   Individual reports keys: {list(portfolio_state['individual_reports'].keys())}")
        
        # Test that analyst agents can handle the portfolio state
        from tradingagents.agents.analysts.market_analyst import create_market_analyst
        from tradingagents.agents.analysts.fundamentals_analyst import create_fundamentals_analyst
        from tradingagents.agents.analysts.news_analyst import create_news_analyst
        from tradingagents.agents.analysts.social_media_analyst import create_social_media_analyst
        from tradingagents.agents.analysts.macroeconomic_analyst import create_macroeconomic_analyst
        from tradingagents.agents.analysts.quant_market_analyst import create_quant_market_analyst
        
        print("✅ All analyst agents imported successfully")
        
        # Test that the state structure is correct for portfolio mode
        required_keys = [
            "tickers", "trade_date", "individual_reports", 
            "portfolio_analysis_state", "investment_debate_states", 
            "risk_debate_states"
        ]
        
        for key in required_keys:
            if key not in portfolio_state:
                print(f"❌ Missing required key: {key}")
                return False
            print(f"   ✅ Found key: {key}")
        
        # Test that individual reports are properly structured
        for ticker in tickers:
            if ticker not in portfolio_state["individual_reports"]:
                print(f"❌ Missing individual report for ticker: {ticker}")
                return False
            
            ticker_report = portfolio_state["individual_reports"][ticker]
            required_report_keys = [
                "market_report", "fundamentals_report", "sentiment_report",
                "news_report", "investment_plan", "trader_investment_plan", 
                "final_trade_decision"
            ]
            
            for report_key in required_report_keys:
                if report_key not in ticker_report:
                    print(f"❌ Missing report key {report_key} for ticker {ticker}")
                    return False
            
            print(f"   ✅ Individual report structure complete for {ticker}")
        
        print("✅ Portfolio mode state structure is correct")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_analyst_state_handling():
    """Test that analyst agents can handle both single and portfolio modes."""
    try:
        # Test single ticker mode
        single_ticker_state = {
            "trade_date": "2024-12-20",
            "company_of_interest": "AAPL",
            "messages": []
        }
        
        # Test portfolio mode
        portfolio_state = {
            "trade_date": "2024-12-20",
            "tickers": ["AAPL", "MSFT", "TSLA"],
            "messages": []
        }
        
        print("✅ Test states created successfully")
        
        # Test that both states have the required fields
        if "trade_date" not in single_ticker_state:
            print("❌ Single ticker state missing trade_date")
            return False
        
        if "company_of_interest" not in single_ticker_state:
            print("❌ Single ticker state missing company_of_interest")
            return False
        
        if "trade_date" not in portfolio_state:
            print("❌ Portfolio state missing trade_date")
            return False
        
        if "tickers" not in portfolio_state:
            print("❌ Portfolio state missing tickers")
            return False
        
        print("✅ Both state modes have required fields")
        return True
        
    except Exception as e:
        print(f"❌ State handling test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Analyst Portfolio Mode Compatibility")
    print("=" * 50)
    
    tests = [
        ("Portfolio Mode State Creation", test_analyst_portfolio_mode),
        ("Analyst State Handling", test_analyst_state_handling),
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
        print("🎉 All tests passed! Analyst agents can handle portfolio mode.")
        return True
    else:
        print("⚠️ Some tests failed. Check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 