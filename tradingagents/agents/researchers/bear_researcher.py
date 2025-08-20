from langchain_core.messages import AIMessage
import time
import json
from tradingagents.blackboard.utils import create_agent_blackboard
from tradingagents.agents.utils.debate_utils import increment_debate_count, get_debate_round_info


def create_bear_researcher(llm, memory):
    def bear_node(state) -> dict:
        ticker = state["company_of_interest"]
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "[]")
        bear_history = investment_debate_state.get("bear_history", "[]")

        current_response = investment_debate_state.get("current_response", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

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
        debate_round = investment_debate_state["count"] + 1
        recent_debate = blackboard_agent.get_debate_comments(topic=f"{ticker} Investment Debate")
        debate_context = ""
        if recent_debate:
            debate_context += f"\n\nDEBATE ROUND {debate_round} - Previous Debate Context:\n"
            for comment in recent_debate[-4:]:  # Last 4 comments for context
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

        prompt = f"""You are a Bear Analyst advocating against investing in the stock. Your task is to build a strong, evidence-based case emphasizing risks, challenges, and negative market indicators. Leverage the provided research and data to address concerns and counter bullish arguments effectively.

DEBATE ROUND {debate_round}: This is round {debate_round} of the debate. If this is round 1, provide your initial bearish argument. If this is a later round, build upon your previous arguments and directly address the bull analyst's counter-arguments from the previous round.

{blackboard_context}
{debate_context}
{research_context}

Current Market Situation:
{curr_situation}

Past Memories and Lessons:
{past_memory_str}

Your task is to:
1. Analyze the current market data and research reports
2. Build a compelling bearish case for {ticker}
3. Address any bullish concerns raised in previous debate rounds
4. Provide specific evidence and reasoning
5. Consider the debate context and previous arguments
6. Maintain a critical but balanced tone

Focus on:
- Risks and challenges analysis
- Competitive weaknesses identification
- Negative market indicators and trends
- Counter-arguments to bullish claims
- Specific evidence from the provided data

Provide a comprehensive analysis that builds upon previous rounds and directly addresses the ongoing debate."""

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
        round_info = get_debate_round_info(state)
        current_round = round_info["round"]
        current_step = round_info["step_name"]
        
        print(f"[DEBUG] Bear Researcher: Round {current_round}, Step {current_step}, Count {investment_debate_state['count']}")

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
            "count": investment_debate_state["count"],  # Keep current count
        }

        # Increment the count for the next step
        updated_state = {"investment_debate_state": new_investment_debate_state}
        updated_state = increment_debate_count(updated_state)
        
        print(f"[DEBUG] Bear Researcher completed. New count: {updated_state['investment_debate_state']['count']}")

        # Return the complete state update
        return updated_state

    return bear_node
