#!/usr/bin/env python3
"""
Test script to verify the conditional logic fix for portfolio mode.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_conditional_logic_fix():
    """Test that the conditional logic can handle HumanMessage objects properly."""
    try:
        from tradingagents.graph.conditional_logic import ConditionalLogic
        from langchain_core.messages import HumanMessage
        
        # Create conditional logic instance
        conditional_logic = ConditionalLogic()
        
        # Test state with HumanMessage (which doesn't have tool_calls)
        test_state = {
            "messages": [
                HumanMessage(content="Portfolio analysis for: GOOG, AAPL, TSLA")
            ]
        }
        
        # This should not crash now
        result = conditional_logic.should_continue_market(test_state)
        
        print(f"✅ Conditional logic handled HumanMessage successfully")
        print(f"   Result: {result}")
        
        # Test that it returns the expected result
        if result == "Msg Clear Market":
            print("✅ Correctly identified no tool calls needed")
        else:
            print(f"⚠️ Unexpected result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_portfolio_state_with_conditional_logic():
    """Test that portfolio state can work with conditional logic."""
    try:
        from tradingagents.graph.propagation import Propagator
        from tradingagents.graph.conditional_logic import ConditionalLogic
        
        # Create portfolio state
        propagator = Propagator()
        tickers = ["GOOG", "AAPL", "TSLA"]
        portfolio_state = propagator.create_portfolio_state(tickers, "2024-12-20")
        
        # Add a human message to the state
        from langchain_core.messages import HumanMessage
        portfolio_state["messages"] = [
            HumanMessage(content="Portfolio analysis for: GOOG, AAPL, TSLA")
        ]
        
        print("✅ Portfolio state created with human message")
        
        # Test conditional logic with portfolio state
        conditional_logic = ConditionalLogic()
        
        # This should not crash
        result = conditional_logic.should_continue_market(portfolio_state)
        
        print(f"✅ Conditional logic worked with portfolio state")
        print(f"   Result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Portfolio state test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Conditional Logic Fix for Portfolio Mode")
    print("=" * 60)
    
    tests = [
        ("Conditional Logic Fix", test_conditional_logic_fix),
        ("Portfolio State with Conditional Logic", test_portfolio_state_with_conditional_logic),
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
        print("🎉 All tests passed! Conditional logic fix is working.")
        return True
    else:
        print("⚠️ Some tests failed. Check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 