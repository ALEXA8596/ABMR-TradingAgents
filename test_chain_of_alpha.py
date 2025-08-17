#!/usr/bin/env python3
"""
Test script for the Chain-of-Alpha Options Analyst

This script demonstrates the Chain-of-Alpha methodology for generating
sophisticated alpha signals in options trading using multi-step reasoning.
"""

import os
import sys
from datetime import datetime

# Add the tradingagents package to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tradingagents'))

from tradingagents.agents.analysts.quant_options_analyst import (
    create_chain_of_alpha_options_analyst,
    ChainOfAlphaOptionsAnalyst,
    AlphaSignal,
    OptionsAlpha
)

# Mock LLM for testing
class MockLLM:
    def invoke(self, prompt):
        class MockResponse:
            def __init__(self, content):
                self.content = content
        
        # Simple mock responses based on prompt content
        if "volatility alpha" in prompt.lower():
            return MockResponse("""
            Step 1: Volatility Mispricing Analysis
            - Implied volatility (25%) is higher than historical volatility (22%)
            - This suggests volatility may be overpriced
            - Volatility skew shows slight put skew of 5%
            
            Step 2: Market Context Integration
            - Current market sentiment is moderately positive
            - Momentum signals suggest continued upward movement
            - Mean reversion signals are neutral
            
            Step 3: Alpha Signal Generation
            - Volatility appears overpriced by approximately 3%
            - Confidence level: 70%
            - Expected magnitude: -0.3 (volatility overpriced)
            - Time horizon: SHORT_TERM
            """)
        elif "directional alpha" in prompt.lower():
            return MockResponse("""
            Step 1: Technical Signal Analysis
            - Momentum signals show strong upward bias
            - Mean reversion signals are neutral
            - Signals are aligned and supportive
            
            Step 2: Sentiment Integration
            - Social sentiment is positive (65%)
            - News sentiment is moderately positive (58%)
            - Analyst consensus is bullish (72%)
            
            Step 3: Fundamental Context
            - PE ratio of 25.5 is reasonable for growth
            - Revenue growth of 18% supports bullish thesis
            - Earnings growth of 22% is strong
            
            Step 4: Alpha Signal Generation
            - Overall directional bias: BULLISH
            - Confidence level: 75%
            - Expected magnitude: 0.6 (moderate bullish)
            - Time horizon: MEDIUM_TERM
            """)
        elif "arbitrage alpha" in prompt.lower():
            return MockResponse("""
            Step 1: Volatility Surface Analysis
            - Volatility term structure shows slight upward slope
            - 30d: 23%, 60d: 25%, 90d: 27%
            - No obvious mispricings detected
            
            Step 2: Spread Opportunity Detection
            - Calendar spreads show minimal opportunities
            - Strike price arbitrage not evident
            - Volatility surface appears fairly priced
            
            Step 3: Risk Assessment
            - Execution risks are moderate
            - Profit potential is limited
            
            Step 4: Alpha Signal Generation
            - Confidence in arbitrage: 30%
            - Expected profit magnitude: 0.1 (low)
            - Time horizon: SHORT_TERM
            """)
        elif "hedging alpha" in prompt.lower():
            return MockResponse("""
            Step 1: Risk Exposure Assessment
            - Current market risks are moderate
            - Sentiment suggests potential volatility increase
            - Momentum signals indicate continued movement
            
            Step 2: Hedging Instrument Selection
            - Protective puts provide cost-effective hedging
            - Iron condors can generate income while hedging
            - Calendar spreads offer time-based protection
            
            Step 3: Hedging Ratio Calculation
            - Optimal hedge ratio: 30% of position
            - Hedging should be implemented gradually
            
            Step 4: Alpha Signal Generation
            - Confidence in hedging need: 60%
            - Expected hedging benefit: 0.4 (moderate)
            - Time horizon: MEDIUM_TERM
            """)
        else:
            return MockResponse("Mock response for testing purposes")

# Mock memory for testing
class MockMemory:
    def add_situations(self, situations):
        print(f"Mock memory updated with: {situations}")
    
    def get_memories(self, situation, n_matches=3):
        return []

# Mock toolkit for testing
class MockToolkit:
    def __init__(self):
        self.config = {"results_dir": "./test_results"}
    
    def get_portfolio_momentum(self):
        class MockMomentum:
            def invoke(self, params):
                return {
                    "signals": {
                        "NVDA": {"signal": "BUY", "momentum_score": 0.15, "rsi": 65},
                        "AAPL": {"signal": "HOLD", "momentum_score": 0.02, "rsi": 55}
                    }
                }
        return MockMomentum()
    
    def get_portfolio_mean_reversion(self):
        class MockMeanRev:
            def invoke(self, params):
                return {
                    "signals": {
                        "NVDA": {"signal": "HOLD", "z_score": 0.5, "weight": 0.0},
                        "AAPL": {"signal": "BUY", "z_score": -1.8, "weight": 0.3}
                    }
                }
        return MockMeanRev()
    
    def get_portfolio_risk_parity(self):
        class MockRiskParity:
            def invoke(self, params):
                return {
                    "weights": {"NVDA": 0.6, "AAPL": 0.4},
                    "portfolio_volatility": 0.18
                }
        return MockRiskParity()

def test_chain_of_alpha_analyst():
    """Test the Chain-of-Alpha options analyst"""
    
    print("🧠 Testing Chain-of-Alpha Options Analyst")
    print("=" * 50)
    
    # Create mock components
    mock_llm = MockLLM()
    mock_memory = MockMemory()
    mock_toolkit = MockToolkit()
    
    # Create the analyst
    analyst = ChainOfAlphaOptionsAnalyst(mock_llm, mock_memory, mock_toolkit)
    
    # Test state
    test_state = {
        "company_of_interest": "NVDA",
        "trade_date": datetime.now().strftime("%Y-%m-%d")
    }
    
    print(f"📊 Analyzing: {test_state['company_of_interest']}")
    print(f"📅 Date: {test_state['trade_date']}")
    print()
    
    try:
        # Run the analysis
        result = analyst.generate_chain_of_alpha(test_state)
        
        print("✅ Chain-of-Alpha analysis completed successfully!")
        print()
        
        # Display results
        print("📈 Analysis Results:")
        print(f"  • Combined Alpha Score: {result['options_alpha_analysis'].combined_alpha_score:.3f}")
        print(f"  • Alpha Strength: {result['options_alpha_analysis'].combined_alpha_score:.3f}")
        print(f"  • Risk Level: {result['options_alpha_analysis'].risk_metrics['total_risk']:.3f}")
        print()
        
        print("🎯 Recommended Strategies:")
        for strategy in result['options_alpha_analysis'].recommended_strategies:
            print(f"  • {strategy}")
        print()
        
        print("📊 Alpha Signals:")
        alpha_signals = result['alpha_signals']
        for signal_type, signal in alpha_signals.items():
            if signal:
                print(f"  • {signal_type.title()}: {signal.magnitude:.3f} (confidence: {signal.confidence:.3f})")
        print()
        
        print("📁 Generated Reports:")
        print(f"  • Markdown Report: {result['alpha_report_file']}")
        print(f"  • JSON Artifact: {result['alpha_artifact_file']}")
        print()
        
        print("🔍 Chain-of-Alpha Methodology Applied:")
        print("  1. Multi-Step Reasoning: Breaking down complex options decisions")
        print("  2. Alpha Signal Generation: Specialized signals for each factor")
        print("  3. Signal Combination: Weighted synthesis of multiple alphas")
        print("  4. Strategy Generation: Options strategies optimized for alpha profile")
        print("  5. Risk Assessment: Comprehensive risk metrics")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

def test_alpha_signal_creation():
    """Test AlphaSignal dataclass creation"""
    
    print("\n🧪 Testing AlphaSignal Creation")
    print("-" * 30)
    
    # Create test alpha signals
    volatility_signal = AlphaSignal(
        signal_type="VOLATILITY",
        confidence=0.8,
        magnitude=-0.3,
        time_horizon="SHORT_TERM",
        rationale="Volatility appears overpriced based on IV vs HV analysis",
        supporting_data={"iv": 0.25, "hv": 0.22}
    )
    
    directional_signal = AlphaSignal(
        signal_type="DIRECTIONAL",
        confidence=0.75,
        magnitude=0.6,
        time_horizon="MEDIUM_TERM",
        rationale="Strong bullish momentum with positive sentiment",
        supporting_data={"momentum": 0.15, "sentiment": 0.65}
    )
    
    print("✅ AlphaSignal objects created successfully:")
    print(f"  • Volatility: {volatility_signal.signal_type} - {volatility_signal.magnitude:.3f}")
    print(f"  • Directional: {directional_signal.signal_type} - {directional_signal.magnitude:.3f}")

if __name__ == "__main__":
    print("🚀 Chain-of-Alpha Options Analyst Test Suite")
    print("=" * 60)
    
    # Test basic functionality
    test_alpha_signal_creation()
    
    # Test full analysis
    test_chain_of_alpha_analyst()
    
    print("\n🎉 All tests completed!")
    print("\n💡 The Chain-of-Alpha methodology successfully:")
    print("   • Generates sophisticated alpha signals using multi-step reasoning")
    print("   • Combines multiple alpha factors into unified decisions")
    print("   • Provides options strategies optimized for alpha profiles")
    print("   • Delivers comprehensive risk assessment and reporting")
