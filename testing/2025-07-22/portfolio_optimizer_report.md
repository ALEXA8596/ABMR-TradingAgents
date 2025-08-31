# Multithreaded Batch Portfolio Report (2025-07-22)

- Runtime: 00:03:37 (217.84s)

## Decisions

- AAPL: SELL
- AMZN: SELL
- GOOG: SELL
- META: SELL
- NVDA: SELL

## LLM Views (bounded)

- AAPL: -0.02
- AMZN: -0.02
- GOOG: -0.02
- META: -0.02
- NVDA: -0.02

## Resizing Summary

## Trades

- AAPL: delta=-77, target_qty=77, current_qty=0, price=214.15695190429688
- AMZN: delta=-76, target_qty=76, current_qty=0, price=227.47000122070312
- GOOG: delta=-79, target_qty=79, current_qty=0, price=192.11000061035156
- META: delta=-29, target_qty=29, current_qty=0, price=704.8099975585938
- NVDA: delta=-179, target_qty=179, current_qty=0, price=167.02999877929688

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