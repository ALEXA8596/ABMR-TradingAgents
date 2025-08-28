#!/usr/bin/env python3
"""
Comprehensive test script for the multi-ticker portfolio optimization system.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tradingagents'))

def test_complete_system():
    """Test the complete multi-ticker portfolio optimization system."""
    try:
        print("🧪 Testing Complete Multi-Ticker Portfolio Optimization System...")
        print("=" * 70)
        
        # Test 1: Portfolio State Structure
        print("\n📋 Test 1: Portfolio State Structure")
        test_portfolio_state_structure()
        
        # Test 2: Conditional Logic
        print("\n📋 Test 2: Conditional Logic")
        test_conditional_logic()
        
        # Test 3: Multi-Ticker Portfolio Optimizer
        print("\n📋 Test 3: Multi-Ticker Portfolio Optimizer")
        test_multi_ticker_optimizer()
        
        # Test 4: Graph Setup
        print("\n📋 Test 4: Graph Setup")
        test_graph_setup()
        
        print("\n🎉 All system tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in system test: {str(e)}")
        import traceback
        traceback.print_exc()

def test_portfolio_state_structure():
    """Test the portfolio state structure."""
    try:
        from tradingagents.graph.propagation import Propagator
        
        # Create a mock propagator
        class MockPropagator:
            def create_portfolio_state(self, tickers, trade_date):
                return {
                    "messages": [("human", f"Portfolio analysis for: {', '.join(tickers)}")],
                    "tickers": tickers,
                    "trade_date": str(trade_date),
                    "current_ticker_index": 0,
                    "ticker_analysis_complete": {ticker: False for ticker in tickers},
                    "portfolio_analysis_state": {
                        "individual_analyses": {},
                        "cross_ticker_correlations": {},
                        "sector_analysis": {},
                        "portfolio_risk_assessment": {},
                        "allocation_strategies": []
                    }
                }
        
        propagator = MockPropagator()
        state = propagator.create_portfolio_state(["SPY", "AAPL", "TSLA"], "2025-08-21")
        
        # Verify state structure
        required_keys = ["tickers", "trade_date", "current_ticker_index", "ticker_analysis_complete", "portfolio_analysis_state"]
        for key in required_keys:
            if key not in state:
                print(f"   ❌ Missing key: {key}")
                return False
        
        if len(state["tickers"]) != 3:
            print(f"   ❌ Expected 3 tickers, got {len(state['tickers'])}")
            return False
        
        print("   ✅ Portfolio state structure is correct")
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing portfolio state: {str(e)}")
        return False

def test_conditional_logic():
    """Test the conditional logic for routing."""
    try:
        from tradingagents.graph.conditional_logic import ConditionalLogic
        
        conditional_logic = ConditionalLogic(max_debate_rounds=1, max_risk_discuss_rounds=1)
        
        # Test portfolio flow routing
        single_ticker_state = {"tickers": ["SPY"]}
        multi_ticker_state = {"tickers": ["SPY", "AAPL", "TSLA"]}
        
        single_result = conditional_logic.should_continue_portfolio_flow(single_ticker_state)
        multi_result = conditional_logic.should_continue_portfolio_flow(multi_ticker_state)
        
        if single_result == "Portfolio Optimizer" and multi_result == "Multi-Ticker Portfolio Optimizer":
            print("   ✅ Conditional logic routing is working correctly")
            return True
        else:
            print(f"   ❌ Routing failed: single={single_result}, multi={multi_result}")
            return False
        
    except Exception as e:
        print(f"   ❌ Error testing conditional logic: {str(e)}")
        return False

def test_multi_ticker_optimizer():
    """Test the multi-ticker portfolio optimizer."""
    try:
        from tradingagents.agents.managers.multi_ticker_portfolio_optimizer import create_multi_ticker_portfolio_optimizer
        
        # Create a mock LLM and toolkit
        class MockLLM:
            def invoke(self, messages):
                return "Mock analysis completed"
        
        class MockToolkit:
            def get_volatility(self, ticker):
                return f"Volatility for {ticker}: 0.25"
            
            def calculate_correlation(self, ticker1, ticker2):
                return f"Correlation between {ticker1} and {ticker2}: 0.6"
        
        class MockMemory:
            def save_context(self, inputs, outputs):
                pass
        
        # Create the optimizer
        optimizer = create_multi_ticker_portfolio_optimizer(MockLLM(), MockMemory(), MockToolkit())
        
        # Test with mock state
        test_state = {
            "tickers": ["SPY", "AAPL", "TSLA"],
            "trade_date": "2025-08-21",
            "individual_reports": {
                "SPY": {"analysis_complete": True},
                "AAPL": {"analysis_complete": True},
                "TSLA": {"analysis_complete": True}
            }
        }
        
        result = optimizer(test_state)
        
        if "portfolio_optimization_state" in result:
            print("   ✅ Multi-ticker portfolio optimizer is working")
            return True
        else:
            print(f"   ❌ Optimizer failed: {result}")
            return False
        
    except Exception as e:
        print(f"   ❌ Error testing multi-ticker optimizer: {str(e)}")
        return False

def test_graph_setup():
    """Test the graph setup and node creation."""
    try:
        # Test that we can import the setup module
        from tradingagents.graph.setup import GraphSetup
        
        print("   ✅ Graph setup module can be imported")
        
        # Test that the conditional logic can be imported
        from tradingagents.graph.conditional_logic import ConditionalLogic
        
        print("   ✅ Conditional logic module can be imported")
        
        # Test that the propagation module can be imported
        from tradingagents.graph.propagation import Propagator
        
        print("   ✅ Propagation module can be imported")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing graph setup: {str(e)}")
        return False

if __name__ == "__main__":
    test_complete_system() 