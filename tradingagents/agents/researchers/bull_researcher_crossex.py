from langchain_core.messages import AIMessage
import json
from tradingagents.agents.utils.debate_utils import increment_debate_count, get_debate_round_info

def create_bull_crossex_researcher(llm, memory):
    def bull_crossex_node(state) -> dict:
        print(f"[DEBUG] Bull Cross Examination Researcher executing...")
        investment_debate_state = state["investment_debate_state"]
        
        # Get the bear's response from bear_history
        bear_history = investment_debate_state.get("bear_history", "[]")
        try:
            bear_history_list = json.loads(bear_history) if bear_history else []
            bear_response = bear_history_list[-1] if bear_history_list else "No bear response available"
        except Exception:
            bear_response = "No bear response available"
        
        bull_history = investment_debate_state.get("bull_history", "[]")
        
        print(f"[DEBUG] Current count: {investment_debate_state.get('count', 0)}")
        print(f"[DEBUG] Bear response: {str(bear_response)[:100]}...")

        # Get current debate round information
        round_info = get_debate_round_info(state)
        current_round = round_info["round"]
        current_step = round_info["step_name"]
        
        print(f"[DEBUG] Round: {current_round}, Step: {current_step}")

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
  "rebuttals": [{
      "rebuttal": "...", // Rebuttal to the bear's argument
      "source": "..." // Source of the rebuttal (e.g., "Bear Response")
  }, ...]
}"""

        prompt = f"""You are a Bull Analyst conducting a cross-examination of the Bear Analyst's arguments in Round {current_round}. Your goal is to critically analyze the bear's response, generate insightful questions, and provide strong rebuttals to their claims.

Current Debate Status: Round {current_round}, {current_step} Step

Key points to focus on:

- Questions: Formulate questions that challenge the bear's assumptions, data, or reasoning.
- Rebuttals: Provide counterarguments to the bear's claims, using evidence and sound logic.

Resources available:
Bear's latest response: {bear_response}
Reflections from similar situations and lessons learned: {past_memory_str}

Respond ONLY with a valid JSON object in the following format:
{json_format}
The content of the questions and rebuttals should be detailed and evidence-based. Source indicates where the information was obtained from, such as the bear's response or past reflections.
"""
        response = llm.invoke(prompt)

        # Parse the JSON from the LLM response
        crossex_json = {}
        try:
            crossex_json = json.loads(response.content)
        except Exception:
            pass

        # Post cross-examination to blackboard
        from tradingagents.blackboard.utils import create_agent_blackboard
        blackboard_agent = create_agent_blackboard("BCR_001", "BullCrossExaminer")
        
        ticker = state["company_of_interest"]
        
        # Format the cross-examination for posting
        crossex_text = f"Cross-Examination of Bear Arguments:\n\n"
        
        if "questions" in crossex_json:
            crossex_text += "**Questions:**\n"
            for i, q in enumerate(crossex_json["questions"], 1):
                crossex_text += f"{i}. {q.get('question', 'N/A')}\n"
            crossex_text += "\n"
        
        if "rebuttals" in crossex_json:
            crossex_text += "**Rebuttals:**\n"
            for i, r in enumerate(crossex_json["rebuttals"], 1):
                crossex_text += f"{i}. {r.get('rebuttal', 'N/A')}\n"
        
        # Post debate comment to blackboard
        blackboard_agent.post_debate_comment(
            topic=f"{ticker} Investment Debate - Cross Examination",
            position="Bullish Cross-Examination",
            argument=crossex_text,
            reply_to=None  # Could link to bear's last comment if needed
        )

        # Parse Bull History and append the new cross-examination
        try:
            bull_history_list = json.loads(bull_history)
        except Exception:
            bull_history_list = []
        bull_history_list.append(crossex_json)
        new_bull_history = json.dumps(bull_history_list)

        # Update the debate state
        new_investment_debate_state = {
            "history": investment_debate_state.get("history", "[]"),
            "bull_history": new_bull_history,
            "bear_history": investment_debate_state.get("bear_history", "[]"),
            "current_response": crossex_json,
            "judge_decision": investment_debate_state.get("judge_decision", ""),
            "count": investment_debate_state["count"],  # Keep current count
        }

        # Increment the count for the next step
        updated_state = {"investment_debate_state": new_investment_debate_state}
        updated_state = increment_debate_count(updated_state)
        
        print(f"[DEBUG] Bull Cross Examination Researcher completed. New count: {updated_state['investment_debate_state']['count']}")

        # Return the complete state update
        return updated_state

    return bull_crossex_node
