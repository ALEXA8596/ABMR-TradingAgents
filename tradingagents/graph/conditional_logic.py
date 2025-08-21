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
        if last_message.tool_calls:
            return "tools_market"
        return "Msg Clear Market"

    def should_continue_social(self, state: AgentState):
        """Determine if social media analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools_social"
        return "Msg Clear Social"

    def should_continue_news(self, state: AgentState):
        """Determine if news analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools_news"
        return "Msg Clear News"

    def should_continue_fundamentals(self, state: AgentState):
        """Determine if fundamentals analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools_fundamentals"
        return "Msg Clear Fundamentals"
    
    # def should_continue_trader(self, state: AgentState):
    #     """Determine if trader should continue."""
    #     messages = state["messages"]
    #     last_message = messages[-1]
    #     if last_message.tool_calls:
    #         return "tools_trader"
    #     return "Msg Clear Trader"
    def should_continue_risk_judgment(self, state: AgentState):
        """Determine if risk judgment should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools_Risk Judge"
        return "Msg Clear Risk Judge"

    def should_continue_debate(self, state: AgentState) -> str:
        """Determine if debate should continue."""

        # 1 => Bullish Researcher
        # 2 => Bearish Researcher
        # 3 => Bullish Cross Examination Researcher
        # 4 => Bearish Cross Examination Researcher
        # 5 => Bullish Researcher
        # 6 => Bearish Researcher
        # 7 => Research Manager
        # Repeat 3 to 7 as needed

        count = state["investment_debate_state"]["count"]

        if count >= 4 * self.max_debate_rounds:
            return "Research Manager"

        sequence = [
            "Bull Researcher",
            "Bear Researcher",
            "Bull Cross Examination Researcher",
            "Bear Cross Examination Researcher",
        ]

        return sequence[count % len(sequence)]

    def should_continue_risk_analysis(self, state: AgentState) -> str:
        """Determine if risk analysis should continue."""
        print(f"[DEBUG] should_continue_risk_analysis: count={state['risk_debate_state']['count']}, max_risk_discuss_rounds={self.max_risk_discuss_rounds}")
        # Check if we've reached the maximum number of rounds
        if (
            state["risk_debate_state"]["count"] >= 3 * self.max_risk_discuss_rounds
        ):  # 3 rounds of back-and-forth between 3 agents
            print("[DEBUG] Risk debate complete. Handing off to Risk Judge.")
            return "Risk Judge"
        
        # Determine whose turn it is based on the count
        # Count % 3 = 0: Risky Analyst
        # Count % 3 = 1: Safe Analyst  
        # Count % 3 = 2: Neutral Analyst
        turn = state["risk_debate_state"]["count"] % 3
        if turn == 0:
            print("[DEBUG] Next: Risky Analyst")
            return "Risky Analyst"
        elif turn == 1:
            print("[DEBUG] Next: Safe Analyst")
            return "Safe Analyst"
        else:
            print("[DEBUG] Next: Neutral Analyst")
            return "Neutral Analyst"

    def should_continue_portfolio_flow(self, state: AgentState) -> str:
        """Determine if portfolio optimization flow should continue."""
        # Check if portfolio optimization has been completed
        if "portfolio_optimization_state" not in state or not state["portfolio_optimization_state"]:
            return "Portfolio Optimizer"
        else:
            return "END"