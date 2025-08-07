from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from tradingagents.blackboard.utils import create_agent_blackboard


def create_macro_economic_analyst(llm, toolkit):

    def macro_economic_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        # Blackboard integration
        blackboard_agent = create_agent_blackboard("MEA_001", "MacroEconomicAnalyst")
        # Read recent macro analysis reports for context
        recent_analyses = blackboard_agent.get_analysis_reports(ticker=ticker)
        blackboard_context = ""
        if recent_analyses:
            blackboard_context += "\n\nRecent Macro Economic Analysis Reports on Blackboard:\n"
            for analysis in recent_analyses[-3:]:
                content = analysis.get('content', {})
                blackboard_context += f"- {analysis['sender'].get('role', 'Unknown')}: {content.get('recommendation', 'N/A')} (Confidence: {content.get('confidence', 'N/A')})\n"

        if toolkit.config["online_tools"]:
            tools = [
                toolkit.get_YFin_data_online,
                toolkit.get_stockstats_indicators_report_online,
            ]
        else:
            tools = [
                toolkit.get_YFin_data,
                toolkit.get_stockstats_indicators_report,
            ]

        system_message = (
            """You are a Macro Economic Analyst specializing in analyzing macroeconomic factors and their impact on financial markets. Your role is to provide comprehensive analysis of economic indicators and their effects on bond yields, equity markets, and overall market sentiment.

Key Analysis Areas:

1. **Inflation Analysis**:
   - Monitor inflation rates (CPI, PCE) and their impact on bond yields
   - Analyze inflationary pressures from commodity prices (oil, gold)
   - Assess currency-driven inflation effects

2. **Economic Growth Indicators**:
   - GDP growth impact on capital demand and interest rates
   - Unemployment rate correlation with monetary policy
   - Consumer confidence effects on economic activity

3. **Monetary Policy Analysis**:
   - Fed Funds Rate impact on short and long-term yields
   - Money supply effects on liquidity and interest rates
   - Central bank policy expectations and market reactions

4. **Market Risk Assessment**:
   - VIX volatility index analysis and safe-haven flows
   - S&P 500 correlation with bond yields
   - Risk-on vs risk-off market sentiment

5. **Currency & International Factors**:
   - US Dollar Index strength/weakness impact
   - Exchange rate effects on inflation and capital flows
   - International trade and capital flow analysis

6. **Commodity Price Analysis**:
   - Crude oil price impact on inflation expectations
   - Gold price correlation with economic uncertainty
   - Commodity-driven inflationary pressures

Your analysis should include:
- Current macroeconomic environment assessment
- Impact on bond yields and equity markets
- Risk factors and market sentiment analysis
- Forward-looking economic outlook
- Investment implications for the target asset

Provide detailed, nuanced analysis that helps traders understand the macroeconomic context and its implications for their investment decisions."""
            + """ Make sure to append a Markdown table at the end of the report to organize key macroeconomic indicators and their current status."""
            + f"\n\nBlackboard Context:{blackboard_context}"
        )

        json_format = (" Respond ONLY with a valid JSON object in the following format:"
"""
{   
    "prefix": "...", // The prefix of the response. If previous messages contain FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**, make sure to include it in your response too. Else, leave it empty.
    "content": "...", // Overall macro economic analysis writeup
    "macro_indicators": [{
        "indicator": "...", // Name of the macroeconomic indicator (e.g., "Inflation Rate", "GDP Growth", "Fed Funds Rate")
        "current_status": "...", // Current status/value of the indicator
        "impact": "...", // Impact on bond yields and markets
        "trend": "..." // Trend direction (Increasing, Decreasing, Stable)
    }], // A list of key macroeconomic indicators
    "confidence": "", // The confidence of the analysis, a number between 1 and 100
    "market_sentiment": "", // Overall market sentiment assessment (Bullish, Bearish, Neutral)
    "risk_level": "", // Risk level assessment (Low, Medium, High)
    "table": "" // A Markdown table with key macroeconomic indicators and their status
}
""")

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "For your reference, the current date is {current_date}. The company we want to look at is {ticker}"
                    "The JSON format for the response is as follows:\n{json_format}"
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)
        prompt = prompt.partial(json_format=json_format)

        # Create the chain
        chain = prompt | llm

        # Get the messages from the state
        messages = state["messages"]

        # Invoke the chain
        response = chain.invoke({"messages": messages})

        # Parse the response
        try:
            # Extract JSON from the response
            response_text = response.content
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            else:
                json_str = response_text

            result = json.loads(json_str)
            
            # Post analysis to blackboard
            analysis_content = {
                "prefix": result.get("prefix", ""),
                "content": result.get("content", ""),
                "macro_indicators": result.get("macro_indicators", []),
                "confidence": result.get("confidence", "Medium"),
                "market_sentiment": result.get("market_sentiment", "Neutral"),
                "risk_level": result.get("risk_level", "Medium"),
                "table": result.get("table", "")
            }
            
            confidence = result.get("confidence", "Medium")
            if isinstance(confidence, int):
                if confidence >= 80:
                    confidence = "High"
                elif confidence >= 50:
                    confidence = "Medium"
                else:
                    confidence = "Low"
            
            blackboard_agent.post_analysis_report(
                ticker=ticker,
                analysis=analysis_content,
                confidence=confidence
            )
            
            return {
                "messages": messages + [response],
                "macro_analysis": result
            }
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Response text: {response.content}")
            return {
                "messages": messages + [response],
                "macro_analysis": {"error": "Failed to parse response"}
            }

    return macro_economic_analyst_node 