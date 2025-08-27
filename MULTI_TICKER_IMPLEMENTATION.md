# Multi-Ticker Portfolio System Implementation

## Overview

This document describes the implementation of a multi-ticker portfolio analysis system for the TradingAgents framework. The system extends the existing single-ticker analysis to support portfolio-level analysis with multiple tickers simultaneously.

## Key Features

### 1. **Portfolio-Level Analysis**
- Analyze multiple tickers simultaneously
- Cross-ticker correlation analysis
- Sector diversification analysis
- Portfolio risk aggregation
- Portfolio balance optimization

### 2. **Enhanced Blackboard System**
- New message types for portfolio analysis
- Cross-ticker correlation messages
- Sector analysis messages
- Portfolio risk assessment messages
- Portfolio optimization messages

### 3. **Multi-Ticker Portfolio Optimizer**
- Correlation-based allocation strategies
- Sector-balanced allocations
- Risk-adjusted position sizing
- Portfolio-level risk metrics

## Architecture Changes

### Blackboard Schema Updates

New message types added to `tradingagents/blackboard/schema.py`:

```python
# Multi-ticker portfolio message types
PORTFOLIO_ANALYSIS = "PortfolioAnalysis"
CROSS_TICKER_CORRELATION = "CrossTickerCorrelation"
PORTFOLIO_BALANCE = "PortfolioBalance"
SECTOR_ANALYSIS = "SectorAnalysis"
PORTFOLIO_RISK_ASSESSMENT = "PortfolioRiskAssessment"
PORTFOLIO_OPTIMIZATION = "PortfolioOptimization"
```

### Blackboard Utilities

Enhanced `tradingagents/blackboard/utils.py` with new methods:

- `post_portfolio_analysis()` - Post portfolio-level analysis
- `post_cross_ticker_correlation()` - Post correlation analysis
- `post_portfolio_balance()` - Post portfolio balance recommendations
- `post_sector_analysis()` - Post sector analysis
- `post_portfolio_risk_assessment()` - Post portfolio risk assessment
- `post_portfolio_optimization()` - Post optimization results

### New Portfolio Optimizer

Created `tradingagents/agents/managers/multi_ticker_portfolio_optimizer.py`:

- **Correlation Analysis**: Calculates correlations between tickers
- **Sector Analysis**: Analyzes sector breakdown and concentration
- **Risk Metrics**: Portfolio-level risk calculations
- **Optimization Strategies**: Multiple allocation strategies
  - Equal weight allocation
  - Risk-adjusted allocation
  - Correlation-adjusted allocation
  - Sector-balanced allocation

### Trading Graph Updates

Enhanced `tradingagents/graph/trading_graph.py`:

- `propagate_portfolio()` method for multi-ticker analysis
- Portfolio blackboard context methods
- Multi-ticker state management

### CLI Updates

Enhanced CLI in `cli/main.py`:

- Analysis mode selection (single vs. portfolio)
- Multi-ticker input support
- Portfolio-specific display updates

## Usage Examples

### 1. **Single Ticker Analysis (Existing)**
```python
from tradingagents.graph.trading_graph import TradingAgentsGraph

ta = TradingAgentsGraph(debug=True, config=config)
_, decision = ta.propagate("AAPL", "2024-12-20")
```

### 2. **Multi-Ticker Portfolio Analysis (New)**
```python
from tradingagents.graph.trading_graph import TradingAgentsGraph

ta = TradingAgentsGraph(debug=True, config=config)
tickers = ["AAPL", "MSFT", "GOOGL"]
_, portfolio_decision = ta.propagate_portfolio(tickers, "2024-12-20")
```

### 3. **CLI Usage**
```bash
# Run the CLI
python -m cli.main analyze

# Select "Multi-Ticker Portfolio Analysis" mode
# Enter tickers: AAPL,MSFT,GOOGL
```

## Agent Roles in Multi-Ticker System

### **Analysts** (Market, Social, News, Fundamentals)
- **Current Role**: Analyze single ticker in isolation
- **New Role**: Analyze each ticker individually, consider sector relationships

### **Research Team** (Bull/Bear Researchers + Manager)
- **Current Role**: Debate single ticker investment thesis
- **New Role**: Debate each ticker individually, consider portfolio diversification

### **Trader**
- **Current Role**: Create single ticker investment plan
- **New Role**: Create individual ticker plans, consider portfolio-level position sizing

### **Risk Management**
- **Current Role**: Evaluate single ticker risk
- **New Role**: Evaluate individual ticker risks + portfolio-level risk aggregation

### **Portfolio Optimizer** (Most Critical Change)
- **Current Role**: Optimize single ticker position
- **New Role**: 
  - Portfolio balance across multiple tickers
  - Correlation management
  - Sector allocation
  - Risk parity principles
  - Cross-hedging strategies

## Portfolio Optimization Strategies

### 1. **Equal Weight Allocation**
- Simple equal distribution across all tickers
- Good baseline for comparison

### 2. **Risk-Adjusted Allocation**
- Adjusts weights based on individual ticker risk characteristics
- Considers volatility and market cap

### 3. **Correlation-Adjusted Allocation**
- Reduces allocation for highly correlated tickers
- Improves portfolio diversification

### 4. **Sector-Balanced Allocation**
- Balances sector exposure
- Prevents over-concentration in single sectors

## Risk Metrics

### Portfolio-Level Risk Assessment
- **Correlation Risk**: Measures portfolio diversification
- **Sector Concentration Risk**: Monitors sector exposure
- **Volatility Risk**: Portfolio-level volatility metrics
- **Market Cap Risk**: Balance between large and small caps

### Risk Aggregation
- Portfolio VaR calculation
- Stress testing across scenarios
- Cross-ticker risk dependencies

## Testing

Run the test script to verify the system:

```bash
python test_multi_ticker.py
```

## Future Enhancements

### 1. **Advanced Portfolio Models**
- Black-Litterman model integration
- Risk parity optimization
- Kelly Criterion for position sizing

### 2. **Real-Time Portfolio Monitoring**
- Live correlation updates
- Dynamic rebalancing recommendations
- Real-time risk alerts

### 3. **Multi-Asset Support**
- Options and derivatives integration
- Cryptocurrency support
- International markets

### 4. **Machine Learning Integration**
- Correlation prediction models
- Risk factor analysis
- Automated portfolio optimization

## Benefits

1. **True Portfolio Management**: Not just individual stock analysis
2. **Risk Diversification**: Systematic risk reduction across positions
3. **Correlation Awareness**: Avoid concentration in correlated assets
4. **Sector Balance**: Prevent over-exposure to single sectors
5. **Cross-Hedging**: Use correlations for portfolio protection

## Conclusion

The multi-ticker portfolio system transforms TradingAgents from a single-ticker analysis tool into a comprehensive portfolio management system. It provides portfolio balance and awareness by considering relationships between all positions and optimizing for overall portfolio performance rather than individual stock performance.

The system maintains backward compatibility while adding powerful new portfolio-level capabilities that enable users to make more informed investment decisions across multiple positions simultaneously. 