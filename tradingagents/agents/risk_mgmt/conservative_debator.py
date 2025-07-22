from langchain_core.messages import AIMessage
import time
import json


def create_safe_debator(llm):
    def safe_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "[]")
        safe_history = risk_debate_state.get("safe_history", "[]")

        current_risky_response = risk_debate_state.get("current_risky_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        trader_decision = state["trader_investment_plan"]
        
        json_format = """{  
  "content": "...", // Overall writeup of the response
  "arguments": [{
      "title": "...", // Short title for the argument
      "content": "...", // Detailed content of the argument
      "source": "...", // Source of the information (e.g., "Market Research Report")
      "confidence": "..." // Confidence level in the argument (1-100)
  }, ...],
  "counterpoints": [{
      "title": "...",
      "content": "...",
      "source": "...",
      "confidence": "...",
      "target": "..." // The agent you are responding to, e.g. "Conservative", "Neutral"
    }, ...]
}"""

        prompt = f"""As the Safe/Conservative Risk Analyst, your primary objective is to protect assets, minimize volatility, and ensure steady, reliable growth. You prioritize stability, security, and risk mitigation, carefully assessing potential losses, economic downturns, and market volatility. When evaluating the trader's decision or plan, critically examine high-risk elements, pointing out where the decision may expose the firm to undue risk and where more cautious alternatives could secure long-term gains. Here is the trader's decision:

{trader_decision}

Your task is to actively counter the arguments of the Risky and Neutral Analysts, highlighting where their views may overlook potential threats or fail to prioritize sustainability. Respond directly to their points, drawing from the following data sources to build a convincing case for a low-risk approach adjustment to the trader's decision:

Market Research Report: {market_research_report}
Social Media Sentiment Report: {sentiment_report}
Latest World Affairs Report: {news_report}
Company Fundamentals Report: {fundamentals_report}
Here is the current conversation history: {history} Here is the last response from the risky analyst: {current_risky_response} Here is the last response from the neutral analyst: {current_neutral_response}. If there are no responses from the other viewpoints, do not halluncinate and just present your point.

Engage by questioning their optimism and emphasizing the potential downsides they may have overlooked. Address each of their counterpoints to showcase why a conservative stance is ultimately the safest path for the firm's assets. Focus on debating and critiquing their arguments to demonstrate the strength of a low-risk strategy over their approaches. Output conversationally as if you are speaking without any special formatting.

Respond ONLY with a valid JSON object in the following format:
{json_format}
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
            history_list = json.loads(history) if history else []
        except Exception:
            history_list = []
        history_list.append(argument_json)
        new_history = json.dumps(history_list)

        # Parse Safe History and append the new argument
        try:
            safe_history_list = json.loads(safe_history) if safe_history else []
        except Exception:
            safe_history_list = []
        safe_history_list.append(argument_json)
        new_safe_history = json.dumps(safe_history_list)

        argument = json.dumps(argument_json)

        new_risk_debate_state = {
            "history": new_history,
            "risky_history": risk_debate_state.get("risky_history", "[]"),
            "safe_history": new_safe_history,
            "neutral_history": risk_debate_state.get("neutral_history", "[]"),
            "latest_speaker": "Safe",
            "current_risky_response": risk_debate_state.get(
                "current_risky_response", ""
            ),
            "current_safe_response": argument,
            "current_neutral_response": risk_debate_state.get(
                "current_neutral_response", ""
            ),
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return safe_node
