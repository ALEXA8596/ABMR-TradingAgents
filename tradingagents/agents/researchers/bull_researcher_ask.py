# Done

from langchain_core.messages import AIMessage
import json

def create_bull_researcher_ask(llm, memory):
    def bull_researcher_ask_node(state) -> dict:
        # Handle both single ticker and multi-ticker portfolio modes
        if "investment_debate_states" in state and state.get("tickers"):
            # Multi-ticker portfolio mode - use the first ticker for now
            # In a real implementation, you might want to track which ticker is currently being debated
            ticker = state["tickers"][0] if state["tickers"] else "SPY"
            investment_debate_state = state["investment_debate_states"].get(ticker, {})
            is_portfolio_mode = True
        else:
            # Single ticker mode
            investment_debate_state = state.get("investment_debate_state", {})
            ticker = None
            is_portfolio_mode = False
        
        bear_response = investment_debate_state.get("current_response", "")
        bull_history = investment_debate_state.get("bull_history", "[]")

        curr_situation = f"Bear Response: {bear_response}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        json_format = """{
  "questions": [{
      "question": "...", // Question for the bear researcher
      "source": "..." // Source of the question (e.g., "Bear Response")
  }, ...],
}"""

        prompt = f"""You are a Bull Analyst conducting a cross-examination of the Bear Analyst's arguments. Your goal is to critically analyze the bear's response, generate insightful questions to their claims.

Key points to focus on:

- Questions: Formulate questions that challenge the bear's assumptions, data, or reasoning.

Resources available:
Bear's latest response: {bear_response}
Reflections from similar situations and lessons learned: {past_memory_str}

Respond ONLY with a valid JSON object in the following format:
{json_format}
The content of the questions should be detailed and evidence-based. Source indicates where the information was obtained from, such as the bear's response or past reflections.
"""
        response = llm.invoke(prompt)

        # Parse the JSON from the LLM response
        crossex_json = {}
        try:
            crossex_json = json.loads(response.content)
        except Exception:
            pass

        # Parse Bull History and append the new cross-examination
        try:
            bull_history_list = json.loads(bull_history)
        except Exception:
            bull_history_list = []
        bull_history_list.append(crossex_json)
        new_bull_history = json.dumps(bull_history_list)

        new_investment_debate_state = {
            "bull_history": new_bull_history,
            "bear_history": investment_debate_state.get("bear_history", "[]"),
            "current_response": crossex_json,
            "count": investment_debate_state.get("count", 0) + 1,
        }

        # Return the appropriate state structure based on mode
        if is_portfolio_mode:
            # In portfolio mode, update the ticker-specific state
            return {
                "investment_debate_states": {
                    ticker: new_investment_debate_state
                }
            }
        else:
            # Single ticker mode - use the existing logic
            return {"investment_debate_state": new_investment_debate_state}

    return bull_researcher_ask_node
