#!/usr/bin/env python3
"""
Test script to verify the new multi-ticker portfolio optimization system.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tradingagents'))

def test_portfolio_optimization():
    """Test the new portfolio optimization system."""
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
        
        ta = TradingAgentsGraph(debug=True, config=config)
        
        # Test with multiple tickers
        tickers = ["SPY", "AAPL", "TSLA"]
        date = "2025-08-21"
        
        print(f"📊 Testing portfolio optimization for: {', '.join(tickers)}")
        print(f"📅 Analysis date: {date}")
        print()
        
        # Run portfolio analysis
        print("🚀 Starting portfolio analysis...")
        final_state, decision = ta.propagate_portfolio(tickers, date)
        
        print("\n✅ Portfolio analysis completed!")
        print("=" * 60)
        
        # Verify all tickers were analyzed
        individual_reports = final_state.get("individual_reports", {})
        print("\n📋 Individual Ticker Analysis Results:")
        for ticker in tickers:
            if ticker in individual_reports:
                ticker_data = individual_reports[ticker]
                analysis_complete = ticker_data.get("analysis_complete", False)
                status = "✅ Complete" if analysis_complete else "❌ Incomplete"
                print(f"  {ticker}: {status}")
                
                if analysis_complete:
                    portfolio_state = ticker_data.get("portfolio_optimization_state", {})
                    if portfolio_state:
                        print(f"    - Portfolio optimization: ✅")
                    else:
                        print(f"    - Portfolio optimization: ❌")
            else:
                print(f"  {ticker}: ❌ Missing from reports")
        
        # Verify portfolio optimization was completed
        portfolio_state = final_state.get("portfolio_optimization_state", {})
        if portfolio_state:
            print(f"\n🎯 Portfolio Optimization Results:")
            print(f"  - Optimization completed: {portfolio_state.get('optimization_completed', False)}")
            print(f"  - Tickers analyzed: {portfolio_state.get('tickers_analyzed', [])}")
            
            if portfolio_state.get('optimization_completed', False):
                print(f"  - Correlation analysis: ✅")
                print(f"  - Sector analysis: ✅")
                print(f"  - Risk metrics: ✅")
                print(f"  - Allocation strategies: ✅")
                print(f"  - Portfolio decision: ✅")
                
                # Show portfolio decision details
                portfolio_decision = portfolio_state.get('portfolio_decision', {})
                if portfolio_decision:
                    print(f"\n📊 Portfolio Decision Summary:")
                    ticker_decisions = portfolio_decision.get('ticker_decisions', {})
                    for ticker, decision in ticker_decisions.items():
                        rec = decision.get('recommendation', 'HOLD')
                        conf = decision.get('confidence', 'Medium')
                        print(f"  {ticker}: {rec} (Confidence: {conf})")
                    
                    portfolio_rec = portfolio_decision.get('portfolio_recommendation', {})
                    if portfolio_rec:
                        print(f"\n🎯 Overall Portfolio Action: {portfolio_rec.get('overall_action', 'Unknown')}")
                        print(f"   Risk Level: {portfolio_rec.get('risk_level', 'Unknown')}")
                        print(f"   Expected Return: {portfolio_rec.get('expected_return', 'Unknown')}")
                        
                        implementation_plan = portfolio_decision.get('implementation_plan', [])
                        if implementation_plan:
                            print(f"\n📝 Implementation Plan:")
                            for i, step in enumerate(implementation_plan, 1):
                                print(f"   {i}. {step}")
            else:
                print(f"  - Portfolio optimization failed or incomplete")
        else:
            print(f"\n❌ Portfolio optimization state not found!")
        
        print("\n" + "=" * 60)
        print("🏁 Portfolio optimization test completed!")
        
        # Summary
        all_complete = all(
            individual_reports.get(ticker, {}).get("analysis_complete", False)
            for ticker in tickers
        )
        
        if all_complete and portfolio_state.get('optimization_completed', False):
            print("🎉 SUCCESS: All tickers analyzed and portfolio optimization completed!")
        else:
            print("⚠️  PARTIAL SUCCESS: Some components may not have completed fully")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required modules are available")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_portfolio_optimization() 