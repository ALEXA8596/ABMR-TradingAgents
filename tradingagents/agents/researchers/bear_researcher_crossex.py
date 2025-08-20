from langchain_core.messages import AIMessage
import json
from tradingagents.agents.utils.debate_utils import increment_debate_count, get_debate_round_info

def create_bear_crossex_researcher(llm, memory):
    def bear_crossex_node(state) -> dict:
        investment_debate_state = state["investment_debate_state"]
        bull_response = investment_debate_state.get("current_response", "")
        bear_history = investment_debate_state.get("bear_history", "[]")

        # Get current debate round information
        round_info = get_debate_round_info(state)
        current_round = round_info["round"]
        current_step = round_info["step_name"]

        curr_situation = f"Bull Response: {bull_response}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        json_format = """{
  "questions": [{
      "question": "...", // Question for the bull researcher
      "source": "..." // Source of the question (e.g., "Bull Response")
  }, ...],
  "rebuttals": [{
      "rebuttal": "...", // Rebuttal to the bull's argument
      "source": "..." // Source of the rebuttal (e.g., "Bull Response")
  }, ...]
}"""

        prompt = f"""You are a Bear Analyst conducting a cross-examination of the Bull Analyst's arguments in Round {current_round}. Your goal is to critically analyze the bull's response, generate insightful questions, and provide strong rebuttals to their claims.

Current Debate Status: Round {current_round}, {current_step} Step

Key points to focus on:

- Questions: Formulate questions that challenge the bull's assumptions, data, or reasoning.
- Rebuttals: Provide counterarguments to the bull's claims, using evidence and sound logic.

Resources available:
Bull's latest response: {bull_response}
Reflections from similar situations and lessons learned: {past_memory_str}

Respond ONLY with a valid JSON object in the following format:
{json_format}
The content of the questions and rebuttals should be detailed and evidence-based. Source indicates where the information was obtained from, such as the bull's response or past reflections.
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

        # Update the debate state
        new_investment_debate_state = {
            "bear_history": new_bear_history,
            "bull_history": investment_debate_state.get("bull_history", "[]"),
            "current_response": crossex_json,
            "count": investment_debate_state["count"],  # Keep current count
        }

        # Increment the count for the next step
        updated_state = {"investment_debate_state": new_investment_debate_state}
        updated_state = increment_debate_count(updated_state)

        return updated_state

    return bear_crossex_node
