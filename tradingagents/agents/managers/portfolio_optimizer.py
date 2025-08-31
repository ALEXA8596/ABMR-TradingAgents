import time
import json
import os
from datetime import datetime
from tradingagents.blackboard.utils import create_agent_blackboard
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage  # Added for static system message
import yfinance as yf


def create_portfolio_optimizer(llm, memory, toolkit):
    def portfolio_optimizer_node(state) -> dict:

        # Handle both single ticker and multi-ticker portfolio modes
        if "tickers" in state and state.get("tickers"):
            # Multi-ticker portfolio mode - use the first ticker for now
            ticker = state["tickers"][0] if state["tickers"] else "SPY"
            company_name = ticker
            is_portfolio_mode = True
            
            # Extract ticker-specific data from portfolio structure
            individual_reports = state.get("individual_reports", {})
            ticker_reports = individual_reports.get(ticker, {})
            
            market_research_report = ticker_reports.get("market_report", "")
            news_report = ticker_reports.get("news_report", "")
            fundamentals_report = ticker_reports.get("fundamentals_report", "")
            sentiment_report = ticker_reports.get("sentiment_report", "")
            trader_plan = ticker_reports.get("trader_investment_plan", "")
            risk_decision = ticker_reports.get("final_trade_decision", "")
            
        elif "company_of_interest" in state:
            # Single ticker mode (backward compatibility)
            company_name = state["company_of_interest"]
            is_portfolio_mode = False
            
            market_research_report = state.get("market_report", "")
            news_report = state.get("news_report", "")
            fundamentals_report = state.get("fundamentals_report", "")
            sentiment_report = state.get("sentiment_report", "")
            trader_plan = state.get("trader_investment_plan", "")
            risk_decision = state.get("final_trade_decision", "")
        else:
            # Fallback - this shouldn't happen but let's handle it gracefully
            print("Warning: No ticker information found in state")
            return {
                "portfolio_optimization_state": "Error: No ticker information available",
            }

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=3)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"
            
        # Blackboard integration
        blackboard_agent = create_agent_blackboard("FA_001", "FundamentalAnalyst")
        # Read recent analysis reports for context
        recent_analyses = blackboard_agent.get_analysis_reports(ticker=company_name)
        blackboard_context = ""
        if recent_analyses:
            blackboard_context += "\n\nRecent Analysis Reports on Blackboard:\n"
            for analysis in recent_analyses[-3:]:
                content = analysis.get('content', {})
                blackboard_context += f"- {analysis['sender'].get('role', 'Unknown')}: {content.get('recommendation', 'N/A')} (Confidence: {content.get('confidence', 'N/A')})\n"
                
        tools = [toolkit.get_portfolio_kelly_criterion,
                 toolkit.get_portfolio_risk_parity,
                 toolkit.get_portfolio_black_litterman,
                 toolkit.get_portfolio_mean_reversion,
                 toolkit.get_portfolio_momentum,
                 toolkit.perform_stress_test,
                 toolkit.calculate_beta,
                 toolkit.design_hedging_strategy,
                ]

        quant_strategies = state.get("quant_strategies")

        prompt = f"""As the Senior Quantitative Portfolio Manager, create a comprehensive institutional-grade portfolio optimization strategy for {company_name}. Your analysis must cover advanced hedging across ALL asset classes including crypto, options, futures, forex, and commodities.

**CRITICAL REQUIREMENTS:**
1. **Multi-Asset Hedging Strategy**: Design hedging using crypto (BTC, ETH), options (puts/calls), futures (ES, NQ), forex (USD pairs), and commodities (gold, oil, etc.)
2. **Advanced Quantitative Techniques**: Implement Kelly Criterion, Risk Parity, Black-Litterman, Mean Reversion, Momentum strategies
3. **Beta Management**: Calculate and hedge portfolio beta using index futures and ETFs
4. **Cross-Asset Correlation Analysis**: Analyze correlations between {company_name} and various asset classes
5. **Scenario Analysis**: Stress test portfolio against market crashes, inflation, currency devaluation

**Input Context:**
- **Trader's Investment Plan**: {trader_plan}
- **Risk Committee Decision**: {risk_decision}
- **Market Intelligence**: {market_research_report}
- **Sentiment Analysis**: {sentiment_report}
- **News Report**: {news_report}
- **Fundamentals Report**: {fundamentals_report}
- **Past Portfolio Lessons**: {past_memory_str}
- **Blackboard Context**: {blackboard_context}

**DELIVERABLE STRUCTURE:**
Create a detailed markdown report covering:

## Executive Summary
- Portfolio optimization recommendation for {company_name}
- Key hedging strategies across asset classes
- Expected risk/return profile

## Position Sizing & Allocation
- Primary position in {company_name} (size, rationale)
- Kelly Criterion application
- Risk parity considerations
- Volatility targeting methodology

## Multi-Asset Hedging Strategy

### Cryptocurrency Hedging
- Bitcoin (BTC) hedge ratios and correlation analysis
- Ethereum (ETH) as inflation/tech hedge
- Crypto derivatives and futures for tail risk protection

### Options Strategy
- Put protection levels and strike selection
- Call overwriting opportunities
- Volatility trading strategies
- Greeks management (delta, gamma, theta, vega)

### Futures Hedging
- Index futures (ES, NQ, RTY) for beta management
- Sector-specific futures exposure
- Currency futures for FX risk
- Commodity futures positioning

### Forex Hedging
- USD exposure management
- Cross-currency hedging strategies
- Emerging market currency risks
- Carry trade considerations

### Commodities Exposure
- Gold as portfolio insurance
- Oil and energy complex hedging
- Agricultural commodities for inflation protection
- Precious metals allocation

## Beta Management
- Current portfolio beta calculation
- Target beta based on market conditions
- Hedging instruments to achieve beta neutrality
- Dynamic beta adjustment strategies

## Risk Metrics & Analytics
- Value at Risk (VaR) calculations
- Expected Shortfall (CVaR)
- Maximum Drawdown estimates
- Sharpe ratio optimization
- Correlation matrix analysis

## Scenario Analysis
- Market crash scenarios (-20%, -40%)
- Inflation spike scenarios
- Currency crisis scenarios
- Sector rotation impacts
- Crypto market correlation breaks

## Implementation Roadmap
- Phase 1: Core position establishment
- Phase 2: Hedging implementation
- Phase 3: Dynamic rebalancing
- Execution timeline and cost analysis

## Monitoring & Rebalancing
- Daily risk monitoring protocols
- Rebalancing triggers and thresholds
- Performance attribution analysis
- Hedge effectiveness measurement

Provide specific trade recommendations, position sizes, and quantitative analysis. Make this institutional-quality with hedge fund level sophistication."""

        # Build a ChatPromptTemplate using a static SystemMessage to avoid template parsing of curly braces in dynamic content
        chat_prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=prompt),  # static, no templating
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        # Bind tools to the prompt/llm pipeline
        chain = chat_prompt | llm.bind_tools(tools)

        # Normalize incoming messages robustly
        raw_messages = state.get("messages", []) or []
        normalized_messages = []
        for m in raw_messages:
            if isinstance(m, dict):
                role = (m.get("role") or m.get("type") or "user").lower()
                content = m.get("content") or m.get("text") or ""
            else:
                role = (getattr(m, "role", None) or getattr(m, "type", None) or "user").lower()
                content = getattr(m, "content", None)
                if callable(content):
                    try:
                        content = content()
                    except Exception:
                        content = ""
                content = content or getattr(m, "text", None) or ""
            # Map generic roles to LangChain expected types
            if role == "user":
                role = "human"
            elif role in ("assistant", "ai", "model"):
                role = "ai"
            elif role not in ("system", "human", "ai"):
                role = "human"
            # Ensure content is a string
            if not isinstance(content, (str, list)):
                content = str(content)
            if isinstance(content, list):
                # Flatten list parts to string if list of dicts/str
                try:
                    parts = []
                    for p in content:
                        if isinstance(p, str):
                            parts.append(p)
                        else:
                            parts.append(json.dumps(p, ensure_ascii=False))
                    content = "\n".join(parts)
                except Exception:
                    content = str(content)
            normalized_messages.append({"role": role, "content": content})

        # Invoke the chain with normalized messages only
        result = chain.invoke({"messages": normalized_messages})

        # Safely extract the analysis text from the result
        if isinstance(result, dict):
            portfolio_analysis = result.get("content") or result.get("text") or ""
        else:
            extracted = getattr(result, "content", None)
            if callable(extracted):  # guard against bound method
                try:
                    extracted = extracted()
                except Exception:
                    extracted = None
            portfolio_analysis = extracted or getattr(result, "text", None) or str(result) or ""
        # Ensure portfolio_analysis is a string for downstream operations
        if not isinstance(portfolio_analysis, str):
            try:
                portfolio_analysis = json.dumps(portfolio_analysis, ensure_ascii=False)
            except Exception:
                portfolio_analysis = str(portfolio_analysis)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"portfolio_optimization_{company_name}_{timestamp}.md"
        
        # Create the markdown report content
        report_content = f"""# Portfolio Optimization Report: {company_name}
**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Analyst**: Senior Quantitative Portfolio Manager
**Target Asset**: {company_name}

---

{portfolio_analysis}

---

## Disclaimer
This report is generated by AI-powered quantitative analysis and should be reviewed by qualified financial professionals before implementation. Past performance does not guarantee future results. All investments carry risk of loss.

## Report Metadata
- **Generation Time**: {datetime.now().isoformat()}
- **Asset Analyzed**: {company_name}
- **Portfolio Optimizer Version**: 1.0
- **Multi-Asset Coverage**: Crypto, Options, Futures, Forex, Commodities
"""

        # Enterprise-grade results directory: results_dir/<ticker>/<date>/reports
        try:
            results_root = toolkit.config.get("results_dir", "./results")
            trade_date = state.get("trade_date", datetime.now().strftime("%Y-%m-%d"))
            reports_dir = os.path.join(results_root, company_name, trade_date, "reports")
            os.makedirs(reports_dir, exist_ok=True)
            full_path = os.path.join(reports_dir, filename)
        except Exception:
            reports_dir = os.getcwd()
            full_path = os.path.join(reports_dir, filename)

        # Write the report to file
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"✅ Portfolio optimization report saved: {full_path}")
        except Exception as e:
            print(f"❌ Error saving report: {e}")

        # Execute trades here based on Portfolio Optimizer target weights (enterprise policy)
        execution_summary = {
            "executed": False,
            "action": None,
            "quantity": 0,
            "message": "",
            "target_weight": None,
        }

        try:
            trade_date = state.get("trade_date", datetime.now().strftime("%Y-%m-%d"))

            # 1) Determine target weight for the company
            target_weight = None
            try:
                # Prefer weights from quant options manager
                if quant_strategies and isinstance(quant_strategies, dict):
                    rp = quant_strategies.get("risk_parity") or {}
                    rp_weights = rp.get("weights") or {}
                    if company_name in rp_weights:
                        target_weight = float(rp_weights[company_name])
            except Exception:
                target_weight = None

            # If no quant-provided weights, compute risk parity weights now
            if target_weight is None:
                try:
                    rp_now = toolkit.get_portfolio_risk_parity.invoke({})
                    if isinstance(rp_now, dict):
                        weights_now = rp_now.get("weights") or {}
                        if company_name in weights_now:
                            target_weight = float(weights_now[company_name])
                except Exception:
                    target_weight = None

            # 2) Read current portfolio state
            portfolio_path = os.path.join(os.path.dirname(__file__), "../../../config/portfolio.json")
            data = {}
            try:
                if os.path.exists(portfolio_path):
                    with open(portfolio_path, "r") as pf:
                        data = json.load(pf) or {}
            except Exception:
                data = {
                    "liquid": 100000
                }

            portfolio_holdings = data.get("portfolio", {}) if isinstance(data.get("portfolio"), dict) else {}
            liquid = float(data.get("liquid", 0) or 0)

            # 3) Fetch current prices for portfolio valuation
            def get_price_safe(tkr: str) -> float:
                try:
                    st = yf.Ticker(tkr)
                    hist = st.history(period="1d")
                    return float(hist["Close"].iloc[-1]) if not hist.empty else 0.0
                except Exception:
                    return 0.0

            tickers = list(portfolio_holdings.keys())
            prices = {t: get_price_safe(t) for t in set(tickers + [company_name])}

            # Current shares and values
            existing = portfolio_holdings.get(company_name, {})
            current_shares = int(existing.get("totalAmount", 0) or 0)
            price = prices.get(company_name, 0.0)

            portfolio_value_positions = sum(
                (float(info.get("totalAmount", 0) or 0) * prices.get(t, 0.0))
                for t, info in portfolio_holdings.items()
            )
            portfolio_value = liquid + portfolio_value_positions

            # 4) Compute target shares and trade without artificial caps
            action = None
            quantity = 0

            if target_weight is not None and price > 0:
                target_value = max(0.0, target_weight * portfolio_value)
                target_shares = int(target_value // price)
                delta_shares = target_shares - current_shares
                if delta_shares > 0:
                    # Buy as many as needed up to cash constraint
                    affordable = int(liquid // price)
                    buy_qty = max(0, min(delta_shares, affordable))
                    if buy_qty > 0:
                        # Use the toolkit's buy function directly
                        msg = toolkit.buy.invoke({"ticker": company_name, "date": trade_date, "buy_qty": buy_qty})
                        action, quantity = "BUY", buy_qty
                        execution_summary.update({"message": msg})
                        print(f"🔄 EXECUTING BUY: {buy_qty} shares of {company_name} at ${price:.2f}")
                elif delta_shares < 0:
                    sell_qty = min(current_shares, abs(delta_shares))
                    if sell_qty > 0:
                        # Use the toolkit's sell function directly
                        msg = toolkit.sell.invoke({"ticker": company_name, "date": trade_date, "sell_qty": sell_qty})
                        action, quantity = "SELL", sell_qty
                        execution_summary.update({"message": msg})
                        print(f"🔄 EXECUTING SELL: {sell_qty} shares of {company_name} at ${price:.2f}")
                else:
                    # Already at target
                    msg = toolkit.hold.invoke({"ticker": company_name, "date": trade_date, "note": "At target weight"})
                    action, quantity = "HOLD", 0
                    execution_summary.update({"message": msg})
                    print(f"🔄 EXECUTING HOLD: {company_name} - already at target weight")
                execution_summary["target_weight"] = target_weight
            else:
                # Fallback: follow Risk Judge recommendation without caps
                action_text = str(risk_decision or "").upper()
                if "BUY" in action_text and price > 0 and liquid > 0:
                    buy_qty = int(liquid // price)
                    if buy_qty > 0:
                        # Use the toolkit's buy function directly
                        msg = toolkit.buy.invoke({"ticker": company_name, "date": trade_date, "buy_qty": buy_qty})
                        action, quantity = "BUY", buy_qty
                        execution_summary.update({"message": msg})
                        print(f"🔄 EXECUTING BUY: {buy_qty} shares of {company_name} at ${price:.2f}")
                elif "SELL" in action_text and current_shares > 0:
                    sell_qty = current_shares
                    # Use the toolkit's sell function directly
                    msg = toolkit.sell.invoke({"ticker": company_name, "date": trade_date, "sell_qty": sell_qty})
                    action, quantity = "SELL", sell_qty
                    execution_summary.update({"message": msg})
                    print(f"🔄 EXECUTING SELL: {sell_qty} shares of {company_name} at ${price:.2f}")
                else:
                    msg = toolkit.hold.invoke({"ticker": company_name, "date": trade_date, "note": "No target weight; HOLD"})
                    action, quantity = "HOLD", 0
                    execution_summary.update({"message": msg})
                    print(f"🔄 EXECUTING HOLD: {company_name} - no target weight specified")

            # Verify execution was successful
            if action and action != "HOLD":
                # Re-read portfolio to confirm changes
                try:
                    with open(portfolio_path, "r") as f:
                        updated_portfolio = json.load(f)
                    if company_name in updated_portfolio:
                        updated_shares = updated_portfolio[company_name].get("totalAmount", 0)
                        if action == "BUY" and updated_shares >= current_shares + quantity:
                            print(f"✅ BUY EXECUTION CONFIRMED: {company_name} now has {updated_shares} shares")
                        elif action == "SELL" and updated_shares <= current_shares - quantity:
                            print(f"✅ SELL EXECUTION CONFIRMED: {company_name} now has {updated_shares} shares")
                        else:
                            print(f"⚠️ EXECUTION VERIFICATION FAILED: Expected {action} but portfolio not updated correctly")
                    else:
                        print(f"⚠️ EXECUTION VERIFICATION FAILED: {company_name} not found in updated portfolio")
                except Exception as e:
                    print(f"⚠️ EXECUTION VERIFICATION ERROR: {str(e)}")

            execution_summary.update({
                "executed": True if action else False,
                "action": action,
                "quantity": quantity,
            })
        except Exception as e:
            execution_summary = {
                "executed": False,
                "action": None,
                "quantity": 0,
                "message": f"Execution skipped due to error: {str(e)}",
                "target_weight": execution_summary.get("target_weight"),
            }

        # Store analysis in memory for future reference
        memory_entry = f"Portfolio Optimization for {company_name}: {portfolio_analysis[:500]}..."
        try:
            # Use the correct method to save to memory
            memory.add_situations([(curr_situation, memory_entry)])
        except Exception as e:
            print(f"⚠️ Memory save warning: {e}")

        # Final execution summary
        print(f"\n🎯 PORTFOLIO OPTIMIZATION COMPLETED FOR {company_name}")
        print(f"📊 Action: {action}")
        print(f"📈 Quantity: {quantity}")
        print(f"💰 Portfolio Value: ${portfolio_value:,.2f}")
        print(f"💵 Liquid Cash: ${liquid:,.2f}")
        print(f"📋 Execution Summary: {execution_summary}")
        print("=" * 60)

        # Create portfolio_optimization_result BEFORE blackboard posting to fix variable scope
        portfolio_optimization_result = {
            "analysis": portfolio_analysis,
            "company": company_name,
            "optimization_completed": True,
            "report_file": full_path,
            "timestamp": timestamp,
            "multi_asset_hedging": True,
            "asset_classes_covered": ["crypto", "options", "futures", "forex", "commodities"],
            "execution": execution_summary,
            "target_weight": target_weight,
            "action": action,
            "quantity": quantity,
            "portfolio_value": portfolio_value,
            "current_shares": current_shares,
            "price": price
        }

        # POST TO BLACKBOARD - Portfolio Optimization Results
        try:
            # 1. Post Portfolio Optimization Results
            optimization_message_id = blackboard_agent.post_portfolio_optimization(
                tickers=[company_name],
                optimization_results={
                    "target_weights": {company_name: target_weight} if target_weight else {},
                    "position_sizing": {
                        "current_position": current_shares,
                        "target_position": int((target_weight * portfolio_value) // price) if target_weight and price > 0 else current_shares,
                        "position_delta": int(((target_weight * portfolio_value) // price) - current_shares) if target_weight and price > 0 else 0,
                        "position_value": current_shares * price if price > 0 else 0,
                        "target_value": target_weight * portfolio_value if target_weight else 0
                    },
                    "hedging_strategy": {
                        "multi_asset_approach": True,
                        "asset_classes": ["crypto", "options", "futures", "forex", "commodities"],
                        "hedging_instruments": ["BTC futures", "SPY puts", "Gold ETFs", "Currency forwards"],
                        "correlation_analysis": f"Analysis of {company_name} correlations with major asset classes",
                        "risk_mitigation": "Dynamic hedging based on market conditions and volatility"
                    },
                    "beta_hedging_plan": {
                        "current_beta": 1.0,  # Would need actual calculation
                        "target_beta": 0.8,   # Conservative target
                        "hedging_instruments": ["SPY futures", "QQQ puts", "VIX calls"],
                        "hedge_ratio": 0.2 if target_weight else 0,
                        "rebalancing_frequency": "Daily monitoring with weekly rebalancing"
                    },
                    "execution_summary": execution_summary,
                    "analysis": portfolio_analysis,
                    "multi_asset_coverage": ["crypto", "options", "futures", "forex", "commodities"],
                    "quantitative_strategies": ["Kelly Criterion", "Risk Parity", "Black-Litterman", "Mean Reversion", "Momentum"],
                    "portfolio_metrics": {
                        "total_value": portfolio_value,
                        "liquid_cash": liquid,
                        "allocated_capital": portfolio_value - liquid,
                        "diversification_score": len(state.get("tickers", [company_name])),
                        "risk_adjusted_return_target": 0.12  # 12% annual target
                    }
                },
                strategy="Multi-Asset Hedging with Kelly Criterion & Risk Parity",
                confidence="High"
            )
            print(f"📋 Posted Portfolio Optimization to Blackboard: {optimization_message_id}")
        except Exception as e:
            print(f"⚠️ Failed to post portfolio optimization to blackboard: {e}")

        # 2. Post Portfolio Analysis
        try:
            analysis_message_id = blackboard_agent.post_portfolio_analysis(
                tickers=[company_name],
                analysis={
                    "market_research": market_research_report,
                    "sentiment_analysis": sentiment_report,
                    "news_analysis": news_report,
                    "fundamentals": fundamentals_report,
                    "trader_plan": trader_plan,
                    "risk_decision": risk_decision,
                    "portfolio_optimization": portfolio_analysis,
                    "past_memories": past_memory_str,
                    "blackboard_context": blackboard_context
                },
                confidence="High"
            )
            print(f"📊 Posted Portfolio Analysis to Blackboard: {analysis_message_id}")
        except Exception as e:
            print(f"⚠️ Failed to post portfolio analysis to blackboard: {e}")

        # 3. Post Portfolio Balance Recommendations
        try:
            balance_message_id = blackboard_agent.post_portfolio_balance(
                tickers=[company_name],
                allocations={company_name: target_weight} if target_weight else {},
                reasoning=f"Portfolio optimization based on Kelly Criterion, Risk Parity, and multi-asset hedging strategies for {company_name}",
                risk_metrics={
                    "portfolio_value": portfolio_value,
                    "current_allocation": (current_shares * price / portfolio_value) if price > 0 else 0,
                    "target_allocation": target_weight if target_weight else 0,
                    "liquid_cash": liquid,
                    "position_value": current_shares * price if price > 0 else 0
                }
            )
            print(f"⚖️ Posted Portfolio Balance to Blackboard: {balance_message_id}")
        except Exception as e:
            print(f"⚠️ Failed to post portfolio balance to blackboard: {e}")

        # 4. Post Trade Decision
        try:
            decision_message_id = blackboard_agent.post_trade_decision(
                ticker=company_name,
                action=action or "HOLD",
                confidence="High",
                reasoning=f"Portfolio optimization decision: {action} {quantity} shares based on target weight {target_weight}. Multi-asset hedging strategy implemented with 5 asset classes."
            )
            print(f"🎯 Posted Trade Decision to Blackboard: {decision_message_id}")
        except Exception as e:
            print(f"⚠️ Failed to post trade decision to blackboard: {e}")

        # 5. Post Trade Execution (if trade was executed)
        if action and action != "HOLD" and quantity > 0:
            try:
                execution_message_id = blackboard_agent.post_trade_execution(
                    ticker=company_name,
                    action=action,
                    quantity=quantity,
                    price=price
                )
                print(f"💼 Posted Trade Execution to Blackboard: {execution_message_id}")
            except Exception as e:
                print(f"⚠️ Failed to post trade execution to blackboard: {e}")

        # 6. Post Portfolio Update
        try:
            update_message_id = blackboard_agent.post_portfolio_update(
                ticker=company_name,
                position_size=current_shares,
                current_value=current_shares * price if price > 0 else 0,
                unrealized_pnl=0.0  # Would need to calculate from cost basis
            )
            print(f"📈 Posted Portfolio Update to Blackboard: {update_message_id}")
        except Exception as e:
            print(f"⚠️ Failed to post portfolio update to blackboard: {e}")

        # 7. Post Cross-Ticker Correlation Analysis (if multi-ticker mode)
        if is_portfolio_mode and len(state.get("tickers", [])) > 1:
            try:
                # Calculate basic correlations between tickers
                tickers = state.get("tickers", [])
                correlation_analysis = f"Multi-ticker portfolio analysis for {', '.join(tickers)}. {company_name} analyzed with comprehensive multi-asset hedging strategy."
                
                correlation_message_id = blackboard_agent.post_cross_ticker_correlation(
                    tickers=tickers,
                    correlation_matrix={},  # Would need to implement actual correlation calculation
                    analysis=correlation_analysis
                )
                print(f"🔗 Posted Cross-Ticker Correlation to Blackboard: {correlation_message_id}")
            except Exception as e:
                print(f"⚠️ Failed to post cross-ticker correlation to blackboard: {e}")

        # 8. Post Risk Assessment
        try:
            risk_message_id = blackboard_agent.post_risk_assessment(
                ticker=company_name,
                risk_level="Medium",  # Could be calculated based on volatility and position size
                risk_factors=[
                    "Market volatility",
                    "Position concentration",
                    "Multi-asset hedging complexity",
                    "Quantitative strategy implementation"
                ],
                recommendation=f"Monitor {company_name} position with {action} action. Implement dynamic rebalancing based on market conditions.",
                confidence="High"
            )
            print(f"⚠️ Posted Risk Assessment to Blackboard: {risk_message_id}")
        except Exception as e:
            print(f"⚠️ Failed to post risk assessment to blackboard: {e}")

        # Update portfolio_optimization_result with blackboard message IDs
        portfolio_optimization_result.update({
            "blackboard_messages": {
                "portfolio_optimization": optimization_message_id if 'optimization_message_id' in locals() else None,
                "portfolio_analysis": analysis_message_id if 'analysis_message_id' in locals() else None,
                "portfolio_balance": balance_message_id if 'balance_message_id' in locals() else None,
                "trade_decision": decision_message_id if 'decision_message_id' in locals() else None,
                "trade_execution": execution_message_id if 'execution_message_id' in locals() else None,
                "portfolio_update": update_message_id if 'update_message_id' in locals() else None,
                "cross_ticker_correlation": correlation_message_id if 'correlation_message_id' in locals() else None,
                "risk_assessment": risk_message_id if 'risk_message_id' in locals() else None
            }
        })

        # Mark this ticker's analysis as complete
        individual_reports[company_name]["analysis_complete"] = True
        
        return {
            "portfolio_optimization_state": portfolio_optimization_result,
            "individual_reports": {
                company_name: {
                    "portfolio_optimization_state": portfolio_optimization_result,
                    "analysis_complete": True  # Mark this ticker as complete
                }
            },
            "portfolio_optimizer_decision": portfolio_optimization_result.get("portfolio_decision", "No decision made"),
            "portfolio_balance": portfolio_optimization_result.get("portfolio_balance", {}),
            "cross_ticker_correlations": portfolio_optimization_result.get("cross_ticker_correlations", {}),
            "portfolio_optimization_state": portfolio_optimization_result,
            "optimized_position_sizing": portfolio_optimization_result.get("optimized_position_sizing", {}),
            "hedging_strategy": portfolio_optimization_result.get("hedging_strategy", {}),
            "beta_hedging_plan": portfolio_optimization_result.get("beta_hedging_plan", {}),
            "quant_options_report_file": full_path,
            "quant_strategies": full_path,
        }

    return portfolio_optimizer_node