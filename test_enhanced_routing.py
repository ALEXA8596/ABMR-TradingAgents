#!/usr/bin/env python3
"""
Test Enhanced Routing Logic with Restored Agents
Verify that our enhanced flows (with crossex and neutral) still prevent infinite loops
"""

from tradingagents.graph.conditional_logic import ConditionalLogic

def test_enhanced_debate_flow():
    """Test the enhanced Bull → Bear → Bull Crossex → Bear Crossex → Research Manager flow"""
    print("🧪 Testing Enhanced Debate Flow...")
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
    
    print("Testing enhanced debate flow progression:")
    
    # Test count 0 → should go to Bull Researcher
    result = conditional_logic.should_continue_debate(test_state)
    print(f"✅ Count 0: {result} (Expected: Bull Researcher)")
    assert result == "Bull Researcher", f"Expected Bull Researcher, got {result}"
    
    # Test count 1 → should go to Bear Researcher  
    test_state["investment_debate_states"]["SPY"]["count"] = 1
    result = conditional_logic.should_continue_debate(test_state)
    print(f"✅ Count 1: {result} (Expected: Bear Researcher)")
    assert result == "Bear Researcher", f"Expected Bear Researcher, got {result}"
    
    # Test count 2 → should go to Bull Crossex Researcher (RESTORED)
    test_state["investment_debate_states"]["SPY"]["count"] = 2
    result = conditional_logic.should_continue_debate(test_state)
    print(f"✅ Count 2: {result} (Expected: Bull Crossex Researcher)")
    assert result == "Bull Crossex Researcher", f"Expected Bull Crossex Researcher, got {result}"
    
    # Test count 3 → should go to Bear Crossex Researcher (RESTORED)
    test_state["investment_debate_states"]["SPY"]["count"] = 3
    result = conditional_logic.should_continue_debate(test_state)
    print(f"✅ Count 3: {result} (Expected: Bear Crossex Researcher)")
    assert result == "Bear Crossex Researcher", f"Expected Bear Crossex Researcher, got {result}"
    
    # Test count 4+ → should go to Research Manager (END CONDITION)
    test_state["investment_debate_states"]["SPY"]["count"] = 4
    result = conditional_logic.should_continue_debate(test_state)
    print(f"✅ Count 4: {result} (Expected: Research Manager)")
    assert result == "Research Manager", f"Expected Research Manager, got {result}"
    
    # Test higher counts → should always go to Research Manager (NO INFINITE LOOP)
    for count in [5, 10, 50, 100]:
        test_state["investment_debate_states"]["SPY"]["count"] = count
        result = conditional_logic.should_continue_debate(test_state)
        print(f"✅ Count {count}: {result} (Expected: Research Manager)")
        assert result == "Research Manager", f"Expected Research Manager, got {result}"
    
    print("\n🎉 Enhanced Debate Flow Test PASSED - No infinite loop risk!")
    return True

def test_enhanced_risk_analysis_flow():
    """Test the enhanced Risky → Safe → Neutral → Risk Judge flow"""
    print("\n🧪 Testing Enhanced Risk Analysis Flow...")
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
                "current_neutral_response": "",  # RESTORED
                "latest_speaker": "",
                "judge_decision": ""
            }
        }
    }
    
    print("Testing enhanced risk analysis flow progression:")
    
    # Test count 0 → currently at Risky Analyst, should go to Safe Analyst
    result = conditional_logic.should_continue_risk_analysis(test_state)
    print(f"✅ Count 0 (at Risky Analyst): {result} (Expected: Safe Analyst)")
    assert result == "Safe Analyst", f"Expected Safe Analyst, got {result}"
    
    # Test count 1 → currently at Safe Analyst, should go to Neutral Analyst
    test_state["risk_debate_states"]["SPY"]["count"] = 1
    result = conditional_logic.should_continue_risk_analysis(test_state)
    print(f"✅ Count 1 (at Safe Analyst): {result} (Expected: Neutral Analyst)")
    assert result == "Neutral Analyst", f"Expected Neutral Analyst, got {result}"
    
    # Test count 2 → currently at Neutral Analyst, should go to Risk Judge
    test_state["risk_debate_states"]["SPY"]["count"] = 2
    result = conditional_logic.should_continue_risk_analysis(test_state)
    print(f"✅ Count 2 (at Neutral Analyst): {result} (Expected: Risk Judge)")
    assert result == "Risk Judge", f"Expected Risk Judge, got {result}"
    
    # Test count 3+ → should go to Risk Judge (END CONDITION)
    test_state["risk_debate_states"]["SPY"]["count"] = 3
    result = conditional_logic.should_continue_risk_analysis(test_state)
    print(f"✅ Count 3+ (termination): {result} (Expected: Risk Judge)")
    assert result == "Risk Judge", f"Expected Risk Judge, got {result}"
    
    print("\n🎉 Enhanced Risk Analysis Flow Test PASSED - No infinite loop risk!")
    return True

def test_enhanced_recursion_protection():
    """Test that enhanced flows still prevent recursion at extreme counts"""
    print("\n🧪 Testing Enhanced Recursion Protection...")
    print("=" * 60)
    
    conditional_logic = ConditionalLogic()
    
    # Simulate extreme count scenarios
    extreme_counts = [100, 200, 500, 1000]
    
    for count in extreme_counts:
        # Test enhanced debate flow
        debate_state = {
            "tickers": ["SPY"],
            "investment_debate_states": {
                "SPY": {"count": count}
            }
        }
        result = conditional_logic.should_continue_debate(debate_state)
        print(f"✅ Enhanced debate at count {count}: {result} (Always terminates)")
        assert result == "Research Manager", f"Should always terminate at Research Manager"
        
        # Test enhanced risk analysis flow  
        risk_state = {
            "tickers": ["SPY"],
            "risk_debate_states": {
                "SPY": {"count": count}
            }
        }
        result = conditional_logic.should_continue_risk_analysis(risk_state)
        print(f"✅ Enhanced risk analysis at count {count}: {result} (Always terminates)")
        assert result == "Risk Judge", f"Should always terminate at Risk Judge"
    
    print("\n🎉 Enhanced Recursion Protection Test PASSED - No recursion risk!")
    return True

def main():
    """Run all enhanced routing tests"""
    print("🚀 Testing Enhanced Agent Routing Logic (with Restored Agents)")
    print("=" * 80)
    print("This test verifies that restored crossex and neutral agents")
    print("do not reintroduce infinite loops or recursion issues.\n")
    
    try:
        # Run all tests
        test_enhanced_debate_flow()
        test_enhanced_risk_analysis_flow() 
        test_enhanced_recursion_protection()
        
        print("\n" + "=" * 80)
        print("🎉 ALL ENHANCED TESTS PASSED!")
        print("✅ Enhanced routing logic working correctly")
        print("✅ Crossex researchers successfully restored")
        print("✅ Neutral analyst successfully restored")
        print("✅ No infinite loop risks detected")
        print("✅ Recursion protection maintained")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 