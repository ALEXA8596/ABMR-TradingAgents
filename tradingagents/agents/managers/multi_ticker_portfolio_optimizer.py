# -*- coding: utf-8 -*-
"""
Multi-Ticker Portfolio Optimizer

This agent handles portfolio optimization across multiple tickers, considering:
- Cross-ticker correlations
- Sector diversification
- Portfolio risk balance
- Position sizing across multiple positions
"""

import time
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple
from tradingagents.blackboard.utils import create_agent_blackboard
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
import yfinance as yf
import numpy as np
import pandas as pd


def create_multi_ticker_portfolio_optimizer(llm, memory, toolkit):
    def multi_ticker_portfolio_optimizer(state):
        """Multi-ticker portfolio optimization agent."""
        tickers = state.get("tickers", [])
        current_ticker_index = state.get("current_ticker_index", 0)
        individual_reports = state.get("individual_reports", {})
        
        print(f"🔍 Multi-Ticker Portfolio Optimizer: Processing ticker {current_ticker_index + 1}/{len(tickers)}")
        
        # Check if we've completed all tickers
        if current_ticker_index >= len(tickers):
            # All tickers analyzed, proceed to portfolio optimization
            return {
                "portfolio_optimization_state": {
                    "message": "All ticker analyses completed. Proceeding to portfolio optimization.",
                    "optimization_completed": True,
                    "tickers_analyzed": list(individual_reports.keys()),
                    "total_tickers": len(tickers)
                }
            }
        
        current_ticker = tickers[current_ticker_index]
        
        # Check if current ticker analysis is complete
        current_ticker_report = individual_reports.get(current_ticker, {})
        
        # Consider ticker complete if it has any non-empty analysis reports (even if data retrieval failed)
        has_any_analysis = any([
            current_ticker_report.get("market_report") and current_ticker_report.get("market_report") != "",
            current_ticker_report.get("fundamentals_report") and current_ticker_report.get("fundamentals_report") != "",
            current_ticker_report.get("sentiment_report") and current_ticker_report.get("sentiment_report") != "",
            current_ticker_report.get("news_report") and current_ticker_report.get("news_report") != ""
        ])
        
        if has_any_analysis or current_ticker_report.get("analysis_complete", False):
            # Current ticker complete, move to next ticker
            next_index = current_ticker_index + 1
            if next_index >= len(tickers):
                # This was the last ticker, proceed to portfolio optimization
                return {
                    "portfolio_optimization_state": {
                        "message": f"Completed analysis for {current_ticker}. All tickers done. Proceeding to portfolio optimization.",
                        "optimization_completed": True,
                        "tickers_analyzed": [t for t in tickers if individual_reports.get(t, {}).get("analysis_complete", False)],
                        "total_tickers": len(tickers)
                    }
                }
            else:
                # Move to next ticker
                return {
                    "current_ticker_index": next_index,
                    "portfolio_optimization_state": {
                        "message": f"Completed analysis for {current_ticker}. Moving to next ticker: {tickers[next_index]}",
                        "optimization_completed": False,
                        "tickers_analyzed": [t for t in tickers[:next_index] if individual_reports.get(t, {}).get("analysis_complete", False)],
                        "total_tickers": len(tickers),
                        "current_ticker": tickers[next_index]
                    }
                }
        else:
            # Current ticker needs analysis - this should trigger the analysis flow
            # Return a state that indicates we need to continue with current ticker
            return {
                "portfolio_optimization_state": {
                    "message": f"Current ticker {current_ticker} needs analysis. Continuing with analysis flow.",
                    "optimization_completed": False,
                    "tickers_analyzed": [t for t in tickers[:current_ticker_index] if individual_reports.get(t, {}).get("analysis_complete", False)],
                    "total_tickers": len(tickers),
                    "current_ticker": current_ticker,
                    "analysis_required": True
                }
            }
    
    return multi_ticker_portfolio_optimizer 