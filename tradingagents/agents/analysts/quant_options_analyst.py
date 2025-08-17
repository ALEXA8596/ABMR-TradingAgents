import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass

from tradingagents.blackboard.utils import create_agent_blackboard


@dataclass
class AlphaSignal:
    """Structured alpha signal for options trading"""
    signal_type: str  # "VOLATILITY", "DIRECTIONAL", "ARBITRAGE", "HEDGING"
    confidence: float  # 0-1 confidence score
    magnitude: float  # Signal strength (-1 to 1)
    time_horizon: str  # "SHORT_TERM", "MEDIUM_TERM", "LONG_TERM"
    rationale: str  # Chain-of-thought reasoning
    supporting_data: Dict[str, Any]  # Raw data supporting the signal


@dataclass
class OptionsAlpha:
    """Comprehensive options alpha analysis"""
    ticker: str
    timestamp: datetime
    volatility_alpha: Optional[AlphaSignal]
    directional_alpha: Optional[AlphaSignal]
    arbitrage_alpha: Optional[AlphaSignal]
    hedging_alpha: Optional[AlphaSignal]
    combined_alpha_score: float
    recommended_strategies: List[str]
    risk_metrics: Dict[str, float]


class ChainOfAlphaOptionsAnalyst:
    """
    Chain-of-Alpha based quant options analyst implementing multi-step reasoning
    for generating sophisticated alpha signals in options trading.
    
    Based on the Chain-of-Alpha research methodology for unleashing the power
    of large language models in financial alpha generation.
    """
    
    def __init__(self, llm, memory, toolkit):
        self.llm = llm
        self.memory = memory
        self.toolkit = toolkit
        self.alpha_history = []
        
    def generate_chain_of_alpha(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main Chain-of-Alpha analysis pipeline for options trading.
        
        Implements multi-step reasoning chains:
        1. Data Collection & Preprocessing
        2. Volatility Alpha Generation
        3. Directional Alpha Generation  
        4. Arbitrage Alpha Detection
        5. Hedging Alpha Synthesis
        6. Multi-Factor Alpha Combination
        7. Strategy Recommendation
        """
        
        ticker = state["company_of_interest"]
        trade_date = state.get("trade_date", datetime.now().strftime("%Y-%m-%d"))
        
        print(f"🔍 Starting Chain-of-Alpha analysis for {ticker}")
        
        # Step 1: Multi-Source Data Collection
        market_data = self._collect_market_data(ticker)
        options_data = self._collect_options_data(ticker)
        sentiment_data = self._collect_sentiment_data(ticker)
        fundamental_data = self._collect_fundamental_data(ticker)
        
        # Step 2: Chain-of-Thought Alpha Generation
        volatility_alpha = self._generate_volatility_alpha(
            ticker, market_data, options_data, sentiment_data
        )
        
        directional_alpha = self._generate_directional_alpha(
            ticker, market_data, sentiment_data, fundamental_data
        )
        
        arbitrage_alpha = self._generate_arbitrage_alpha(
            ticker, options_data, market_data
        )
        
        hedging_alpha = self._generate_hedging_alpha(
            ticker, market_data, options_data, sentiment_data
        )
        
        # Step 3: Multi-Factor Alpha Combination
        combined_alpha = self._combine_alpha_signals(
            volatility_alpha, directional_alpha, arbitrage_alpha, hedging_alpha
        )
        
        # Step 4: Strategy Generation
        strategies = self._generate_options_strategies(
            ticker, combined_alpha, options_data
        )
        
        # Step 5: Risk Assessment
        risk_metrics = self._assess_risk_metrics(
            ticker, combined_alpha, strategies, options_data
        )
        
        # Create comprehensive alpha analysis
        options_alpha = OptionsAlpha(
            ticker=ticker,
            timestamp=datetime.now(),
            volatility_alpha=volatility_alpha,
            directional_alpha=directional_alpha,
            arbitrage_alpha=arbitrage_alpha,
            hedging_alpha=hedging_alpha,
            combined_alpha_score=combined_alpha["score"],
            recommended_strategies=strategies,
            risk_metrics=risk_metrics
        )
        
        # Store in history
        self.alpha_history.append(options_alpha)
        
        # Generate reports
        report_data = self._generate_alpha_reports(ticker, trade_date, options_alpha)
        
        # Update blackboard
        self._update_blackboard(ticker, options_alpha)
        
        # Update memory
        self._update_memory(ticker, options_alpha)
        
        return {
            "options_alpha_analysis": options_alpha,
            "alpha_report_file": report_data["markdown_path"],
            "alpha_artifact_file": report_data["json_path"],
            "chain_of_alpha_completed": True,
            "alpha_signals": {
                "volatility": volatility_alpha,
                "directional": directional_alpha,
                "arbitrage": arbitrage_alpha,
                "hedging": hedging_alpha
            }
        }
    
    def _collect_market_data(self, ticker: str) -> Dict[str, Any]:
        """Collect comprehensive market data using existing alpha functions"""
        try:
            # Use existing momentum alpha
            momentum_data = self.toolkit.get_portfolio_momentum.invoke({
                "short_period": 20,
                "long_period": 60,
                "momentum_threshold": 0.02
            })
            
            # Use existing mean reversion alpha
            mean_rev_data = self.toolkit.get_portfolio_mean_reversion.invoke({
                "lookback_days": 60,
                "z_score_threshold": 2.0
            })
            
            # Use existing risk parity alpha
            risk_parity_data = self.toolkit.get_portfolio_risk_parity.invoke({
                "lookback_days": 252
            })
            
            return {
                "momentum": momentum_data,
                "mean_reversion": mean_rev_data,
                "risk_parity": risk_parity_data,
                "ticker": ticker
            }
        except Exception as e:
            print(f"Error collecting market data: {e}")
            return {"error": str(e)}
    
    def _collect_options_data(self, ticker: str) -> Dict[str, Any]:
        """Collect options-specific data for alpha generation"""
        try:
            # This would integrate with options data providers
            # For now, we'll create a mock structure
            return {
                "implied_volatility": 0.25,
                "historical_volatility": 0.22,
                "volatility_skew": 0.05,
                "term_structure": {
                    "30d": 0.23,
                    "60d": 0.25,
                    "90d": 0.27
                },
                "greeks": {
                    "delta": 0.6,
                    "gamma": 0.02,
                    "theta": -0.01,
                    "vega": 0.15
                }
            }
        except Exception as e:
            print(f"Error collecting options data: {e}")
            return {"error": str(e)}
    
    def _collect_sentiment_data(self, ticker: str) -> Dict[str, Any]:
        """Collect sentiment data for alpha generation"""
        try:
            # This would integrate with sentiment analysis tools
            return {
                "social_sentiment": 0.65,
                "news_sentiment": 0.58,
                "analyst_ratings": 0.72,
                "insider_activity": 0.45
            }
        except Exception as e:
            print(f"Error collecting sentiment data: {e}")
            return {"error": str(e)}
    
    def _collect_fundamental_data(self, ticker: str) -> Dict[str, Any]:
        """Collect fundamental data for alpha generation"""
        try:
            # This would integrate with fundamental data providers
            return {
                "pe_ratio": 25.5,
                "pb_ratio": 3.2,
                "debt_to_equity": 0.15,
                "revenue_growth": 0.18,
                "earnings_growth": 0.22
            }
        except Exception as e:
            print(f"Error collecting fundamental data: {e}")
            return {"error": str(e)}
    
    def _generate_volatility_alpha(self, ticker: str, market_data: Dict, 
                                  options_data: Dict, sentiment_data: Dict) -> AlphaSignal:
        """
        Generate volatility alpha using Chain-of-Thought reasoning.
        
        Chain of reasoning:
        1. Compare implied vs historical volatility
        2. Analyze volatility skew and term structure
        3. Consider market sentiment impact on volatility
        4. Generate volatility alpha signal
        """
        
        prompt = f"""
        As a quantitative options analyst, analyze the volatility alpha for {ticker}.
        
        Market Data: {market_data}
        Options Data: {options_data}
        Sentiment Data: {sentiment_data}
        
        Use Chain-of-Thought reasoning to analyze:
        
        Step 1: Volatility Mispricing Analysis
        - Compare implied vs historical volatility
        - Identify volatility regime (low/medium/high)
        - Assess volatility skew patterns
        
        Step 2: Market Context Integration
        - How does current market sentiment affect volatility?
        - What do momentum and mean reversion signals suggest about volatility?
        
        Step 3: Alpha Signal Generation
        - Is volatility overpriced or underpriced?
        - What's the confidence level in this assessment?
        - What's the expected magnitude of volatility correction?
        
        Respond with a structured analysis and then provide:
        1. Signal type: VOLATILITY
        2. Confidence: 0-1 score
        3. Magnitude: -1 to 1 (negative = volatility overpriced, positive = underpriced)
        4. Time horizon: SHORT_TERM/MEDIUM_TERM/LONG_TERM
        5. Detailed rationale
        """
        
        try:
            response = self.llm.invoke(prompt)
            
            # Parse the response to extract alpha signal components
            # This is a simplified parser - in production you'd want more robust parsing
            content = response.content.lower()
            
            # Extract confidence (look for patterns like "confidence: 0.8" or "80% confidence")
            confidence = 0.5  # default
            if "confidence" in content:
                # Simple confidence extraction logic
                confidence = 0.7  # Placeholder
            
            # Extract magnitude (look for directional indicators)
            magnitude = 0.0  # default
            if "overpriced" in content or "high" in content:
                magnitude = -0.5
            elif "underpriced" in content or "low" in content:
                magnitude = 0.5
            
            # Determine time horizon
            time_horizon = "MEDIUM_TERM"
            if "short" in content:
                time_horizon = "SHORT_TERM"
            elif "long" in content:
                time_horizon = "LONG_TERM"
            
            return AlphaSignal(
                signal_type="VOLATILITY",
                confidence=confidence,
                magnitude=magnitude,
                time_horizon=time_horizon,
                rationale=response.content,
                supporting_data={
                    "market_data": market_data,
                    "options_data": options_data,
                    "sentiment_data": sentiment_data
                }
            )
            
        except Exception as e:
            print(f"Error generating volatility alpha: {e}")
            return AlphaSignal(
                signal_type="VOLATILITY",
                confidence=0.0,
                magnitude=0.0,
                time_horizon="MEDIUM_TERM",
                rationale=f"Error in volatility alpha generation: {e}",
                supporting_data={}
            )
    
    def _generate_directional_alpha(self, ticker: str, market_data: Dict,
                                  sentiment_data: Dict, fundamental_data: Dict) -> AlphaSignal:
        """
        Generate directional alpha using Chain-of-Thought reasoning.
        
        Chain of reasoning:
        1. Analyze momentum and mean reversion signals
        2. Integrate sentiment analysis
        3. Consider fundamental factors
        4. Generate directional alpha signal
        """
        
        prompt = f"""
        As a quantitative options analyst, analyze the directional alpha for {ticker}.
        
        Market Data: {market_data}
        Sentiment Data: {sentiment_data}
        Fundamental Data: {fundamental_data}
        
        Use Chain-of-Thought reasoning to analyze:
        
        Step 1: Technical Signal Analysis
        - What do momentum signals indicate?
        - What do mean reversion signals suggest?
        - Are signals aligned or conflicting?
        
        Step 2: Sentiment Integration
        - How does social and news sentiment align with technical signals?
        - What does analyst consensus suggest?
        
        Step 3: Fundamental Context
        - How do valuation metrics support technical signals?
        - What growth prospects suggest about direction?
        
        Step 4: Alpha Signal Generation
        - What's the overall directional bias?
        - What's the confidence level?
        - What's the expected magnitude of move?
        
        Respond with structured analysis and provide:
        1. Signal type: DIRECTIONAL
        2. Confidence: 0-1 score
        3. Magnitude: -1 to 1 (negative = bearish, positive = bullish)
        4. Time horizon: SHORT_TERM/MEDIUM_TERM/LONG_TERM
        5. Detailed rationale
        """
        
        try:
            response = self.llm.invoke(prompt)
            
            # Parse response for directional alpha
            content = response.content.lower()
            
            confidence = 0.5
            magnitude = 0.0
            time_horizon = "MEDIUM_TERM"
            
            # Extract directional bias
            if "bullish" in content or "up" in content or "positive" in content:
                magnitude = 0.6
            elif "bearish" in content or "down" in content or "negative" in content:
                magnitude = -0.6
            
            # Extract confidence indicators
            if "strong" in content or "high confidence" in content:
                confidence = 0.8
            elif "weak" in content or "low confidence" in content:
                confidence = 0.3
            
            return AlphaSignal(
                signal_type="DIRECTIONAL",
                confidence=confidence,
                magnitude=magnitude,
                time_horizon=time_horizon,
                rationale=response.content,
                supporting_data={
                    "market_data": market_data,
                    "sentiment_data": sentiment_data,
                    "fundamental_data": fundamental_data
                }
            )
            
        except Exception as e:
            print(f"Error generating directional alpha: {e}")
            return AlphaSignal(
                signal_type="DIRECTIONAL",
                confidence=0.0,
                magnitude=0.0,
                time_horizon="MEDIUM_TERM",
                rationale=f"Error in directional alpha generation: {e}",
                supporting_data={}
            )
    
    def _generate_arbitrage_alpha(self, ticker: str, options_data: Dict,
                                 market_data: Dict) -> AlphaSignal:
        """
        Generate arbitrage alpha using Chain-of-Thought reasoning.
        
        Chain of reasoning:
        1. Analyze volatility surface for mispricings
        2. Check for calendar spread opportunities
        3. Identify strike price arbitrage
        4. Generate arbitrage alpha signal
        """
        
        prompt = f"""
        As a quantitative options analyst, analyze arbitrage opportunities for {ticker}.
        
        Options Data: {options_data}
        Market Data: {market_data}
        
        Use Chain-of-Thought reasoning to analyze:
        
        Step 1: Volatility Surface Analysis
        - Are there inconsistencies in implied volatility across strikes?
        - Is the volatility term structure properly priced?
        
        Step 2: Spread Opportunity Detection
        - Are there calendar spread opportunities?
        - Are there strike price arbitrage opportunities?
        
        Step 3: Risk Assessment
        - What are the execution risks?
        - What's the profit potential vs risk?
        
        Step 4: Alpha Signal Generation
        - What's the confidence in arbitrage opportunity?
        - What's the expected profit magnitude?
        
        Respond with structured analysis and provide:
        1. Signal type: ARBITRAGE
        2. Confidence: 0-1 score
        3. Magnitude: 0 to 1 (profit potential)
        4. Time horizon: SHORT_TERM/MEDIUM_TERM/LONG_TERM
        5. Detailed rationale
        """
        
        try:
            response = self.llm.invoke(prompt)
            
            content = response.content.lower()
            
            confidence = 0.5
            magnitude = 0.0
            time_horizon = "SHORT_TERM"  # Arbitrage typically short-term
            
            # Extract arbitrage opportunity indicators
            if "opportunity" in content or "mispricing" in content:
                magnitude = 0.4
            if "strong" in content or "clear" in content:
                confidence = 0.7
            
            return AlphaSignal(
                signal_type="ARBITRAGE",
                confidence=confidence,
                magnitude=magnitude,
                time_horizon=time_horizon,
                rationale=response.content,
                supporting_data={
                    "options_data": options_data,
                    "market_data": market_data
                }
            )
            
        except Exception as e:
            print(f"Error generating arbitrage alpha: {e}")
            return AlphaSignal(
                signal_type="ARBITRAGE",
                confidence=0.0,
                magnitude=0.0,
                time_horizon="SHORT_TERM",
                rationale=f"Error in arbitrage alpha generation: {e}",
                supporting_data={}
            )
    
    def _generate_hedging_alpha(self, ticker: str, market_data: Dict,
                               options_data: Dict, sentiment_data: Dict) -> AlphaSignal:
        """
        Generate hedging alpha using Chain-of-Thought reasoning.
        
        Chain of reasoning:
        1. Assess current portfolio risk exposure
        2. Identify optimal hedging instruments
        3. Calculate hedging ratios
        4. Generate hedging alpha signal
        """
        
        prompt = f"""
        As a quantitative options analyst, analyze hedging opportunities for {ticker}.
        
        Market Data: {market_data}
        Options Data: {options_data}
        Sentiment Data: {sentiment_data}
        
        Use Chain-of-Thought reasoning to analyze:
        
        Step 1: Risk Exposure Assessment
        - What are the current market risks?
        - How does sentiment suggest risk changes?
        
        Step 2: Hedging Instrument Selection
        - What options strategies provide optimal hedging?
        - What's the cost vs benefit of different hedges?
        
        Step 3: Hedging Ratio Calculation
        - What's the optimal hedge ratio?
        - How should hedging be timed?
        
        Step 4: Alpha Signal Generation
        - What's the confidence in hedging need?
        - What's the expected hedging benefit?
        
        Respond with structured analysis and provide:
        1. Signal type: HEDGING
        2. Confidence: 0-1 score
        3. Magnitude: 0 to 1 (hedging benefit)
        4. Time horizon: SHORT_TERM/MEDIUM_TERM/LONG_TERM
        5. Detailed rationale
        """
        
        try:
            response = self.llm.invoke(prompt)
            
            content = response.content.lower()
            
            confidence = 0.5
            magnitude = 0.0
            time_horizon = "MEDIUM_TERM"
            
            # Extract hedging indicators
            if "hedge" in content or "protection" in content:
                magnitude = 0.5
            if "high risk" in content or "volatile" in content:
                magnitude = 0.7
            
            return AlphaSignal(
                signal_type="HEDGING",
                confidence=confidence,
                magnitude=magnitude,
                time_horizon=time_horizon,
                rationale=response.content,
                supporting_data={
                    "market_data": market_data,
                    "options_data": options_data,
                    "sentiment_data": sentiment_data
                }
            )
            
        except Exception as e:
            print(f"Error generating hedging alpha: {e}")
            return AlphaSignal(
                signal_type="HEDGING",
                confidence=0.0,
                magnitude=0.0,
                time_horizon="MEDIUM_TERM",
                rationale=f"Error in hedging alpha generation: {e}",
                supporting_data={}
            )
    
    def _combine_alpha_signals(self, volatility_alpha: AlphaSignal,
                               directional_alpha: AlphaSignal,
                               arbitrage_alpha: AlphaSignal,
                               hedging_alpha: AlphaSignal) -> Dict[str, Any]:
        """
        Combine multiple alpha signals using weighted scoring methodology.
        
        This implements the Chain-of-Alpha approach of synthesizing
        multiple specialized alpha signals into a unified decision framework.
        """
        
        # Weight each alpha signal based on its importance for options trading
        weights = {
            "volatility": 0.35,    # Volatility is crucial for options
            "directional": 0.25,   # Direction matters but less than volatility
            "arbitrage": 0.20,     # Arbitrage opportunities
            "hedging": 0.20        # Risk management
        }
        
        # Calculate weighted alpha score
        volatility_score = volatility_alpha.confidence * volatility_alpha.magnitude
        directional_score = directional_alpha.confidence * directional_alpha.magnitude
        arbitrage_score = arbitrage_alpha.confidence * arbitrage_alpha.magnitude
        hedging_score = hedging_alpha.confidence * hedging_alpha.magnitude
        
        combined_score = (
            weights["volatility"] * volatility_score +
            weights["directional"] * directional_score +
            weights["arbitrage"] * arbitrage_score +
            weights["hedging"] * hedging_score
        )
        
        # Normalize to -1 to 1 range
        combined_score = max(-1.0, min(1.0, combined_score))
        
        # Determine overall alpha strength
        if abs(combined_score) > 0.7:
            alpha_strength = "STRONG"
        elif abs(combined_score) > 0.4:
            alpha_strength = "MODERATE"
        else:
            alpha_strength = "WEAK"
        
        return {
            "score": combined_score,
            "strength": alpha_strength,
            "component_scores": {
                "volatility": volatility_score,
                "directional": directional_score,
                "arbitrage": arbitrage_score,
                "hedging": hedging_score
            },
            "weights": weights
        }
    
    def _generate_options_strategies(self, ticker: str, combined_alpha: Dict,
                                   options_data: Dict) -> List[str]:
        """
        Generate options strategies based on combined alpha signals.
        
        Uses Chain-of-Thought reasoning to determine optimal
        options strategies for the given alpha profile.
        """
        
        alpha_score = combined_alpha["score"]
        alpha_strength = combined_alpha["strength"]
        
        strategies = []
        
        if alpha_strength == "STRONG":
            if alpha_score > 0.5:
                # Strong bullish alpha
                strategies.extend([
                    "Long Call Spreads",
                    "Bull Call Spreads",
                    "Covered Calls (if holding stock)"
                ])
            elif alpha_score < -0.5:
                # Strong bearish alpha
                strategies.extend([
                    "Long Put Spreads",
                    "Bear Put Spreads",
                    "Protective Puts"
                ])
        elif alpha_strength == "MODERATE":
            if alpha_score > 0.2:
                strategies.extend([
                    "Iron Condors (bullish bias)",
                    "Calendar Spreads"
                ])
            elif alpha_score < -0.2:
                strategies.extend([
                    "Iron Condors (bearish bias)",
                    "Calendar Spreads"
                ])
            else:
                strategies.extend([
                    "Iron Condors (neutral)",
                    "Butterfly Spreads"
                ])
        else:
            # Weak alpha - focus on income generation
            strategies.extend([
                "Iron Condors",
                "Butterfly Spreads",
                "Calendar Spreads"
            ])
        
        return strategies
    
    def _assess_risk_metrics(self, ticker: str, combined_alpha: Dict,
                            strategies: List[str], options_data: Dict) -> Dict[str, float]:
        """
        Assess risk metrics for the generated alpha signals and strategies.
        """
        
        alpha_score = combined_alpha["score"]
        alpha_strength = combined_alpha["strength"]
        
        # Calculate risk metrics based on alpha characteristics
        volatility_risk = 0.5  # Base volatility risk
        directional_risk = abs(alpha_score) * 0.3  # Higher alpha = higher directional risk
        execution_risk = 0.2  # Base execution risk
        
        # Adjust based on alpha strength
        if alpha_strength == "STRONG":
            volatility_risk *= 1.5
            directional_risk *= 1.3
        elif alpha_strength == "WEAK":
            volatility_risk *= 0.7
            directional_risk *= 0.5
        
        total_risk = min(1.0, volatility_risk + directional_risk + execution_risk)
        
        return {
            "volatility_risk": round(volatility_risk, 3),
            "directional_risk": round(directional_risk, 3),
            "execution_risk": round(execution_risk, 3),
            "total_risk": round(total_risk, 3),
            "risk_reward_ratio": round(abs(alpha_score) / total_risk if total_risk > 0 else 0, 3)
        }
    
    def _generate_alpha_reports(self, ticker: str, trade_date: str,
                               options_alpha: OptionsAlpha) -> Dict[str, str]:
        """
        Generate comprehensive alpha analysis reports.
        """
        
        # Prepare results directory
        results_root = self.toolkit.config.get("results_dir", "./results")
        reports_dir = os.path.join(results_root, ticker, trade_date, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        # Generate JSON artifact
        json_path = os.path.join(
            reports_dir, 
            f"chain_of_alpha_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        try:
            # Convert dataclass to dict for JSON serialization
            alpha_dict = {
                "ticker": options_alpha.ticker,
                "timestamp": options_alpha.timestamp.isoformat(),
                "volatility_alpha": {
                    "signal_type": options_alpha.volatility_alpha.signal_type,
                    "confidence": options_alpha.volatility_alpha.confidence,
                    "magnitude": options_alpha.volatility_alpha.magnitude,
                    "time_horizon": options_alpha.volatility_alpha.time_horizon,
                    "rationale": options_alpha.volatility_alpha.rationale
                } if options_alpha.volatility_alpha else None,
                "directional_alpha": {
                    "signal_type": options_alpha.directional_alpha.signal_type,
                    "confidence": options_alpha.directional_alpha.confidence,
                    "magnitude": options_alpha.directional_alpha.magnitude,
                    "time_horizon": options_alpha.directional_alpha.time_horizon,
                    "rationale": options_alpha.directional_alpha.rationale
                } if options_alpha.directional_alpha else None,
                "arbitrage_alpha": {
                    "signal_type": options_alpha.arbitrage_alpha.signal_type,
                    "confidence": options_alpha.arbitrage_alpha.confidence,
                    "magnitude": options_alpha.arbitrage_alpha.magnitude,
                    "time_horizon": options_alpha.arbitrage_alpha.time_horizon,
                    "rationale": options_alpha.arbitrage_alpha.rationale
                } if options_alpha.arbitrage_alpha else None,
                "hedging_alpha": {
                    "signal_type": options_alpha.hedging_alpha.signal_type,
                    "confidence": options_alpha.hedging_alpha.confidence,
                    "magnitude": options_alpha.hedging_alpha.magnitude,
                    "time_horizon": options_alpha.hedging_alpha.time_horizon,
                    "rationale": options_alpha.hedging_alpha.rationale
                } if options_alpha.hedging_alpha else None,
                "combined_alpha_score": options_alpha.combined_alpha_score,
                "recommended_strategies": options_alpha.recommended_strategies,
                "risk_metrics": options_alpha.risk_metrics
            }
            
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(alpha_dict, f, indent=2)
                
        except Exception as e:
            print(f"Error saving JSON artifact: {e}")
            json_path = None
        
        # Generate Markdown report
        md_path = os.path.join(reports_dir, "chain_of_alpha_report.md")
        
        try:
            lines = []
            lines.append(f"# Chain-of-Alpha Options Analysis Report: {ticker} ({trade_date})\n")
            
            lines.append("## Executive Summary\n")
            lines.append(f"**Combined Alpha Score**: {options_alpha.combined_alpha_score:.3f}\n")
            lines.append(f"**Alpha Strength**: {options_alpha.combined_alpha_score:.3f}\n")
            lines.append(f"**Risk Level**: {options_alpha.risk_metrics['total_risk']:.3f}\n")
            
            lines.append("\n## Alpha Signal Analysis\n")
            
            # Volatility Alpha
            if options_alpha.volatility_alpha:
                va = options_alpha.volatility_alpha
                lines.append(f"### Volatility Alpha\n")
                lines.append(f"- **Signal**: {va.signal_type}\n")
                lines.append(f"- **Confidence**: {va.confidence:.3f}\n")
                lines.append(f"- **Magnitude**: {va.magnitude:.3f}\n")
                lines.append(f"- **Time Horizon**: {va.time_horizon}\n")
                lines.append(f"- **Rationale**: {va.rationale[:200]}...\n")
            
            # Directional Alpha
            if options_alpha.directional_alpha:
                da = options_alpha.directional_alpha
                lines.append(f"\n### Directional Alpha\n")
                lines.append(f"- **Signal**: {da.signal_type}\n")
                lines.append(f"- **Confidence**: {da.confidence:.3f}\n")
                lines.append(f"- **Magnitude**: {da.magnitude:.3f}\n")
                lines.append(f"- **Time Horizon**: {da.time_horizon}\n")
                lines.append(f"- **Rationale**: {da.rationale[:200]}...\n")
            
            # Arbitrage Alpha
            if options_alpha.arbitrage_alpha:
                aa = options_alpha.arbitrage_alpha
                lines.append(f"\n### Arbitrage Alpha\n")
                lines.append(f"- **Signal**: {aa.signal_type}\n")
                lines.append(f"- **Confidence**: {aa.confidence:.3f}\n")
                lines.append(f"- **Magnitude**: {aa.magnitude:.3f}\n")
                lines.append(f"- **Time Horizon**: {aa.time_horizon}\n")
                lines.append(f"- **Rationale**: {aa.rationale[:200]}...\n")
            
            # Hedging Alpha
            if options_alpha.hedging_alpha:
                ha = options_alpha.hedging_alpha
                lines.append(f"\n### Hedging Alpha\n")
                lines.append(f"- **Signal**: {ha.signal_type}\n")
                lines.append(f"- **Confidence**: {ha.confidence:.3f}\n")
                lines.append(f"- **Magnitude**: {ha.magnitude:.3f}\n")
                lines.append(f"- **Time Horizon**: {ha.time_horizon}\n")
                lines.append(f"- **Rationale**: {ha.rationale[:200]}...\n")
            
            lines.append("\n## Recommended Strategies\n")
            for strategy in options_alpha.recommended_strategies:
                lines.append(f"- {strategy}\n")
            
            lines.append("\n## Risk Metrics\n")
            for metric, value in options_alpha.risk_metrics.items():
                lines.append(f"- **{metric.replace('_', ' ').title()}**: {value}\n")
            
            lines.append("\n## Chain-of-Alpha Methodology\n")
            lines.append("This analysis uses the Chain-of-Alpha approach:\n")
            lines.append("1. **Multi-Step Reasoning**: Breaking down complex options decisions into logical chains\n")
            lines.append("2. **Alpha Signal Generation**: Creating specialized signals for volatility, direction, arbitrage, and hedging\n")
            lines.append("3. **Signal Combination**: Weighted synthesis of multiple alpha factors\n")
            lines.append("4. **Strategy Generation**: Options strategies optimized for the combined alpha profile\n")
            lines.append("5. **Risk Assessment**: Comprehensive risk metrics for informed decision making\n")
            
            with open(md_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
                
        except Exception as e:
            print(f"Error saving Markdown report: {e}")
            md_path = None
        
        return {
            "json_path": json_path,
            "markdown_path": md_path
        }
    
    def _update_blackboard(self, ticker: str, options_alpha: OptionsAlpha):
        """Update the blackboard with alpha analysis results"""
        try:
            bb = create_agent_blackboard("COA_001", "ChainOfAlphaOptionsAnalyst")
            bb.post_investment_decision(
                ticker=ticker,
                decision="Chain-of-Alpha Options Analysis",
                reasoning=f"Combined Alpha Score: {options_alpha.combined_alpha_score:.3f}",
                confidence=str(options_alpha.combined_alpha_score)
            )
        except Exception as e:
            print(f"Error updating blackboard: {e}")
    
    def _update_memory(self, ticker: str, options_alpha: OptionsAlpha):
        """Update memory with alpha analysis results"""
        try:
            self.memory.add_situations([
                (
                    f"Chain-of-Alpha analysis for {ticker}",
                    f"Combined Alpha Score: {options_alpha.combined_alpha_score:.3f}, "
                    f"Strategies: {', '.join(options_alpha.recommended_strategies)}"
                )
            ])
        except Exception as e:
            print(f"Error updating memory: {e}")


def create_chain_of_alpha_options_analyst(llm, memory, toolkit):
    """
    Factory function to create a Chain-of-Alpha options analyst.
    
    This implements the research methodology from "Chain-of-Alpha: Unleashing the Power
    of Large Language Models for Financial Alpha Generation" specifically adapted for
    options trading applications.
    """
    
    analyst = ChainOfAlphaOptionsAnalyst(llm, memory, toolkit)
    return analyst.generate_chain_of_alpha
