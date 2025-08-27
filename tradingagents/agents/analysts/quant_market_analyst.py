from langchain_core.messages import AIMessage
from tradingagents.agents.utils.agent_utils import Toolkit

def create_quant_market_analyst(llm, toolkit: Toolkit):
    """Create a quantitative market analyst agent."""
    
    def quant_market_analyst_node(state) -> dict:
        print(f"[DEBUG] Quant Market Analyst executing...")
        
        # Handle both single ticker and multi-ticker modes
        if "tickers" in state:
            # Multi-ticker portfolio mode
            tickers = state["tickers"]
            company = tickers[0]  # Analyze first ticker for now
            is_portfolio_mode = True
        elif "company_of_interest" in state:
            # Single ticker mode (backward compatibility)
            company = state["company_of_interest"]
            is_portfolio_mode = False
        else:
            # Fallback - this shouldn't happen but let's handle it gracefully
            print("Warning: No ticker information found in state")
            return {
                "quant_market_report": "Error: No ticker information available",
            }
        
        # Create a prompt for quantitative market analysis
        prompt = f"""As a Quantitative Market Analyst, you specialize in technical analysis, statistical modeling, and quantitative approaches to market evaluation.

Company: {company}

Your task is to provide a comprehensive quantitative market analysis including:

1. Technical Indicators Analysis
   - Moving averages, RSI, MACD, Bollinger Bands
   - Volume analysis and price momentum
   - Support and resistance levels

2. Statistical Analysis
   - Volatility measures (standard deviation, beta)
   - Correlation analysis with market indices
   - Risk-adjusted return metrics

3. Quantitative Models
   - Trend analysis and pattern recognition
   - Statistical significance of price movements
   - Probability-based trading signals

4. Market Microstructure
   - Liquidity analysis
   - Order flow dynamics
   - Market efficiency indicators

5. Risk Metrics
   - Value at Risk (VaR)
   - Maximum drawdown analysis
   - Sharpe ratio and other risk-adjusted measures

Provide your analysis in a structured format with specific quantitative insights and actionable recommendations.

Focus on data-driven insights and statistical significance rather than qualitative assessments."""

        # Get the response from the LLM
        response = llm.invoke(prompt)
        
        # Update the state with the quant market analysis
        state["quant_market_report"] = response.content
        
        print(f"[DEBUG] Quant Market Analyst completed analysis for {company}")
        
        return state
    
    return quant_market_analyst_node 