#!/usr/bin/env python3
"""
Бэктестинг стратегии консенсуса
Тестируем на исторических сценариях
"""

import sys
from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass

from test_data import get_all_scenarios, TestScenario, MockPosition
from consensus import ConsensusEngine, SymbolConsensus
from colorama import Fore, Style, init

init(autoreset=True)


@dataclass
class Trade:
    """Сделка"""
    symbol: str
    side: str  # LONG или SHORT
    entry_price: float
    exit_price: float
    entry_time: datetime
    exit_time: datetime
    pnl: float
    pnl_percent: float
    signal: str


@dataclass
class BacktestResult:
    """Результат бэктеста"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    avg_profit: float
    avg_loss: float
    max_drawdown: float
    trades: List[Trade]


class Backtester:
    """Бэктестер стратегии"""
    
    def __init__(self, min_consensus: float = 60.0):
        self.min_consensus = min_consensus
        self.engine = ConsensusEngine(min_consensus)
    
    def run_scenario(self, scenario: TestScenario) -> List[Trade]:
        """
        Прогоняем один сценарий
        
        Returns:
            Список сделок
        """
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📊 СЦЕНАРИЙ: {scenario.name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   {scenario.description}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        trades = []
        
        # Конвертируем позиции в формат для consensus engine
        from scraper import Trader, Position
        
        traders = []
        positions = {}
        
        for mock_trader in scenario.traders:
            trader = Trader(
                encrypted_uid=mock_trader.encrypted_uid,
                nick_name=mock_trader.nick_name,
                rank=mock_trader.rank,
                roi=mock_trader.roi,
                win_rate=mock_trader.win_rate,
                pnl=0,
                following_count=0,
                trade_period_days=30
            )
            traders.append(trader)
            
            # Конвертируем позиции
            trader_positions = []
            for mock_pos in scenario.positions.get(mock_trader.encrypted_uid, []):
                pos = Position(
                    symbol=mock_pos.symbol,
                    side=mock_pos.side,
                    entry_price=mock_pos.entry_price,
                    mark_price=mock_pos.exit_price,
                    pnl=mock_pos.pnl,
                    roe=0,
                    leverage=1,
                    update_time=0
                )
                trader_positions.append(pos)
            
            if trader_positions:
                positions[mock_trader.encrypted_uid] = trader_positions
        
        # Рассчитываем консенсус
        consensus_list = self.engine.calculate_consensus(
            traders, positions, tracked_symbols=None
        )
        
        # Показываем консенсус
        self.engine.print_consensus(consensus_list)
        
        # Создаём сделки на основе сигналов
        for cons in consensus_list:
            # Ищем позиции по этой монете
            symbol_positions = []
            for uid, pos_list in positions.items():
                for pos in pos_list:
                    if pos.symbol == cons.symbol:
                        symbol_positions.append(pos)
            
            if not symbol_positions:
                continue
            
            # Берём среднюю цену входа и выхода
            avg_entry = sum(p.entry_price for p in symbol_positions) / len(symbol_positions)
            avg_exit = sum(p.mark_price for p in symbol_positions) / len(symbol_positions)
            
            # Определяем направление сделки по консенсусу
            if cons.signal in ["STRONG_BUY", "BUY"]:
                side = "LONG"
                # Если цена выросла — профит
                pnl = avg_exit - avg_entry
                pnl_pct = ((avg_exit - avg_entry) / avg_entry) * 100
            elif cons.signal in ["STRONG_SELL", "SELL"]:
                side = "SHORT"
                # Если цена упала — профит (short)
                pnl = avg_entry - avg_exit
                pnl_pct = ((avg_entry - avg_exit) / avg_entry) * 100
            else:
                # Нет сигнала — не торгуем
                continue
            
            trade = Trade(
                symbol=cons.symbol,
                side=side,
                entry_price=avg_entry,
                exit_price=avg_exit,
                entry_time=scenario.date,
                exit_time=scenario.date,
                pnl=pnl,
                pnl_percent=pnl_pct,
                signal=cons.signal
            )
            trades.append(trade)
            
            # Показываем сделку
            emoji = "🟢" if pnl > 0 else "🔴"
            print(f"{emoji} {trade.symbol} {trade.side}: ${trade.pnl:+.2f} ({trade.pnl_percent:+.2f}%)")
        
        return trades
    
    def run_all_scenarios(self) -> BacktestResult:
        """Прогоняем все сценарии"""
        scenarios = get_all_scenarios()
        all_trades = []
        
        for scenario in scenarios:
            trades = self.run_scenario(scenario)
            all_trades.extend(trades)
        
        # Рассчитываем метрики
        return self._calculate_metrics(all_trades)
    
    def _calculate_metrics(self, trades: List[Trade]) -> BacktestResult:
        """Рассчитывает метрики бэктеста"""
        if not trades:
            return BacktestResult(0, 0, 0, 0, 0, 0, 0, 0, [])
        
        winning = [t for t in trades if t.pnl > 0]
        losing = [t for t in trades if t.pnl <= 0]
        
        total_pnl = sum(t.pnl for t in trades)
        
        avg_profit = sum(t.pnl for t in winning) / len(winning) if winning else 0
        avg_loss = sum(t.pnl for t in losing) / len(losing) if losing else 0
        
        # Расчёт макс просадки (упрощённый)
        max_dd = 0
        peak = 0
        for t in trades:
            if t.pnl > 0:
                peak += t.pnl
            else:
                dd = abs(t.pnl)
                if dd > max_dd:
                    max_dd = dd
        
        return BacktestResult(
            total_trades=len(trades),
            winning_trades=len(winning),
            losing_trades=len(losing),
            win_rate=len(winning) / len(trades) * 100 if trades else 0,
            total_pnl=total_pnl,
            avg_profit=avg_profit,
            avg_loss=avg_loss,
            max_drawdown=max_dd,
            trades=trades
        )
    
    def print_report(self, result: BacktestResult):
        """Печатает финальный отчёт"""
        print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}📈 БЭКТЕСТ РЕЗУЛЬТАТЫ{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}\n")
        
        print(f"📊 Общая статистика:")
        print(f"   Всего сделок: {result.total_trades}")
        print(f"   Прибыльных: {result.winning_trades}")
        print(f"   Убыточных: {result.losing_trades}")
        print(f"   Win Rate: {result.win_rate:.1f}%")
        
        print(f"\n💰 P&L:")
        print(f"   Общий P&L: ${result.total_pnl:+.2f}")
        print(f"   Средний профит: ${result.avg_profit:+.2f}")
        print(f"   Средний убыток: ${result.avg_loss:+.2f}")
        print(f"   Макс просадка: ${result.max_drawdown:.2f}")
        
        # Соотношение прибыли и убытков
        if result.avg_loss != 0:
            rr_ratio = abs(result.avg_profit / result.avg_loss)
            print(f"   Risk/Reward: 1:{rr_ratio:.2f}")
        
        print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}\n")


def main():
    """Главная функция"""
    print(f"{Fore.CYAN}🚀 ЗАПУСК БЭКТЕСТА{Style.RESET_ALL}\n")
    
    backtester = Backtester(min_consensus=60.0)
    result = backtester.run_all_scenarios()
    backtester.print_report(result)
    
    # Рекомендация
    if result.win_rate >= 60 and result.total_pnl > 0:
        print(f"{Fore.GREEN}✅ СТРАТЕГИЯ ПРИБЫЛЬНАЯ! Win Rate {result.win_rate:.1f}%{Style.RESET_ALL}")
    elif result.win_rate >= 50:
        print(f"{Fore.YELLOW}⚠️ СТРАТЕГИЯ НЕЙТРАЛЬНАЯ. Требуется доработка{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}❌ СТРАТЕГИЯ УБЫТОЧНАЯ. Нужно пересмотреть{Style.RESET_ALL}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
