from .utils.agent_utils import Toolkit, create_msg_delete
from .utils.agent_states import AgentState, InvestDebateState, RiskDebateState
from .utils.memory import FinancialSituationMemory

from .analysts.fundamentals_analyst import create_fundamentals_analyst
from .analysts.market_analyst import create_market_analyst
from .analysts.news_analyst import create_news_analyst
from .analysts.social_media_analyst import create_social_media_analyst
from .analysts.macroeconomic_analyst import create_macroeconomic_analyst
from .analysts.quant_market_analyst import create_quant_market_analyst

from .researchers.bear_researcher import create_bear_researcher
from .researchers.bull_researcher import create_bull_researcher

# Cross Examination Agents - RESTORED
from .researchers.bear_researcher_crossex import create_bear_crossex_researcher
from .researchers.bull_researcher_crossex import create_bull_crossex_researcher

from .risk_mgmt.aggresive_debator import create_risky_debator
from .risk_mgmt.conservative_debator import create_safe_debator
from .risk_mgmt.neutral_debator import create_neutral_debator  # RESTORED

from .managers.research_manager import create_research_manager
from .managers.risk_manager import create_risk_manager
from .managers.portfolio_optimizer_refactored import create_portfolio_optimizer
from .managers.multi_ticker_portfolio_optimizer import create_multi_ticker_portfolio_optimizer
from .managers.quantoptions_manager import create_quant_options_manager
from .managers.portfolio_manager import create_portfolio_manager
from .managers.execution_manager import create_execution_manager

from .trader.trader import create_trader

__all__ = [
    "FinancialSituationMemory",
    "Toolkit",
    "AgentState",
    "create_msg_delete",
    "InvestDebateState",
    "RiskDebateState",
    "create_bear_researcher",
    "create_bull_researcher",
    "create_bear_crossex_researcher",  # RESTORED
    "create_bull_crossex_researcher",  # RESTORED
    "create_research_manager",
    "create_fundamentals_analyst",
    "create_market_analyst",
    "create_macroeconomic_analyst",
    "create_quant_market_analyst",
    "create_neutral_debator",  # RESTORED
    "create_news_analyst",
    "create_risky_debator",
    "create_risk_manager",
    "create_safe_debator",
    "create_social_media_analyst",
    "create_portfolio_optimizer",
    "create_multi_ticker_portfolio_optimizer",
    "create_quant_options_manager",
    "create_portfolio_manager",
    "create_execution_manager",
    "create_trader",
]
