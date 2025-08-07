#!/usr/bin/env python3
"""
Test script for the new Macro Economic Analyst.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.agents.analysts.macro_economic_analyst import create_macro_economic_analyst
from tradingagents.agents.utils.agent_utils import Toolkit
from tradingagents.default_config import DEFAULT_CONFIG
from langchain_openai import ChatOpenAI
from tradingagents.blackboard.storage import clear_blackboard, read_messages

def test_macro_economic_analyst():
    """Test the macro economic analyst functionality."""
    
    print("🧪 Testing Macro Economic Analyst...")
    
    # Clear blackboard for fresh test
    clear_blackboard()
    
    # Initialize components
    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = "openai"
    config["backend_url"] = "https://api.openai.com/v1"
    
    # Create LLM (you'll need to set your API key)
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            base_url="https://api.openai.com/v1"
        )
    except Exception as e:
        print(f"❌ Error creating LLM: {e}")
        print("💡 Make sure you have set your OpenAI API key in the environment")
        return False
    
    # Create toolkit
    toolkit = Toolkit(config=config)
    
    # Create macro economic analyst
    macro_analyst = create_macro_economic_analyst(llm, toolkit)
    
    # Create test state
    test_state = {
        "trade_date": "2025-01-03",
        "company_of_interest": "TSLA",
        "messages": []
    }
    
    try:
        # Run the analyst
        print("🔍 Running macro economic analysis for TSLA...")
        result = macro_analyst(test_state)
        
        print("✅ Macro Economic Analyst test completed!")
        print(f"📊 Result keys: {list(result.keys())}")
        
        if "macro_analysis" in result:
            analysis = result["macro_analysis"]
            print(f"📈 Analysis confidence: {analysis.get('confidence', 'N/A')}")
            print(f"📊 Market sentiment: {analysis.get('market_sentiment', 'N/A')}")
            print(f"⚠️ Risk level: {analysis.get('risk_level', 'N/A')}")
            
            if "macro_indicators" in analysis:
                print(f"📋 Macro indicators analyzed: {len(analysis['macro_indicators'])}")
                for indicator in analysis["macro_indicators"][:3]:  # Show first 3
                    print(f"  - {indicator.get('indicator', 'N/A')}: {indicator.get('current_status', 'N/A')}")
        
        # Check blackboard
        messages = read_messages()
        macro_messages = [msg for msg in messages if msg.get('sender', {}).get('role') == 'MacroEconomicAnalyst']
        
        print(f"📝 Blackboard messages from Macro Economic Analyst: {len(macro_messages)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error running macro economic analyst: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_macro_economic_analyst()
    if success:
        print("\n🎉 Macro Economic Analyst test passed!")
    else:
        print("\n💥 Macro Economic Analyst test failed!")
        sys.exit(1) 