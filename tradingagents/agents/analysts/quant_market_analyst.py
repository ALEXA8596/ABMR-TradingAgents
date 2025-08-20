from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from tradingagents.blackboard.utils import create_agent_blackboard


def create_market_analyst(llm, toolkit):

    def market_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        # Blackboard integration
        blackboard_agent = create_agent_blackboard("QMA_001", "QuantMarketAnalyst")
        # Read recent market analysis reports for context
        recent_analyses = blackboard_agent.get_analysis_reports(ticker=ticker)
        blackboard_context = ""
        if recent_analyses:
            blackboard_context += "\n\nRecent Market Analysis Reports on Blackboard:\n"
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
            """You are a trading assistant tasked with analyzing financial markets. Your role is to select the **most relevant indicators** for a given market condition or trading strategy from the following list. The goal is to choose up to **8 indicators** that provide complementary insights without redundancy. Categories and each category's indicators are:

Moving Averages:
- close_50_sma: 50 SMA: A medium-term trend indicator. Usage: Identify trend direction and serve as dynamic support/resistance. Tips: It lags price; combine with faster indicators for timely signals.
- close_200_sma: 200 SMA: A long-term trend benchmark. Usage: Confirm overall market trend and identify golden/death cross setups. Tips: It reacts slowly; best for strategic trend confirmation rather than frequent trading entries.
- close_10_ema: 10 EMA: A responsive short-term average. Usage: Capture quick shifts in momentum and potential entry points. Tips: Prone to noise in choppy markets; use alongside longer averages for filtering false signals.

MACD Related:
- macd: MACD: Computes momentum via differences of EMAs. Usage: Look for crossovers and divergence as signals of trend changes. Tips: Confirm with other indicators in low-volatility or sideways markets.
- macds: MACD Signal: An EMA smoothing of the MACD line. Usage: Use crossovers with the MACD line to trigger trades. Tips: Should be part of a broader strategy to avoid false positives.
- macdh: MACD Histogram: Shows the gap between the MACD line and its signal. Usage: Visualize momentum strength and spot divergence early. Tips: Can be volatile; complement with additional filters in fast-moving markets.

Momentum Indicators:
- rsi: RSI: Measures momentum to flag overbought/oversold conditions. Usage: Apply 70/30 thresholds and watch for divergence to signal reversals. Tips: In strong trends, RSI may remain extreme; always cross-check with trend analysis.

Volatility Indicators:
- boll: Bollinger Middle: A 20 SMA serving as the basis for Bollinger Bands. Usage: Acts as a dynamic benchmark for price movement. Tips: Combine with the upper and lower bands to effectively spot breakouts or reversals.
- boll_ub: Bollinger Upper Band: Typically 2 standard deviations above the middle line. Usage: Signals potential overbought conditions and breakout zones. Tips: Confirm signals with other tools; prices may ride the band in strong trends.
- boll_lb: Bollinger Lower Band: Typically 2 standard deviations below the middle line. Usage: Indicates potential oversold conditions. Tips: Use additional analysis to avoid false reversal signals.
- atr: ATR: Averages true range to measure volatility. Usage: Set stop-loss levels and adjust position sizes based on current market volatility. Tips: It's a reactive measure, so use it as part of a broader risk management strategy.

Volume-Based Indicators:
- vwma: VWMA: A moving average weighted by volume. Usage: Confirm trends by integrating price action with volume data. Tips: Watch for skewed results from volume spikes; use in combination with other volume analyses.

- Select indicators that provide diverse and complementary information. Avoid redundancy (e.g., do not select both rsi and stochrsi). Also briefly explain why they are suitable for the given market context. When you tool call, please use the exact name of the indicators provided above as they are defined parameters, otherwise your call will fail. Please make sure to call get_YFin_data first to retrieve the CSV that is needed to generate indicators. Write a very detailed and nuanced report of the trends you observe. Do not simply state the trends are mixed, provide detailed and finegrained analysis and insights that may help traders make decisions."""
            + """ Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read."""
            + f"\n\nBlackboard Context:{blackboard_context}"
        )

        json_format = (" Respond ONLY with a valid JSON object in the following format:"
"""
{   
    "prefix": "...", // The prefix of the response. If previous messages contain FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**, make sure to include it in your response too. Else, leave it empty.
    "content": "...", // Overall writeup of the response
    "indicators": [{
        "name": "...", // Include just the name of the indicator, e.g. close_50_sma
        "rationale": "This indicator is relevant because..."
    }], // A list of indicators selected, each with a name and reason for selection
    "confidence": "", // The confidence of the response, a number between 1 and 100
    "decision": "", // the decision of the response as a scale from 1 to 100, where 1 is do not trade and 100 is trade
    "table": "" // A Markdown table with key points in the report, organized and easy to read
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

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke(state["messages"])

        report = ""

        print(result.content)
        
        if len(result.tool_calls) == 0:
            report = result.content.encode('utf-8', errors='replace').decode('utf-8') if result.content else ""

        # Escape the result content to handle Unicode characters
        if hasattr(result, 'content') and result.content:
            result.content = result.content.encode('utf-8', errors='replace').decode('utf-8')
       
        # Post the generated report to the blackboard
        # Extract recommendation and confidence heuristically
        recommendation = "Neutral"
        confidence = "Medium"
        if "BUY" in report.upper():
            recommendation = "Bullish"
        elif "SELL" in report.upper():
            recommendation = "Bearish"
        if "HIGH" in report.upper() and "CONFIDENCE" in report.upper():
            confidence = "High"
        elif "LOW" in report.upper() and "CONFIDENCE" in report.upper():
            confidence = "Low"
        analysis_content = {
            "ticker": ticker,
            "recommendation": recommendation,
            "confidence": confidence,
            "analysis": report
        }
        blackboard_agent.post_analysis_report(
            ticker=ticker,
            analysis=analysis_content,
            confidence=confidence
        )
       
        return {
            "messages": [result],
            "market_report": report,
        }

    return market_analyst_node
