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

    def should_continue_debate(self, state: AgentState) -> str:
        """Determine if debate should continue."""
        print(f"[DEBUG] should_continue_debate: count={state['investment_debate_state']['count']}, max_debate_rounds={self.max_debate_rounds}")
        # Check if we've reached the maximum number of rounds
        if (
            state["investment_debate_state"]["count"] >= 2 * self.max_debate_rounds
        ):  # 2 rounds of back-and-forth between 2 agents
            print("[DEBUG] Debate complete. Handing off to Research Manager.")
            return "Research Manager"
        
        # Determine whose turn it is based on the count
        # Even counts (0, 2, 4, 6, 8...) = Bull's turn
        # Odd counts (1, 3, 5, 7, 9...) = Bear's turn
        if state["investment_debate_state"]["count"] % 2 == 0:
            print("[DEBUG] Next: Bull Researcher")
            return "Bull Researcher"
        else:
            print("[DEBUG] Next: Bear Researcher")
            return "Bear Researcher"

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
