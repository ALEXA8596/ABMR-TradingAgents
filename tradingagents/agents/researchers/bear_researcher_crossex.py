from langchain_core.messages import AIMessage
import json
from tradingagents.agents.utils.debate_utils import increment_debate_count, get_debate_round_info

def create_bear_crossex_researcher(llm, memory):
    def _crossex_single_ticker_bear(ticker: str, state, llm, memory):
        """Cross-examine bull arguments for a single ticker and return the analysis."""
        # Get debate state for this ticker
        investment_debate_states = state.get("investment_debate_states", {})
        investment_debate_state = investment_debate_states.get(ticker, {})
        
        # Get the bull's response from bull_history
        bull_history = investment_debate_state.get("bull_history", "")
        bull_response = bull_history.split("Bull Researcher Round")[-1].strip() if bull_history else "No bull response available"
        
        bear_history = investment_debate_state.get("bear_history", "")
        bear_response = bear_history.split("Bear Researcher Round")[-1].strip() if bear_history else "No bear response available"

        # Create cross-examination prompt
        system_message = f"""As a Bear Cross-Examiner, your role is to critically analyze and challenge the Bull Researcher's arguments for {ticker}.

Your task is to:
- Identify weaknesses in the bullish case
- Present counter-evidence to bull arguments  
- Highlight overlooked bearish factors
- Question the validity of bullish assumptions
- Strengthen the overall bearish position

Use logical reasoning and evidence-based arguments to cross-examine the bull case.
Present your cross-examination as structured questions and rebuttals.

Bull Arguments to Examine: {bull_response}
Bear Arguments to Support: {bear_response}"""

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Cross-examine the bull arguments for {ticker} and present compelling rebuttals."}
        ]

        response = llm.invoke(messages)
        response_text = getattr(response, 'content', '') or str(response)

        return {
            "response": response_text,
            "messages": [response],
            "ticker": ticker
        }

    def bear_crossex_node(state) -> dict:
        print(f"[DEBUG] Bear Cross Examination Researcher executing...")
        
        # Handle both single ticker and portfolio modes
        if "tickers" in state and state.get("tickers"):
            # Multi-ticker portfolio mode - process ALL tickers that need bear cross-examination
            tickers = state["tickers"]
            researcher_completion = state.get("researcher_completion", {})
            bear_crossex_completion = researcher_completion.get("bear_crossex", {})
            
            # Find all tickers that need bear cross-examination
            tickers_to_process = [
                ticker for ticker in tickers 
                if not bear_crossex_completion.get(ticker, False)
            ]
            
            if not tickers_to_process:
                # All tickers already have bear cross-examination, mark all as complete
                updated_researcher_completion = {
                    **researcher_completion,
                    "bear_crossex": {ticker: True for ticker in tickers}
                }
                return {
                    "messages": [],
                    "researcher_completion": updated_researcher_completion
                }
            
            # Process all tickers that need bear cross-examination
            all_responses = {}
            all_messages = []
            updated_debate_states = {}
            
            for ticker in tickers_to_process:
                print(f"🐻⚖️ Bear Cross-Examiner processing {ticker}...")
                
                # Process this ticker
                ticker_crossex = _crossex_single_ticker_bear(ticker, state, llm, memory)
                all_responses[ticker] = ticker_crossex["response"]
                all_messages.extend(ticker_crossex["messages"])
                
                # Update debate state for this ticker
                investment_debate_states = state.get("investment_debate_states", {})
                current_debate_state = investment_debate_states.get(ticker, {})
                
                # Increment debate count and update state
                new_count = current_debate_state.get("count", 0) + 1
                updated_debate_states[ticker] = {
                    **current_debate_state,
                    "history": current_debate_state.get("history", "") + f"\n\nBear Cross-Ex Round {new_count}: {ticker_crossex['response']}",
                    "bear_crossex_history": current_debate_state.get("bear_crossex_history", "") + f"\n\nRound {new_count}: {ticker_crossex['response']}",
                    "current_response": ticker_crossex["response"],
                    "count": new_count
                }
            
            # Mark all processed tickers as complete for bear cross-examination
            updated_bear_crossex_completion = {**bear_crossex_completion}
            for ticker in tickers_to_process:
                updated_bear_crossex_completion[ticker] = True
            
            updated_researcher_completion = {
                **researcher_completion,
                "bear_crossex": updated_bear_crossex_completion
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
            ticker_crossex = _crossex_single_ticker_bear(ticker, state, llm, memory)
            
            # Update single ticker debate state
            investment_debate_state = state.get("investment_debate_state", {})
            new_count = investment_debate_state.get("count", 0) + 1
            
            updated_investment_debate_state = {
                **investment_debate_state,
                "history": investment_debate_state.get("history", "") + f"\n\nBear Cross-Ex Round {new_count}: {ticker_crossex['response']}",
                "bear_crossex_history": investment_debate_state.get("bear_crossex_history", "") + f"\n\nRound {new_count}: {ticker_crossex['response']}",
                "current_response": ticker_crossex["response"],
                "count": new_count
            }
            
            return {
                "messages": ticker_crossex["messages"],
                "investment_debate_state": updated_investment_debate_state
            }
        else:
            # Fallback - this shouldn't happen but let's handle it gracefully
            print("Warning: No ticker information found in state")
            return {
                "messages": [],
                "investment_plan": "Error: No ticker information available",
            }

    return bear_crossex_node
