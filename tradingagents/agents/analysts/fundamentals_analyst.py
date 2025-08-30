# -*- coding: utf-8 -*-
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from tradingagents.blackboard.utils import create_agent_blackboard

def create_fundamentals_analyst(llm, toolkit):
    def _analyze_single_ticker_fundamentals(ticker: str, current_date: str, toolkit, llm, memory):
        """Analyze a single ticker for fundamentals and return the report and messages."""
        # Blackboard integration
        blackboard_agent = create_agent_blackboard("FA_001", "FundamentalAnalyst")
        recent_analyses = blackboard_agent.get_analysis_reports(ticker=ticker)
        
        blackboard_context = ""
        if recent_analyses:
            blackboard_context += "\n\nRecent Fundamental Analysis Reports on Blackboard:\n"
            for analysis in recent_analyses[-3:]:
                content = analysis.get('content', {})
                analysis_data = content.get('analysis', {})
                if isinstance(analysis_data, dict):
                    blackboard_context += f"- {analysis['sender'].get('role', 'Unknown')}: {analysis_data.get('recommendation', 'N/A')} (Confidence: {analysis_data.get('confidence', 'N/A')})\n"

        # Get fundamentals data and perform analysis
        curr_situation = f"Fundamentals analysis for {ticker} on {current_date}{blackboard_context}"
        past_memories = []
        past_memory_str = ""
        if memory:
            past_memories = memory.get_memories(curr_situation, n_matches=2)
            past_memory_str = "\n\n".join([rec["recommendation"] for rec in past_memories])

        # Create analysis chain
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional fundamental analyst providing comprehensive financial analysis.
            
Analyze the fundamentals for {ticker} and create a detailed report covering:
- Financial statements analysis (income, balance sheet, cash flow)
- Valuation metrics and ratios
- Profitability and efficiency analysis
- Growth trends and projections
- Competitive positioning
- Financial health assessment

Format your response as a structured analysis with clear sections and actionable insights.
Include financial metrics table with key ratios and their interpretation.

Current date: {current_date}
Past relevant analysis: {past_memory_str}
{blackboard_context}"""),
            MessagesPlaceholder(variable_name="messages"),
        ])

        chain = prompt | llm
        result = chain.invoke({
            "messages": [("human", f"Provide fundamental analysis for {ticker}")],
            "ticker": ticker,
            "current_date": current_date,
            "past_memory_str": past_memory_str,
            "blackboard_context": blackboard_context
        })

        # Extract recommendation and confidence from response
        report = getattr(result, 'content', '') or str(result)
        recommendation = "Neutral"
        confidence = "Medium"
        
        if "BUY" in report.upper() or "UNDERVALUED" in report.upper():
            recommendation = "Bullish"
        elif "SELL" in report.upper() or "OVERVALUED" in report.upper():
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

    def fundamentals_analyst_node(state, memory=None):
        current_date = state["trade_date"]
        
        # Handle both single ticker and multi-ticker portfolio modes
        if "tickers" in state and state.get("tickers"):
            # Multi-ticker portfolio mode - process ALL tickers that need fundamentals analysis
            tickers = state["tickers"]
            individual_reports = state.get("individual_reports", {})
            analyst_completion = state.get("analyst_completion", {})
            fundamentals_completion = analyst_completion.get("fundamentals", {})
            
            # Process each ticker that needs fundamentals analysis
            all_messages = []  # Collect all messages from analysis
            
            for ticker in tickers:
                if not fundamentals_completion.get(ticker, False):
                    try:
                        result = _analyze_single_ticker_fundamentals(ticker, current_date, toolkit, llm, memory)
                        
                        # Update individual reports
                        if ticker not in individual_reports:
                            individual_reports[ticker] = {}
                        individual_reports[ticker]["fundamentals_report"] = result["report"]
                        
                        # Collect messages from this analysis
                        all_messages.extend(result["messages"])
                        
                        # Mark this ticker as complete for fundamentals analysis
                        fundamentals_completion[ticker] = True
                        
                    except Exception as e:
                        print(f"Error analyzing {ticker} for fundamentals: {e}")
                        # Mark as complete to avoid infinite loops
                        fundamentals_completion[ticker] = True
            
            # Update the analyst_completion state properly
            updated_analyst_completion = {
                **analyst_completion,
                "fundamentals": fundamentals_completion
            }
            
            # Update the state - MUST include messages for proper graph routing
            return {
                "messages": all_messages,  # ← This is what was missing!
                "individual_reports": individual_reports,
                "analyst_completion": updated_analyst_completion,
                "fundamentals_report": f"Completed fundamentals analysis for: {', '.join(tickers)}"
            }
        elif "company_of_interest" in state:
            # Single ticker mode (backward compatibility)
            ticker = state["company_of_interest"]
            
            # Process single ticker with original logic
            ticker_report = _analyze_single_ticker_fundamentals(ticker, current_date, toolkit, llm, memory)
            
            return {
                "messages": ticker_report["messages"],
                "fundamentals_report": ticker_report["report"],
            }
        else:
            # Fallback - this shouldn't happen but let's handle it gracefully
            print("Warning: No ticker information found in state")
            return {
                "messages": [],
                "fundamentals_report": "Error: No ticker information available",
            }

    return fundamentals_analyst_node
