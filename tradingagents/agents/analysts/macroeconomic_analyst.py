from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from tradingagents.blackboard.utils import create_agent_blackboard


def create_macroeconomic_analyst(llm, toolkit):
    def _analyze_single_ticker_macro(ticker: str, current_date: str, toolkit, llm, memory):
        """Analyze a single ticker for macroeconomic factors and return the report and messages."""
        # Blackboard integration
        blackboard_agent = create_agent_blackboard("MEA_001", "MacroeconomicAnalyst")
        recent_analyses = blackboard_agent.get_analysis_reports(ticker=ticker)
        
        blackboard_context = ""
        if recent_analyses:
            blackboard_context += "\n\nRecent Macroeconomic Analysis Reports on Blackboard:\n"
            for analysis in recent_analyses[-3:]:
                content = analysis.get('content', {})
                blackboard_context += f"- {analysis['sender'].get('role', 'Unknown')}: {content.get('recommendation', 'N/A')} (Confidence: {content.get('confidence', 'N/A')})\n"

        # Get macroeconomic data and perform analysis
        curr_situation = f"Macroeconomic analysis for {ticker} on {current_date}{blackboard_context}"
        past_memories = []
        past_memory_str = ""
        if memory:
            past_memories = memory.get_memories(curr_situation, n_matches=2)
            past_memory_str = "\n\n".join([rec["recommendation"] for rec in past_memories])

        # Create analysis chain
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional macroeconomic analyst providing comprehensive analysis.
            
Analyze the macroeconomic environment for {ticker} and create a detailed report covering:
- Economic indicators (GDP, inflation, unemployment, etc.)
- Monetary policy impacts
- Interest rate environment
- Global economic trends affecting the security
- Sector-specific economic factors
- Risk assessment from macroeconomic perspective

Format your response as a structured analysis with clear sections and actionable insights.
Include economic variables table with current values, trends, and market impacts.

Current date: {current_date}
Past relevant analysis: {past_memory_str}
{blackboard_context}"""),
            MessagesPlaceholder(variable_name="messages"),
        ])

        chain = prompt | llm
        result = chain.invoke({
            "messages": [("human", f"Provide macroeconomic analysis for {ticker}")],
            "ticker": ticker,
            "current_date": current_date,
            "past_memory_str": past_memory_str,
            "blackboard_context": blackboard_context
        })

        # Extract recommendation and confidence from response
        report = getattr(result, 'content', '') or str(result)
        recommendation = "Neutral"
        confidence = "Medium"
        
        if "POSITIVE" in report.upper() or "BULLISH" in report.upper():
            recommendation = "Bullish"
        elif "NEGATIVE" in report.upper() or "BEARISH" in report.upper():
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

    def macroeconomic_analyst_node(state, memory=None):
        current_date = state["trade_date"]
        
        # Handle both single ticker and multi-ticker portfolio modes
        if "tickers" in state and state.get("tickers"):
            # Multi-ticker portfolio mode - process ALL tickers that need macroeconomic analysis
            tickers = state["tickers"]
            individual_reports = state.get("individual_reports", {})
            analyst_completion = state.get("analyst_completion", {})
            macro_completion = analyst_completion.get("macroeconomic", {})
            
            # Find all tickers that need macroeconomic analysis
            tickers_to_process = [
                ticker for ticker in tickers 
                if not macro_completion.get(ticker, False) and 
                not individual_reports.get(ticker, {}).get("macroeconomic_report", "")
            ]
            
            if not tickers_to_process:
                # All tickers already have macroeconomic analysis, mark all as complete
                updated_analyst_completion = {
                    **analyst_completion,
                    "macroeconomic": {ticker: True for ticker in tickers}
                }
                return {
                    "messages": [],
                    "macroeconomic_report": "All tickers already analyzed",
                    "individual_reports": individual_reports,
                    "analyst_completion": updated_analyst_completion
                }
            
            # Process all tickers that need macroeconomic analysis
            all_reports = {}
            all_messages = []
            
            for ticker in tickers_to_process:
                print(f"🌍 Macroeconomic Analyst processing {ticker}...")
                
                # Process this ticker
                ticker_report = _analyze_single_ticker_macro(ticker, current_date, toolkit, llm, memory)
                all_reports[ticker] = ticker_report["report"]
                all_messages.extend(ticker_report["messages"])
                
                # Update individual reports
                if ticker not in individual_reports:
                    individual_reports[ticker] = {}
                individual_reports[ticker]["macroeconomic_report"] = ticker_report["report"]
            
            # Mark all processed tickers as complete for macroeconomic analysis
            updated_macro_completion = {**macro_completion}
            for ticker in tickers_to_process:
                updated_macro_completion[ticker] = True
            
            updated_analyst_completion = {
                **analyst_completion,
                "macroeconomic": updated_macro_completion
            }
            
            return {
                "messages": all_messages,
                "macroeconomic_report": f"Completed macroeconomic analysis for: {', '.join(tickers_to_process)}",
                "individual_reports": individual_reports,
                "analyst_completion": updated_analyst_completion
            }
        elif "company_of_interest" in state:
            # Single ticker mode (backward compatibility)
            ticker = state["company_of_interest"]
            company_name = state["company_of_interest"]
            is_portfolio_mode = False
            
            # Process single ticker with original logic
            ticker_report = _analyze_single_ticker_macro(ticker, current_date, toolkit, llm, memory)
            
            return {
                "messages": ticker_report["messages"],
                "macroeconomic_report": ticker_report["report"],
            }
        else:
            # Fallback - this shouldn't happen but let's handle it gracefully
            print("Warning: No ticker information found in state")
            return {
                "messages": [],
                "macroeconomic_report": "Error: No ticker information available",
            }

    return macroeconomic_analyst_node 