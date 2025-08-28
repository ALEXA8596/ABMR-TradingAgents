# 🗺️ Agent Dependency Map

## **Current System Dependencies**

### **Import Dependencies Analysis**

#### **Graph Setup Dependencies (`tradingagents/graph/setup.py`):**
```python
# CURRENT IMPORTS - 20+ agent variants
from tradingagents.agents.researchers.bear_researcher_ask import create_bear_researcher_ask    # ❌ REDUNDANT
from tradingagents.agents.researchers.bull_researcher_ask import create_bull_researcher_ask    # ❌ REDUNDANT
from tradingagents.agents.researchers.bear_researcher_ans import create_bear_researcher_ans    # ❌ REDUNDANT
from tradingagents.agents.researchers.bull_researcher_ans import create_bull_researcher_ans    # ❌ REDUNDANT
from tradingagents.agents.risk_mgmt.aggresive_debator_ask import create_risky_debator_ask      # ❌ REDUNDANT
from tradingagents.agents.risk_mgmt.aggresive_debator_ans import create_risky_debator_ans      # ❌ REDUNDANT
from tradingagents.agents.risk_mgmt.conservative_debator_ask import create_safe_debator_ask    # ❌ REDUNDANT
from tradingagents.agents.risk_mgmt.conservative_debator_ans import create_safe_debator_ans    # ❌ REDUNDANT
```

#### **Core Agent Imports (`tradingagents/agents/__init__.py`):**
```python
# KEEP - Core functionality
from .analysts.market_analyst import create_market_analyst                          # ✅ KEEP
from .analysts.fundamentals_analyst import create_fundamentals_analyst              # ✅ KEEP
from .analysts.news_analyst import create_news_analyst                              # ✅ KEEP
from .analysts.social_media_analyst import create_social_media_analyst              # ✅ KEEP
from .analysts.macroeconomic_analyst import create_macroeconomic_analyst            # ✅ KEEP

from .researchers.bull_researcher import create_bull_researcher                     # ✅ KEEP
from .researchers.bear_researcher import create_bear_researcher                     # ✅ KEEP

from .risk_mgmt.aggresive_debator import create_risky_debator                      # ✅ RENAME
from .risk_mgmt.conservative_debator import create_safe_debator                     # ✅ RENAME
from .risk_mgmt.neutral_debator import create_neutral_debator                       # ❌ REMOVE

from .managers.research_manager import create_research_manager                      # ✅ KEEP
from .managers.risk_manager import create_risk_manager                              # ✅ KEEP
from .managers.portfolio_optimizer import create_portfolio_optimizer               # ⚠️ CONSOLIDATE
from .managers.multi_ticker_portfolio_optimizer import create_multi_ticker_portfolio_optimizer  # ⚠️ CONSOLIDATE
```

### **Graph Routing Dependencies**

#### **Current Complex Routing Logic:**
```python
# COMPLEX ASK/ANSWER ROUTING - TO BE SIMPLIFIED
workflow.add_conditional_edges(
    "Bull Researcher",
    self.conditional_logic.should_continue_debate,
    {
        "Bear Researcher": "Bear Researcher",
        "Bull Researcher Ask": "Bull Researcher Ask",      # ❌ REMOVE
        "Bear Researcher Ask": "Bear Researcher Ask",      # ❌ REMOVE
        "Bull Researcher Ans": "Bull Researcher Ans",     # ❌ REMOVE
        "Bear Researcher Ans": "Bear Researcher Ans",     # ❌ REMOVE
        "Research Manager": "Research Manager",
    },
)
```

#### **Proposed Simplified Routing:**
```python
# SIMPLIFIED ROUTING
workflow.add_conditional_edges(
    "Bull Researcher",
    self.conditional_logic.should_continue_debate,
    {
        "Bear Researcher": "Bear Researcher",
        "Research Manager": "Research Manager",
    },
)
```

### **State Management Dependencies**

#### **Current State Structure:**
```python
# Multi-ticker state with complex debate tracking
{
    "investment_debate_states": {
        "SPY": {
            "history": "[]",
            "current_response": "",
            "judge_decision": "", 
            "bull_history": "[]",
            "bear_history": "[]",
            "count": 0
        }
    },
    "risk_debate_states": {
        "SPY": {
            "history": "[]",
            "current_risky_response": "",
            "current_safe_response": "",
            "current_neutral_response": "",    # ❌ REMOVE neutral
            "latest_speaker": "",
            "judge_decision": "",
            "count": 0
        }
    }
}
```

#### **Proposed Simplified State:**
```python
# Simplified state structure
{
    "investment_debate_states": {
        "SPY": {
            "bull_response": "",
            "bear_response": "",
            "decision": "",
            "count": 0
        }
    },
    "risk_analysis_states": {
        "SPY": {
            "risky_analysis": "",
            "safe_analysis": "",
            "final_decision": "",
            "count": 0
        }
    }
}
```

---

## **File Removal Impact Analysis**

### **Files to Remove (11 files total)**

#### **Research Ask/Answer Files (6 files):**
1. `tradingagents/agents/researchers/bull_researcher_ask.py`
2. `tradingagents/agents/researchers/bull_researcher_ans.py`
3. `tradingagents/agents/researchers/bear_researcher_ask.py`
4. `tradingagents/agents/researchers/bear_researcher_ans.py`
5. `tradingagents/agents/researchers/bull_researcher_crossex.py`
6. `tradingagents/agents/researchers/bear_researcher_crossex.py`

**Impact:** 
- Remove from `__init__.py` imports
- Remove node creation in `setup.py`
- Remove routing logic in `conditional_logic.py`
- Update `should_continue_debate()` method

#### **Risk Ask/Answer Files (4 files):**
1. `tradingagents/agents/risk_mgmt/aggresive_debator_ask.py`
2. `tradingagents/agents/risk_mgmt/aggresive_debator_ans.py`
3. `tradingagents/agents/risk_mgmt/conservative_debator_ask.py`
4. `tradingagents/agents/risk_mgmt/conservative_debator_ans.py`

**Impact:**
- Remove from `__init__.py` imports
- Remove node creation in `setup.py`
- Remove routing logic in `conditional_logic.py`
- Update `should_continue_risk_analysis()` method

#### **Neutral Debator (1 file):**
1. `tradingagents/agents/risk_mgmt/neutral_debator.py`

**Impact:**
- Remove from imports and graph setup
- Simplify risk analysis flow
- Update state management to remove neutral responses

---

## **Consolidation Dependencies**

### **Portfolio Manager Consolidation**

#### **Current Files to Merge:**
- `tradingagents/agents/managers/portfolio_optimizer.py` (500+ lines)
- `tradingagents/agents/managers/multi_ticker_portfolio_optimizer.py` (280+ lines)
- `tradingagents/agents/managers/quantoptions_manager.py` (200+ lines)
- `tradingagents/agents/managers/options_manager.py` (100+ lines)

#### **Consolidation Strategy:**
```python
# NEW UNIFIED FILE: portfolio_manager.py
class PortfolioManager:
    def __init__(self, llm, memory, toolkit):
        self.llm = llm
        self.memory = memory 
        self.toolkit = toolkit
        
    def analyze(self, state):
        tickers = state.get("tickers", [])
        
        if len(tickers) > 1:
            return self._multi_ticker_analysis(state)
        else:
            return self._single_ticker_analysis(state)
            
    def _multi_ticker_analysis(self, state):
        # Logic from multi_ticker_portfolio_optimizer.py
        pass
        
    def _single_ticker_analysis(self, state):
        # Logic from portfolio_optimizer.py
        pass
        
    def _options_analysis(self, state):
        # Logic from quantoptions_manager.py + options_manager.py
        pass
```

### **Risk Debator Renaming**

#### **Files to Rename:**
1. `aggresive_debator.py` → `risky_analyst.py`
2. `conservative_debator.py` → `safe_analyst.py`

#### **Function Renaming:**
- `create_risky_debator()` → `create_risky_analyst()`
- `create_safe_debator()` → `create_safe_analyst()`

#### **Graph Node Renaming:**
- "Risky Analyst" (keep same)
- "Safe Analyst" (keep same)

---

## **Testing Impact Analysis**

### **Files Requiring Test Updates:**
1. `test_complete_system.py` - Full system integration tests
2. `test_multi_ticker_system.py` - Multi-ticker specific tests
3. `test_portfolio_optimization.py` - Portfolio optimization tests
4. `test_system_components.py` - Component-level tests
5. `test_routing_logic.py` - Graph routing tests

### **Test Cases to Update:**
- Remove ask/answer pattern tests
- Update debate flow tests
- Simplify risk analysis tests
- Update portfolio optimization tests
- Test unified portfolio manager

---

## **Implementation Priority Matrix**

### **HIGH PRIORITY (Do First - Low Risk):**
1. **File Deletion** - Remove redundant ask/answer files
2. **Import Cleanup** - Update `__init__.py` imports
3. **Documentation** - Update docs to reflect changes

### **MEDIUM PRIORITY (Core Changes):**
1. **Conditional Logic** - Simplify debate and risk analysis flows
2. **Graph Setup** - Remove ask/answer nodes and edges
3. **State Management** - Simplify state structures

### **LOW PRIORITY (Do Last - High Risk):**
1. **Portfolio Consolidation** - Merge multiple portfolio managers
2. **File Renaming** - Rename risk debators to analysts
3. **Advanced Testing** - Performance and stress testing

---

## **Rollback Dependencies**

### **Critical Backup Points:**
1. **Before file deletion** - Can restore individual files
2. **Before conditional logic changes** - Can restore routing
3. **Before graph setup changes** - Can restore node structure
4. **Before portfolio consolidation** - Can restore individual managers

### **Git Strategy:**
```bash
# Create backup branch
git checkout -b pre-streamlining-backup
git add -A && git commit -m "Complete backup before streamlining"

# Create implementation branch
git checkout -b agent-streamlining
```

---

This dependency map provides a complete roadmap for safely streamlining the agent system while maintaining all critical functionality. 