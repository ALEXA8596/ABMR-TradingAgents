# TradingAgents/graph/conditional_logic.py

from tradingagents.agents.utils.agent_states import AgentState


class ConditionalLogic:
    """Handles conditional logic for determining graph flow."""

    def __init__(self, max_debate_rounds=1, max_risk_discuss_rounds=1):
        """Initialize with configuration parameters."""
        self.max_debate_rounds = max_debate_rounds
        self.max_risk_discuss_rounds = max_risk_discuss_rounds

    def should_continue_market(self, state: AgentState):
        """Determine if market analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        
        # Check if we're in multi-ticker portfolio mode
        if "tickers" in state and len(state.get("tickers", [])) > 1:
            # In multi-ticker mode, check if current ticker analysis is complete
            current_ticker_index = state.get("current_ticker_index", 0)
            tickers = state.get("tickers", [])
            individual_reports = state.get("individual_reports", {})
            
            if current_ticker_index < len(tickers):
                current_ticker = tickers[current_ticker_index]
                current_ticker_report = individual_reports.get(current_ticker, {})
                
                # If there are tool calls, continue with tools
                if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                    return "tools_market"
                
                # If ticker analysis is complete, return to portfolio optimizer
                if self._is_ticker_analysis_complete(current_ticker_report):
                    return "Multi-Ticker Portfolio Optimizer"  # Route back to Multi-Ticker Portfolio Optimizer
                else:
                    # Analysis not complete, continue with tools or return to portfolio optimizer
                    return "tools_market"  # Continue with tools for more analysis
            else:
                # All tickers processed, return to portfolio optimizer
                return "Multi-Ticker Portfolio Optimizer"
        else:
            # Single ticker mode - use original logic
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return "tools_market"
            return "Msg Clear Market"

    def should_continue_quant_market(self, state: AgentState):
        """Determine if quant market analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools_quant_market"
        return "Msg Clear Quant_market"

    def should_continue_macroeconomic(self, state: AgentState):
        """Determine if macroeconomic analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools_macroeconomic"
        return "Msg Clear Macroeconomic"

    def should_continue_social(self, state: AgentState):
        """Determine if social media analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools_social"
        return "Msg Clear Social"

    def should_continue_news(self, state: AgentState):
        """Determine if news analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools_news"
        return "Msg Clear News"

    def should_continue_fundamentals(self, state: AgentState):
        """Determine if fundamentals analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools_fundamentals"
        return "Msg Clear Fundamentals"
    
    def should_continue_risk_judgment(self, state: AgentState):
        """Determine if risk judgment should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools_Risk Judge"
        return "Msg Clear Risk Judge"

    def should_continue_debate(self, state: AgentState) -> str:
        """Determine if debate should continue."""
        # Handle both single ticker and multi-ticker portfolio modes
        if "investment_debate_states" in state and state.get("tickers"):
            # Multi-ticker portfolio mode - use the first ticker for routing logic
            # In a real implementation, you might want to track which ticker is currently being debated
            ticker = state["tickers"][0] if state["tickers"] else "SPY"
            if ticker in state["investment_debate_states"]:
                count = state["investment_debate_states"][ticker].get("count", 0)
            else:
                count = 0
        elif "investment_debate_state" in state:
            # Single ticker mode
            count = state["investment_debate_state"].get("count", 0)
        else:
            # Fallback - no debate state found
            count = 0

        # Simplified flow: Bull → Bear → Research Manager
        # 1 => Bull Researcher
        # 2 => Bear Researcher  
        # 3+ => Research Manager

        if count == 0:
            return "Bull Researcher"
        elif count == 1:
            return "Bear Researcher"
        else:
            # After both researchers have spoken, go to Research Manager
            return "Research Manager"

    def should_continue_risk_analysis(self, state: AgentState) -> str:
        """Determine if risk analysis should continue."""
        # Handle both single ticker and multi-ticker portfolio modes
        if "risk_debate_states" in state and state.get("tickers"):
            # Multi-ticker portfolio mode - use the first ticker for routing logic
            ticker = state["tickers"][0] if state["tickers"] else "SPY"
            if ticker in state["risk_debate_states"]:
                count = state["risk_debate_states"][ticker].get("count", 0)
            else:
                count = 0
        elif "risk_debate_state" in state:
            # Single ticker mode
            count = state["risk_debate_state"].get("count", 0)
        else:
            # Fallback - no risk debate state found
            count = 0
            
        print(f"[DEBUG] should_continue_risk_analysis: count={count}, max_risk_discuss_rounds={self.max_risk_discuss_rounds}")
        # Check if we've reached the maximum number of rounds
        if count >= 2 * self.max_risk_discuss_rounds:  # Simplified: 2 analysts instead of 3
            print("[DEBUG] Risk analysis complete. Handing off to Risk Judge.")
            return "Risk Judge"
        
        # Simplified flow: Risky → Safe → Risk Judge
        # 1 => Risky Analyst
        # 2 => Safe Analyst
        # 3+ => Risk Judge

        if count == 0:
            print("[DEBUG] Next: Risky Analyst")
            return "Risky Analyst"
        elif count == 1:
            print("[DEBUG] Next: Safe Analyst")
            return "Safe Analyst"
        else:
            # After both analysts have spoken, go to Risk Judge
            print("[DEBUG] Next: Risk Judge")
            return "Risk Judge"

    def should_continue_portfolio_flow(self, state: AgentState) -> str:
        """Determine if portfolio optimization flow should continue."""
        # Check if we're in multi-ticker portfolio mode
        if "tickers" in state and len(state.get("tickers", [])) > 1:
            # Multi-ticker portfolio mode - go to multi-ticker portfolio optimizer
            return "Multi-Ticker Portfolio Optimizer"
        else:
            # Single ticker mode - go to regular portfolio optimizer
            return "Portfolio Optimizer"

    def should_continue_ticker_analysis(self, state):
        """Determine if we should continue analyzing the current ticker."""
        current_ticker_index = state.get("current_ticker_index", 0)
        tickers = state.get("tickers", [])
        
        if current_ticker_index >= len(tickers):
            return "portfolio_optimization"
        
        current_ticker = tickers[current_ticker_index]
        individual_reports = state.get("individual_reports", {})
        
        # Check if current ticker analysis is complete
        current_ticker_report = individual_reports.get(current_ticker, {})
        if self._is_ticker_analysis_complete(current_ticker_report):
            # Check if this is the last ticker
            if current_ticker_index == len(tickers) - 1:
                # Last ticker complete, proceed to portfolio optimization
                return "portfolio_optimization"
            else:
                # Move to next ticker
                return "next_ticker"
        else:
            # Current ticker needs analysis - continue with analysis flow
            # This should route back to the analysis agents, not the portfolio optimizer
            return "continue_analysis"

    def _is_ticker_analysis_complete(self, ticker_reports):
        """Check if a ticker's analysis is complete."""
        # Consider ticker complete if it has any non-empty analysis reports (even if data retrieval failed)
        has_any_analysis = any([
            ticker_reports.get("market_report") and ticker_reports.get("market_report") != "",
            ticker_reports.get("fundamentals_report") and ticker_reports.get("fundamentals_report") != "",
            ticker_reports.get("sentiment_report") and ticker_reports.get("sentiment_report") != "",
            ticker_reports.get("news_report") and ticker_reports.get("news_report") != ""
        ])
        
        return has_any_analysis or ticker_reports.get("analysis_complete", False)

    def should_continue_portfolio_analysis(self, state):
        """Determine if portfolio analysis should continue."""
        tickers = state.get("tickers", [])
        individual_reports = state.get("individual_reports", {})
        
        # Check if all ticker analyses are complete
        all_complete = all(
            individual_reports.get(ticker, {}).get("analysis_complete", False)
            for ticker in tickers
        )
        
        if all_complete:
            return "complete"
        else:
            return "continue"