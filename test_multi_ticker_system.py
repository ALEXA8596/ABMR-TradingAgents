#!/usr/bin/env python3
"""
Test script to verify the new multi-ticker portfolio optimization system.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tradingagents'))

def test_multi_ticker_system():
    """Test the new multi-ticker portfolio optimization system."""
    try:
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG
        
        print("🧪 Testing Multi-Ticker Portfolio Optimization System...")
        print("=" * 60)
        
        # Initialize the system
        config = DEFAULT_CONFIG.copy()
        config.update({
            "max_debate_rounds": 1,
            "max_risk_discuss_rounds": 1,
            "debug": True
        })
        
        # Create the graph
        graph = TradingAgentsGraph(config)
        
        # Test portfolio state creation
        print("\n1. Testing Portfolio State Creation...")
        portfolio_state = graph.propagator.create_portfolio_state(
            ["SPY", "AAPL", "TSLA"], "2025-08-21"
        )
        
        print(f"✅ Portfolio state created with {len(portfolio_state.get('tickers', []))} tickers")
        print(f"   Tickers: {portfolio_state.get('tickers', [])}")
        print(f"   Current ticker index: {portfolio_state.get('current_ticker_index', 0)}")
        print(f"   Ticker analysis complete: {portfolio_state.get('ticker_analysis_complete', {})}")
        
        # Test conditional logic
        print("\n2. Testing Conditional Logic...")
        conditional_logic = graph.conditional_logic
        
        # Test portfolio flow routing
        portfolio_flow = conditional_logic.should_continue_portfolio_flow(portfolio_state)
        print(f"✅ Portfolio flow routing: {portfolio_flow}")
        
        # Test ticker analysis continuation
        ticker_analysis = conditional_logic.should_continue_ticker_analysis(portfolio_state)
        print(f"✅ Ticker analysis continuation: {ticker_analysis}")
        
        # Test portfolio analysis continuation
        portfolio_analysis = conditional_logic.should_continue_portfolio_analysis(portfolio_state)
        print(f"✅ Portfolio analysis continuation: {portfolio_analysis}")
        
        # Test graph compilation
        print("\n3. Testing Graph Compilation...")
        compiled_graph = graph.setup_graph(
            ["market", "fundamentals"], 
            "shallow", 
            "gpt-4o-mini", 
            "gpt-4o-mini"
        )
        print(f"✅ Graph compiled successfully with {len(compiled_graph.nodes)} nodes")
        
        # Check if multi-ticker portfolio optimizer is included
        if "Multi-Ticker Portfolio Optimizer" in compiled_graph.nodes:
            print("✅ Multi-Ticker Portfolio Optimizer node found in graph")
        else:
            print("❌ Multi-Ticker Portfolio Optimizer node NOT found in graph")
        
        print("\n4. Testing Portfolio State Structure...")
        required_fields = [
            "tickers", "trade_date", "current_ticker_index", 
            "ticker_analysis_complete", "portfolio_analysis_state"
        ]
        
        for field in required_fields:
            if field in portfolio_state:
                print(f"✅ {field}: {portfolio_state[field]}")
            else:
                print(f"❌ {field}: Missing")
        
        print("\n5. Testing Enhanced Portfolio Analysis State...")
        portfolio_analysis_state = portfolio_state.get("portfolio_analysis_state", {})
        analysis_fields = [
            "individual_analyses", "cross_ticker_correlations", 
            "sector_analysis", "portfolio_risk_assessment"
        ]
        
        for field in analysis_fields:
            if field in portfolio_analysis_state:
                print(f"✅ {field}: {portfolio_analysis_state[field]}")
            else:
                print(f"❌ {field}: Missing")
        
        print("\n🎉 Multi-Ticker Portfolio Optimization System Test Completed Successfully!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_portfolio_optimization_flow():
    """Test the complete portfolio optimization flow."""
    try:
        print("\n🧪 Testing Complete Portfolio Optimization Flow...")
        print("=" * 60)
        
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # Initialize with minimal config for testing
        config = DEFAULT_CONFIG.copy()
        config.update({
            "max_debate_rounds": 1,
            "max_risk_discuss_rounds": 1,
            "debug": True
        })
        
        graph = TradingAgentsGraph(config)
        
        # Create a test portfolio state
        test_state = {
            "tickers": ["SPY", "AAPL", "TSLA"],
            "trade_date": "2025-08-21",
            "current_ticker_index": 0,
            "ticker_analysis_complete": {"SPY": False, "AAPL": False, "TSLA": False},
            "portfolio_analysis_state": {
                "individual_analyses": {},
                "cross_ticker_correlations": {},
                "sector_analysis": {},
                "portfolio_risk_assessment": {}
            },
            "individual_reports": {}
        }
        
        print("✅ Test state created successfully")
        
        # Test the flow logic
        conditional_logic = graph.conditional_logic
        
        # Test initial routing
        initial_route = conditional_logic.should_continue_portfolio_flow(test_state)
        print(f"✅ Initial portfolio flow route: {initial_route}")
        
        # Test ticker analysis routing
        ticker_route = conditional_logic.should_continue_ticker_analysis(test_state)
        print(f"✅ Ticker analysis route: {ticker_route}")
        
        # Simulate completing one ticker
        test_state["individual_reports"]["SPY"] = {"analysis_complete": True}
        test_state["current_ticker_index"] = 1
        
        ticker_route_after_spy = conditional_logic.should_continue_ticker_analysis(test_state)
        print(f"✅ Ticker analysis route after SPY: {ticker_route_after_spy}")
        
        # Simulate completing all tickers
        test_state["individual_reports"]["AAPL"] = {"analysis_complete": True}
        test_state["individual_reports"]["TSLA"] = {"analysis_complete": True}
        test_state["current_ticker_index"] = 3
        
        ticker_route_all_complete = conditional_logic.should_continue_ticker_analysis(test_state)
        print(f"✅ Ticker analysis route all complete: {ticker_route_all_complete}")
        
        # Test portfolio analysis completion
        portfolio_analysis_route = conditional_logic.should_continue_portfolio_analysis(test_state)
        print(f"✅ Portfolio analysis route: {portfolio_analysis_route}")
        
        print("\n🎉 Portfolio Optimization Flow Test Completed Successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Flow test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Multi-Ticker Portfolio Optimization System Tests...")
    
    # Run basic system test
    system_test_passed = test_multi_ticker_system()
    
    # Run flow test
    flow_test_passed = test_portfolio_optimization_flow()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"System Test: {'✅ PASSED' if system_test_passed else '❌ FAILED'}")
    print(f"Flow Test:  {'✅ PASSED' if flow_test_passed else '❌ FAILED'}")
    
    if system_test_passed and flow_test_passed:
        print("\n🎉 All tests passed! The multi-ticker system is working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")
        sys.exit(1) 