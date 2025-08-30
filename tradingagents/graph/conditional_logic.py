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
        
        # CRITICAL FIX: Check for tool calls first - this should always return tools_market
        # Handle both object attributes and dictionary keys
        has_tool_calls = False
        if hasattr(last_message, 'tool_calls'):
            has_tool_calls = bool(last_message.tool_calls)
        elif isinstance(last_message, dict) and 'tool_calls' in last_message:
            has_tool_calls = bool(last_message['tool_calls'])
        
        if has_tool_calls:
            print(f"[DEBUG] Tool calls detected, continuing with tools_market")
            return "tools_market"
        
        # Check if we're in multi-ticker portfolio mode
        if "tickers" in state and len(state.get("tickers", [])) > 1:
            # For multi-ticker mode, check if market analysis is complete for all tickers
            tickers = state.get("tickers", [])
            individual_reports = state.get("individual_reports", {})
            
            # CRITICAL FIX: Check both completion flags and actual reports
            all_tickers_have_market_reports = True
            for ticker in tickers:
                has_market_report = bool(individual_reports.get(ticker, {}).get("market_report", ""))
                if not has_market_report:
                    all_tickers_have_market_reports = False
                    break
            
            if all_tickers_have_market_reports:
                # All tickers have market reports, proceed to next step
                print(f"[DEBUG] Market analysis complete for all tickers: {tickers}")
                return "Msg Clear Market"
            else:
                # Some tickers still need market analysis, continue with market analyst
                incomplete_tickers = [t for t in tickers if not individual_reports.get(t, {}).get("market_report", "")]
                print(f"[DEBUG] Market analysis incomplete for tickers: {incomplete_tickers}")
                return "tools_market"
        else:
            # Single ticker mode - proceed to next step
            return "Msg Clear Market"

    def should_continue_macroeconomic(self, state: AgentState):
        """Determine if macroeconomic analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        
        # CRITICAL FIX: Check for tool calls first
        has_tool_calls = False
        if hasattr(last_message, 'tool_calls'):
            has_tool_calls = bool(last_message.tool_calls)
        elif isinstance(last_message, dict) and 'tool_calls' in last_message:
            has_tool_calls = bool(last_message['tool_calls'])
        
        if has_tool_calls:
            print(f"[DEBUG] Tool calls detected, continuing with tools_macroeconomic")
            return "tools_macroeconomic"
        
        # Check if we're in multi-ticker portfolio mode
        if "tickers" in state and len(state.get("tickers", [])) > 1:
            # For phase-based routing, check if all tickers completed macroeconomic analysis
            tickers = state.get("tickers", [])
            individual_reports = state.get("individual_reports", {})
            
            # CRITICAL FIX: Check both completion flags and actual reports
            all_tickers_complete = True
            for ticker in tickers:
                has_macroeconomic_report = bool(individual_reports.get(ticker, {}).get("macroeconomic_report", ""))
                if not has_macroeconomic_report:
                    all_tickers_complete = False
                    break
            
            if all_tickers_complete:
                # All tickers completed macroeconomic analysis, proceed to next step
                print(f"[DEBUG] Macroeconomic analysis complete for all tickers: {tickers}")
                return "Msg Clear Macroeconomic"
            else:
                # Some tickers still need macroeconomic analysis, continue with tools
                incomplete_tickers = [t for t in tickers if not individual_reports.get(t, {}).get("macroeconomic_report", "")]
                print(f"[DEBUG] Macroeconomic analysis incomplete for tickers: {incomplete_tickers}")
                return "tools_macroeconomic"
                
        else:
            # Single ticker mode - use original logic
            has_tool_calls = False
            if hasattr(last_message, 'tool_calls'):
                has_tool_calls = bool(last_message.tool_calls)
            elif isinstance(last_message, dict) and 'tool_calls' in last_message:
                has_tool_calls = bool(last_message['tool_calls'])
                
            if has_tool_calls:
                return "tools_macroeconomic"
            return "Msg Clear Macroeconomic"

    def should_continue_social(self, state: AgentState):
        """Determine if social media analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        
        # CRITICAL FIX: Check for tool calls first - this should always return tools_social
        # Handle both object attributes and dictionary keys
        has_tool_calls = False
        if hasattr(last_message, 'tool_calls'):
            has_tool_calls = bool(last_message.tool_calls)
        elif isinstance(last_message, dict) and 'tool_calls' in last_message:
            has_tool_calls = bool(last_message['tool_calls'])
        
        if has_tool_calls:
            print(f"[DEBUG] Tool calls detected, continuing with tools_social")
            return "tools_social"
        
        # Check if we're in multi-ticker portfolio mode
        if "tickers" in state and len(state.get("tickers", [])) > 1:
            # For phase-based routing, check if all tickers completed social media analysis
            tickers = state.get("tickers", [])
            analyst_completion = state.get("analyst_completion", {})
            social_completion = analyst_completion.get("social", {})
            
            # CRITICAL FIX: Check if all tickers have completed social media analysis
            # Also check individual_reports to ensure we have actual sentiment reports
            individual_reports = state.get("individual_reports", {})
            
            all_tickers_complete = True
            for ticker in tickers:
                # Check both completion flag and actual report existence
                ticker_complete = social_completion.get(ticker, False)
                has_sentiment_report = bool(individual_reports.get(ticker, {}).get("sentiment_report"))
                
                if not ticker_complete or not has_sentiment_report:
                    all_tickers_complete = False
                    break
            
            if all_tickers_complete:
                # All tickers completed social media analysis, proceed to next step
                print(f"[DEBUG] Social media analysis complete for all tickers: {tickers}")
                return "Msg Clear Social"
            else:
                # Some tickers still need social media analysis, continue with tools
                incomplete_tickers = [t for t in tickers if not social_completion.get(t, False) or not individual_reports.get(t, {}).get("sentiment_report")]
                print(f"[DEBUG] Social media analysis incomplete for tickers: {incomplete_tickers}")
                return "tools_social"
                
        else:
            # Single ticker mode - use original logic
            has_tool_calls = False
            if hasattr(last_message, 'tool_calls'):
                has_tool_calls = bool(last_message.tool_calls)
            elif isinstance(last_message, dict) and 'tool_calls' in last_message:
                has_tool_calls = bool(last_message['tool_calls'])
                
            if has_tool_calls:
                return "tools_social"
            return "Msg Clear Social"

    def should_continue_news(self, state: AgentState):
        """Determine if news analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        
        # CRITICAL FIX: Check for tool calls first
        has_tool_calls = False
        if hasattr(last_message, 'tool_calls'):
            has_tool_calls = bool(last_message.tool_calls)
        elif isinstance(last_message, dict) and 'tool_calls' in last_message:
            has_tool_calls = bool(last_message['tool_calls'])
        
        if has_tool_calls:
            print(f"[DEBUG] Tool calls detected, continuing with tools_news")
            return "tools_news"
        
        # Check if we're in multi-ticker portfolio mode
        if "tickers" in state and len(state.get("tickers", [])) > 1:
            # For phase-based routing, check if all tickers completed news analysis
            tickers = state.get("tickers", [])
            analyst_completion = state.get("analyst_completion", {})
            news_completion = analyst_completion.get("news", {})
            individual_reports = state.get("individual_reports", {})
            
            # CRITICAL FIX: Check both completion flags and actual reports
            all_tickers_complete = True
            for ticker in tickers:
                ticker_complete = news_completion.get(ticker, False)
                has_news_report = bool(individual_reports.get(ticker, {}).get("news_report", ""))
                if not ticker_complete or not has_news_report:
                    all_tickers_complete = False
                    break
            
            if all_tickers_complete:
                # All tickers completed news analysis, proceed to next step
                print(f"[DEBUG] News analysis complete for all tickers: {tickers}")
                return "Msg Clear News"
            else:
                # Some tickers still need news analysis, continue with tools
                incomplete_tickers = [t for t in tickers if not news_completion.get(t, False) or not individual_reports.get(t, {}).get("news_report", "")]
                print(f"[DEBUG] News analysis incomplete for tickers: {incomplete_tickers}")
                return "tools_news"
                
        else:
            # Single ticker mode - use original logic
            has_tool_calls = False
            if hasattr(last_message, 'tool_calls'):
                has_tool_calls = bool(last_message.tool_calls)
            elif isinstance(last_message, dict) and 'tool_calls' in last_message:
                has_tool_calls = bool(last_message['tool_calls'])
                
            if has_tool_calls:
                return "tools_news"
            return "Msg Clear News"

    def should_continue_quant_market(self, state: AgentState):
        """Determine if quant market analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools_quant_market"
        return "Msg Clear Quant_market"

    def should_continue_fundamentals(self, state: AgentState):
        """Determine if fundamentals analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        
        # CRITICAL FIX: Check for tool calls first
        has_tool_calls = False
        if hasattr(last_message, 'tool_calls'):
            has_tool_calls = bool(last_message.tool_calls)
        elif isinstance(last_message, dict) and 'tool_calls' in last_message:
            has_tool_calls = bool(last_message['tool_calls'])
        
        if has_tool_calls:
            print(f"[DEBUG] Tool calls detected, continuing with tools_fundamentals")
            return "tools_fundamentals"
        
        # Check if we're in multi-ticker portfolio mode
        if "tickers" in state and len(state.get("tickers", [])) > 1:
            # For phase-based routing, check if all tickers completed fundamentals analysis
            tickers = state.get("tickers", [])
            analyst_completion = state.get("analyst_completion", {})
            fundamentals_completion = analyst_completion.get("fundamentals", {})
            individual_reports = state.get("individual_reports", {})
            
            # CRITICAL FIX: Check both completion flags and actual reports
            all_tickers_complete = True
            for ticker in tickers:
                ticker_complete = fundamentals_completion.get(ticker, False)
                has_fundamentals_report = bool(individual_reports.get(ticker, {}).get("fundamentals_report", ""))
                if not ticker_complete or not has_fundamentals_report:
                    all_tickers_complete = False
                    break
            
            if all_tickers_complete:
                # All tickers completed fundamentals analysis, proceed to next step
                print(f"[DEBUG] Fundamentals analysis complete for all tickers: {tickers}")
                return "Msg Clear Fundamentals"
            else:
                # Some tickers still need fundamentals analysis, continue with tools
                incomplete_tickers = [t for t in tickers if not fundamentals_completion.get(t, False) or not individual_reports.get(t, {}).get("fundamentals_report", "")]
                print(f"[DEBUG] Fundamentals analysis incomplete for tickers: {incomplete_tickers}")
                return "tools_fundamentals"
                
        else:
            # Single ticker mode - use original logic
            has_tool_calls = False
            if hasattr(last_message, 'tool_calls'):
                has_tool_calls = bool(last_message.tool_calls)
            elif isinstance(last_message, dict) and 'tool_calls' in last_message:
                has_tool_calls = bool(last_message['tool_calls'])
                
            if has_tool_calls:
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
        if "tickers" in state and state.get("tickers"):
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

        # Check if we've reached the maximum number of debate rounds
        # Each round consists of: Bull → Bear → Bull Crossex → Bear Crossex (4 steps)
        max_steps = 4 * self.max_debate_rounds
        if count >= max_steps:
            print(f"[DEBUG] Debate complete after {self.max_debate_rounds} rounds. Handing off to Research Manager.")
            return "Research Manager"
        
        # Enhanced flow with crossex: Multiple rounds of Bull → Bear → Bull Crossex → Bear Crossex
        # Round 1: count 0-3
        # Round 2: count 4-7  
        # Round 3: count 8-11
        # etc.
        
        # Calculate which step within the current round (0-3)
        step_within_round = count % 4
        
        if step_within_round == 0:
            return "Bull Researcher"
        elif step_within_round == 1:
            return "Bear Researcher"
        elif step_within_round == 2:
            return "Bull Crossex Researcher"
        elif step_within_round == 3:
            return "Bear Crossex Researcher"
        else:
            # This should never happen, but fallback to Research Manager
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
        if count >= 3 * self.max_risk_discuss_rounds:  # Enhanced: 3 analysts (RESTORED neutral)
            print("[DEBUG] Risk analysis complete. Handing off to Risk Judge.")
            return "Risk Judge"
        
        # Enhanced flow with neutral: Risky → Safe → Neutral → Risk Judge
        # count represents which analyst we're currently at:
        # 0 = currently at Risky Analyst, go to Safe Analyst
        # 1 = currently at Safe Analyst, go to Neutral Analyst 
        # 2 = currently at Neutral Analyst, go to Risk Judge
        # 3+ = go to Risk Judge (GUARANTEED TERMINATION)

        if count == 0:
            print("[DEBUG] Currently at Risky Analyst, going to Safe Analyst")
            return "Safe Analyst"
        elif count == 1:
            print("[DEBUG] Currently at Safe Analyst, going to Neutral Analyst")
            return "Neutral Analyst"
        else:
            # After all analysts (including neutral), go to Risk Judge
            print("[DEBUG] Currently at Neutral Analyst or beyond, going to Risk Judge")
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
        individual_reports = state.get("individual_reports", {})
        
        print(f"[DEBUG] should_continue_ticker_analysis: index={current_ticker_index}, total_tickers={len(tickers)}")
        
        if current_ticker_index >= len(tickers):
            print("[DEBUG] All tickers processed, proceeding to portfolio optimization")
            return "portfolio_optimization"
        
        current_ticker = tickers[current_ticker_index]
        current_ticker_report = individual_reports.get(current_ticker, {})
        
        # Check if current ticker analysis is complete
        is_complete = self._is_ticker_analysis_complete(current_ticker_report)
        print(f"[DEBUG] Ticker {current_ticker} analysis complete: {is_complete}")
        
        if is_complete:
            # Check if this is the last ticker
            if current_ticker_index == len(tickers) - 1:
                # Last ticker complete, proceed to portfolio optimization
                print("[DEBUG] Last ticker complete, proceeding to portfolio optimization")
                return "portfolio_optimization"
            else:
                # Move to next ticker
                print(f"[DEBUG] Moving to next ticker: {current_ticker_index + 1}")
                return "next_ticker"
        else:
            # Current ticker needs analysis - continue with current ticker processing
            print(f"[DEBUG] Ticker {current_ticker} needs more analysis, continuing with current ticker")
            return "next_ticker"

    def _is_ticker_analysis_complete(self, ticker_reports):
        """Check if a ticker's analysis is complete."""
        # Require the ticker to have completed the full analysis pipeline
        # At minimum, we need market analysis and either fundamentals OR a complete flag
        has_market_report = bool(ticker_reports.get("market_report"))
        has_investment_plan = bool(ticker_reports.get("investment_plan"))
        has_final_decision = bool(ticker_reports.get("final_trade_decision"))
        is_marked_complete = ticker_reports.get("analysis_complete", False)
        
        # For a ticker to be considered complete, it needs either:
        # 1. Explicit completion flag, OR
        # 2. Market report AND investment plan AND final decision
        is_complete = is_marked_complete or (has_market_report and has_investment_plan and has_final_decision)
        
        print(f"[DEBUG] Ticker analysis check: market={has_market_report}, plan={has_investment_plan}, decision={has_final_decision}, complete_flag={is_marked_complete} -> {is_complete}")
        
        return is_complete

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