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


def _is_ticker_analysis_complete(ticker_reports):
    """Check if a ticker's analysis is complete."""
    # Consider ticker complete if it has any non-empty analysis reports (even if data retrieval failed)
    has_any_analysis = any([
        ticker_reports.get("market_report") and ticker_reports.get("market_report") != "",
        ticker_reports.get("fundamentals_report") and ticker_reports.get("fundamentals_report") != "",
        ticker_reports.get("sentiment_report") and ticker_reports.get("sentiment_report") != "",
        ticker_reports.get("news_report") and ticker_reports.get("news_report") != ""
    ])
    
    return has_any_analysis or ticker_reports.get("analysis_complete", False)


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
            portfolio_analysis = _perform_portfolio_optimization(tickers, individual_reports)
            return {
                "portfolio_optimization_state": portfolio_analysis,
                "portfolio_optimizer_decision": portfolio_analysis.get("final_decision", "HOLD"),
                "cross_ticker_correlations": portfolio_analysis.get("correlations", {}),
                "sector_allocations": portfolio_analysis.get("sector_breakdown", {}),
                "risk_metrics": portfolio_analysis.get("risk_metrics", {})
            }
        
        current_ticker = tickers[current_ticker_index]
        
        # Check if we're returning from analysis (individual reports have been updated)
        if current_ticker in individual_reports:
            current_ticker_report = individual_reports[current_ticker]
            
            # Check if current ticker analysis is complete
            if _is_ticker_analysis_complete(current_ticker_report):
                # Current ticker complete, move to next ticker
                next_index = current_ticker_index + 1
                if next_index >= len(tickers):
                    # This was the last ticker, proceed to portfolio optimization
                    portfolio_analysis = _perform_portfolio_optimization(tickers, individual_reports)
                    return {
                        "portfolio_optimization_state": portfolio_analysis,
                        "portfolio_optimizer_decision": portfolio_analysis.get("final_decision", "HOLD"),
                        "cross_ticker_correlations": portfolio_analysis.get("correlations", {}),
                        "sector_allocations": portfolio_analysis.get("sector_breakdown", {}),
                        "risk_metrics": portfolio_analysis.get("risk_metrics", {})
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


def _perform_portfolio_optimization(tickers: List[str], individual_reports: Dict[str, Any]) -> Dict[str, Any]:
    """Perform comprehensive portfolio optimization analysis."""
    try:
        # Analyze cross-ticker correlations
        correlations = _analyze_cross_ticker_correlations(tickers, individual_reports)
        
        # Analyze sector breakdown
        sector_breakdown = _analyze_sector_breakdown(tickers, individual_reports)
        
        # Calculate portfolio risk metrics
        risk_metrics = _calculate_portfolio_risk_metrics(tickers, individual_reports)
        
        # Generate allocation strategies
        allocation_strategies = _generate_allocation_strategies(tickers, individual_reports, correlations, sector_breakdown, risk_metrics)
        
        # Create final portfolio decision
        final_decision = _create_portfolio_decision(allocation_strategies, risk_metrics)
        
        return {
            "message": "Portfolio optimization completed successfully",
            "optimization_completed": True,
            "tickers_analyzed": list(individual_reports.keys()),
            "total_tickers": len(tickers),
            "correlations": correlations,
            "sector_breakdown": sector_breakdown,
            "risk_metrics": risk_metrics,
            "allocation_strategies": allocation_strategies,
            "final_decision": final_decision
        }
    except Exception as e:
        return {
            "message": f"Portfolio optimization failed: {str(e)}",
            "optimization_completed": False,
            "error": str(e)
        }


def _analyze_cross_ticker_correlations(tickers: List[str], individual_reports: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze correlations between different tickers."""
    correlations = {}
    
    # Simple correlation analysis based on analysis reports
    for i, ticker1 in enumerate(tickers):
        for j, ticker2 in enumerate(tickers):
            if i < j:  # Only analyze unique pairs
                # Analyze sentiment correlation
                sentiment1 = _extract_sentiment(individual_reports.get(ticker1, {}))
                sentiment2 = _extract_sentiment(individual_reports.get(ticker2, {}))
                
                correlation_score = _calculate_sentiment_correlation(sentiment1, sentiment2)
                
                correlations[f"{ticker1}-{ticker2}"] = {
                    "correlation": correlation_score,
                    "strength": "strong" if abs(correlation_score) > 0.7 else "moderate" if abs(correlation_score) > 0.4 else "weak"
                }
    
    return correlations


def _analyze_sector_breakdown(tickers: List[str], individual_reports: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze sector allocation and diversification."""
    # Simplified sector mapping (in a real system, this would come from company data)
    sector_mapping = {
        "SPY": "ETF",
        "AAPL": "Technology",
        "TSLA": "Automotive/Technology"
    }
    
    sector_breakdown = {}
    for ticker in tickers:
        sector = sector_mapping.get(ticker, "Unknown")
        if sector not in sector_breakdown:
            sector_breakdown[sector] = []
        sector_breakdown[sector].append(ticker)
    
    return sector_breakdown


def _calculate_portfolio_risk_metrics(tickers: List[str], individual_reports: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate portfolio-level risk metrics."""
    risk_metrics = {
        "total_tickers": len(tickers),
        "diversification_score": len(set([_get_sector(ticker) for ticker in tickers])),
        "overall_sentiment": _calculate_overall_sentiment(individual_reports),
        "risk_level": "Medium",  # Default risk level
        "volatility_estimate": "Medium"
    }
    
    return risk_metrics


def _generate_allocation_strategies(tickers: List[str], individual_reports: Dict[str, Any], 
                                  correlations: Dict[str, Any], sector_breakdown: Dict[str, Any], 
                                  risk_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Generate portfolio allocation strategies."""
    strategies = {
        "conservative": {
            "description": "Conservative allocation focusing on stability",
            "recommended_weights": {ticker: 1.0/len(tickers) for ticker in tickers},
            "risk_level": "Low"
        },
        "balanced": {
            "description": "Balanced allocation with moderate risk",
            "recommended_weights": {ticker: 1.0/len(tickers) for ticker in tickers},
            "risk_level": "Medium"
        },
        "aggressive": {
            "description": "Aggressive allocation for higher returns",
            "recommended_weights": {ticker: 1.0/len(tickers) for ticker in tickers},
            "risk_level": "High"
        }
    }
    
    return strategies


def _create_portfolio_decision(allocation_strategies: Dict[str, Any], risk_metrics: Dict[str, Any]) -> str:
    """Create final portfolio decision based on analysis."""
    # Simple decision logic based on risk metrics
    if risk_metrics.get("diversification_score", 0) >= 3:
        return "BUY"  # Good diversification
    elif risk_metrics.get("diversification_score", 0) >= 2:
        return "HOLD"  # Moderate diversification
    else:
        return "SELL"  # Poor diversification


def _extract_sentiment(report: Dict[str, Any]) -> float:
    """Extract sentiment score from analysis report."""
    # Simple sentiment extraction (in a real system, this would use NLP)
    text = str(report.get("market_report", "")) + str(report.get("sentiment_report", ""))
    
    positive_words = ["bullish", "positive", "growth", "strong", "buy", "up"]
    negative_words = ["bearish", "negative", "decline", "weak", "sell", "down"]
    
    positive_count = sum(1 for word in positive_words if word.lower() in text.lower())
    negative_count = sum(1 for word in negative_words if word.lower() in text.lower())
    
    if positive_count == 0 and negative_count == 0:
        return 0.0
    
    return (positive_count - negative_count) / (positive_count + negative_count)


def _calculate_sentiment_correlation(sentiment1: float, sentiment2: float) -> float:
    """Calculate correlation between two sentiment scores."""
    # Simple correlation calculation
    return (sentiment1 + sentiment2) / 2 if sentiment1 != 0 or sentiment2 != 0 else 0.0


def _get_sector(ticker: str) -> str:
    """Get sector for a ticker."""
    sector_mapping = {
        "SPY": "ETF",
        "AAPL": "Technology",
        "TSLA": "Automotive/Technology"
    }
    return sector_mapping.get(ticker, "Unknown")


def _calculate_overall_sentiment(individual_reports: Dict[str, Any]) -> str:
    """Calculate overall portfolio sentiment."""
    sentiments = [_extract_sentiment(report) for report in individual_reports.values()]
    
    if not sentiments:
        return "Neutral"
    
    avg_sentiment = sum(sentiments) / len(sentiments)
    
    if avg_sentiment > 0.3:
        return "Bullish"
    elif avg_sentiment < -0.3:
        return "Bearish"
    else:
        return "Neutral" 