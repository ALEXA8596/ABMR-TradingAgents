import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from tradingagents.blackboard.utils import create_agent_blackboard
from tradingagents.blackboard.schema import (
    INVESTMENT_DECISION, PORTFOLIO_RECOMMENDATION, 
    TRADE_ACTION_BUY, TRADE_ACTION_SELL, TRADE_ACTION_HOLD
)


class PortfolioManager:
    """
    Central decision-making agent that aggregates all analyst inputs,
    resolves conflicts, and makes final investment decisions.
    """
    
    def __init__(self):
        self.agent_id = "PM_001"
        self.role = "PortfolioManager"
        self.decision_authority = "HIGHEST"
        self.risk_limits = self.load_risk_limits()
        self.blackboard = create_agent_blackboard(self.agent_id, self.role)
        
        # Agent priority hierarchy for conflict resolution
        self.agent_priority = {
            'RiskManager': 1,           # Highest priority
            'ResearchManager': 2,        # Second priority
            'PortfolioManager': 3,       # Final decision maker
            'TechnicalAnalyst': 4,
            'FundamentalAnalyst': 5,
            'SocialMediaAnalyst': 6,
            'NewsAnalyst': 7,
            'MacroeconomicAnalyst': 8
        }
        
        # Portfolio constraints
        self.portfolio_constraints = {
            'max_allocation_per_asset': 0.20,    # 20% max per asset
            'min_diversification': 5,            # Minimum 5 assets
            'max_sector_concentration': 0.40,    # 40% max per sector
            'target_volatility': 0.15,          # 15% target volatility
            'max_drawdown': 0.20,               # 20% max drawdown
            'var_limit': 0.05                   # 5% Value at Risk limit
        }
    
    def load_risk_limits(self) -> Dict[str, Any]:
        """Load risk limits from configuration."""
        return {
            'max_portfolio_risk': 0.15,
            'max_position_risk': 0.05,
            'max_correlation': 0.70
        }
    
    def aggregate_analyst_inputs(self, ticker: str) -> Dict[str, Any]:
        """
        Collect and aggregate all analyst recommendations for a ticker.
        
        Args:
            ticker: The ticker symbol to analyze
            
        Returns:
            Dictionary containing aggregated analyst inputs
        """
        print(f"[DEBUG] Portfolio Manager: Aggregating inputs for {ticker}")
        
        # Get all recent analysis reports from blackboard
        recent_analyses = self.blackboard.get_analysis_reports(ticker=ticker)
        
        aggregated_inputs = {
            'ticker': ticker,
            'analyst_recommendations': {},
            'risk_assessments': {},
            'confidence_levels': {},
            'timestamp': datetime.now().isoformat()
        }
        
        if not recent_analyses:
            print(f"[WARNING] No analysis reports found for {ticker}")
            return aggregated_inputs
        
        # Process each analysis report
        for analysis in recent_analyses:
            sender_role = analysis.get('sender', {}).get('role', 'Unknown')
            content = analysis.get('content', {})
            
            # Extract recommendation and confidence
            if 'analysis' in content and isinstance(content['analysis'], dict):
                analysis_data = content['analysis']
                recommendation = analysis_data.get('recommendation', 'N/A')
                confidence = analysis_data.get('confidence', 'N/A')
            else:
                recommendation = content.get('recommendation', 'N/A')
                confidence = content.get('confidence', 'N/A')
            
            # Store by agent role
            aggregated_inputs['analyst_recommendations'][sender_role] = {
                'recommendation': recommendation,
                'confidence': confidence,
                'timestamp': analysis.get('timestamp'),
                'message_id': analysis.get('message_id')
            }
            
            # Extract risk assessment if available
            if 'risk_level' in content:
                aggregated_inputs['risk_assessments'][sender_role] = content['risk_level']
            
            # Store confidence level
            if confidence != 'N/A':
                aggregated_inputs['confidence_levels'][sender_role] = confidence
        
        print(f"[DEBUG] Portfolio Manager: Aggregated {len(aggregated_inputs['analyst_recommendations'])} analyst inputs")
        return aggregated_inputs
    
    def resolve_conflicts(self, aggregated_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve conflicts between different analyst recommendations.
        
        Args:
            aggregated_inputs: Aggregated analyst inputs
            
        Returns:
            Resolved decision with reasoning
        """
        print(f"[DEBUG] Portfolio Manager: Resolving conflicts for {aggregated_inputs['ticker']}")
        
        recommendations = aggregated_inputs['analyst_recommendations']
        risk_assessments = aggregated_inputs['risk_assessments']
        
        # Rule 1: Check for high risk signals
        if self.has_high_risk_signal(risk_assessments):
            return self.handle_high_risk_scenario(aggregated_inputs)
        
        # Rule 2: Check for strong sell signals
        if self.has_strong_sell_signal(recommendations):
            return self.validate_sell_recommendation(aggregated_inputs)
        
        # Rule 3: Weight by confidence and priority
        return self.weight_by_confidence_and_priority(aggregated_inputs)
    
    def has_high_risk_signal(self, risk_assessments: Dict[str, str]) -> bool:
        """Check if any agent has identified high risk."""
        for agent, risk_level in risk_assessments.items():
            if risk_level in ['High', 'Critical', 'Extreme']:
                print(f"[DEBUG] High risk signal detected from {agent}: {risk_level}")
                return True
        return False
    
    def has_strong_sell_signal(self, recommendations: Dict[str, Any]) -> bool:
        """Check if there's a strong sell recommendation from high-priority agents."""
        for agent, data in recommendations.items():
            if (data['recommendation'] == 'Sell' and 
                self.agent_priority.get(agent, 999) <= 2):  # High priority agents
                print(f"[DEBUG] Strong sell signal detected from {agent}")
                return True
        return False
    
    def handle_high_risk_scenario(self, aggregated_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Handle scenarios where high risk is detected."""
        return {
            'decision': TRADE_ACTION_SELL,
            'confidence': 'High',
            'reasoning': 'High risk signal detected - prioritizing capital preservation',
            'risk_level': 'High',
            'portfolio_action': 'Reduce exposure immediately',
            'timestamp': datetime.now().isoformat()
        }
    
    def validate_sell_recommendation(self, aggregated_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and potentially override sell recommendations."""
        recommendations = aggregated_inputs['analyst_recommendations']
        
        # Count buy vs sell recommendations
        buy_count = sum(1 for data in recommendations.values() 
                       if data['recommendation'] == 'Buy')
        sell_count = sum(1 for data in recommendations.values() 
                        if data['recommendation'] == 'Sell')
        
        if sell_count > buy_count:
            return {
                'decision': TRADE_ACTION_SELL,
                'confidence': 'Medium',
                'reasoning': 'Sell recommendation supported by multiple analysts',
                'portfolio_action': 'Reduce position size',
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'decision': TRADE_ACTION_HOLD,
                'confidence': 'Medium',
                'reasoning': 'Conflicting signals - maintaining current position',
                'portfolio_action': 'Monitor closely',
                'timestamp': datetime.now().isoformat()
            }
    
    def weight_by_confidence_and_priority(self, aggregated_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Weight recommendations by confidence and agent priority."""
        recommendations = aggregated_inputs['analyst_recommendations']
        
        # Calculate weighted scores
        buy_score = 0
        sell_score = 0
        hold_score = 0
        
        for agent, data in recommendations.items():
            priority = self.agent_priority.get(agent, 999)
            confidence_multiplier = self.get_confidence_multiplier(data['confidence'])
            
            # Higher priority agents get more weight
            weight = (10 - priority) * confidence_multiplier
            
            if data['recommendation'] == 'Buy':
                buy_score += weight
            elif data['recommendation'] == 'Sell':
                sell_score += weight
            elif data['recommendation'] == 'Hold':
                hold_score += weight
        
        # Determine decision based on highest score
        if buy_score > sell_score and buy_score > hold_score:
            decision = TRADE_ACTION_BUY
            reasoning = f"Buy recommendation supported by weighted score: {buy_score:.2f}"
        elif sell_score > buy_score and sell_score > hold_score:
            decision = TRADE_ACTION_SELL
            reasoning = f"Sell recommendation supported by weighted score: {sell_score:.2f}"
        else:
            decision = TRADE_ACTION_HOLD
            reasoning = f"Hold recommendation supported by weighted score: {hold_score:.2f}"
        
        return {
            'decision': decision,
            'confidence': 'Medium',
            'reasoning': reasoning,
            'portfolio_action': 'Execute based on decision',
            'timestamp': datetime.now().isoformat()
        }
    
    def get_confidence_multiplier(self, confidence: str) -> float:
        """Convert confidence levels to numerical multipliers."""
        confidence_map = {
            'High': 1.0,
            'Medium': 0.7,
            'Low': 0.4,
            'Very High': 1.2,
            'Very Low': 0.2
        }
        return confidence_map.get(confidence, 0.5)
    
    def make_final_decision(self, ticker: str) -> Dict[str, Any]:
        """
        Make final investment decision for a ticker.
        
        Args:
            ticker: The ticker symbol to analyze
            
        Returns:
            Final investment decision with portfolio actions
        """
        print(f"[DEBUG] Portfolio Manager: Making final decision for {ticker}")
        
        # Step 1: Aggregate all analyst inputs
        aggregated_inputs = self.aggregate_analyst_inputs(ticker)
        
        # Step 2: Resolve conflicts
        resolved_decision = self.resolve_conflicts(aggregated_inputs)
        
        # Step 3: Apply portfolio constraints
        final_decision = self.apply_portfolio_constraints(resolved_decision, ticker)
        
        # Step 4: Post decision to blackboard
        self.post_decision_to_blackboard(ticker, final_decision)
        
        return final_decision
    
    def apply_portfolio_constraints(self, decision: Dict[str, Any], ticker: str) -> Dict[str, Any]:
        """Apply portfolio-level constraints to the decision."""
        # For now, apply basic constraints
        # TODO: Implement full portfolio optimization
        
        decision['portfolio_constraints'] = {
            'max_allocation': self.portfolio_constraints['max_allocation_per_asset'],
            'position_sizing': 'Dynamic based on risk',
            'stop_loss': '5% below entry',
            'take_profit': '15% above entry'
        }
        
        return decision
    
    def post_decision_to_blackboard(self, ticker: str, decision: Dict[str, Any]):
        """Post the final decision to the blackboard."""
        # Use the new portfolio decision method
        self.blackboard.post_portfolio_decision(
            ticker=ticker,
            decision=decision['decision'],
            confidence=decision['confidence'],
            reasoning=decision['reasoning'],
            portfolio_action=decision['portfolio_action']
        )
        
        print(f"[DEBUG] Portfolio Manager: Posted portfolio decision to blackboard: {decision['decision']}")


def create_portfolio_manager():
    """Factory function to create a Portfolio Manager instance."""
    return PortfolioManager() 