from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from tradingagents.blackboard.utils import create_agent_blackboard


def create_social_media_analyst(llm, toolkit):
    def _analyze_single_ticker_social(ticker: str, current_date: str, toolkit, llm, memory):
        """Analyze a single ticker for social media sentiment and return the report and messages."""
        # Blackboard integration
        blackboard_agent = create_agent_blackboard("SMA_001", "SocialMediaAnalyst")
        recent_analyses = blackboard_agent.get_analysis_reports(ticker=ticker)
        
        blackboard_context = ""
        if recent_analyses:
            blackboard_context += "\n\nRecent Social Media Analysis Reports on Blackboard:\n"
            for analysis in recent_analyses[-3:]:
                content = analysis.get('content', {})
                analysis_data = content.get('analysis', {})
                if isinstance(analysis_data, dict):
                    blackboard_context += f"- {analysis['sender'].get('role', 'Unknown')}: {analysis_data.get('recommendation', 'N/A')} (Confidence: {analysis_data.get('confidence', 'N/A')})\n"

        # Get social media data and perform analysis
        curr_situation = f"Social media analysis for {ticker} on {current_date}{blackboard_context}"
        past_memories = []
        past_memory_str = ""
        if memory:
            past_memories = memory.get_memories(curr_situation, n_matches=2)
            past_memory_str = "\n\n".join([rec["recommendation"] for rec in past_memories])

        # Create analysis chain
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional social media analyst providing comprehensive sentiment analysis.
            
Analyze the social media sentiment for {ticker} and create a detailed report covering:
- Reddit sentiment and discussions
- Twitter/X sentiment trends
- Social media volume and engagement
- Key topics and themes
- Sentiment shifts and timing
- Impact on market sentiment

Format your response as a structured analysis with clear sections and actionable insights.
Include sentiment trends table with key metrics and confidence levels.

Current date: {current_date}
Past relevant analysis: {past_memory_str}
{blackboard_context}"""),
            MessagesPlaceholder(variable_name="messages"),
        ])

        chain = prompt | llm
        result = chain.invoke({
            "messages": [("human", f"Provide social media sentiment analysis for {ticker}")],
            "ticker": ticker,
            "current_date": current_date,
            "past_memory_str": past_memory_str,
            "blackboard_context": blackboard_context
        })

        # Extract recommendation and confidence from response
        report = getattr(result, 'content', '') or str(result)
        recommendation = "Neutral"
        confidence = "Medium"
        
        if "BULLISH" in report.upper() or "POSITIVE" in report.upper():
            recommendation = "Bullish"
        elif "BEARISH" in report.upper() or "NEGATIVE" in report.upper():
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

    def social_media_analyst_node(state, memory=None):
        current_date = state["trade_date"]
        
        # Handle both single ticker and multi-ticker portfolio modes
        if "tickers" in state and state.get("tickers"):
            # Multi-ticker portfolio mode - process ALL tickers that need social media analysis
            tickers = state["tickers"]
            individual_reports = state.get("individual_reports", {})
            analyst_completion = state.get("analyst_completion", {})
            social_completion = analyst_completion.get("social", {})
            
            # CRITICAL FIX: Check if we've already completed analysis for all tickers
            all_complete = True
            for ticker in tickers:
                ticker_complete = social_completion.get(ticker, False)
                has_sentiment_report = bool(individual_reports.get(ticker, {}).get("sentiment_report"))
                if not ticker_complete or not has_sentiment_report:
                    all_complete = False
                    break
            
            if all_complete:
                # All tickers already analyzed, return current state without re-analyzing
                print(f"[DEBUG] Social media analysis already complete for all tickers: {tickers}")
                # CRITICAL FIX: Return proper state with existing messages to maintain graph flow
                return {
                    "messages": state.get("messages", []),
                    "individual_reports": individual_reports,
                    "analyst_completion": analyst_completion,
                    "sentiment_report": f"Social media analysis already complete for: {', '.join(tickers)}",
                    # Ensure we don't lose any existing state
                    "tickers": tickers,
                    "trade_date": current_date
                }
            
            # Process each ticker that needs social media analysis
            all_messages = []  # Collect all messages from analysis
            processed_tickers = []
            
            for ticker in tickers:
                if not social_completion.get(ticker, False) or not individual_reports.get(ticker, {}).get("sentiment_report"):
                    try:
                        print(f"[DEBUG] Processing social media analysis for ticker: {ticker}")
                        result = _analyze_single_ticker_social(ticker, current_date, toolkit, llm, memory)
                        
                        # Update individual reports
                        if ticker not in individual_reports:
                            individual_reports[ticker] = {}
                        individual_reports[ticker]["sentiment_report"] = result["report"]
                        
                        # Collect messages from this analysis
                        all_messages.extend(result["messages"])
                        
                        # Mark this ticker as complete for social media analysis
                        social_completion[ticker] = True
                        processed_tickers.append(ticker)
                        
                        print(f"[DEBUG] Completed social media analysis for ticker: {ticker}")
                        
                    except Exception as e:
                        print(f"Error analyzing {ticker} for social media: {e}")
                        # Mark as complete to avoid infinite loops
                        social_completion[ticker] = True
                        processed_tickers.append(ticker)
            
            # Update the analyst_completion state properly
            updated_analyst_completion = {
                **analyst_completion,
                "social": social_completion
            }
            
            # Update the state - MUST include messages for proper graph routing
            return {
                "messages": all_messages,  # ← This is what was missing!
                "individual_reports": individual_reports,
                "analyst_completion": updated_analyst_completion,
                "sentiment_report": f"Completed social media analysis for: {', '.join(processed_tickers)}"
            }
        else:
            # Single ticker mode
            company_name = state.get("company_of_interest", "SPY")
            try:
                result = _analyze_single_ticker_social(company_name, current_date, toolkit, llm, memory)
                return {
                    "sentiment_report": result["report"],
                    "messages": result["messages"]
                }
            except Exception as e:
                print(f"Error in social media analysis: {e}")
                return {
                    "sentiment_report": f"Error in social media analysis: {e}",
                    "messages": []
                }

    return social_media_analyst_node
