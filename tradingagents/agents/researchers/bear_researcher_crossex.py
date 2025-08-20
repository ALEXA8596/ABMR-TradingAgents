from langchain_core.messages import AIMessage
import json
from tradingagents.agents.utils.debate_utils import increment_debate_count, get_debate_round_info

def create_bear_crossex_researcher(llm, memory):
    def bear_crossex_node(state) -> dict:
        print(f"[DEBUG] Bear Cross Examination Researcher executing...")
        investment_debate_state = state["investment_debate_state"]
        
        # Get the bull's response from bull_history
        bull_history = investment_debate_state.get("bull_history", "[]")
        try:
            bull_history_list = json.loads(bull_history) if bull_history else []
            bull_response = bull_history_list[-1] if bull_history_list else "No bull response available"
        except Exception:
            bull_response = "No bull response available"
        
        bear_history = investment_debate_state.get("bear_history", "[]")
        
        print(f"[DEBUG] Current count: {investment_debate_state.get('count', 0)}")
        print(f"[DEBUG] Bull response: {str(bull_response)[:100]}...")
        
        # Get current debate round information
        round_info = get_debate_round_info(state)
        current_round = round_info["round"]
        current_step = round_info["step_name"]
        
        print(f"[DEBUG] Round: {current_round}, Step: {current_step}")

        # Get past memory for context
        past_memory_str = memory.get_past_memory("investment_debate", state["company_of_interest"])

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

        # Post cross-examination to blackboard
        from tradingagents.blackboard.utils import create_agent_blackboard
        blackboard_agent = create_agent_blackboard("BECR_001", "BearCrossExaminer")
        
        ticker = state["company_of_interest"]
        
        # Format the cross-examination for posting
        crossex_text = f"Cross-Examination of Bull Arguments:\n\n"
        
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
            position="Bearish Cross-Examination",
            argument=crossex_text,
            reply_to=None  # Could link to bull's last comment if needed
        )

        # Parse Bear History and append the new cross-examination
        try:
            bear_history_list = json.loads(bear_history)
        except Exception:
            bear_history_list = []
        bear_history_list.append(crossex_json)
        new_bear_history = json.dumps(bear_history_list)

        # Update the debate state
        new_investment_debate_state = {
            "history": investment_debate_state.get("history", "[]"),
            "bear_history": new_bear_history,
            "bull_history": investment_debate_state.get("bull_history", "[]"),
            "current_response": crossex_json,
            "judge_decision": investment_debate_state.get("judge_decision", ""),
            "count": investment_debate_state["count"],  # Keep current count
        }

        # Increment the count for the next step
        updated_state = {"investment_debate_state": new_investment_debate_state}
        updated_state = increment_debate_count(updated_state)
        
        # Return the complete state update
        return updated_state

    return bear_crossex_node
