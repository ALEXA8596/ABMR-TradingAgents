"""
Enterprise-grade Alpaca API integration for live trading and portfolio management.

This module provides comprehensive Alpaca integration including:
- Live portfolio data retrieval
- Real-time trade execution
- Position management
- Risk controls and safety checks
"""

import os
import json
import time
from decimal import Decimal, ROUND_DOWN
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import APIError, REST
import pandas as pd


class AlpacaPortfolioProvider:
    """Enterprise-grade Alpaca portfolio data provider with comprehensive position management"""
    
    def __init__(self):
        """Initialize Alpaca API connection with proper error handling"""
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.secret_key = os.getenv('ALPACA_SECRET_KEY')
        self.base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
        
        if not all([self.api_key, self.secret_key]):
            raise ValueError("Alpaca API credentials not found in environment variables")
        
        try:
            self.api = tradeapi.REST(
                key_id=self.api_key,
                secret_key=self.secret_key,
                base_url=self.base_url,
                api_version='v2'
            )
            
            # Verify connection
            account = self.api.get_account()
            print(f"✅ Connected to Alpaca - Account Status: {account.status}")
            print(f"📊 Portfolio Value: ${float(account.portfolio_value):,.2f}")
            print(f"💰 Buying Power: ${float(account.buying_power):,.2f}")
            
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Alpaca API: {e}")
    
    def get_live_portfolio(self) -> Dict:
        """
        Fetch live portfolio data from Alpaca in the format expected by portfolio optimizer.
        
        Returns portfolio in the same format as portfolio.json:
        {
            "cash": float,
            "equity_positions": {"SYMBOL": quantity, ...},
            "crypto_positions": {"SYMBOL": quantity, ...},  # If supported
            ...
        }
        """
        try:
            account = self.api.get_account()
            positions = self.api.list_positions()
            
            portfolio = {
                "cash": float(account.cash),
                "equity_positions": {},
                "crypto_positions": {},
                "bond_positions": {},
                "commodity_positions": {}
            }
            
            print(f"\n🔍 Fetching live portfolio from Alpaca...")
            print(f"💵 Cash Available: ${float(account.cash):,.2f}")
            
            for position in positions:
                symbol = position.symbol
                qty = float(position.qty)
                market_value = float(position.market_value)
                
                # Categorize positions (basic categorization, can be enhanced)
                if self._is_crypto_symbol(symbol):
                    portfolio["crypto_positions"][symbol] = qty
                elif self._is_bond_symbol(symbol):
                    portfolio["bond_positions"][symbol] = qty
                elif self._is_commodity_symbol(symbol):
                    portfolio["commodity_positions"][symbol] = qty
                else:
                    portfolio["equity_positions"][symbol] = qty
                
                print(f"📈 {symbol}: {qty} shares (${market_value:,.2f})")
            
            # Calculate total portfolio value
            total_positions_value = sum(float(pos.market_value) for pos in positions)
            total_portfolio_value = float(account.portfolio_value)
            
            print(f"\n💼 Portfolio Summary:")
            print(f"   Cash: ${float(account.cash):,.2f}")
            print(f"   Positions: ${total_positions_value:,.2f}")
            print(f"   Total Value: ${total_portfolio_value:,.2f}")
            
            # Save a backup of live portfolio for reference
            self._save_portfolio_snapshot(portfolio)
            
            return portfolio
            
        except Exception as e:
            print(f"❌ Error fetching live portfolio: {e}")
            # Fallback to static portfolio if live fetch fails
            return self._load_fallback_portfolio()
    
    def get_portfolio_metrics(self) -> Dict:
        """Get comprehensive portfolio performance metrics"""
        try:
            account = self.api.get_account()
            portfolio_history = self.api.get_portfolio_history(period='1M', timeframe='1Day')
            
            metrics = {
                "total_value": float(account.portfolio_value),
                "cash": float(account.cash),
                "buying_power": float(account.buying_power),
                "day_pl": float(account.day_trade_count),
                "total_pl": float(account.portfolio_value) - float(account.last_day_portfolio_value) if account.last_day_portfolio_value else 0,
                "equity": float(account.equity),
                "last_equity": float(account.last_equity),
                "day_trade_count": int(account.day_trade_count),
                "pattern_day_trader": account.pattern_day_trader,
                "trading_blocked": account.trading_blocked,
                "transfers_blocked": account.transfers_blocked,
                "account_blocked": account.account_blocked,
                "created_at": str(account.created_at),
                "trade_suspended_by_user": account.trade_suspended_by_user,
                "multiplier": float(account.multiplier),
                "shorting_enabled": account.shorting_enabled,
                "long_market_value": float(account.long_market_value),
                "short_market_value": float(account.short_market_value),
                "position_count": len(self.api.list_positions())
            }
            
            return metrics
            
        except Exception as e:
            print(f"❌ Error fetching portfolio metrics: {e}")
            return {}
    
    def _is_crypto_symbol(self, symbol: str) -> bool:
        """Identify if symbol is cryptocurrency"""
        crypto_symbols = ['BTC', 'ETH', 'LTC', 'BCH', 'BTCUSD', 'ETHUSD']
        return any(crypto in symbol.upper() for crypto in crypto_symbols)
    
    def _is_bond_symbol(self, symbol: str) -> bool:
        """Identify if symbol is a bond/fixed income"""
        bond_symbols = ['TLT', 'AGG', 'BND', 'TIP', 'HYG', 'LQD', 'IEF', 'SHY']
        return symbol.upper() in bond_symbols
    
    def _is_commodity_symbol(self, symbol: str) -> bool:
        """Identify if symbol is a commodity"""
        commodity_symbols = ['GLD', 'SLV', 'USO', 'UNG', 'DBA', 'DBC', 'PDBC']
        return symbol.upper() in commodity_symbols
    
    def _save_portfolio_snapshot(self, portfolio: Dict) -> None:
        """Save portfolio snapshot for backup/analysis"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            snapshot_path = f"results/portfolio_snapshots/portfolio_{timestamp}.json"
            
            os.makedirs(os.path.dirname(snapshot_path), exist_ok=True)
            
            with open(snapshot_path, 'w') as f:
                json.dump(portfolio, f, indent=2)
                
            print(f"💾 Portfolio snapshot saved: {snapshot_path}")
            
        except Exception as e:
            print(f"⚠️ Could not save portfolio snapshot: {e}")
    
    def _load_fallback_portfolio(self) -> Dict:
        """Load fallback portfolio if live fetch fails"""
        try:
            with open('portfolio.json', 'r') as f:
                portfolio = json.load(f)
            print("⚠️ Using fallback portfolio.json due to API error")
            return portfolio
        except Exception as e:
            print(f"❌ Could not load fallback portfolio: {e}")
            # Return empty portfolio as last resort
            return {
                "cash": 0,
                "equity_positions": {},
                "crypto_positions": {},
                "bond_positions": {},
                "commodity_positions": {}
            }


class AlpacaTradeExecutor:
    """Enterprise-grade trade execution engine with comprehensive safety checks"""
    
    def __init__(self):
        """Initialize trade executor with risk controls"""
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.secret_key = os.getenv('ALPACA_SECRET_KEY')
        self.base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
        
        if not all([self.api_key, self.secret_key]):
            raise ValueError("Alpaca API credentials not found in environment variables")
        
        try:
            self.api = tradeapi.REST(
                key_id=self.api_key,
                secret_key=self.secret_key,
                base_url=self.base_url,
                api_version='v2'
            )
            
            # Risk management settings
            self.max_position_size = 0.15  # Max 15% of portfolio in single position
            self.max_daily_trades = 50     # Max trades per day
            self.min_trade_value = 100     # Minimum trade value
            self.dry_run = True           # Set to False for live trading
            
            print("🤖 Alpaca Trade Executor initialized with safety controls")
            
        except Exception as e:
            raise ConnectionError(f"Failed to initialize trade executor: {e}")
    
    def execute_portfolio_recommendations(self, recommendations: Dict, current_portfolio: Dict) -> Dict:
        """
        Execute portfolio optimization recommendations with comprehensive safety checks.
        
        Args:
            recommendations: Output from portfolio optimizer
            current_portfolio: Current live portfolio state
            
        Returns:
            Dictionary with execution results and status
        """
        
        print(f"\n🎯 EXECUTING PORTFOLIO OPTIMIZATION RECOMMENDATIONS")
        print(f"{'='*60}")
        
        execution_results = {
            "executed_trades": [],
            "failed_trades": [],
            "skipped_trades": [],
            "total_value_traded": 0,
            "execution_summary": "",
            "safety_checks": [],
            "dry_run": self.dry_run
        }
        
        try:
            # Extract recommendations
            symbol = recommendations.get('symbol', '')
            trade_direction = recommendations.get('trade_direction', 'HOLD')
            recommended_position = recommendations.get('recommended_position', 0)
            recommended_value = recommendations.get('recommended_value', 0)
            
            print(f"📊 Symbol: {symbol}")
            print(f"📈 Direction: {trade_direction}")
            print(f"💰 Recommended Value: ${recommended_value:,.2f}")
            print(f"📦 Recommended Position: {recommended_position}")
            
            # Safety checks
            safety_passed = self._perform_safety_checks(
                symbol, trade_direction, recommended_value, current_portfolio, execution_results
            )
            
            if not safety_passed:
                execution_results["execution_summary"] = "❌ Safety checks failed - No trades executed"
                return execution_results
            
            # Execute based on trade direction
            if trade_direction == "BUY":
                result = self._execute_buy_order(symbol, recommended_value, execution_results)
            elif trade_direction == "SELL":
                result = self._execute_sell_order(symbol, recommended_position, execution_results)
            else:  # HOLD
                execution_results["skipped_trades"].append({
                    "symbol": symbol,
                    "reason": "HOLD recommendation - no action needed"
                })
                result = True
            
            # Generate execution summary
            execution_results["execution_summary"] = self._generate_execution_summary(execution_results)
            
            return execution_results
            
        except Exception as e:
            print(f"❌ Error in trade execution: {e}")
            execution_results["execution_summary"] = f"❌ Execution failed: {e}"
            return execution_results
    
    def _perform_safety_checks(self, symbol: str, direction: str, value: float, portfolio: Dict, results: Dict) -> bool:
        """Comprehensive safety checks before trade execution"""
        
        print(f"\n🛡️ PERFORMING SAFETY CHECKS")
        print(f"{'='*40}")
        
        safety_checks = []
        
        # Check 1: Account status
        try:
            account = self.api.get_account()
            if account.trading_blocked:
                safety_checks.append("❌ FAIL: Trading is blocked on account")
                return False
            else:
                safety_checks.append("✅ PASS: Account trading enabled")
        except Exception as e:
            safety_checks.append(f"❌ FAIL: Could not verify account status: {e}")
            return False
        
        # Check 2: Market hours (basic check)
        current_time = datetime.now()
        if not self._is_market_open(current_time):
            safety_checks.append("⚠️ WARNING: Market may be closed")
        else:
            safety_checks.append("✅ PASS: Market appears to be open")
        
        # Check 3: Position size limits
        portfolio_value = float(account.portfolio_value)
        position_percentage = (value / portfolio_value) if portfolio_value > 0 else 0
        
        if position_percentage > self.max_position_size:
            safety_checks.append(f"❌ FAIL: Position size {position_percentage:.1%} exceeds limit {self.max_position_size:.1%}")
            return False
        else:
            safety_checks.append(f"✅ PASS: Position size {position_percentage:.1%} within limits")
        
        # Check 4: Minimum trade value
        if abs(value) < self.min_trade_value and direction != "HOLD":
            safety_checks.append(f"❌ FAIL: Trade value ${abs(value):,.2f} below minimum ${self.min_trade_value}")
            return False
        else:
            safety_checks.append(f"✅ PASS: Trade value ${abs(value):,.2f} meets minimum requirements")
        
        # Check 5: Symbol validity
        try:
            asset = self.api.get_asset(symbol)
            if not asset.tradable:
                safety_checks.append(f"❌ FAIL: {symbol} is not tradable")
                return False
            else:
                safety_checks.append(f"✅ PASS: {symbol} is tradable")
        except Exception as e:
            safety_checks.append(f"❌ FAIL: Could not verify {symbol} tradability: {e}")
            return False
        
        # Store safety check results
        results["safety_checks"] = safety_checks
        
        # Print safety check results
        for check in safety_checks:
            print(f"   {check}")
        
        print(f"\n✅ All safety checks passed - Ready to execute trades")
        return True
    
    def _execute_buy_order(self, symbol: str, target_value: float, results: Dict) -> bool:
        """Execute buy order with proper error handling"""
        
        try:
            # Get current price
            quote = self.api.get_latest_quote(symbol)
            current_price = float(quote.ask_price) if quote.ask_price else float(quote.bid_price)
            
            # Calculate shares to buy
            shares_to_buy = int(target_value / current_price)
            actual_value = shares_to_buy * current_price
            
            print(f"\n📈 EXECUTING BUY ORDER")
            print(f"   Symbol: {symbol}")
            print(f"   Current Price: ${current_price:.2f}")
            print(f"   Shares to Buy: {shares_to_buy}")
            print(f"   Total Value: ${actual_value:,.2f}")
            
            if self.dry_run:
                print(f"🧪 DRY RUN: Would submit buy order for {shares_to_buy} shares of {symbol}")
                results["executed_trades"].append({
                    "symbol": symbol,
                    "side": "buy",
                    "qty": shares_to_buy,
                    "price": current_price,
                    "value": actual_value,
                    "status": "DRY_RUN",
                    "timestamp": datetime.now().isoformat()
                })
            else:
                # Submit actual order
                order = self.api.submit_order(
                    symbol=symbol,
                    qty=shares_to_buy,
                    side='buy',
                    type='market',
                    time_in_force='day'
                )
                
                print(f"✅ Buy order submitted: {order.id}")
                results["executed_trades"].append({
                    "symbol": symbol,
                    "side": "buy",
                    "qty": shares_to_buy,
                    "price": current_price,
                    "value": actual_value,
                    "order_id": order.id,
                    "status": order.status,
                    "timestamp": datetime.now().isoformat()
                })
            
            results["total_value_traded"] += actual_value
            return True
            
        except Exception as e:
            print(f"❌ Failed to execute buy order for {symbol}: {e}")
            results["failed_trades"].append({
                "symbol": symbol,
                "side": "buy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    def _execute_sell_order(self, symbol: str, shares_to_sell: float, results: Dict) -> bool:
        """Execute sell order with proper error handling"""
        
        try:
            # Check current position
            try:
                position = self.api.get_position(symbol)
                current_shares = float(position.qty)
            except APIError:
                print(f"⚠️ No position found for {symbol} - cannot sell")
                results["skipped_trades"].append({
                    "symbol": symbol,
                    "reason": "No position to sell"
                })
                return True
            
            # Determine actual shares to sell
            actual_shares_to_sell = min(abs(shares_to_sell), current_shares)
            
            if actual_shares_to_sell == 0:
                print(f"⚠️ No shares to sell for {symbol}")
                results["skipped_trades"].append({
                    "symbol": symbol,
                    "reason": "Zero shares to sell"
                })
                return True
            
            # Get current price
            quote = self.api.get_latest_quote(symbol)
            current_price = float(quote.bid_price) if quote.bid_price else float(quote.ask_price)
            actual_value = actual_shares_to_sell * current_price
            
            print(f"\n📉 EXECUTING SELL ORDER")
            print(f"   Symbol: {symbol}")
            print(f"   Current Price: ${current_price:.2f}")
            print(f"   Current Position: {current_shares} shares")
            print(f"   Shares to Sell: {actual_shares_to_sell}")
            print(f"   Total Value: ${actual_value:,.2f}")
            
            if self.dry_run:
                print(f"🧪 DRY RUN: Would submit sell order for {actual_shares_to_sell} shares of {symbol}")
                results["executed_trades"].append({
                    "symbol": symbol,
                    "side": "sell",
                    "qty": actual_shares_to_sell,
                    "price": current_price,
                    "value": actual_value,
                    "status": "DRY_RUN",
                    "timestamp": datetime.now().isoformat()
                })
            else:
                # Submit actual order
                order = self.api.submit_order(
                    symbol=symbol,
                    qty=int(actual_shares_to_sell),
                    side='sell',
                    type='market',
                    time_in_force='day'
                )
                
                print(f"✅ Sell order submitted: {order.id}")
                results["executed_trades"].append({
                    "symbol": symbol,
                    "side": "sell",
                    "qty": actual_shares_to_sell,
                    "price": current_price,
                    "value": actual_value,
                    "order_id": order.id,
                    "status": order.status,
                    "timestamp": datetime.now().isoformat()
                })
            
            results["total_value_traded"] += actual_value
            return True
            
        except Exception as e:
            print(f"❌ Failed to execute sell order for {symbol}: {e}")
            results["failed_trades"].append({
                "symbol": symbol,
                "side": "sell",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    def _is_market_open(self, current_time: datetime) -> bool:
        """Basic market hours check (can be enhanced with Alpaca's market calendar)"""
        # Basic check for weekdays during typical market hours (ET)
        if current_time.weekday() >= 5:  # Weekend
            return False
        
        # This is a simplified check - in production, use Alpaca's calendar API
        market_open = current_time.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = current_time.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return market_open <= current_time <= market_close
    
    def _generate_execution_summary(self, results: Dict) -> str:
        """Generate comprehensive execution summary"""
        
        executed_count = len(results["executed_trades"])
        failed_count = len(results["failed_trades"])
        skipped_count = len(results["skipped_trades"])
        total_value = results["total_value_traded"]
        
        summary = f"""
🎯 TRADE EXECUTION SUMMARY
{'='*50}
✅ Executed: {executed_count} trades
❌ Failed: {failed_count} trades  
⏭️ Skipped: {skipped_count} trades
💰 Total Value Traded: ${total_value:,.2f}
🧪 Mode: {'DRY RUN' if results['dry_run'] else 'LIVE TRADING'}

📋 EXECUTED TRADES:
"""
        
        for trade in results["executed_trades"]:
            summary += f"   {trade['side'].upper()} {trade['qty']} {trade['symbol']} @ ${trade['price']:.2f} = ${trade['value']:,.2f}\n"
        
        if results["failed_trades"]:
            summary += f"\n❌ FAILED TRADES:\n"
            for trade in results["failed_trades"]:
                summary += f"   {trade['symbol']}: {trade['error']}\n"
        
        if results["skipped_trades"]:
            summary += f"\n⏭️ SKIPPED TRADES:\n"
            for trade in results["skipped_trades"]:
                summary += f"   {trade['symbol']}: {trade['reason']}\n"
        
        return summary
    
    def set_live_trading(self, enable: bool = False) -> None:
        """Enable or disable live trading (safety feature)"""
        self.dry_run = not enable
        mode = "LIVE TRADING" if enable else "DRY RUN"
        print(f"🔄 Trade execution mode set to: {mode}")
        
        if enable:
            print("⚠️ WARNING: Live trading enabled - real money will be used!")


def test_alpaca_connection():
    """Test Alpaca API connection and basic functionality"""
    try:
        print("🧪 Testing Alpaca API Connection...")
        
        # Test portfolio provider
        portfolio_provider = AlpacaPortfolioProvider()
        live_portfolio = portfolio_provider.get_live_portfolio()
        metrics = portfolio_provider.get_portfolio_metrics()
        
        print(f"\n✅ Portfolio Provider Test Passed")
        print(f"   Cash: ${live_portfolio.get('cash', 0):,.2f}")
        print(f"   Positions: {len(live_portfolio.get('equity_positions', {}))}")
        
        # Test trade executor
        trade_executor = AlpacaTradeExecutor()
        print(f"\n✅ Trade Executor Test Passed")
        print(f"   Dry Run Mode: {trade_executor.dry_run}")
        
        return True
        
    except Exception as e:
        print(f"❌ Alpaca connection test failed: {e}")
        return False


if __name__ == "__main__":
    # Run connection test
    test_alpaca_connection()