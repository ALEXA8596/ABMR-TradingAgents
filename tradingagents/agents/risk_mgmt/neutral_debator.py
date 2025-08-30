import time
import json
from tradingagents.blackboard.utils import create_agent_blackboard


def create_neutral_debator(llm):
    def _analyze_single_ticker_neutral(ticker: str, state, llm):
        """Analyze a single ticker from neutral risk perspective and return the analysis."""
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
        
        current_safe_response = risk_debate_state.get("current_safe_response", "")
        current_risky_response = risk_debate_state.get("current_risky_response", "")

        # Blackboard integration
        blackboard_agent = create_agent_blackboard("ND_001", "NeutralDebator")
        recent_risk_debates = blackboard_agent.get_risk_assessments(ticker=ticker)
        
        blackboard_context = ""
        if recent_risk_debates:
            blackboard_context += "\n\nRecent Risk Assessments on Blackboard:\n"
            for assessment in recent_risk_debates[-3:]:
                content = assessment.get('content', {})
                blackboard_context += f"- {assessment['sender'].get('role', 'Unknown')}: {content.get('risk_level', 'N/A')} - {content.get('recommendation', 'N/A')[:100]}...\n"

        # Create neutral risk analysis prompt
        system_message = f"""As a Neutral Risk Analyst, your role is to provide a balanced, objective perspective on {ticker}.

Your analysis should focus on:
- Balanced risk-return assessment
- Objective evaluation of opportunities and threats
- Moderate position sizing recommendations
- Risk-adjusted performance metrics
- Balanced portfolio considerations
- Evidence-based decision making

Analyze the trader's decision and market conditions from a balanced risk management perspective.
Provide specific recommendations that balance growth potential with risk mitigation.

Market Research: {market_research_report}
Sentiment Report: {sentiment_report}
News Report: {news_report}
Fundamentals: {fundamentals_report}
Trader Decision: {trader_decision}

Conservative Analyst Response: {current_safe_response}
Aggressive Analyst Response: {current_risky_response}

{blackboard_context}"""

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Provide neutral risk analysis for {ticker} focusing on balanced risk-return optimization."}
        ]

        response = llm.invoke(messages)
        response_text = getattr(response, 'content', '') or str(response)

        # Post to blackboard
        # Extract risk factors from the response (simplified approach)
        risk_factors = ["Balanced approach", "Moderate risk", "Market equilibrium"]
        
        blackboard_agent.post_risk_assessment(
            ticker=ticker,
            risk_level="Neutral",
            risk_factors=risk_factors,
            recommendation=response_text
        )

        return {
            "response": response_text,
            "messages": [response],
            "ticker": ticker
        }

    def neutral_node(state) -> dict:
        # Handle both single ticker and multi-ticker portfolio modes
        if "tickers" in state and state.get("tickers"):
            # Multi-ticker portfolio mode - process ALL tickers that need neutral risk analysis
            tickers = state["tickers"]
            risk_completion = state.get("risk_completion", {})
            neutral_completion = risk_completion.get("neutral", {})
            
            # Find all tickers that need neutral risk analysis
            tickers_to_process = [
                ticker for ticker in tickers 
                if not neutral_completion.get(ticker, False)
            ]
            
            if not tickers_to_process:
                # All tickers already have neutral risk analysis, mark all as complete
                updated_risk_completion = {
                    **risk_completion,
                    "neutral": {ticker: True for ticker in tickers}
                }
                return {
                    "messages": [],
                    "risk_completion": updated_risk_completion
                }
            
            # Process all tickers that need neutral risk analysis
            all_responses = {}
            all_messages = []
            updated_debate_states = {}
            
            for ticker in tickers_to_process:
                print(f"⚖️ Neutral Risk Analyst processing {ticker}...")
                
                # Process this ticker
                ticker_analysis = _analyze_single_ticker_neutral(ticker, state, llm)
                all_responses[ticker] = ticker_analysis["response"]
                all_messages.extend(ticker_analysis["messages"])
                
                # Update risk debate state for this ticker
                risk_debate_states = state.get("risk_debate_states", {})
                current_debate_state = risk_debate_states.get(ticker, {})
                
                # Update risk debate state
                updated_debate_states[ticker] = {
                    **current_debate_state,
                    "history": current_debate_state.get("history", "") + f"\n\nNeutral Risk Analysis: {ticker_analysis['response']}",
                    "neutral_history": current_debate_state.get("neutral_history", "") + f"\n\nAnalysis: {ticker_analysis['response']}",
                    "current_neutral_response": ticker_analysis["response"],
                    "count": current_debate_state.get("count", 0) + 1  # FIXED: Increment count in multi-ticker mode
                }
            
            # Mark all processed tickers as complete for neutral risk analysis
            updated_neutral_completion = {**neutral_completion}
            for ticker in tickers_to_process:
                updated_neutral_completion[ticker] = True
            
            updated_risk_completion = {
                **risk_completion,
                "neutral": updated_neutral_completion
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
            ticker_analysis = _analyze_single_ticker_neutral(ticker, state, llm)
            
            # Update single ticker risk debate state
            risk_debate_state = state.get("risk_debate_state", {})
            
            updated_risk_debate_state = {
                **risk_debate_state,
                "history": risk_debate_state.get("history", "") + f"\n\nNeutral Risk Analysis: {ticker_analysis['response']}",
                "neutral_history": risk_debate_state.get("neutral_history", "") + f"\n\nAnalysis: {ticker_analysis['response']}",
                "current_neutral_response": ticker_analysis["response"],
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
                "current_neutral_response": "Error: No ticker information available",
            }

    return neutral_node
