from langchain_core.messages import AIMessage
import time
import json
from tradingagents.blackboard.utils import create_agent_blackboard
from tradingagents.agents.utils.debate_utils import increment_debate_count, get_debate_round_info


def create_bear_researcher(llm, memory):
    def bear_node(state) -> dict:
        # Handle both single ticker and portfolio modes
        if "tickers" in state:
            # Multi-ticker portfolio mode
            tickers = state["tickers"]
            ticker = tickers[0]  # Analyze first ticker for now
            is_portfolio_mode = True
            
            # Extract ticker-specific debate state from portfolio structure
            investment_debate_states = state.get("investment_debate_states", {})
            investment_debate_state = investment_debate_states.get(ticker, {})
            
            # Also extract ticker-specific risk debate state
            risk_debate_states = state.get("risk_debate_states", {})
            risk_debate_state = risk_debate_states.get(ticker, {})
            
        elif "company_of_interest" in state:
            # Single ticker mode (backward compatibility)
            ticker = state["company_of_interest"]
            is_portfolio_mode = False
            
            # Use single ticker debate states
            investment_debate_state = state.get("investment_debate_state", {})
            risk_debate_state = state.get("risk_debate_state", {})
        else:
            # Fallback - this shouldn't happen but let's handle it gracefully
            print("Warning: No ticker information found in state")
            return {
                "investment_plan": "Error: No ticker information available",
            }

        # Now we have the correct debate state for the current ticker
        history = investment_debate_state.get("history", "[]")
        bear_history = investment_debate_state.get("bear_history", "[]")

        current_response = investment_debate_state.get("current_response", "")
        
        # Extract reports based on mode
        if is_portfolio_mode:
            individual_reports = state.get("individual_reports", {})
            ticker_reports = individual_reports.get(ticker, {})
            market_research_report = ticker_reports.get("market_report", "")
            sentiment_report = ticker_reports.get("sentiment_report", "")
            news_report = ticker_reports.get("news_report", "")
            fundamentals_report = ticker_reports.get("fundamentals_report", "")
        else:
            market_research_report = state.get("market_report", "")
            sentiment_report = state.get("sentiment_report", "")
            news_report = state.get("news_report", "")
            fundamentals_report = state.get("fundamentals_report", "")

        # Blackboard integration
        blackboard_agent = create_agent_blackboard("BER_001", "BearResearcher")
        
        # Read recent analyst reports for context
        recent_analyses = blackboard_agent.get_analysis_reports(ticker=ticker)
        blackboard_context = ""
        if recent_analyses:
            blackboard_context += "\n\nRecent Analyst Reports on Blackboard:\n"
            for analysis in recent_analyses[-3:]:  # Last 3 analyses
                content = analysis.get('content', {})
                analysis_data = content.get('analysis', {})
                if isinstance(analysis_data, dict):
                    blackboard_context += f"- {analysis['sender'].get('role', 'Unknown')}: {analysis_data.get('recommendation', 'N/A')} (Confidence: {analysis_data.get('confidence', 'N/A')})\n"

        # Read full debate context for multi-round debates
        debate_round = investment_debate_state.get("count", 0) + 1
        recent_debate = blackboard_agent.get_debate_comments(topic=f"{ticker} Investment Debate")
        debate_context = ""
        if recent_debate:
            debate_context += f"\n\nDEBATE ROUND {debate_round} - Previous Debate Context:\n"
            for comment in recent_debate[-6:]:  # Last 6 comments for context (3 agents x 2 rounds)
                content = comment.get('content', {})
                debate_context += f"- {comment['sender'].get('role', 'Unknown')}: {content.get('position', 'N/A')} - {content.get('argument', 'N/A')[:200]}...\n"

        # Read research arguments for context
        research_args = blackboard_agent.get_research_arguments(ticker=ticker)
        research_context = ""
        if research_args:
            research_context += f"\n\nPrevious Research Arguments:\n"
            for arg in research_args[-2:]:  # Last 2 arguments
                content = arg.get('content', {})
                research_context += f"- {arg['sender'].get('role', 'Unknown')}: {content.get('position', 'N/A')} - {content.get('argument', 'N/A')[:150]}...\n"

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"
            
        json_format = """{
  "arguments": [{
      "title": "...", // Short title for the argument
      "content": "...", // Detailed content of the argument
      "source": "...", // Source of the information (e.g., "Market Research Report")
      "confidence": "..." // Confidence level in the argument (1-100)
  }, ...],
  "risks": [{
      "title": "...",
      "content": "...",
      "source": "...",
      "confidence": "..."
  }, ...],
  "counterpoints": [{
      "title": "...",
      "content": "...",
      "source": "...",
      "confidence": "..."
    }, ...]
}"""

        prompt = f"""As the Bearish Research Analyst, your role is to identify and articulate the risks, challenges, and potential downsides of investing in the company. You should focus on valuation concerns, competitive threats, market risks, and negative catalysts.

DEBATE ROUND {debate_round}: This is round {debate_round} of the investment debate. If this is round 1, provide your initial bearish position. If this is a later round, build upon your previous arguments and directly address the bullish analyst's counter-arguments from the previous round.

{blackboard_context}
{debate_context}

Current Market Situation:
Market Research: {market_research_report}
Social Media Sentiment: {sentiment_report}
News Analysis: {news_report}
Fundamentals: {fundamentals_report}

Your task is to:
1. Analyze the market conditions and company fundamentals
2. Build a compelling bearish case with specific evidence
3. Address potential bullish arguments proactively
4. Provide concrete examples and data points
5. Consider the debate context and previous arguments
6. Maintain a cautious but data-driven tone

Focus on:
- Valuation concerns and overvaluation risks
- Competitive threats and market challenges
- Negative market indicators and trends
- Counter-arguments to bullish concerns
- Evidence from provided data and research

Respond in the following JSON format:
{json_format}"""

        response = llm.invoke(prompt)

        # Extract confidence from response
        confidence = "Medium"
        response_text = response.content.upper()
        if "HIGH" in response_text and "CONFIDENCE" in response_text:
            confidence = "High"
        elif "LOW" in response_text and "CONFIDENCE" in response_text:
            confidence = "Low"

        # Extract evidence sources from response
        evidence_sources = []
        if "RISK" in response_text:
            evidence_sources.append("Risk Analysis")
        if "FUNDAMENTAL" in response_text:
            evidence_sources.append("Fundamental Analysis")
        if "TECHNICAL" in response_text:
            evidence_sources.append("Technical Analysis")
        if "NEWS" in response_text:
            evidence_sources.append("News Analysis")
        if "SENTIMENT" in response_text:
            evidence_sources.append("Sentiment Analysis")
        if not evidence_sources:
            evidence_sources = ["Market Analysis"]

        # Determine reply_to for threading
        reply_to = None
        if recent_debate:
            # Reply to the last bull comment if it exists
            bull_comments = [c for c in recent_debate if c.get('content', {}).get('position') == 'Bullish']
            if bull_comments:
                reply_to = bull_comments[-1].get('message_id')

        # Post debate comment to blackboard
        blackboard_agent.post_debate_comment(
            topic=f"{ticker} Investment Debate",
            position="Bearish",
            argument=response.content,
            reply_to=reply_to
        )

        # Post research argument to blackboard
        blackboard_agent.post_research_argument(
            ticker=ticker,
            position="Bearish",
            argument=response.content,
            confidence=confidence,
            evidence_sources=evidence_sources,
            reply_to=reply_to
        )

        # Post research summary
        key_points = [
            "Risks and challenges analysis",
            "Competitive weaknesses identification",
            "Negative market indicators",
            "Counter-arguments to bullish claims"
        ]
        blackboard_agent.post_research_summary(
            ticker=ticker,
            position="Bearish",
            key_points=key_points,
            conclusion=f"Bearish case for {ticker} based on risks and negative indicators.",
            confidence=confidence
        )

        argument = f"Bear Analyst: {response.content}"

        # Get current debate round information
        round_info = get_debate_round_info(state, ticker)
        current_round = round_info["round"]
        current_step = round_info["step_name"]
        
        # Parse history fields as JSON arrays
        try:
            history_list = json.loads(history) if history else []
        except Exception:
            history_list = []
        
        try:
            bear_history_list = json.loads(bear_history) if bear_history else []
        except Exception:
            bear_history_list = []
        
        # Append new argument
        history_list.append(argument)
        bear_history_list.append(argument)

        new_investment_debate_state = {
            "history": json.dumps(history_list),
            "bear_history": json.dumps(bear_history_list),
            "bull_history": investment_debate_state.get("bull_history", "[]"),
            "current_response": argument,
            "judge_decision": investment_debate_state.get("judge_decision", ""),
            "count": investment_debate_state.get("count", 0),  # Keep current count
        }

        # Increment the count for the next step
        if is_portfolio_mode:
            # In portfolio mode, update the ticker-specific state
            updated_state = {
                "investment_debate_states": {
                    ticker: new_investment_debate_state
                }
            }
            # Increment the count manually since increment_debate_count expects single ticker mode
            updated_state["investment_debate_states"][ticker]["count"] = new_investment_debate_state["count"] + 1
        else:
            # Single ticker mode - use the existing logic
            updated_state = {"investment_debate_state": new_investment_debate_state}
            updated_state = increment_debate_count(updated_state)
        
        # Return the complete state update
        return updated_state

    return bear_node
