from langchain_core.messages import AIMessage
import time
import json
from tradingagents.blackboard.utils import create_agent_blackboard
from tradingagents.agents.utils.debate_utils import increment_debate_count, get_debate_round_info


def create_bear_researcher(llm, memory):
    def _research_single_ticker_bear(ticker: str, state, llm, memory):
        """Research a single ticker from bear perspective and return the analysis."""
        # Extract reports for this ticker
        individual_reports = state.get("individual_reports", {})
        ticker_reports = individual_reports.get(ticker, {})
        
        market_research_report = ticker_reports.get("market_report", "")
        sentiment_report = ticker_reports.get("sentiment_report", "")
        news_report = ticker_reports.get("news_report", "")
        fundamentals_report = ticker_reports.get("fundamentals_report", "")
        macroeconomic_report = ticker_reports.get("macroeconomic_report", "")

        # Get debate state for this ticker
        investment_debate_states = state.get("investment_debate_states", {})
        investment_debate_state = investment_debate_states.get(ticker, {})
        
        history = investment_debate_state.get("history", "")
        bear_history = investment_debate_state.get("bear_history", "")
        current_response = investment_debate_state.get("current_response", "")

        # Blackboard integration
        blackboard_agent = create_agent_blackboard("BR_001", "BearResearcher")
        recent_debates = blackboard_agent.get_debate_comments(topic=f"{ticker} Investment Debate")
        
        blackboard_context = ""
        if recent_debates:
            blackboard_context += "\n\nRecent Debate Comments on Blackboard:\n"
            for debate in recent_debates[-3:]:
                content = debate.get('content', {})
                blackboard_context += f"- {debate['sender'].get('role', 'Unknown')}: {content.get('position', 'N/A')} - {content.get('argument', 'N/A')[:100]}...\n"

        # Prepare context for bear research
        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}\n\n{macroeconomic_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)
        past_memory_str = "\n\n".join([rec["recommendation"] for rec in past_memories])

        # Build bear argument prompt
        system_message = f"""As a Bear Researcher, your role is to develop and present the strongest possible bearish case for {ticker}. 
        
Your analysis should focus on:
- Risks and challenges analysis
- Competitive weaknesses identification
- Negative market indicators
- Overvaluation concerns
- Negative sentiment trends
- Counter-arguments to bullish claims

Use the provided analysis reports to build compelling bear arguments with specific evidence and reasoning.
Present your case as a structured argument with confidence levels and supporting data.

Past relevant insights: {past_memory_str}
{blackboard_context}"""

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Develop a comprehensive bearish research case for {ticker} based on the available analysis."}
        ]

        response = llm.invoke(messages)
        response_text = getattr(response, 'content', '') or str(response)

        # Post to blackboard
        blackboard_agent.post_debate_comment(
            topic=f"{ticker} Investment Debate",
            position="Bearish",
            argument=response_text
        )

        return {
            "response": response_text,
            "messages": [response],
            "ticker": ticker
        }

    def bear_node(state) -> dict:
        # Handle both single ticker and portfolio modes
        if "tickers" in state and state.get("tickers"):
            # Multi-ticker portfolio mode - process ALL tickers that need bear research
            tickers = state["tickers"]
            researcher_completion = state.get("researcher_completion", {})
            bear_completion = researcher_completion.get("bear", {})
            
            # Find all tickers that need bear research
            tickers_to_process = [
                ticker for ticker in tickers 
                if not bear_completion.get(ticker, False)
            ]
            
            if not tickers_to_process:
                # All tickers already have bear research, mark all as complete
                updated_researcher_completion = {
                    **researcher_completion,
                    "bear": {ticker: True for ticker in tickers}
                }
                return {
                    "messages": [],
                    "researcher_completion": updated_researcher_completion
                }
            
            # Process all tickers that need bear research
            all_responses = {}
            all_messages = []
            updated_debate_states = {}
            
            for ticker in tickers_to_process:
                print(f"🐻 Bear Researcher processing {ticker}...")
                
                # Process this ticker
                ticker_research = _research_single_ticker_bear(ticker, state, llm, memory)
                all_responses[ticker] = ticker_research["response"]
                all_messages.extend(ticker_research["messages"])
                
                # Update debate state for this ticker
                investment_debate_states = state.get("investment_debate_states", {})
                current_debate_state = investment_debate_states.get(ticker, {})
                
                # Increment debate count and update state
                new_count = current_debate_state.get("count", 0) + 1
                updated_debate_states[ticker] = {
                    **current_debate_state,
                    "history": current_debate_state.get("history", "") + f"\n\nBear Researcher Round {new_count}: {ticker_research['response']}",
                    "bear_history": current_debate_state.get("bear_history", "") + f"\n\nRound {new_count}: {ticker_research['response']}",
                    "current_response": ticker_research["response"],
                    "count": new_count
                }
            
            # Mark all processed tickers as complete for bear research
            updated_bear_completion = {**bear_completion}
            for ticker in tickers_to_process:
                updated_bear_completion[ticker] = True
            
            updated_researcher_completion = {
                **researcher_completion,
                "bear": updated_bear_completion
            }
            
            return {
                "messages": all_messages,
                "investment_debate_states": updated_debate_states,
                "researcher_completion": updated_researcher_completion
            }
        elif "company_of_interest" in state:
            # Single ticker mode (backward compatibility)
            ticker = state["company_of_interest"]
            
            # Process single ticker with simplified logic
            ticker_research = _research_single_ticker_bear(ticker, state, llm, memory)
            
            # Update single ticker debate state
            investment_debate_state = state.get("investment_debate_state", {})
            new_count = investment_debate_state.get("count", 0) + 1
            
            updated_investment_debate_state = {
                **investment_debate_state,
                "history": investment_debate_state.get("history", "") + f"\n\nBear Researcher Round {new_count}: {ticker_research['response']}",
                "bear_history": investment_debate_state.get("bear_history", "") + f"\n\nRound {new_count}: {ticker_research['response']}",
                "current_response": ticker_research["response"],
                "count": new_count
            }
            
            return {
                "messages": ticker_research["messages"],
                "investment_debate_state": updated_investment_debate_state
            }
        else:
            # Fallback - this shouldn't happen but let's handle it gracefully
            print("Warning: No ticker information found in state")
            return {
                "messages": [],
                "investment_plan": "Error: No ticker information available",
            }

    return bear_node
