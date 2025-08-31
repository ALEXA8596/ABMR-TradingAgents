# Multithreaded Batch Portfolio Report (2025-07-23)

- Runtime: 00:03:41 (221.34s)

## Decisions

- AAPL: SELL
- AMZN: HOLD
- GOOG: SELL
- META: HOLD
- NVDA: HOLD

## LLM Views (bounded)

- AAPL: -0.02
- AMZN: 0.0
- GOOG: -0.02
- META: 0.0
- NVDA: 0.0

## Resizing Summary

## Trades

- AAPL: delta=128, target_qty=51, current_qty=-77, price=213.9072265625
- AMZN: delta=189, target_qty=113, current_qty=-76, price=228.2899932861328
- GOOG: delta=132, target_qty=53, current_qty=-79, price=191.50999450683594
- META: delta=65, target_qty=36, current_qty=-29, price=713.5800170898438
- NVDA: delta=330, target_qty=151, current_qty=-179, price=170.77999877929688

## Risk Parity Reference

```json
{
  "strategy": "Risk Parity",
  "weights": {
    "AAPL": 0.2161,
    "AMZN": 0.2164,
    "GOOG": 0.2348,
    "META": 0.1903,
    "NVDA": 0.1424
  },
  "individual_volatilities": {
    "AAPL": 0.3511,
    "AMZN": 0.3506,
    "GOOG": 0.3231,
    "META": 0.3988,
    "NVDA": 0.5327
  },
  "portfolio_volatility": 0.3107,
  "diversification_ratio": 1.22,
  "methodology": "Inverse volatility weighting to equalize risk contribution"
}
```