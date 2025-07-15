from langchain_core.messages import AIMessage
import time
import json


def create_bull_researcher(llm, memory):
    def bull_node(state) -> dict:
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bull_history = investment_debate_state.get("bull_history", "")

        current_response = investment_debate_state.get("current_response", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""You are a Bull Analyst advocating for investing in the stock. Your task is to build a strong, evidence-based case emphasizing growth potential, competitive advantages, and positive market indicators. Leverage the provided research and data to address concerns and counter bearish arguments effectively.

Key points to focus on:
- Growth Potential: Highlight the company's market opportunities, revenue projections, and scalability.
- Competitive Advantages: Emphasize factors like unique products, strong branding, or dominant market positioning.
- Positive Indicators: Use financial health, industry trends, and recent positive news as evidence.
- Bear Counterpoints: Critically analyze the bear argument with specific data and sound reasoning, addressing concerns thoroughly and showing why the bull perspective holds stronger merit. Cite which resource you got the information from or whether it's a basic economic principle.
- Engagement: Present your argument in a conversational style, engaging directly with the bear analyst's points and debating effectively rather than just listing data.

Resources available:
Market research report: {market_research_report}
Social media sentiment report: {sentiment_report}
Latest world affairs news: {news_report}
Company fundamentals report: {fundamentals_report}
Conversation history of the debate: {history}
Last bear argument: {current_response}
Reflections from similar situations and lessons learned: {past_memory_str}
Use this information to deliver a compelling bull argument, refute the bear's concerns, and engage in a dynamic debate that demonstrates the strengths of the bull position. You must also address reflections and learn from lessons and mistakes you made in the past.

Respond ONLY with a valid JSON object in the following format:
{
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
}
Confidence indicates the level of certainty in the argument presented from a scale from 1 to 100
"""
        response = llm.invoke(prompt)
        
        # Parse the JSON from the LLM response
        argument_json = {}
        try:
            argument_json = json.loads(response.content)
        except Exception:
            pass

        # Parse History and append the new argument
        try:
            history_list = json.loads(history)
        except Exception:
            history_list = []
        history_list.append(argument_json)
        new_history = json.dumps(history_list)

        # Parse Bull History and append the new argument
        try:
            bull_history_list = json.loads(bull_history)
        except Exception:
            bull_history_list = []
        bull_history_list.append(argument_json)
        new_bull_history = json.dumps(bull_history_list)

        new_investment_debate_state = {
            "history": new_history,
            "bull_history": new_bull_history,
            "bear_history": investment_debate_state.get("bear_history", ""),
            "current_response": argument_json,
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bull_node
