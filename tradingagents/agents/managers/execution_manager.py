import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from tradingagents.blackboard.utils import create_agent_blackboard
from tradingagents.blackboard.schema import (
    TRADE_EXECUTION, PORTFOLIO_UPDATE, TRADE_DECISION,
    TRADE_ACTION_BUY, TRADE_ACTION_SELL, TRADE_ACTION_HOLD
)


class ExecutionManager:
    """
    Agent responsible for trade execution and position management.
    Receives decisions from Portfolio Manager and executes trades accordingly.
    """
    
    def __init__(self):
        self.agent_id = "EM_001"
        self.role = "ExecutionManager"
        self.execution_authority = "EXECUTION_ONLY"
        self.blackboard = create_agent_blackboard(self.agent_id, self.role)
        
        # Position tracking
        self.current_positions = {}
        self.position_history = []
        
        # Execution parameters
        self.execution_params = {
            'max_slippage': 0.02,        # 2% max slippage
            'execution_timeout': 300,     # 5 minutes timeout
            'retry_attempts': 3,         # Max retry attempts
            'batch_size_limit': 1000     # Max shares per trade
        }
        
        # Risk controls
        self.risk_controls = {
            'max_position_size': 0.20,   # 20% max per position
            'stop_loss_pct': 0.10,       # 10% stop loss
            'take_profit_pct': 0.15,     # 15% take profit
            'max_daily_trades': 50       # Max trades per day
        }
    
    def execute_trades(self, portfolio_decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute trades based on portfolio decisions.
        
        Args:
            portfolio_decisions: List of portfolio decisions to execute
            
        Returns:
            Execution results summary
        """
        print(f"[DEBUG] Execution Manager: Executing {len(portfolio_decisions)} portfolio decisions")
        
        execution_results = {
            'execution_id': f"EXEC_{int(time.time())}",
            'timestamp': datetime.now().isoformat(),
            'decisions_processed': len(portfolio_decisions),
            'trades_executed': [],
            'errors': [],
            'summary': {}
        }
        
        for decision in portfolio_decisions:
            try:
                trade_result = self.execute_single_decision(decision)
                execution_results['trades_executed'].append(trade_result)
            except Exception as e:
                error_msg = f"Error executing decision for {decision.get('ticker', 'Unknown')}: {str(e)}"
                execution_results['errors'].append(error_msg)
                print(f"[ERROR] Execution Manager: {error_msg}")
        
        # Generate execution summary
        execution_results['summary'] = self.generate_execution_summary(execution_results['trades_executed'])
        
        # Post execution results to blackboard
        self.post_execution_results(execution_results)
        
        return execution_results
    
    def execute_single_decision(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single portfolio decision.
        
        Args:
            decision: Single portfolio decision
            
        Returns:
            Trade execution result
        """
        ticker = decision.get('ticker', 'Unknown')
        action = decision.get('decision', 'Hold')
        confidence = decision.get('confidence', 'Medium')
        
        print(f"[DEBUG] Execution Manager: Executing {action} for {ticker}")
        
        # Validate decision
        if not self.validate_decision(decision):
            raise ValueError(f"Invalid decision format for {ticker}")
        
        # Check risk limits
        if not self.check_risk_limits(decision):
            raise ValueError(f"Risk limits exceeded for {ticker}")
        
        # Execute based on action
        if action == TRADE_ACTION_BUY:
            trade_result = self.execute_buy_order(decision)
        elif action == TRADE_ACTION_SELL:
            trade_result = self.execute_sell_order(decision)
        elif action == TRADE_ACTION_HOLD:
            trade_result = self.execute_hold_action(decision)
        else:
            raise ValueError(f"Unknown action: {action}")
        
        # Update position tracking
        self.update_position_tracking(trade_result)
        
        return trade_result
    
    def validate_decision(self, decision: Dict[str, Any]) -> bool:
        """Validate that a decision has all required fields."""
        required_fields = ['ticker', 'decision', 'confidence', 'reasoning']
        return all(field in decision for field in required_fields)
    
    def check_risk_limits(self, decision: Dict[str, Any]) -> bool:
        """Check if the decision violates any risk limits."""
        ticker = decision.get('ticker')
        current_position = self.current_positions.get(ticker, 0)
        
        # Check position size limits
        if decision.get('decision') == TRADE_ACTION_BUY:
            # Would this exceed max position size?
            # For now, assume we're within limits
            pass
        
        # Check daily trade limits
        today_trades = len([t for t in self.position_history 
                           if t.get('date') == datetime.now().date().isoformat()])
        if today_trades >= self.risk_controls['max_daily_trades']:
            print(f"[WARNING] Daily trade limit reached: {today_trades}")
            return False
        
        return True
    
    def execute_buy_order(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a buy order."""
        ticker = decision.get('ticker')
        confidence = decision.get('confidence')
        
        # Calculate position size based on confidence and risk
        position_size = self.calculate_position_size(decision)
        
        # Simulate trade execution
        execution_price = self.simulate_market_price(ticker, 'buy')
        execution_time = datetime.now()
        
        trade_result = {
            'ticker': ticker,
            'action': 'BUY',
            'quantity': position_size,
            'execution_price': execution_price,
            'execution_time': execution_time.isoformat(),
            'confidence': confidence,
            'status': 'EXECUTED',
            'trade_id': f"BUY_{ticker}_{int(execution_time.timestamp())}"
        }
        
        print(f"[DEBUG] Execution Manager: Executed BUY {position_size} shares of {ticker} at ${execution_price}")
        return trade_result
    
    def execute_sell_order(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a sell order."""
        ticker = decision.get('ticker')
        confidence = decision.get('confidence')
        
        # Get current position
        current_position = self.current_positions.get(ticker, 0)
        
        if current_position <= 0:
            print(f"[WARNING] No position to sell for {ticker}")
            return {
                'ticker': ticker,
                'action': 'SELL',
                'quantity': 0,
                'execution_price': 0,
                'execution_time': datetime.now().isoformat(),
                'confidence': confidence,
                'status': 'NO_POSITION',
                'trade_id': f"SELL_{ticker}_{int(time.time())}"
            }
        
        # Simulate trade execution
        execution_price = self.simulate_market_price(ticker, 'sell')
        execution_time = datetime.now()
        
        trade_result = {
            'ticker': ticker,
            'action': 'SELL',
            'quantity': current_position,
            'execution_price': execution_price,
            'execution_time': execution_time.isoformat(),
            'confidence': confidence,
            'status': 'EXECUTED',
            'trade_id': f"SELL_{ticker}_{int(execution_time.timestamp())}"
        }
        
        print(f"[DEBUG] Execution Manager: Executed SELL {current_position} shares of {ticker} at ${execution_price}")
        return trade_result
    
    def execute_hold_action(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a hold action (no trade, just monitoring)."""
        ticker = decision.get('ticker')
        confidence = decision.get('confidence')
        
        trade_result = {
            'ticker': ticker,
            'action': 'HOLD',
            'quantity': 0,
            'execution_price': 0,
            'execution_time': datetime.now().isoformat(),
            'confidence': confidence,
            'status': 'NO_ACTION',
            'trade_id': f"HOLD_{ticker}_{int(time.time())}"
        }
        
        print(f"[DEBUG] Execution Manager: HOLD action for {ticker}")
        return trade_result
    
    def calculate_position_size(self, decision: Dict[str, Any]) -> int:
        """Calculate position size based on decision confidence and risk parameters."""
        confidence = decision.get('confidence', 'Medium')
        base_position = 100  # Base position size
        
        # Adjust based on confidence
        confidence_multiplier = {
            'Very High': 1.5,
            'High': 1.2,
            'Medium': 1.0,
            'Low': 0.7,
            'Very Low': 0.5
        }.get(confidence, 1.0)
        
        position_size = int(base_position * confidence_multiplier)
        
        # Apply risk limits
        max_position = int(base_position * self.risk_controls['max_position_size'] * 10)
        position_size = min(position_size, max_position)
        
        return max(1, position_size)  # Minimum 1 share
    
    def simulate_market_price(self, ticker: str, action: str) -> float:
        """Simulate market price for testing purposes."""
        # In a real system, this would get actual market data
        import random
        
        # Base prices for common tickers
        base_prices = {
            'SPY': 450.0,
            'AAPL': 175.0,
            'TSLA': 250.0,
            'QQQ': 380.0
        }
        
        base_price = base_prices.get(ticker, 100.0)
        
        # Add some realistic price movement
        price_change = random.uniform(-0.02, 0.02)  # ±2%
        execution_price = base_price * (1 + price_change)
        
        # Round to 2 decimal places
        return round(execution_price, 2)
    
    def update_position_tracking(self, trade_result: Dict[str, Any]):
        """Update position tracking after trade execution."""
        ticker = trade_result.get('ticker')
        action = trade_result.get('action')
        quantity = trade_result.get('quantity', 0)
        price = trade_result.get('execution_price', 0)
        
        # Update current positions
        if ticker not in self.current_positions:
            self.current_positions[ticker] = 0
        
        if action == 'BUY':
            self.current_positions[ticker] += quantity
        elif action == 'SELL':
            self.current_positions[ticker] -= quantity
        
        # Ensure position doesn't go negative
        self.current_positions[ticker] = max(0, self.current_positions[ticker])
        
        # Add to position history
        self.position_history.append({
            'ticker': ticker,
            'action': action,
            'quantity': quantity,
            'price': price,
            'date': datetime.now().date().isoformat(),
            'timestamp': datetime.now().isoformat()
        })
    
    def generate_execution_summary(self, trades_executed: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of execution results."""
        if not trades_executed:
            return {'message': 'No trades executed'}
        
        total_buy_volume = sum(t.get('quantity', 0) for t in trades_executed if t.get('action') == 'BUY')
        total_sell_volume = sum(t.get('quantity', 0) for t in trades_executed if t.get('action') == 'SELL')
        total_hold_count = sum(1 for t in trades_executed if t.get('action') == 'HOLD')
        
        return {
            'total_trades': len(trades_executed),
            'buy_volume': total_buy_volume,
            'sell_volume': total_sell_volume,
            'hold_count': total_hold_count,
            'execution_rate': f"{len([t for t in trades_executed if t.get('status') == 'EXECUTED'])}/{len(trades_executed)}"
        }
    
    def post_execution_results(self, execution_results: Dict[str, Any]):
        """Post execution results to the blackboard."""
        # Post each trade execution individually
        for trade in execution_results['trades_executed']:
            if trade['action'] != 'HOLD':
                self.blackboard.post_trade_execution(
                    ticker=trade['ticker'],
                    action=trade['action'],
                    quantity=trade['quantity'],
                    price=trade['execution_price']
                )
        
        # Post portfolio update for affected tickers
        for trade in execution_results['trades_executed']:
            if trade['action'] != 'HOLD':
                self.blackboard.post_portfolio_update(
                    ticker=trade['ticker'],
                    position_size=self.current_positions.get(trade['ticker'], 0),
                    current_value=self.current_positions.get(trade['ticker'], 0) * trade['execution_price'],
                    unrealized_pnl=0.0
                )
        
        print(f"[DEBUG] Execution Manager: Posted execution results to blackboard")
    
    def get_current_positions(self) -> Dict[str, int]:
        """Get current positions for all tickers."""
        return self.current_positions.copy()
    
    def get_position_history(self) -> List[Dict[str, Any]]:
        """Get position history."""
        return self.position_history.copy()


def create_execution_manager():
    """Factory function to create an Execution Manager instance."""
    return ExecutionManager() 