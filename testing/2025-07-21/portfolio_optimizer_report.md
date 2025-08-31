# Multithreaded Batch Portfolio Report (2025-07-21)

- Runtime: 00:03:28 (208.99s)

## Decisions

- AAPL: SELL
- AMZN: SELL
- GOOG: SELL
- META: HOLD
- NVDA: SELL

## LLM Views (bounded)

- AAPL: -0.02
- AMZN: -0.02
- GOOG: -0.02
- META: 0.0
- NVDA: -0.02

## Resizing Summary

## Trades

- AAPL: delta=-61, target_qty=61, current_qty=0, price=232.13999938964844
- AMZN: delta=-65, target_qty=65, current_qty=0, price=229.0
- GOOG: delta=-60, target_qty=60, current_qty=0, price=213.52999877929688
- META: delta=0, target_qty=44, current_qty=0, price=738.7000122070312
- NVDA: delta=-145, target_qty=145, current_qty=0, price=174.17999267578125

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