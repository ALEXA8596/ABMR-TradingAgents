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

        # 1 => Bullish Researcher
        # 2 => Bearish Researcher
        # 3 => Bullish Researcher Ask
        # 4 => Bullish Researcher Ans
        # 5 => Bearish Researcher Ask
        # 6 => Bullish Researcher Ans
        # 7 => Bullish Researcher
        # 8 => Bearish Researcher
        # 9 => Research Manager
        # Repeat 3 to 9 as needed

        if count == 0:
            return "Bull Researcher"
        elif count == 1:
            return "Bear Researcher"
        elif count == 2:
            return "Bull Researcher Ask"
        elif count == 3:
            return "Bull Researcher Ans"
        elif count == 4:
            return "Bear Researcher Ask"
        elif count == 5:
            return "Bull Researcher Ans"
        elif count == 6:
            return "Bull Researcher"
        elif count == 7:
            return "Bear Researcher"
        elif count == 8:
            return "Research Manager"
        else:
            # For counts >= 9, repeat 3-9 as needed
            repeat_sequence = [
                "Bull Researcher Ask",
                "Bull Researcher Ans",
                "Bear Researcher Ask",
                "Bull Researcher Ans",
                "Bull Researcher",
                "Bear Researcher",
                "Research Manager",
            ]
            idx = (count - 2) % len(repeat_sequence)
            return repeat_sequence[idx]

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
        if (
            count >= 3 * self.max_risk_discuss_rounds
        ):  # 3 rounds of back-and-forth between 3 agents
            print("[DEBUG] Risk debate complete. Handing off to Risk Judge.")
            return "Risk Judge"
        
        
        # 1 => Risky Analyst
        # 2 => Safe Analyst
        # 3 => Neutral Analyst
        # 4 => Risky Analyst Ask
        # 5 => Risky Analyst Ans
        # 6 => Safe Analyst Ask
        # 7 => Risky Analyst Ans
        # 8 => Risky Analyst
        # 9 => Safe Analyst
        # Repeat 4 to 9 as needed

        # 1 => Risky Analyst
        # 2 => Safe Analyst
        # 3 => Neutral Analyst
        # 4 => Risky Analyst Ask
        # 5 => Risky Analyst Ans
        # 6 => Safe Analyst Ask
        # 7 => Risky Analyst Ans
        # 8 => Risky Analyst
        # 9 => Safe Analyst
        # Repeat 4 to 9 as needed

        if count == 0:
            print("[DEBUG] Next: Risky Analyst")
            return "Risky Analyst"
        elif count == 1:
            print("[DEBUG] Next: Safe Analyst")
            return "Safe Analyst"
        elif count == 2:
            print("[DEBUG] Next: Neutral Analyst")
            return "Neutral Analyst"
        elif count == 3:
            print("[DEBUG] Next: Risky Analyst Ask")
            return "Risky Analyst Ask"
        elif count == 4:
            print("[DEBUG] Next: Risky Analyst Ans")
            return "Risky Analyst Ans"
        elif count == 5:
            print("[DEBUG] Next: Safe Analyst Ask")
            return "Safe Analyst Ask"
        elif count == 6:
            print("[DEBUG] Next: Risky Analyst Ans")
            return "Risky Analyst Ans"
        elif count == 7:
            print("[DEBUG] Next: Risky Analyst")
            return "Risky Analyst"
        elif count == 8:
            print("[DEBUG] Next: Safe Analyst")
            return "Safe Analyst"
        else:
            # For counts >= 9, repeat sequence 4-9 pattern (mapped via repeat_sequence) dynamically
            repeat_sequence = [
                "Risky Analyst Ask",  # analogous to original position 4
                "Risky Analyst Ans",  # 5
                "Safe Analyst Ask",   # 6
                "Risky Analyst Ans",  # 7
                "Risky Analyst",      # 8
                "Safe Analyst",       # 9
            ]
            idx = (count - 3) % len(repeat_sequence)
            next_role = repeat_sequence[idx]
            print(f"[DEBUG] Next (loop): {next_role}")
            return next_role

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