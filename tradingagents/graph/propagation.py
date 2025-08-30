# TradingAgents/graph/propagation.py

from typing import Dict, Any
from tradingagents.agents.utils.agent_states import (
    AgentState,
    InvestDebateState,
    RiskDebateState,
)


class Propagator:
    """Handles state initialization and propagation through the graph."""

    def __init__(self, max_recur_limit=100):
        """Initialize with configuration parameters."""
        self.max_recur_limit = max_recur_limit

    def create_initial_state(
        self, company_name: str, trade_date: str
    ) -> Dict[str, Any]:
        """Create the initial state for the agent graph."""
        return {
            "messages": [("human", company_name)],
            "company_of_interest": company_name,
            "trade_date": str(trade_date),
            "investment_debate_state": {
                "history": "[]",
                "current_response": "",
                "judge_decision": "",
                "bull_history": "[]",
                "bear_history": "[]",
                "count": 0
            },
            "risk_debate_state": {
                "history": "[]",
                "current_risky_response": "",
                "current_safe_response": "",
                "current_neutral_response": "",
                "latest_speaker": "",
                "judge_decision": "",
                "count": 0,
            },
            "market_report": "",
            "fundamentals_report": "",
            "sentiment_report": "",
            "news_report": "",
        }

    def create_portfolio_state(
        self, tickers: list, trade_date: str
    ) -> Dict[str, Any]:
        """Create enhanced portfolio state for true multi-ticker analysis."""
        return {
            "messages": [("human", f"Portfolio analysis for: {', '.join(tickers)}")],
            "tickers": tickers,
            "trade_date": str(trade_date),
            "current_ticker_index": 0,  # Track which ticker we're processing
            "ticker_analysis_complete": {ticker: False for ticker in tickers},
            
            # Phase-based processing tracking
            "current_phase": "analysts",  # analysts -> researchers -> risk -> optimization
            "current_analyst_type": "market",  # Which analyst type is currently processing
            
            # Analyst completion tracking (for phase-based processing)
            "analyst_completion": {
                "market": {ticker: False for ticker in tickers},
                "macroeconomic": {ticker: False for ticker in tickers},
                "social": {ticker: False for ticker in tickers},
                "news": {ticker: False for ticker in tickers},
                "fundamentals": {ticker: False for ticker in tickers}
            },
            
            # Researcher completion tracking
            "researcher_completion": {
                "bull": {ticker: False for ticker in tickers},
                "bear": {ticker: False for ticker in tickers},
                "bull_crossex": {ticker: False for ticker in tickers},
                "bear_crossex": {ticker: False for ticker in tickers}
            },
            
            # Risk analysis completion tracking
            "risk_completion": {
                "conservative": {ticker: False for ticker in tickers},
                "aggressive": {ticker: False for ticker in tickers},
                "neutral": {ticker: False for ticker in tickers}
            },
            
            # Investment debate states for each ticker
            "investment_debate_states": {
                ticker: {
                    "history": "",
                    "bull_history": "",
                    "bear_history": "",
                    "bull_crossex_history": "",
                    "bear_crossex_history": "",
                    "current_response": "",
                    "judge_decision": "",
                    "count": 0,
                }
                for ticker in tickers
            },
            
            # Risk debate states for each ticker
            "risk_debate_states": {
                ticker: {
                    "history": "",
                    "risky_history": "",
                    "safe_history": "",
                    "neutral_history": "",
                    "latest_speaker": "",
                    "current_risky_response": "",
                    "current_safe_response": "",
                    "current_neutral_response": "",
                    "count": 0,
                }
                for ticker in tickers
            },
            
            # Individual reports for each ticker
            "individual_reports": {
                ticker: {
                    "market_report": "",
                    "macroeconomic_report": "",
                    "sentiment_report": "",
                    "news_report": "",
                    "fundamentals_report": "",
                    "investment_plan": "",
                    "trader_investment_plan": "",
                    "final_trade_decision": "",
                    "analysis_complete": False,
                }
                for ticker in tickers
            },
        }

    def get_graph_args(self) -> Dict[str, Any]:
        """Get arguments for the graph invocation."""
        return {
            "stream_mode": "values",
            "config": {"recursion_limit": self.max_recur_limit},
        }
