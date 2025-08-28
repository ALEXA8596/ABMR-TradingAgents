#!/usr/bin/env python3
"""
Test Simplified Routing Logic
Verify that our streamlined agent flows don't cause infinite loops
"""

from tradingagents.graph.conditional_logic import ConditionalLogic
from tradingagents.agents.utils.agent_states import AgentState

def test_simplified_debate_flow():
    """Test the simplified Bull → Bear → Research Manager flow"""
    print("🧪 Testing Simplified Debate Flow...")
    print("=" * 60)
    
    conditional_logic = ConditionalLogic()
    
    # Test state for multi-ticker portfolio
    test_state = {
        "tickers": ["SPY", "AAPL", "TSLA"],
        "investment_debate_states": {
            "SPY": {
                "count": 0,
                "history": "[]",
                "current_response": "",
                "judge_decision": "",
                "bull_history": "[]",
                "bear_history": "[]"
            }
        }
    }
    
    print("Testing debate flow progression:")
    
    # Test count 0 → should go to Bull Researcher
    result = conditional_logic.should_continue_debate(test_state)
    print(f"✅ Count 0: {result} (Expected: Bull Researcher)")
    assert result == "Bull Researcher", f"Expected Bull Researcher, got {result}"
    
    # Test count 1 → should go to Bear Researcher  
    test_state["investment_debate_states"]["SPY"]["count"] = 1
    result = conditional_logic.should_continue_debate(test_state)
    print(f"✅ Count 1: {result} (Expected: Bear Researcher)")
    assert result == "Bear Researcher", f"Expected Bear Researcher, got {result}"
    
    # Test count 2+ → should go to Research Manager (END CONDITION)
    test_state["investment_debate_states"]["SPY"]["count"] = 2
    result = conditional_logic.should_continue_debate(test_state)
    print(f"✅ Count 2: {result} (Expected: Research Manager)")
    assert result == "Research Manager", f"Expected Research Manager, got {result}"
    
    # Test higher counts → should always go to Research Manager (NO INFINITE LOOP)
    for count in [3, 4, 5, 10, 50, 100]:
        test_state["investment_debate_states"]["SPY"]["count"] = count
        result = conditional_logic.should_continue_debate(test_state)
        print(f"✅ Count {count}: {result} (Expected: Research Manager)")
        assert result == "Research Manager", f"Expected Research Manager, got {result}"
    
    print("\n🎉 Debate Flow Test PASSED - No infinite loop risk!")
    return True

def test_simplified_risk_analysis_flow():
    """Test the simplified Risky → Safe → Risk Judge flow"""
    print("\n🧪 Testing Simplified Risk Analysis Flow...")
    print("=" * 60)
    
    conditional_logic = ConditionalLogic()
    
    # Test state for risk analysis
    test_state = {
        "tickers": ["SPY"],
        "risk_debate_states": {
            "SPY": {
                "count": 0,
                "history": "[]",
                "current_risky_response": "",
                "current_safe_response": "",
                "latest_speaker": "",
                "judge_decision": ""
            }
        }
    }
    
    print("Testing risk analysis flow progression:")
    
    # Test count 0 → should go to Risky Analyst
    result = conditional_logic.should_continue_risk_analysis(test_state)
    print(f"✅ Count 0: {result} (Expected: Risky Analyst)")
    assert result == "Risky Analyst", f"Expected Risky Analyst, got {result}"
    
    # Test count 1 → should go to Safe Analyst
    test_state["risk_debate_states"]["SPY"]["count"] = 1
    result = conditional_logic.should_continue_risk_analysis(test_state)
    print(f"✅ Count 1: {result} (Expected: Safe Analyst)")
    assert result == "Safe Analyst", f"Expected Safe Analyst, got {result}"
    
    # Test count 2+ → should go to Risk Judge (END CONDITION)
    test_state["risk_debate_states"]["SPY"]["count"] = 2
    result = conditional_logic.should_continue_risk_analysis(test_state)
    print(f"✅ Count 2: {result} (Expected: Risk Judge)")
    assert result == "Risk Judge", f"Expected Risk Judge, got {result}"
    
    # Test higher counts → should always go to Risk Judge (NO INFINITE LOOP)
    for count in [3, 4, 5, 10, 50, 100]:
        test_state["risk_debate_states"]["SPY"]["count"] = count
        result = conditional_logic.should_continue_risk_analysis(test_state)
        print(f"✅ Count {count}: {result} (Expected: Risk Judge)")
        assert result == "Risk Judge", f"Expected Risk Judge, got {result}"
    
    print("\n🎉 Risk Analysis Flow Test PASSED - No infinite loop risk!")
    return True

def test_no_recursion_risk():
    """Test that we can't hit recursion limits with simplified logic"""
    print("\n🧪 Testing Recursion Limit Protection...")
    print("=" * 60)
    
    conditional_logic = ConditionalLogic()
    
    # Simulate extreme count scenarios that previously caused recursion
    extreme_counts = [100, 200, 500, 1000]
    
    for count in extreme_counts:
        # Test debate flow
        debate_state = {
            "tickers": ["SPY"],
            "investment_debate_states": {
                "SPY": {"count": count}
            }
        }
        result = conditional_logic.should_continue_debate(debate_state)
        print(f"✅ Debate at count {count}: {result} (Always terminates)")
        assert result == "Research Manager", f"Should always terminate at Research Manager"
        
        # Test risk analysis flow  
        risk_state = {
            "tickers": ["SPY"],
            "risk_debate_states": {
                "SPY": {"count": count}
            }
        }
        result = conditional_logic.should_continue_risk_analysis(risk_state)
        print(f"✅ Risk analysis at count {count}: {result} (Always terminates)")
        assert result == "Risk Judge", f"Should always terminate at Risk Judge"
    
    print("\n🎉 Recursion Protection Test PASSED - No recursion risk even at extreme counts!")
    return True

def main():
    """Run all simplified routing tests"""
    print("🚀 Testing Simplified Agent Routing Logic")
    print("=" * 80)
    print("This test verifies that our streamlined flows prevent infinite loops")
    print("and eliminate the GraphRecursionError issue.\n")
    
    try:
        # Run all tests
        test_simplified_debate_flow()
        test_simplified_risk_analysis_flow() 
        test_no_recursion_risk()
        
        print("\n" + "=" * 80)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Simplified routing logic working correctly")
        print("✅ No infinite loop risks detected")
        print("✅ GraphRecursionError should be RESOLVED!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 