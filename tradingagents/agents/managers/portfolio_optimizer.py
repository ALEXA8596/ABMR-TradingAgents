import time
import json
import os
from datetime import datetime
from tradingagents.blackboard.utils import create_agent_blackboard


def create_portfolio_optimizer(llm, memory, toolkit):
    def portfolio_optimizer_node(state) -> dict:

        company_name = state["company_of_interest"]
        
        market_research_report = state["market_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        sentiment_report = state["sentiment_report"]
        trader_plan = state["trader_investment_plan"]
        risk_decision = state["final_trade_decision"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=3)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"
            
        # Blackboard integration
        blackboard_agent = create_agent_blackboard("FA_001", "FundamentalAnalyst")
        # Read recent analysis reports for context
        recent_analyses = blackboard_agent.get_analysis_reports(ticker=company_name)
        blackboard_context = ""
        if recent_analyses:
            blackboard_context += "\n\nRecent Analysis Reports on Blackboard:\n"
            for analysis in recent_analyses[-3:]:
                content = analysis.get('content', {})
                blackboard_context += f"- {analysis['sender'].get('role', 'Unknown')}: {content.get('recommendation', 'N/A')} (Confidence: {content.get('confidence', 'N/A')})\n"
                
        tools = [toolkit.get_portfolio_kelly_criterion,
                 toolkit.get_portfolio_risk_parity,
                 toolkit.get_portfolio_black_litterman,
                 toolkit.get_portfolio_mean_reversion,
                 toolkit.get_portfolio_momentum,
                 toolkit.perform_stress_test,
                 toolkit.calculate_beta,
                 toolkit.design_hedging_strategy,
                ]

        prompt = f"""As the Senior Quantitative Portfolio Manager, create a comprehensive institutional-grade portfolio optimization strategy for {company_name}. Your analysis must cover advanced hedging across ALL asset classes including crypto, options, futures, forex, and commodities.

**CRITICAL REQUIREMENTS:**
1. **Multi-Asset Hedging Strategy**: Design hedging using crypto (BTC, ETH), options (puts/calls), futures (ES, NQ), forex (USD pairs), and commodities (gold, oil, etc.)
2. **Advanced Quantitative Techniques**: Implement Kelly Criterion, Risk Parity, Black-Litterman, Mean Reversion, Momentum strategies
3. **Beta Management**: Calculate and hedge portfolio beta using index futures and ETFs
4. **Cross-Asset Correlation Analysis**: Analyze correlations between {company_name} and various asset classes
5. **Scenario Analysis**: Stress test portfolio against market crashes, inflation, currency devaluation

**Input Context:**
- **Trader's Investment Plan**: {trader_plan}
- **Risk Committee Decision**: {risk_decision}
- **Market Intelligence**: {market_research_report}
- **Sentiment Analysis**: {sentiment_report}
- **News Report**: {news_report}
- **Fundamentals Report**: {fundamentals_report}
- **Past Portfolio Lessons**: {past_memory_str}

**DELIVERABLE STRUCTURE:**
Create a detailed markdown report covering:

## Executive Summary
- Portfolio optimization recommendation for {company_name}
- Key hedging strategies across asset classes
- Expected risk/return profile

## Position Sizing & Allocation
- Primary position in {company_name} (size, rationale)
- Kelly Criterion application
- Risk parity considerations
- Volatility targeting methodology

## Multi-Asset Hedging Strategy

### Cryptocurrency Hedging
- Bitcoin (BTC) hedge ratios and correlation analysis
- Ethereum (ETH) as inflation/tech hedge
- Crypto derivatives and futures for tail risk protection

### Options Strategy
- Put protection levels and strike selection
- Call overwriting opportunities
- Volatility trading strategies
- Greeks management (delta, gamma, theta, vega)

### Futures Hedging
- Index futures (ES, NQ, RTY) for beta management
- Sector-specific futures exposure
- Currency futures for FX risk
- Commodity futures positioning

### Forex Hedging
- USD exposure management
- Cross-currency hedging strategies
- Emerging market currency risks
- Carry trade considerations

### Commodities Exposure
- Gold as portfolio insurance
- Oil and energy complex hedging
- Agricultural commodities for inflation protection
- Precious metals allocation

## Beta Management
- Current portfolio beta calculation
- Target beta based on market conditions
- Hedging instruments to achieve beta neutrality
- Dynamic beta adjustment strategies

## Risk Metrics & Analytics
- Value at Risk (VaR) calculations
- Expected Shortfall (CVaR)
- Maximum Drawdown estimates
- Sharpe ratio optimization
- Correlation matrix analysis

## Scenario Analysis
- Market crash scenarios (-20%, -40%)
- Inflation spike scenarios
- Currency crisis scenarios
- Sector rotation impacts
- Crypto market correlation breaks

## Implementation Roadmap
- Phase 1: Core position establishment
- Phase 2: Hedging implementation
- Phase 3: Dynamic rebalancing
- Execution timeline and cost analysis

## Monitoring & Rebalancing
- Daily risk monitoring protocols
- Rebalancing triggers and thresholds
- Performance attribution analysis
- Hedge effectiveness measurement

Provide specific trade recommendations, position sizes, and quantitative analysis. Make this institutional-quality with hedge fund level sophistication."""

        response = llm.invoke(prompt, tools=tools)

        # Create the markdown report
        portfolio_analysis = response.content
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"portfolio_optimization_{company_name}_{timestamp}.md"
        
        # Create the markdown report content
        report_content = f"""# Portfolio Optimization Report: {company_name}
**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Analyst**: Senior Quantitative Portfolio Manager
**Target Asset**: {company_name}

---

{portfolio_analysis}

---

## Disclaimer
This report is generated by AI-powered quantitative analysis and should be reviewed by qualified financial professionals before implementation. Past performance does not guarantee future results. All investments carry risk of loss.

## Report Metadata
- **Generation Time**: {datetime.now().isoformat()}
- **Asset Analyzed**: {company_name}
- **Portfolio Optimizer Version**: 1.0
- **Multi-Asset Coverage**: Crypto, Options, Futures, Forex, Commodities
"""

        # Write the report to file
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"✅ Portfolio optimization report saved: {filename}")
        except Exception as e:
            print(f"❌ Error saving report: {e}")

        # Store analysis in memory for future reference
        memory_entry = f"Portfolio Optimization for {company_name}: {portfolio_analysis[:500]}..."
        try:
            # Use the correct method to save to memory
            memory.add_situations([(curr_situation, memory_entry)])
        except Exception as e:
            print(f"⚠️ Memory save warning: {e}")

        return {
            "portfolio_optimization_state": {
                "analysis": portfolio_analysis,
                "company": company_name,
                "optimization_completed": True,
                "report_file": filename,
                "timestamp": timestamp,
                "multi_asset_hedging": True,
                "asset_classes_covered": ["crypto", "options", "futures", "forex", "commodities"]
            }
        }

    return portfolio_optimizer_node 