import time
import json
from tradingagents.blackboard.utils import create_agent_blackboard
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def create_risk_manager(llm, memory, toolkit):
    def risk_manager_node(state) -> dict:

        # Handle both single ticker and multi-ticker portfolio modes
        if "tickers" in state and state.get("tickers"):
            # Multi-ticker portfolio mode - use the first ticker for now
            ticker = state["tickers"][0] if state["tickers"] else "SPY"
            is_portfolio_mode = True
            
            # Extract ticker-specific data from portfolio structure
            individual_reports = state.get("individual_reports", {})
            ticker_reports = individual_reports.get(ticker, {})
            
            current_date = state["trade_date"]
            
            # Extract ticker-specific debate states from portfolio structure
            risk_debate_states = state.get("risk_debate_states", {})
            risk_debate_state = risk_debate_states.get(ticker, {})
            
            investment_debate_states = state.get("investment_debate_states", {})
            investment_debate_state = investment_debate_states.get(ticker, {})
            
            history = risk_debate_state.get("history", "[]")
            market_research_report = ticker_reports.get("market_report", "")
            news_report = ticker_reports.get("news_report", "")
            fundamentals_report = ticker_reports.get("fundamentals_report", "")
            sentiment_report = ticker_reports.get("sentiment_report", "")
            trader_plan = ticker_reports.get("investment_plan", "")
            
        elif "company_of_interest" in state:
            # Single ticker mode (backward compatibility)
            ticker = state["company_of_interest"]
            is_portfolio_mode = False
            
            current_date = state["trade_date"]
            history = state["risk_debate_state"]["history"]
            risk_debate_state = state["risk_debate_state"]
            market_research_report = state.get("market_report", "")
            news_report = state.get("news_report", "")
            fundamentals_report = state.get("fundamentals_report", "")
            sentiment_report = state.get("sentiment_report", "")
            trader_plan = state.get("investment_plan", "")
        else:
            # Fallback - this shouldn't happen but let's handle it gracefully
            print("Warning: No ticker information found in state")
            return {
                "final_trade_decision": "Error: No ticker information available",
            }

        # Enterprise policy: Risk Judge recommends only; execution happens in Portfolio Optimizer.

        # Blackboard integration
        blackboard_agent = create_agent_blackboard("RKM_001", "RiskManager")
        recent_analyses = blackboard_agent.get_analysis_reports(ticker=ticker)
        recent_decisions = blackboard_agent.get_investment_decisions(ticker=ticker)

        blackboard_context = ""
        if recent_analyses:
            blackboard_context += "\n\nRecent Analyst Reports on Blackboard:\n"
            for analysis in recent_analyses[-3:]:
                content = analysis.get('content', {})
                analysis_data = content.get('analysis', {})
                if isinstance(analysis_data, dict):
                    blackboard_context += f"- {analysis['sender'].get('role', 'Unknown')}: {analysis_data.get('recommendation', 'N/A')} (Confidence: {analysis_data.get('confidence', 'N/A')})\n"

        if recent_decisions:
            blackboard_context += "\n\nRecent Investment Decisions on Blackboard:\n"
            for decision in recent_decisions[-2:]:
                content = decision.get('content', {})
                blackboard_context += f"- {decision['sender'].get('role', 'Unknown')}: {content.get('decision', 'N/A')} (Confidence: {content.get('confidence', 'N/A')})\n"

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        # Build system message (use existing base prompt text)
        system_message = f"""As the Risk Management Judge and Debate Facilitator, your goal is to evaluate the debate between three risk analysts—Risky, Neutral, and Safe/Conservative—and determine the best course of action for the trader. Your decision must result in a clear recommendation: Buy, Sell, or Hold. Choose Hold only if strongly justified by specific arguments, not as a fallback when all sides seem valid. Strive for clarity and decisiveness.

Guidelines for Decision-Making:
1. **Summarize Key Arguments**: Extract the strongest points from each analyst, focusing on relevance to the context.
2. **Provide Rationale**: Support your recommendation with direct quotes and counterarguments from the debate.
3. **Refine the Trader's Plan**: Start with the trader's original plan, **{trader_plan}**, and adjust it based on the analysts' insights.
4. **Learn from Past Mistakes**: Use lessons from **{past_memory_str}** to address prior misjudgments and improve the decision you are making now to make sure you don't make a wrong BUY/SELL/HOLD call that loses money.

Do not execute any trades or call tools. Produce a clear BUY/SELL/HOLD recommendation with rationale; execution will be handled later by the Portfolio Optimizer."""

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant collaborating with other assistants. Provide a decisive recommendation and concise rationale. Do not call or reference any tools.\n\n{system_message}\nFor your reference, the current date is {current_date}. The company we want to analyze is {ticker}.",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        chain = prompt | llm
        
        print("messages")
        print(state.get("messages", []))

        result = chain.invoke(state.get("messages", []))

        response = result
        response_text = getattr(response, 'content', '') or ''

        # No tool calls expected; proceed with parsing

        # default decision parsing (only after no pending tool calls)
        decision = "Hold"
        risk_level = "Medium"
        confidence = "Medium"
        rt = response_text.upper()
        if "BUY" in rt:
            decision = "Buy"
        elif "SELL" in rt:
            decision = "Sell"

        if "HIGH" in rt and "RISK" in rt:
            risk_level = "High"
        elif "LOW" in rt and "RISK" in rt:
            risk_level = "Low"
        elif "CRITICAL" in rt:
            risk_level = "Critical"

        if "HIGH" in rt and "CONFIDENCE" in rt:
            confidence = "High"
        elif "LOW" in rt and "CONFIDENCE" in rt:
            confidence = "Low"

        risk_factors = []
        if "VOLATILITY" in rt:
            risk_factors.append("Market Volatility")
        if "LIQUIDITY" in rt:
            risk_factors.append("Liquidity Risk")
        if "REGULATORY" in rt:
            risk_factors.append("Regulatory Risk")
        if "COMPANY" in rt and "SPECIFIC" in rt:
            risk_factors.append("Company-Specific Risk")
        if not risk_factors:
            risk_factors = ["General Market Risk"]

        # Post results to blackboard (preserve existing behavior)
        blackboard_agent.post_risk_assessment(
            ticker=ticker,
            risk_level=risk_level,
            risk_factors=risk_factors,
            recommendation=response_text,
            confidence=confidence,
        )

        blackboard_agent.post_investment_decision(
            ticker=ticker,
            decision=decision,
            reasoning=response_text,
            confidence=confidence,
        )

        debate_summary = f"Risk debate for {ticker} concluded with {decision} decision. Risk level: {risk_level}. {response_text[:200]}..."
        blackboard_agent.post_debate_summary(
            ticker=ticker,
            debate_type="Risk",
            summary=debate_summary,
            decision=decision,
            confidence=confidence,
        )

        new_risk_debate_state = {
            "judge_decision": response_text,
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

        # store serializable message content instead of the full chain result object
        if is_portfolio_mode:
            return {
                "messages": state.get("messages", []) + [{"role": "assistant", "content": response_text}],
                "risk_debate_states": {
                    ticker: new_risk_debate_state
                },
                "individual_reports": {
                    ticker: {
                        "final_trade_decision": response_text
                    }
                },
            }
        else:
            return {
                "messages": state.get("messages", []) + [{"role": "assistant", "content": response_text}],
                "risk_debate_state": new_risk_debate_state,
                "final_trade_decision": response_text,
            }

    return risk_manager_node
