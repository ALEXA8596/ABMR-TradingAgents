# Done

from langchain_core.messages import AIMessage
import json

def create_bear_researcher_ans(llm, memory):
    def bear_researcher_ans_node(state) -> dict:
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
        
        bull_questions = investment_debate_state.get("current_response", "")
        bear_history = investment_debate_state.get("bear_history", "[]")

        curr_situation = f"Bull Questions: {bull_questions}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        json_format = """{
  "answers": [{
      "answer": "...", // Answer to the bull's question
      "source": "..." // Source of the answer (e.g., "Bull Questions")
  }, ...],
}"""

        prompt = f"""You are a Bear Analyst answering cross-examination questions from the Bull Analyst. Your goal is to provide clear, evidence-based answers that strengthen your bearish position.

Key points to focus on:

- Answers: Provide comprehensive answers that address the bull's questions directly.
- Evidence: Support your answers with data, analysis, or logical reasoning.

Resources available:
Bull's questions: {bull_questions}
Reflections from similar situations and lessons learned: {past_memory_str}

Respond ONLY with a valid JSON object in the following format:
{json_format}
The content of the answers should be detailed and evidence-based. Source indicates where the information was obtained from, such as the bull's questions or past reflections.
"""
        response = llm.invoke(prompt)

        # Parse the JSON from the LLM response
        crossex_json = {}
        try:
            crossex_json = json.loads(response.content)
        except Exception:
            pass

        # Parse Bear History and append the new cross-examination
        try:
            bear_history_list = json.loads(bear_history)
        except Exception:
            bear_history_list = []
        bear_history_list.append(crossex_json)
        new_bear_history = json.dumps(bear_history_list)

        new_investment_debate_state = {
            "bear_history": new_bear_history,
            "bull_history": investment_debate_state.get("bull_history", "[]"),
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

    return bear_researcher_ans_node
