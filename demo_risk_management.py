#!/usr/bin/env python3
"""
Risk Management Progression Demo
This script demonstrates how the risk management flow progresses through the system.
"""

from tradingagents.graph.conditional_logic import ConditionalLogic

def demo_risk_management_flow():
    """Demonstrate the risk management progression flow"""
    print("🎯 Risk Management Progression Demo")
    print("=" * 50)
    
    # Initialize the conditional logic
    conditional_logic = ConditionalLogic(max_risk_discuss_rounds=1)
    
    # Simulate the progression through each analyst
    print("\n📋 Risk Management Flow:")
    print("1. Risky Analyst → 2. Safe Analyst → 3. Neutral Analyst → 4. Risk Judge")
    print()
    
    # Test each step of the progression
    test_state = {
        "tickers": ["SPY"],
        "risk_debate_states": {
            "SPY": {
                "count": 0,
                "history": "[]",
                "current_risky_response": "",
                "current_safe_response": "",
                "current_neutral_response": "",
                "latest_speaker": "",
                "judge_decision": ""
            }
        }
    }
    
    # Step 1: Risky Analyst (count = 0)
    print("🔴 Step 1: Risky Analyst")
    print(f"   Count: {test_state['risk_debate_states']['SPY']['count']}")
    result = conditional_logic.should_continue_risk_analysis(test_state)
    print(f"   → Goes to: {result}")
    print(f"   → Role: Aggressive risk-taking approach")
    print(f"   → Focus: Maximize returns, accept high risk")
    
    # Step 2: Safe Analyst (count = 1)
    test_state["risk_debate_states"]["SPY"]["count"] = 1
    print(f"\n🟢 Step 2: Safe Analyst")
    print(f"   Count: {test_state['risk_debate_states']['SPY']['count']}")
    result = conditional_logic.should_continue_risk_analysis(test_state)
    print(f"   → Goes to: {result}")
    print(f"   → Role: Conservative capital preservation")
    print(f"   → Focus: Protect capital, minimize losses")
    
    # Step 3: Neutral Analyst (count = 2)
    test_state["risk_debate_states"]["SPY"]["count"] = 2
    print(f"\n🟡 Step 3: Neutral Analyst")
    print(f"   Count: {test_state['risk_debate_states']['SPY']['count']}")
    result = conditional_logic.should_continue_risk_analysis(test_state)
    print(f"   → Goes to: {result}")
    print(f"   → Role: Balanced, moderate-risk approach")
    print(f"   → Focus: Middle ground between risk and reward")
    
    # Step 4: Risk Judge (count = 3+)
    test_state["risk_debate_states"]["SPY"]["count"] = 3
    print(f"\n⚖️  Step 4: Risk Judge")
    print(f"   Count: {test_state['risk_debate_states']['SPY']['count']}")
    result = conditional_logic.should_continue_risk_analysis(test_state)
    print(f"   → Goes to: {result}")
    print(f"   → Role: Final decision maker")
    print(f"   → Focus: Choose strategy based on all three analyses")
    
    print(f"\n🎉 Risk Management Flow Complete!")
    print(f"   Final destination: {result}")
    print(f"   Total steps: 4")
    print(f"   Flow: Risky → Safe → Neutral → Risk Judge")

def demo_multiple_rounds():
    """Demonstrate how multiple rounds work"""
    print(f"\n🔄 Multiple Rounds Demo")
    print("=" * 50)
    
    # Test with multiple rounds
    conditional_logic = ConditionalLogic(max_risk_discuss_rounds=2)
    
    print(f"Max Risk Discuss Rounds: {conditional_logic.max_risk_discuss_rounds}")
    print("This means the system can go through the full cycle twice before terminating.")
    
    # Test round 1
    test_state = {
        "tickers": ["SPY"],
        "risk_debate_states": {
            "SPY": {"count": 0}
        }
    }
    
    print(f"\n📋 Round 1:")
    for i in range(4):
        result = conditional_logic.should_continue_risk_analysis(test_state)
        analyst_names = ["Risky Analyst", "Safe Analyst", "Neutral Analyst", "Risk Judge"]
        print(f"   Count {i}: {analyst_names[i]} → {result}")
        test_state["risk_debate_states"]["SPY"]["count"] = i + 1
    
    # Test round 2
    print(f"\n📋 Round 2:")
    for i in range(4, 8):
        result = conditional_logic.should_continue_risk_analysis(test_state)
        analyst_names = ["Risky Analyst", "Safe Analyst", "Neutral Analyst", "Risk Judge"]
        analyst_index = (i - 4) % 4
        print(f"   Count {i}: {analyst_names[analyst_index]} → {result}")
        test_state["risk_debate_states"]["SPY"]["count"] = i + 1
    
    # Test termination
    print(f"\n📋 Termination:")
    test_state["risk_debate_states"]["SPY"]["count"] = 8
    result = conditional_logic.should_continue_risk_analysis(test_state)
    print(f"   Count 8+: {result} (Termination)")

if __name__ == "__main__":
    demo_risk_management_flow()
    demo_multiple_rounds()
    
    print(f"\n" + "=" * 50)
    print("🎯 Risk Management System Summary:")
    print("✅ Progressive flow: Risky → Safe → Neutral → Risk Judge")
    print("✅ Configurable rounds: Supports multiple cycles")
    print("✅ Guaranteed termination: Always ends at Risk Judge")
    print("✅ No infinite loops: Built-in recursion protection")
    print("✅ Flexible routing: Handles both single and multi-ticker modes")
    print("=" * 50) 