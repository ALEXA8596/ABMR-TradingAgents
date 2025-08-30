from langchain_core.prompts import MessagesPlaceholder, ChatPromptTemplate
import time
import json
from tradingagents.blackboard.utils import create_agent_blackboard


def create_market_analyst(llm, toolkit):
    def _analyze_single_ticker(ticker: str, current_date: str, toolkit, llm, memory):
        """Analyze a single ticker and return the report and messages."""
        # Blackboard integration
        blackboard_agent = create_agent_blackboard("MA_001", "MarketAnalyst")
        recent_analyses = blackboard_agent.get_analysis_reports(ticker=ticker)
        
        blackboard_context = ""
        if recent_analyses:
            blackboard_context += "\n\nRecent Market Analyses on Blackboard:\n"
            for analysis in recent_analyses[-3:]:
                content = analysis.get('content', {})
                analysis_data = content.get('analysis', {})
                if isinstance(analysis_data, dict):
                    blackboard_context += f"- {analysis['sender'].get('role', 'Unknown')}: {analysis_data.get('recommendation', 'N/A')} (Confidence: {analysis_data.get('confidence', 'N/A')})\n"

        # Get market data and perform analysis
        curr_situation = f"Market analysis for {ticker} on {current_date}{blackboard_context}"
        past_memories = []
        past_memory_str = ""
        if memory:
            past_memories = memory.get_memories(curr_situation, n_matches=2)
            past_memory_str = "\n\n".join([rec["recommendation"] for rec in past_memories])

        # Create analysis chain
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional market analyst providing comprehensive technical analysis.
            
Analyze the provided market data for {ticker} and create a detailed technical analysis report.
Use all available indicators to provide insights on:
- Price action and trends
- Support and resistance levels  
- Technical indicators (RSI, MACD, moving averages, etc.)
- Volume analysis
- Risk factors and opportunities

Format your response as a structured analysis with clear sections and actionable insights.
Include a summary table with key metrics and their interpretation.

Current date: {current_date}
Past relevant analysis: {past_memory_str}
{blackboard_context}"""),
            MessagesPlaceholder(variable_name="messages"),
        ])

        chain = prompt | llm
        result = chain.invoke({
            "messages": [("human", f"Provide technical analysis for {ticker}")],
            "ticker": ticker,
            "current_date": current_date,
            "past_memory_str": past_memory_str,
            "blackboard_context": blackboard_context
        })

        # Extract recommendation and confidence from response
        report = getattr(result, 'content', '') or str(result)
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
            
        # Post to blackboard
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
            "report": report,
            "messages": [result],
            "recommendation": recommendation,
            "confidence": confidence
        }

    def market_analyst_node(state, memory=None):
        current_date = state["trade_date"]
        
        # Handle both single ticker and multi-ticker portfolio modes
        if "tickers" in state and state.get("tickers"):
            # Multi-ticker portfolio mode - process ALL tickers that need market analysis
            tickers = state["tickers"]
            individual_reports = state.get("individual_reports", {})
            analyst_completion = state.get("analyst_completion", {})
            market_completion = analyst_completion.get("market", {})
            
            # Find all tickers that need market analysis
            tickers_to_process = [
                ticker for ticker in tickers 
                if not market_completion.get(ticker, False) and 
                not individual_reports.get(ticker, {}).get("market_report", "")
            ]
            
            if not tickers_to_process:
                # All tickers already have market analysis, mark all as complete
                updated_analyst_completion = {
                    **analyst_completion,
                    "market": {ticker: True for ticker in tickers}
                }
                return {
                    "messages": [],
                    "market_report": "All tickers already analyzed",
                    "individual_reports": individual_reports,
                    "analyst_completion": updated_analyst_completion
                }
            
            # Process all tickers that need market analysis
            all_reports = {}
            all_messages = []
            
            for ticker in tickers_to_process:
                print(f"🔍 Market Analyst processing {ticker}...")
                
                # Process this ticker
                ticker_report = _analyze_single_ticker(ticker, current_date, toolkit, llm, memory or None)
                all_reports[ticker] = ticker_report["report"]
                all_messages.extend(ticker_report["messages"])
                
                # Update individual reports
                if ticker not in individual_reports:
                    individual_reports[ticker] = {}
                individual_reports[ticker]["market_report"] = ticker_report["report"]
            
            # Mark all processed tickers as complete for market analysis
            updated_market_completion = {**market_completion}
            for ticker in tickers_to_process:
                updated_market_completion[ticker] = True
            
            updated_analyst_completion = {
                **analyst_completion,
                "market": updated_market_completion
            }
            
            return {
                "messages": all_messages,
                "market_report": f"Completed market analysis for: {', '.join(tickers_to_process)}",
                "individual_reports": individual_reports,
                "analyst_completion": updated_analyst_completion
            }
        elif "company_of_interest" in state:
            # Single ticker mode
            ticker = state["company_of_interest"] 
            company_name = state["company_of_interest"]
            is_portfolio_mode = False
        else:
            # Fallback
            ticker = "SPY"
            company_name = "SPY"
            is_portfolio_mode = False

        # Blackboard integration
        blackboard_agent = create_agent_blackboard("MA_001", "MarketAnalyst")
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
            f"""You are a trading assistant tasked with analyzing the financial market for {ticker} specifically. 
                    This is part of a multi-ticker portfolio analysis, but you should focus ONLY on {ticker} right now.
                    
                    Your role is to select the **most relevant indicators** for {ticker} from the following comprehensive list. 
                    The goal is to choose up to **8 indicators** that provide complementary insights without redundancy. 
                    Categories and each category's indicators are:

Basic Price Analysis:
- delta: Price change between periods
- log: Log return calculation
- max: Maximum price in range
- min: Minimum price in range
- middle: (close + high + low) / 3 - typical price
- compare: Price comparisons (le, ge, lt, gt, eq, ne)
- count: Count occurrences (both backward and forward)
- cross: Upward and downward crossover signals

Moving Averages:
- close_50_sma: 50 SMA: A medium-term trend indicator. Usage: Identify trend direction and serve as dynamic support/resistance. Tips: It lags price; combine with faster indicators for timely signals.
- close_200_sma: 200 SMA: A long-term trend benchmark. Usage: Confirm overall market trend and identify golden/death cross setups. Tips: It reacts slowly; best for strategic trend confirmation rather than frequent trading entries.
- close_10_ema: 10 EMA: A responsive short-term average. Usage: Capture quick shifts in momentum and potential entry points. Tips: Prone to noise in choppy markets; use alongside longer averages for filtering false signals.
- dma: Different of Moving Average (10, 50): Shows divergence between short and long-term trends
- tema: Triple Exponential Moving Average: Reduces lag while maintaining smoothness
- kama: Kaufman's Adaptive Moving Average: Adjusts to market volatility automatically
- boll: Bollinger Bands: Volatility-based envelope indicator. Usage: Identify overbought/oversold conditions and potential breakout zones. Tips: Bands contract in low volatility and expand in high volatility; use with other indicators for confirmation.
- boll_mb: Bollinger Middle Band: The moving average center line. Usage: Core trend reference and mean reversion target. Tips: Acts as dynamic support/resistance; price often returns to this line.
- boll_lb: Bollinger Lower Band: Typically 2 standard deviations below the middle line. Usage: Indicates potential oversold conditions. Tips: Use additional analysis to avoid false reversal signals.
- atr: ATR: Averages true range to measure volatility. Usage: Set stop-loss levels and adjust position sizes based on current market volatility. Tips: It's a reactive measure, so use it as part of a broader risk management strategy.
- tr: True Range: Single-period volatility measure
- mad: Mean Absolute Deviation: Alternative volatility measure
- z: Z-Score: Standardized price deviation from mean

MACD Related:
- macd: MACD: Computes momentum via differences of EMAs. Usage: Look for crossovers and divergence as signals of trend changes. Tips: Confirm with other indicators in low-volatility or sideways markets.
- macds: MACD Signal: An EMA smoothing of the MACD line. Usage: Use crossovers with the MACD line to trigger trades. Tips: Should be part of a broader strategy to avoid false positives.
- macdh: MACD Histogram: Shows the gap between the MACD line and its signal. Usage: Visualize momentum strength and spot divergence early. Tips: Can be volatile; complement with additional filters in fast-moving markets.

Momentum Indicators:
- rsi: RSI: Measures momentum to flag overbought/oversold conditions. Usage: Apply 70/30 thresholds and watch for divergence to signal reversals. Tips: In strong trends, RSI may remain extreme; always cross-check with trend analysis.
- rsv: Raw Stochastic Value: Basic stochastic calculation before smoothing
- kdj: Stochastic Oscillator: Enhanced stochastic with J-line for early signals
- stochrsi: Stochastic RSI: Combines RSI with stochastic formula for enhanced sensitivity
- wr: Williams %R: Overbought/oversold oscillator similar to stochastic
- roc: Rate of Change: Momentum indicator measuring percentage price change
- ao: Awesome Oscillator: Measures momentum using 5 and 34-period moving averages
- ppo: Percentage Price Oscillator: MACD expressed as percentage
- ker: Kaufman's Efficiency Ratio: Measures trend strength vs noise
- inertia: Inertia Indicator: Momentum measure using linear regression
- kst: Know Sure Thing: Smoothed momentum oscillator using multiple timeframes
- pgo: Pretty Good Oscillator: Normalized price oscillator

Trend & Directional Indicators:
- dmi: Directional Movement Index system including:
- pdi: +DI: Positive Directional Indicator - measures upward price movement
- mdi: -DI: Negative Directional Indicator - measures downward price movement
- adx: Average Directional Movement Index: Measures trend strength
- adxr: Smoothed Moving Average of ADX: Less volatile version of ADX
- trix: Triple Exponential Moving Average: Momentum oscillator with triple smoothing
- aroon: Aroon Oscillator: Measures time since highest high and lowest low
- cti: Correlation Trend Indicator: Measures price correlation with time
- supertrend: Trend following indicator with upper and lower bands

Volume-Based Indicators:
- vwma: VWMA: A moving average weighted by volume. Usage: Confirm trends by integrating price action with volume data. Tips: Watch for skewed results from volume spikes; use in combination with other volume analyses.
- vr: Volume Variation Index: Compares current volume to historical average
- mfi: Money Flow Index: Volume-weighted RSI combining price and volume
- pvo: Percentage Volume Oscillator: MACD applied to volume data

Specialized Oscillators:
- cci: Commodity Channel Index: Measures deviation from statistical mean
- cr: Energy Index (Intermediate Willingness Index): Measures buying/selling pressure
- wt: LazyBear's Wave Trend: Smoothed momentum oscillator
- chop: Choppiness Index: Determines if market is trending or sideways
- bop: Balance of Power: Measures buying vs selling pressure
- eri: Elder-Ray Index: Shows bull and bear power
- ftr: Gaussian Fisher Transform: Normalizes price data for clearer signals
- rvgi: Relative Vigor Index: Measures conviction of price movement
- psl: Psychological Line: Percentage of up days over specified period
- qqe: Quantitative Qualitative Estimation: Smoothed RSI-based indicator

Advanced Analysis:
- ichimoku: Ichimoku Cloud: Complete trend analysis system with multiple components
- coppock: Coppock Curve: Long-term momentum indicator for major trend changes

- Select indicators that provide diverse and complementary information for {ticker} specifically. Avoid redundancy (e.g., do not select both rsi and stochrsi unless specifically needed). Also briefly explain why they are suitable for {ticker} in the given market context. When you tool call, please use the exact name of the indicators provided above as they are defined parameters, otherwise your call will fail. Please make sure to call get_YFin_data first to retrieve the CSV that is needed to generate indicators. Write a very detailed and nuanced report of the trends you observe for {ticker}. Do not simply state the trends are mixed, provide detailed and finegrained analysis and insights that may help traders make decisions."""
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
        
        # Extract report content - this should work regardless of tool calls
        if hasattr(result, 'content') and result.content:
            report = result.content.encode('utf-8', errors='replace').decode('utf-8')

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

        # Handle portfolio mode by updating individual reports
        if is_portfolio_mode:
            # Update the individual reports for the ticker being analyzed
            if "individual_reports" in state:
                if ticker not in state["individual_reports"]:
                    state["individual_reports"][ticker] = {}
                state["individual_reports"][ticker]["market_report"] = report
                
                # DON'T mark as complete here - market analysis is just one step
                # Completion will be determined by the conditional logic based on
                # having market_report + investment_plan + final_trade_decision
            
            # Update analyst completion tracking for phase-based processing
            analyst_completion = state.get("analyst_completion", {})
            market_completion = analyst_completion.get("market", {})
            updated_analyst_completion = {
                **analyst_completion,
                "market": {
                    **market_completion,
                    ticker: True
                }
            }
            
            return {
                "messages": [result],
                "market_report": report,
                "individual_reports": state.get("individual_reports", {}),
                "current_ticker_index": state.get("current_ticker_index", 0),
                "analyst_completion": updated_analyst_completion
            }
        else:
            # Single ticker mode
            return {
                "messages": [result],
                "market_report": report,
            }

    return market_analyst_node
