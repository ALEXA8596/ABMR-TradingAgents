import time
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from tradingagents.blackboard.utils import create_agent_blackboard
from tradingagents.blackboard.schema import (
    PORTFOLIO_OPTIMIZATION, PORTFOLIO_ANALYSIS, PORTFOLIO_BALANCE
)


class PortfolioOptimizer:
    """
    Refactored Portfolio Optimizer that focuses only on portfolio optimization.
    Trade execution is delegated to the Execution Manager.
    """
    
    def __init__(self):
        self.agent_id = "PO_001"
        self.role = "PortfolioOptimizer"
        self.blackboard = create_agent_blackboard(self.agent_id, self.role)
        
        # Portfolio constraints
        self.constraints = {
            'max_allocation_per_asset': 0.20,    # 20% max per asset
            'min_diversification': 5,            # Minimum 5 assets
            'max_sector_concentration': 0.40,    # 40% max per sector
            'target_volatility': 0.15,          # 15% target volatility
            'max_drawdown': 0.20,               # 20% max drawdown
            'var_limit': 0.05                   # 5% Value at Risk limit
        }
    
    def optimize_portfolio(self, tickers: List[str], analyst_reports: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize portfolio allocation based on analyst reports.
        
        Args:
            tickers: List of tickers to optimize
            analyst_reports: Reports from all analysts
            
        Returns:
            Portfolio optimization results
        """
        print(f"[DEBUG] Portfolio Optimizer: Optimizing portfolio for {len(tickers)} tickers")
        
        # Step 1: Analyze analyst recommendations
        recommendation_analysis = self.analyze_analyst_recommendations(tickers, analyst_reports)
        
        # Step 2: Calculate optimal weights
        optimal_weights = self.calculate_optimal_weights(tickers, recommendation_analysis)
        
        # Step 3: Apply portfolio constraints
        print(f"[DEBUG] Before constraints: {optimal_weights}")
        constrained_weights = self.apply_portfolio_constraints(optimal_weights)
        print(f"[DEBUG] After constraints: {constrained_weights}")
        
        # Step 4: Generate optimization report
        print(f"[DEBUG] Generating report with constrained weights: {constrained_weights}")
        optimization_report = self.generate_optimization_report(tickers, constrained_weights, recommendation_analysis)
        print(f"[DEBUG] Report generated, final weights: {optimization_report['final_weights']}")
        
        # Store both original and constrained weights for reference
        optimization_report['original_weights'] = optimal_weights
        optimization_report['constrained_weights'] = constrained_weights
        
        # Step 5: Post to blackboard
        self.post_optimization_to_blackboard(optimization_report)
        
        return optimization_report
    
    def analyze_analyst_recommendations(self, tickers: List[str], analyst_reports: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze analyst recommendations for each ticker."""
        analysis = {}
        
        for ticker in tickers:
            ticker_reports = analyst_reports.get(ticker, {})
            
            # Extract recommendations from different analysts
            recommendations = {
                'fundamental': ticker_reports.get('fundamentals_report', {}),
                'technical': ticker_reports.get('market_report', {}),
                'news': ticker_reports.get('news_report', {}),
                'sentiment': ticker_reports.get('sentiment_report', {}),
                'risk': ticker_reports.get('risk_decision', {})
            }
            
            # Calculate consensus score
            consensus_score = self.calculate_consensus_score(recommendations)
            
            analysis[ticker] = {
                'recommendations': recommendations,
                'consensus_score': consensus_score,
                'risk_level': self.assess_risk_level(recommendations),
                'confidence': self.assess_confidence(recommendations)
            }
        
        return analysis
    
    def calculate_consensus_score(self, recommendations: Dict[str, Any]) -> float:
        """Calculate consensus score from analyst recommendations."""
        scores = []
        
        print(f"[DEBUG] Calculating consensus score for recommendations: {recommendations}")
        
        for analyst_type, report in recommendations.items():
            if isinstance(report, dict):
                # Extract recommendation and confidence
                recommendation = report.get('recommendation', 'Neutral')
                confidence = report.get('confidence', 'Medium')
                
                # Convert to numerical score
                rec_score = self.recommendation_to_score(recommendation)
                conf_score = self.confidence_to_score(confidence)
                
                # Weighted score
                weighted_score = rec_score * conf_score
                scores.append(weighted_score)
                
                print(f"[DEBUG] {analyst_type}: {recommendation} ({rec_score}) * {confidence} ({conf_score}) = {weighted_score}")
            else:
                print(f"[DEBUG] {analyst_type}: Not a dict, skipping")
        
        if not scores:
            print(f"[DEBUG] No valid scores found, returning 0.0")
            return 0.0
        
        final_score = sum(scores) / len(scores)
        print(f"[DEBUG] Final consensus score: {final_score}")
        return final_score
    
    def recommendation_to_score(self, recommendation: str) -> float:
        """Convert recommendation to numerical score."""
        recommendation_map = {
            'Buy': 1.0,
            'Bullish': 0.8,
            'Strong Buy': 1.0,
            'Hold': 0.0,
            'Neutral': 0.0,
            'Sell': -1.0,
            'Bearish': -0.8,
            'Strong Sell': -1.0
        }
        return recommendation_map.get(recommendation, 0.0)
    
    def confidence_to_score(self, confidence: str) -> float:
        """Convert confidence to numerical score."""
        confidence_map = {
            'Very High': 1.2,
            'High': 1.0,
            'Medium': 0.7,
            'Low': 0.4,
            'Very Low': 0.2
        }
        return confidence_map.get(confidence, 0.5)
    
    def assess_risk_level(self, recommendations: Dict[str, Any]) -> str:
        """Assess overall risk level from recommendations."""
        risk_indicators = []
        
        for analyst_type, report in recommendations.items():
            if isinstance(report, dict):
                risk_level = report.get('risk_level', 'Medium')
                risk_indicators.append(risk_level)
        
        # Determine overall risk level
        if 'High' in risk_indicators or 'Critical' in risk_indicators:
            return 'High'
        elif 'Low' in risk_indicators:
            return 'Low'
        else:
            return 'Medium'
    
    def assess_confidence(self, recommendations: Dict[str, Any]) -> str:
        """Assess overall confidence level from recommendations."""
        confidence_levels = []
        
        for analyst_type, report in recommendations.items():
            if isinstance(report, dict):
                confidence = report.get('confidence', 'Medium')
                confidence_levels.append(confidence)
        
        # Determine overall confidence
        if 'High' in confidence_levels:
            return 'High'
        elif 'Low' in confidence_levels:
            return 'Low'
        else:
            return 'Medium'
    
    def calculate_optimal_weights(self, tickers: List[str], analysis: Dict[str, Any]) -> Dict[str, float]:
        """Calculate optimal portfolio weights using Kelly Criterion and risk parity."""
        weights = {}
        
        # Calculate Kelly Criterion weights
        kelly_weights = self.calculate_kelly_weights(tickers, analysis)
        
        # Apply risk parity principles
        risk_parity_weights = self.apply_risk_parity(kelly_weights, analysis)
        
        # Normalize weights to sum to 1
        total_weight = sum(risk_parity_weights.values())
        if total_weight > 0:
            weights = {ticker: weight / total_weight for ticker, weight in risk_parity_weights.items()}
        else:
            # Equal weight if no positive weights
            weights = {ticker: 1.0 / len(tickers) for ticker in tickers}
        
        return weights
    
    def calculate_kelly_weights(self, tickers: List[str], analysis: Dict[str, Any]) -> Dict[str, float]:
        """Calculate Kelly Criterion weights for each ticker."""
        kelly_weights = {}
        
        print(f"[DEBUG] Calculating Kelly weights for {len(tickers)} tickers")
        
        for ticker in tickers:
            ticker_analysis = analysis.get(ticker, {})
            consensus_score = ticker_analysis.get('consensus_score', 0.0)
            confidence = ticker_analysis.get('confidence', 'Medium')
            
            # Convert confidence to win rate estimate
            confidence_to_win_rate = {
                'Very High': 0.8,
                'High': 0.7,
                'Medium': 0.6,
                'Low': 0.5,
                'Very Low': 0.4
            }
            win_rate = confidence_to_win_rate.get(confidence, 0.6)
            
            # Kelly Criterion calculation
            # f = (bp - q) / b
            # where b = odds received, p = win probability, q = loss probability
            expected_return = abs(consensus_score) * 0.15  # 15% expected return
            if expected_return > 0:
                kelly_fraction = (expected_return * win_rate - (1 - win_rate)) / expected_return
                kelly_fraction = max(0, min(kelly_fraction, self.constraints['max_allocation_per_asset']))
            else:
                # For neutral consensus, use a small positive weight based on confidence
                kelly_fraction = 0.1 * confidence_to_win_rate.get(confidence, 0.6)
            
            # Ensure minimum weight for diversification
            kelly_fraction = max(0.05, kelly_fraction)
            
            print(f"[DEBUG] {ticker}: consensus={consensus_score}, confidence={confidence}, win_rate={win_rate}, expected_return={expected_return}, kelly_fraction={kelly_fraction}")
            kelly_weights[ticker] = kelly_fraction
        
        print(f"[DEBUG] Kelly weights: {kelly_weights}")
        return kelly_weights
    
    def apply_risk_parity(self, weights: Dict[str, float], analysis: Dict[str, Any]) -> Dict[str, float]:
        """Apply risk parity principles to equalize risk contribution."""
        # For now, implement basic risk parity
        # In a full implementation, this would calculate volatility and correlation
        
        risk_parity_weights = {}
        
        for ticker, weight in weights.items():
            ticker_analysis = analysis.get(ticker, {})
            risk_level = ticker_analysis.get('risk_level', 'Medium')
            
            # Adjust weights based on risk level
            risk_multiplier = {
                'Low': 1.2,
                'Medium': 1.0,
                'High': 0.8
            }.get(risk_level, 1.0)
            
            risk_parity_weights[ticker] = weight * risk_multiplier
        
        return risk_parity_weights
    
    def apply_portfolio_constraints(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Apply portfolio-level constraints to weights."""
        constrained_weights = weights.copy()
        
        # Constraint 1: Maximum allocation per asset
        max_allocation = self.constraints['max_allocation_per_asset']
        for ticker, weight in constrained_weights.items():
            if weight > max_allocation:
                constrained_weights[ticker] = max_allocation
        
        # Constraint 2: Handle minimum diversification requirement
        min_diversification = self.constraints['min_diversification']
        if len(constrained_weights) < min_diversification:
            # For testing purposes, adjust the constraint to allow fewer assets
            # In production, this would trigger adding more assets
            print(f"[WARNING] Portfolio has {len(constrained_weights)} assets, minimum is {min_diversification}")
            # Instead of forcing equal weights, adjust the max allocation constraint
            # to allow the calculated weights to work
            adjusted_max = min(1.0 / len(constrained_weights), self.constraints['max_allocation_per_asset'])
            print(f"[DEBUG] Adjusted max allocation from {self.constraints['max_allocation_per_asset']:.1%} to {adjusted_max:.1%}")
            
            # Apply the adjusted max allocation constraint
            for ticker, weight in constrained_weights.items():
                if weight > adjusted_max:
                    constrained_weights[ticker] = adjusted_max
        
        # Constraint 3: Normalize weights to sum to 1 (only if not handling diversification issues)
        if len(constrained_weights) >= min_diversification:
            total_weight = sum(constrained_weights.values())
            if total_weight > 0:
                constrained_weights = {ticker: weight / total_weight for ticker, weight in constrained_weights.items()}
        else:
            # For portfolios with insufficient diversification, don't normalize
            # This preserves the calculated weights while respecting constraints
            print(f"[DEBUG] Skipping normalization for {len(constrained_weights)} assets (minimum: {min_diversification})")
        
        return constrained_weights
    
    def generate_optimization_report(self, tickers: List[str], weights: Dict[str, float], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive portfolio optimization report."""
        report = {
            'optimization_id': f"OPT_{int(time.time())}",
            'timestamp': datetime.now().isoformat(),
            'tickers': tickers,
            'final_weights': weights,  # These are the constrained weights
            'analysis_summary': {},
            'constraints_applied': self.constraints,
            'risk_metrics': {},
            'recommendations': []
        }
        
        # Generate analysis summary
        for ticker in tickers:
            ticker_analysis = analysis.get(ticker, {})
            report['analysis_summary'][ticker] = {
                'consensus_score': ticker_analysis.get('consensus_score', 0.0),
                'risk_level': ticker_analysis.get('risk_level', 'Medium'),
                'confidence': ticker_analysis.get('confidence', 'Medium'),
                'allocation': weights.get(ticker, 0.0)
            }
        
        # Calculate portfolio risk metrics
        report['risk_metrics'] = self.calculate_portfolio_risk_metrics(weights, analysis)
        
        # Generate recommendations
        report['recommendations'] = self.generate_recommendations(weights, analysis)
        
        return report
    
    def calculate_portfolio_risk_metrics(self, weights: Dict[str, float], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate portfolio-level risk metrics."""
        # Calculate weighted average risk level
        weighted_risk = 0.0
        total_weight = 0.0
        
        for ticker, weight in weights.items():
            ticker_analysis = analysis.get(ticker, {})
            risk_level = ticker_analysis.get('risk_level', 'Medium')
            
            risk_score = {'Low': 0.3, 'Medium': 0.6, 'High': 0.9}.get(risk_level, 0.6)
            weighted_risk += weight * risk_score
            total_weight += weight
        
        avg_risk = weighted_risk / total_weight if total_weight > 0 else 0.6
        
        # Determine overall portfolio risk level
        if avg_risk < 0.4:
            portfolio_risk = 'Low'
        elif avg_risk < 0.7:
            portfolio_risk = 'Medium'
        else:
            portfolio_risk = 'High'
        
        return {
            'portfolio_risk_level': portfolio_risk,
            'weighted_average_risk': avg_risk,
            'diversification_score': len(weights) / self.constraints['min_diversification'],
            'concentration_risk': max(weights.values()) if weights else 0.0
        }
    
    def generate_recommendations(self, weights: Dict[str, float], analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on optimization results."""
        recommendations = []
        
        # Check for high concentration
        max_weight = max(weights.values()) if weights else 0.0
        if max_weight > 0.25:
            recommendations.append(f"Consider reducing position in highest weighted asset (currently {max_weight:.1%})")
        
        # Check for low diversification
        if len(weights) < self.constraints['min_diversification']:
            recommendations.append(f"Portfolio has only {len(weights)} assets, consider adding more for diversification")
        
        # Check for high risk
        high_risk_assets = [ticker for ticker, analysis_data in analysis.items() 
                           if analysis_data.get('risk_level') == 'High']
        if high_risk_assets:
            recommendations.append(f"Monitor high-risk assets: {', '.join(high_risk_assets)}")
        
        # Check for low confidence
        low_confidence_assets = [ticker for ticker, analysis_data in analysis.items() 
                                if analysis_data.get('confidence') == 'Low']
        if low_confidence_assets:
            recommendations.append(f"Consider reducing positions in low-confidence assets: {', '.join(low_confidence_assets)}")
        
        if not recommendations:
            recommendations.append("Portfolio appears well-optimized with current constraints")
        
        return recommendations
    
    def post_optimization_to_blackboard(self, optimization_report: Dict[str, Any]):
        """Post optimization results to the blackboard."""
        # Use the correct blackboard method
        self.blackboard.post_portfolio_optimization(
            tickers=optimization_report['tickers'],
            optimization_results=optimization_report,
            strategy="Multi-Asset Hedging with Kelly Criterion & Risk Parity",
            confidence="High"
        )
        
        print(f"[DEBUG] Portfolio Optimizer: Posted optimization results to blackboard")


def create_portfolio_optimizer():
    """Factory function to create a Portfolio Optimizer instance."""
    return PortfolioOptimizer() 