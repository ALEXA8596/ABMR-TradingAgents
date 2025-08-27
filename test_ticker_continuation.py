#!/usr/bin/env python3
"""
Test script to verify the ticker analysis continuation logic.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tradingagents'))

def test_ticker_continuation_logic():
    """Test the ticker analysis continuation logic."""
    try:
        print("🧪 Testing Ticker Analysis Continuation Logic...")
        print("=" * 60)
        
        # Import the conditional logic module directly
        from tradingagents.graph.conditional_logic import ConditionalLogic
        
        # Create conditional logic instance
        conditional_logic = ConditionalLogic(max_debate_rounds=1, max_risk_discuss_rounds=1)
        
        # Test 1: First ticker, analysis incomplete
        print("\n📋 Test 1: First ticker, analysis incomplete")
        state1 = {
            "tickers": ["SPY", "AAPL", "TSLA"],
            "current_ticker_index": 0,
            "individual_reports": {
                "SPY": {
                    "market_report": "",
                    "fundamentals_report": "",
                    "sentiment_report": "",
                    "news_report": "",
                    "investment_plan": "",
                    "trader_investment_plan": "",
                    "final_trade_decision": ""
                }
            }
        }
        result1 = conditional_logic.should_continue_ticker_analysis(state1)
        print(f"   Input: First ticker (SPY), analysis incomplete")
        print(f"   Expected: continue_analysis (to continue with analysis)")
        print(f"   Result: {result1}")
        print(f"   {'✅ PASS' if result1 == 'continue_analysis' else '❌ FAIL'}")
        
        # Test 2: First ticker, analysis complete
        print("\n📋 Test 2: First ticker, analysis complete")
        state2 = {
            "tickers": ["SPY", "AAPL", "TSLA"],
            "current_ticker_index": 0,
            "individual_reports": {
                "SPY": {
                    "market_report": "SPY market analysis complete",
                    "fundamentals_report": "SPY fundamentals complete",
                    "sentiment_report": "SPY sentiment complete",
                    "news_report": "SPY news complete",
                    "investment_plan": "SPY investment plan complete",
                    "trader_investment_plan": "SPY trader plan complete",
                    "final_trade_decision": "SPY decision complete"
                }
            }
        }
        result2 = conditional_logic.should_continue_ticker_analysis(state2)
        print(f"   Input: First ticker (SPY), analysis complete")
        print(f"   Expected: next_ticker (to move to next ticker)")
        print(f"   Result: {result2}")
        print(f"   {'✅ PASS' if result2 == 'next_ticker' else '❌ FAIL'}")
        
        # Test 3: Middle ticker, analysis incomplete
        print("\n📋 Test 3: Middle ticker, analysis incomplete")
        state3 = {
            "tickers": ["SPY", "AAPL", "TSLA"],
            "current_ticker_index": 1,
            "individual_reports": {
                "SPY": {
                    "market_report": "SPY market analysis complete",
                    "fundamentals_report": "SPY fundamentals complete",
                    "sentiment_report": "SPY sentiment complete",
                    "news_report": "SPY news complete",
                    "investment_plan": "SPY investment plan complete",
                    "trader_investment_plan": "SPY trader plan complete",
                    "final_trade_decision": "SPY decision complete"
                },
                "AAPL": {
                    "market_report": "",
                    "fundamentals_report": "",
                    "sentiment_report": "",
                    "news_report": "",
                    "investment_plan": "",
                    "trader_investment_plan": "",
                    "final_trade_decision": ""
                }
            }
        }
        result3 = conditional_logic.should_continue_ticker_analysis(state3)
        print(f"   Input: Middle ticker (AAPL), analysis incomplete")
        print(f"   Expected: continue_analysis (to continue with analysis)")
        print(f"   Result: {result3}")
        print(f"   {'✅ PASS' if result3 == 'continue_analysis' else '❌ FAIL'}")
        
        # Test 4: Last ticker, analysis complete
        print("\n📋 Test 4: Last ticker, analysis complete")
        state4 = {
            "tickers": ["SPY", "AAPL", "TSLA"],
            "current_ticker_index": 2,
            "individual_reports": {
                "SPY": {
                    "market_report": "SPY market analysis complete",
                    "fundamentals_report": "SPY fundamentals complete",
                    "sentiment_report": "SPY sentiment complete",
                    "news_report": "SPY news complete",
                    "investment_plan": "SPY investment plan complete",
                    "trader_investment_plan": "SPY trader plan complete",
                    "final_trade_decision": "SPY decision complete"
                },
                "AAPL": {
                    "market_report": "AAPL market analysis complete",
                    "fundamentals_report": "AAPL fundamentals complete",
                    "sentiment_report": "AAPL sentiment complete",
                    "news_report": "AAPL news complete",
                    "investment_plan": "AAPL investment plan complete",
                    "trader_investment_plan": "AAPL trader plan complete",
                    "final_trade_decision": "AAPL decision complete"
                },
                "TSLA": {
                    "market_report": "TSLA market analysis complete",
                    "fundamentals_report": "TSLA fundamentals complete",
                    "sentiment_report": "TSLA sentiment complete",
                    "news_report": "TSLA news complete",
                    "investment_plan": "TSLA investment plan complete",
                    "trader_investment_plan": "TSLA trader plan complete",
                    "final_trade_decision": "TSLA decision complete"
                }
            }
        }
        result4 = conditional_logic.should_continue_ticker_analysis(state4)
        print(f"   Input: Last ticker (TSLA), analysis complete")
        print(f"   Expected: portfolio_optimization (all tickers done)")
        print(f"   Result: {result4}")
        print(f"   {'✅ PASS' if result4 == 'portfolio_optimization' else '❌ FAIL'}")
        
        # Test 5: Beyond last ticker
        print("\n📋 Test 5: Beyond last ticker")
        state5 = {
            "tickers": ["SPY", "AAPL", "TSLA"],
            "current_ticker_index": 3,
            "individual_reports": {
                "SPY": {
                    "market_report": "SPY market analysis complete",
                    "fundamentals_report": "SPY fundamentals complete",
                    "sentiment_report": "SPY sentiment complete",
                    "news_report": "SPY news complete",
                    "investment_plan": "SPY investment plan complete",
                    "trader_investment_plan": "SPY trader plan complete",
                    "final_trade_decision": "SPY decision complete"
                },
                "AAPL": {
                    "market_report": "AAPL market analysis complete",
                    "fundamentals_report": "AAPL fundamentals complete",
                    "sentiment_report": "AAPL sentiment complete",
                    "news_report": "AAPL news complete",
                    "investment_plan": "AAPL investment plan complete",
                    "trader_investment_plan": "AAPL trader plan complete",
                    "final_trade_decision": "AAPL decision complete"
                },
                "TSLA": {
                    "market_report": "TSLA market analysis complete",
                    "fundamentals_report": "TSLA fundamentals complete",
                    "sentiment_report": "TSLA sentiment complete",
                    "news_report": "TSLA news complete",
                    "investment_plan": "TSLA investment plan complete",
                    "trader_investment_plan": "TSLA trader plan complete",
                    "final_trade_decision": "TSLA decision complete"
                }
            }
        }
        result5 = conditional_logic.should_continue_ticker_analysis(state5)
        print(f"   Input: Beyond last ticker (index 3)")
        print(f"   Expected: portfolio_optimization (all tickers done)")
        print(f"   Result: {result5}")
        print(f"   {'✅ PASS' if result5 == 'portfolio_optimization' else '❌ FAIL'}")
        
        print("\n🎉 All ticker continuation logic tests completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ticker_continuation_logic() 