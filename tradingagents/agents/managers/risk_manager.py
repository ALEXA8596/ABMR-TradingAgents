import time
import json
from tradingagents.blackboard.utils import create_agent_blackboard


def create_risk_manager(llm, memory):
    def risk_manager_node(state) -> dict:

        ticker = state["company_of_interest"]

        history = state["risk_debate_state"]["history"]
        risk_debate_state = state["risk_debate_state"]
        market_research_report = state["market_report"]
        news_report = state["news_report"]
        fundamentals_report = state["news_report"]
        sentiment_report = state["sentiment_report"]
        trader_plan = state["investment_plan"]

        # Blackboard integration
        blackboard_agent = create_agent_blackboard("RKM_001", "RiskManager")
        
        # Read recent analyst reports and investment decisions for context
        recent_analyses = blackboard_agent.get_analysis_reports(ticker=ticker)
        recent_decisions = blackboard_agent.get_investment_decisions(ticker=ticker)
        
        blackboard_context = ""
        if recent_analyses:
            blackboard_context += "\n\nRecent Analyst Reports on Blackboard:\n"
            for analysis in recent_analyses[-3:]:  # Last 3 analyses
                content = analysis.get('content', {})
                analysis_data = content.get('analysis', {})
                if isinstance(analysis_data, dict):
                    blackboard_context += f"- {analysis['sender'].get('role', 'Unknown')}: {analysis_data.get('recommendation', 'N/A')} (Confidence: {analysis_data.get('confidence', 'N/A')})\n"
        
        if recent_decisions:
            blackboard_context += "\n\nRecent Investment Decisions on Blackboard:\n"
            for decision in recent_decisions[-2:]:  # Last 2 decisions
                content = decision.get('content', {})
                blackboard_context += f"- {decision['sender'].get('role', 'Unknown')}: {content.get('decision', 'N/A')} (Confidence: {content.get('confidence', 'N/A')})\n"

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""As the Risk Management Judge and Debate Facilitator, your goal is to evaluate the debate between three risk analysts—Risky, Neutral, and Safe/Conservative—and determine the best course of action for the trader. Your decision must result in a clear recommendation: Buy, Sell, or Hold. Choose Hold only if strongly justified by specific arguments, not as a fallback when all sides seem valid. Strive for clarity and decisiveness.

Guidelines for Decision-Making:
1. **Summarize Key Arguments**: Extract the strongest points from each analyst, focusing on relevance to the context.
2. **Provide Rationale**: Support your recommendation with direct quotes and counterarguments from the debate.
3. **Refine the Trader's Plan**: Start with the trader's original plan, **{trader_plan}**, and adjust it based on the analysts' insights.
4. **Learn from Past Mistakes**: Use lessons from **{past_memory_str}** to address prior misjudgments and improve the decision you are making now to make sure you don't make a wrong BUY/SELL/HOLD call that loses money.

Deliverables:
- A clear and actionable recommendation: Buy, Sell, or Hold.
- Detailed reasoning anchored in the debate and past reflections.

Blackboard Context:{blackboard_context}

---

**Analysts Debate History:**  
{history}

---

Focus on actionable insights and continuous improvement. Build on past lessons, critically evaluate all perspectives, and ensure each decision advances better outcomes."""

        response = llm.invoke(prompt)

        # Extract decision, risk level, and confidence from response
        decision = "Hold"
        risk_level = "Medium"
        confidence = "Medium"
        response_text = response.content.upper()
        
        if "BUY" in response_text:
            decision = "Buy"
        elif "SELL" in response_text:
            decision = "Sell"
        
        if "HIGH" in response_text and "RISK" in response_text:
            risk_level = "High"
        elif "LOW" in response_text and "RISK" in response_text:
            risk_level = "Low"
        elif "CRITICAL" in response_text:
            risk_level = "Critical"
        
        if "HIGH" in response_text and "CONFIDENCE" in response_text:
            confidence = "High"
        elif "LOW" in response_text and "CONFIDENCE" in response_text:
            confidence = "Low"

        # Extract risk factors from response
        risk_factors = []
        if "VOLATILITY" in response_text:
            risk_factors.append("Market Volatility")
        if "LIQUIDITY" in response_text:
            risk_factors.append("Liquidity Risk")
        if "REGULATORY" in response_text:
            risk_factors.append("Regulatory Risk")
        if "COMPANY" in response_text and "SPECIFIC" in response_text:
            risk_factors.append("Company-Specific Risk")
        if not risk_factors:
            risk_factors = ["General Market Risk"]

        # Post risk assessment to blackboard
        blackboard_agent.post_risk_assessment(
            ticker=ticker,
            risk_level=risk_level,
            risk_factors=risk_factors,
            recommendation=response.content,
            confidence=confidence
        )

        # Post final investment decision to blackboard
        blackboard_agent.post_investment_decision(
            ticker=ticker,
            decision=decision,
            reasoning=response.content,
            confidence=confidence
        )

        # Post risk debate summary to blackboard
        debate_summary = f"Risk debate for {ticker} concluded with {decision} decision. Risk level: {risk_level}. {response.content[:200]}..."
        blackboard_agent.post_debate_summary(
            ticker=ticker,
            debate_type="Risk",
            summary=debate_summary,
            decision=decision,
            confidence=confidence
        )

        new_risk_debate_state = {
            "judge_decision": response.content,
            "history": risk_debate_state["history"],
            "risky_history": risk_debate_state["risky_history"],
            "safe_history": risk_debate_state["safe_history"],
            "neutral_history": risk_debate_state["neutral_history"],
            "latest_speaker": "Judge",
            "current_risky_response": risk_debate_state["current_risky_response"],
            "current_safe_response": risk_debate_state["current_safe_response"],
            "current_neutral_response": risk_debate_state["current_neutral_response"],
            "count": risk_debate_state["count"],
        }

        return {
            "risk_debate_state": new_risk_debate_state,
            "final_trade_decision": response.content,
        }

    return risk_manager_node
