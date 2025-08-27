"""
Utility functions for managing debate state and count incrementing.
"""

def increment_debate_count(state: dict) -> dict:
    """
    Increment the debate count in the investment_debate_state.
    
    Args:
        state: The current agent state
        
    Returns:
        Updated state with incremented count
    """
    # Handle both single ticker and multi-ticker portfolio modes
    if "investment_debate_states" in state and state.get("tickers"):
        # Multi-ticker portfolio mode - increment count for the first ticker
        # In a real implementation, you might want to track which ticker is currently being debated
        ticker = state["tickers"][0] if state["tickers"] else "SPY"
        if ticker in state["investment_debate_states"]:
            current_count = state["investment_debate_states"][ticker].get("count", 0)
            new_count = current_count + 1
            state["investment_debate_states"][ticker]["count"] = new_count
            print(f"[DEBUG] Debate count incremented for {ticker}: {current_count} -> {new_count}")
    elif "investment_debate_state" in state:
        # Single ticker mode
        current_count = state["investment_debate_state"].get("count", 0)
        new_count = current_count + 1
        state["investment_debate_state"]["count"] = new_count
        print(f"[DEBUG] Debate count incremented: {current_count} -> {new_count}")
    
    return state


def get_debate_round_info(state: dict, ticker: str = None) -> dict:
    """
    Get information about the current debate round.
    
    Args:
        state: The current agent state
        ticker: Optional ticker symbol for portfolio mode
        
    Returns:
        Dictionary with round information
    """
    # Check for multi-ticker portfolio mode first
    if "investment_debate_states" in state and state.get("tickers"):
        if ticker and ticker in state["investment_debate_states"]:
            # Get the specific ticker's debate state
            ticker_debate_state = state["investment_debate_states"][ticker]
            count = ticker_debate_state.get("count", 0)
            round_num = (count // 4) + 1
            step_in_round = count % 4
            
            # Ensure step_in_round is within bounds
            step_names = ["Bull", "Bear", "Bull Cross", "Bear Cross"]
            if 0 <= step_in_round < len(step_names):
                step_name = step_names[step_in_round]
            else:
                step_name = "Unknown"
            
            return {
                "round": round_num,
                "step": step_in_round,
                "total_steps": count,
                "step_name": step_name
            }
        else:
            # In portfolio mode but no specific ticker context, return default values
            return {"round": 0, "step": 0, "total_steps": 0, "step_name": "Bull"}
    
    # Check for single ticker mode
    if "investment_debate_state" in state:
        count = state["investment_debate_state"].get("count", 0)
        round_num = (count // 4) + 1
        step_in_round = count % 4
        
        # Ensure step_in_round is within bounds
        step_names = ["Bull", "Bear", "Bull Cross", "Bear Cross"]
        if 0 <= step_in_round < len(step_names):
            step_name = step_names[step_in_round]
        else:
            step_name = "Unknown"
        
        return {
            "round": round_num,
            "step": step_in_round,
            "total_steps": count,
            "step_name": step_name
        }
    
    # Default return if no debate state found
    return {"round": 0, "step": 0, "total_steps": 0, "step_name": "Bull"} 