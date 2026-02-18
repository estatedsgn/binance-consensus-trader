"""
Тестовые данные и бэктестинг для Binance Consensus Trader
"""

from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime, timedelta


@dataclass
class MockTrader:
    """Тестовый трейдер"""
    encrypted_uid: str
    nick_name: str
    rank: int
    roi: float
    win_rate: float


@dataclass
class MockPosition:
    """Тестовая позиция с историческими данными"""
    symbol: str
    side: str  # LONG или SHORT
    entry_price: float
    exit_price: float  # Цена закрытия (для расчёта PNL)
    entry_time: datetime
    exit_time: datetime
    pnl: float


@dataclass
class TestScenario:
    """Сценарий тестирования"""
    name: str
    description: str
    date: datetime
    traders: List[MockTrader]
    positions: Dict[str, List[MockPosition]]
    expected_consensus: Dict[str, float]  # symbol -> long_percent


# ===== ТЕСТОВЫЕ СЦЕНАРИИ =====

def get_scenario_1_btc_bull_run() -> TestScenario:
    """Сценарий 1: BTC растёт, большинство трейдеров LONG"""
    
    traders = [
        MockTrader("t1", "ProTrader1", 1, 250.0, 70.0),
        MockTrader("t2", "CryptoKing", 2, 200.0, 65.0),
        MockTrader("t3", "WhaleHunter", 3, 180.0, 62.0),
        MockTrader("t4", "AlphaBot", 4, 150.0, 58.0),
        MockTrader("t5", "TrendMaster", 5, 140.0, 60.0),
    ]
    
    # 4 из 5 трейдеров LONG (80% консенсус)
    positions = {
        "t1": [MockPosition("BTCUSDT", "LONG", 40000, 44000, 
                           datetime.now() - timedelta(hours=2),
                           datetime.now(), 10.0)],
        "t2": [MockPosition("BTCUSDT", "LONG", 40200, 44000,
                           datetime.now() - timedelta(hours=1),
                           datetime.now(), 9.45)],
        "t3": [MockPosition("BTCUSDT", "LONG", 39800, 44000,
                           datetime.now() - timedelta(hours=3),
                           datetime.now(), 10.55)],
        "t4": [MockPosition("BTCUSDT", "SHORT", 41000, 44000,
                           datetime.now() - timedelta(hours=1),
                           datetime.now(), -7.3)],
        "t5": [MockPosition("BTCUSDT", "LONG", 40500, 44000,
                           datetime.now() - timedelta(hours=2),
                           datetime.now(), 8.6)],
    }
    
    return TestScenario(
        name="BTC Bull Run",
        description="BTC растёт с 40k до 44k, 80% трейдеров в LONG",
        date=datetime.now(),
        traders=traders,
        positions=positions,
        expected_consensus={"BTCUSDT": 80.0}
    )


def get_scenario_2_eth_crash() -> TestScenario:
    """Сценарий 2: ETH падает, большинство SHORT"""
    
    traders = [
        MockTrader("t1", "BearMaster", 1, 300.0, 75.0),
        MockTrader("t2", "ShortKing", 2, 250.0, 70.0),
        MockTrader("t3", "Doomer", 3, 200.0, 68.0),
        MockTrader("t4", "RektProof", 4, 180.0, 65.0),
        MockTrader("t5", "Cautious", 5, 150.0, 60.0),
        MockTrader("t6", "Bullish", 6, 140.0, 55.0),
    ]
    
    # 5 из 6 трейдеров SHORT (83% консенсус)
    positions = {
        "t1": [MockPosition("ETHUSDT", "SHORT", 2500, 2200,
                           datetime.now() - timedelta(hours=2),
                           datetime.now(), 12.0)],
        "t2": [MockPosition("ETHUSDT", "SHORT", 2520, 2200,
                           datetime.now() - timedelta(hours=1),
                           datetime.now(), 12.7)],
        "t3": [MockPosition("ETHUSDT", "SHORT", 2480, 2200,
                           datetime.now() - timedelta(hours=3),
                           datetime.now(), 11.3)],
        "t4": [MockPosition("ETHUSDT", "SHORT", 2550, 2200,
                           datetime.now() - timedelta(hours=2),
                           datetime.now(), 13.7)],
        "t5": [MockPosition("ETHUSDT", "SHORT", 2490, 2200,
                           datetime.now() - timedelta(hours=1),
                           datetime.now(), 11.6)],
        "t6": [MockPosition("ETHUSDT", "LONG", 2450, 2200,
                           datetime.now() - timedelta(hours=2),
                           datetime.now(), -10.2)],
    }
    
    return TestScenario(
        name="ETH Crash",
        description="ETH падает с 2500 до 2200, 83% трейдеров в SHORT",
        date=datetime.now(),
        traders=traders,
        positions=positions,
        expected_consensus={"ETHUSDT": 16.7}  # 16.7% LONG = 83.3% SHORT
    )


def get_scenario_3_mixed_signals() -> TestScenario:
    """Сценарий 3: Нет чёткого консенсуса (50/50)"""
    
    traders = [
        MockTrader("t1", "BullA", 1, 200.0, 60.0),
        MockTrader("t2", "BearA", 2, 190.0, 58.0),
        MockTrader("t3", "BullB", 3, 180.0, 55.0),
        MockTrader("t4", "BearB", 4, 170.0, 57.0),
        MockTrader("t5", "BullC", 5, 160.0, 54.0),
        MockTrader("t6", "BearC", 6, 150.0, 56.0),
    ]
    
    # 3 LONG, 3 SHORT (50/50)
    positions = {
        "t1": [MockPosition("SOLUSDT", "LONG", 100, 98,
                           datetime.now() - timedelta(hours=1),
                           datetime.now(), -2.0)],
        "t2": [MockPosition("SOLUSDT", "SHORT", 102, 98,
                           datetime.now() - timedelta(hours=1),
                           datetime.now(), 3.9)],
        "t3": [MockPosition("SOLUSDT", "LONG", 101, 98,
                           datetime.now() - timedelta(hours=2),
                           datetime.now(), -3.0)],
        "t4": [MockPosition("SOLUSDT", "SHORT", 103, 98,
                           datetime.now() - timedelta(hours=1),
                           datetime.now(), 4.9)],
        "t5": [MockPosition("SOLUSDT", "LONG", 99, 98,
                           datetime.now() - timedelta(hours=3),
                           datetime.now(), -1.0)],
        "t6": [MockPosition("SOLUSDT", "SHORT", 100, 98,
                           datetime.now() - timedelta(hours=2),
                           datetime.now(), 2.0)],
    }
    
    return TestScenario(
        name="Mixed Signals",
        description="SOL 50/50 разделение, нет консенсуса",
        date=datetime.now(),
        traders=traders,
        positions=positions,
        expected_consensus={"SOLUSDT": 50.0}
    )


def get_all_scenarios() -> List[TestScenario]:
    """Возвращает все тестовые сценарии"""
    return [
        get_scenario_1_btc_bull_run(),
        get_scenario_2_eth_crash(),
        get_scenario_3_mixed_signals(),
    ]
