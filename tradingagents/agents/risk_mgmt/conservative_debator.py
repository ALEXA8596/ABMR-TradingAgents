from langchain_core.messages import AIMessage
import time
import json
from tradingagents.blackboard.utils import create_agent_blackboard


def create_safe_debator(llm):
    def _analyze_single_ticker_conservative(ticker: str, state, llm):
        """Analyze a single ticker from conservative risk perspective and return the analysis."""
        # Extract reports for this ticker
        individual_reports = state.get("individual_reports", {})
        ticker_reports = individual_reports.get(ticker, {})
        
        market_research_report = ticker_reports.get("market_report", "")
        sentiment_report = ticker_reports.get("sentiment_report", "")
        news_report = ticker_reports.get("news_report", "")
        fundamentals_report = ticker_reports.get("fundamentals_report", "")
        trader_decision = ticker_reports.get("trader_investment_plan", "")

        # Get risk debate state for this ticker
        risk_debate_states = state.get("risk_debate_states", {})
        risk_debate_state = risk_debate_states.get(ticker, {})
        
        current_risky_response = risk_debate_state.get("current_risky_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        # Blackboard integration
        blackboard_agent = create_agent_blackboard("SD_001", "SafeDebator")
        recent_risk_debates = blackboard_agent.get_risk_assessments(ticker=ticker)
        
        blackboard_context = ""
        if recent_risk_debates:
            blackboard_context += "\n\nRecent Risk Assessments on Blackboard:\n"
            for assessment in recent_risk_debates[-3:]:
                content = assessment.get('content', {})
                blackboard_context += f"- {assessment['sender'].get('role', 'Unknown')}: {content.get('risk_level', 'N/A')} - {content.get('recommendation', 'N/A')[:100]}...\n"

        # Create conservative risk analysis prompt
        system_message = f"""As a Conservative Risk Analyst, your role is to provide a cautious, safety-focused perspective on {ticker}.

Your analysis should focus on:
- Risk mitigation and capital preservation
- Downside protection strategies
- Conservative position sizing
- Risk-adjusted returns perspective
- Potential loss scenarios
- Safety margin requirements

Analyze the trader's decision and market conditions from a conservative risk management perspective.
Provide specific recommendations for reducing risk exposure while maintaining reasonable return potential.

Market Research: {market_research_report}
Sentiment Report: {sentiment_report}
News Report: {news_report}
Fundamentals: {fundamentals_report}
Trader Decision: {trader_decision}

Risky Analyst Response: {current_risky_response}
Neutral Analyst Response: {current_neutral_response}

{blackboard_context}"""

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Provide conservative risk analysis for {ticker} focusing on capital preservation and downside protection."}
        ]

        response = llm.invoke(messages)
        response_text = getattr(response, 'content', '') or str(response)

        # Post to blackboard
        # Extract risk factors from the response (simplified approach)
        risk_factors = ["Capital preservation", "Downside protection", "Risk mitigation"]
        
        blackboard_agent.post_risk_assessment(
            ticker=ticker,
            risk_level="Conservative",
            risk_factors=risk_factors,
            recommendation=response_text
        )

        return {
            "response": response_text,
            "messages": [response],
            "ticker": ticker
        }

    def safe_node(state) -> dict:
        # Handle both single ticker and multi-ticker portfolio modes
        if "tickers" in state and state.get("tickers"):
            # Multi-ticker portfolio mode - process ALL tickers that need conservative risk analysis
            tickers = state["tickers"]
            risk_completion = state.get("risk_completion", {})
            conservative_completion = risk_completion.get("conservative", {})
            
            # Find all tickers that need conservative risk analysis
            tickers_to_process = [
                ticker for ticker in tickers 
                if not conservative_completion.get(ticker, False)
            ]
            
            if not tickers_to_process:
                # All tickers already have conservative risk analysis, mark all as complete
                updated_risk_completion = {
                    **risk_completion,
                    "conservative": {ticker: True for ticker in tickers}
                }
                return {
                    "messages": [],
                    "risk_completion": updated_risk_completion
                }
            
            # Process all tickers that need conservative risk analysis
            all_responses = {}
            all_messages = []
            updated_debate_states = {}
            
            for ticker in tickers_to_process:
                print(f"🛡️ Conservative Risk Analyst processing {ticker}...")
                
                # Process this ticker
                ticker_analysis = _analyze_single_ticker_conservative(ticker, state, llm)
                all_responses[ticker] = ticker_analysis["response"]
                all_messages.extend(ticker_analysis["messages"])
                
                # Update risk debate state for this ticker
                risk_debate_states = state.get("risk_debate_states", {})
                current_debate_state = risk_debate_states.get(ticker, {})
                
                # Update risk debate state
                updated_debate_states[ticker] = {
                    **current_debate_state,
                    "history": current_debate_state.get("history", "") + f"\n\nConservative Risk Analysis: {ticker_analysis['response']}",
                    "safe_history": current_debate_state.get("safe_history", "") + f"\n\nAnalysis: {ticker_analysis['response']}",
                    "current_safe_response": ticker_analysis["response"],
                    "count": current_debate_state.get("count", 0) + 1  # FIXED: Increment count in multi-ticker mode
                }
            
            # Mark all processed tickers as complete for conservative risk analysis
            updated_conservative_completion = {**conservative_completion}
            for ticker in tickers_to_process:
                updated_conservative_completion[ticker] = True
            
            updated_risk_completion = {
                **risk_completion,
                "conservative": updated_conservative_completion
            }
            
            return {
                "messages": all_messages,
                "risk_debate_states": updated_debate_states,
                "risk_completion": updated_risk_completion
            }
        elif "company_of_interest" in state:
            # Single ticker mode (backward compatibility)
            ticker = state.get("company_of_interest", "UNKNOWN")
            
            # Process single ticker with simplified logic
            ticker_analysis = _analyze_single_ticker_conservative(ticker, state, llm)
            
            # Update single ticker risk debate state
            risk_debate_state = state.get("risk_debate_state", {})
            
            updated_risk_debate_state = {
                **risk_debate_state,
                "history": risk_debate_state.get("history", "") + f"\n\nConservative Risk Analysis: {ticker_analysis['response']}",
                "safe_history": risk_debate_state.get("safe_history", "") + f"\n\nAnalysis: {ticker_analysis['response']}",
                "current_safe_response": ticker_analysis["response"],
                "count": risk_debate_state.get("count", 0) + 1
            }
            
            return {
                "messages": ticker_analysis["messages"],
                "risk_debate_state": updated_risk_debate_state
            }
        else:
            # Fallback - this shouldn't happen but let's handle it gracefully
            print("Warning: No ticker information found in state")
            return {
                "messages": [],
                "current_safe_response": "Error: No ticker information available",
            }

    return safe_node
