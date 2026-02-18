"""
Consensus Engine
Рассчитывает консенсус трейдеров по каждой монете
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
from collections import defaultdict
from scraper import Trader, Position
from colorama import Fore, Style


@dataclass
class SymbolConsensus:
    """Консенсус по конкретной монете"""
    symbol: str
    long_count: int
    short_count: int
    total_count: int
    long_percent: float
    short_percent: float
    avg_leverage_long: float
    avg_leverage_short: float
    total_long_pnl: float
    total_short_pnl: float
    signal: str  # STRONG_BUY, BUY, NEUTRAL, SELL, STRONG_SELL


class ConsensusEngine:
    """Движок консенсуса"""
    
    def __init__(self, min_consensus_percent: float = 60.0):
        self.min_consensus = min_consensus_percent
    
    def calculate_consensus(
        self,
        traders: List[Trader],
        positions: Dict[str, List[Position]],
        tracked_symbols: List[str] = None
    ) -> List[SymbolConsensus]:
        """
        Рассчитывает консенсус для всех монет
        
        Args:
            traders: Список трейдеров
            positions: Словарь позиций {trader_uid: [positions]}
            tracked_symbols: Какие монеты отслеживать (None = все)
        
        Returns:
            Список консенсусов по монетам
        """
        # Собираем данные по монетам
        symbol_data = defaultdict(lambda: {
            'longs': [],
            'shorts': [],
            'long_pnl': [],
            'short_pnl': [],
            'long_leverage': [],
            'short_leverage': []
        })
        
        # Группируем позиции по монетам
        for trader_uid, trader_positions in positions.items():
            for pos in trader_positions:
                symbol = pos.symbol
                
                # Фильтруем только нужные монеты
                if tracked_symbols and symbol not in tracked_symbols:
                    continue
                
                if pos.side == "LONG":
                    symbol_data[symbol]['longs'].append(trader_uid)
                    symbol_data[symbol]['long_pnl'].append(pos.pnl)
                    symbol_data[symbol]['long_leverage'].append(pos.leverage)
                else:
                    symbol_data[symbol]['shorts'].append(trader_uid)
                    symbol_data[symbol]['short_pnl'].append(pos.pnl)
                    symbol_data[symbol]['short_leverage'].append(pos.leverage)
        
        # Рассчитываем консенсус для каждой монеты
        consensus_list = []
        
        for symbol, data in symbol_data.items():
            long_count = len(data['longs'])
            short_count = len(data['shorts'])
            total = long_count + short_count
            
            if total == 0:
                continue
            
            long_percent = (long_count / total) * 100
            short_percent = (short_count / total) * 100
            
            # Расчёт среднего плеча
            avg_leverage_long = sum(data['long_leverage']) / len(data['long_leverage']) if data['long_leverage'] else 0
            avg_leverage_short = sum(data['short_leverage']) / len(data['short_leverage']) if data['short_leverage'] else 0
            
            # Расчёт общего PNL
            total_long_pnl = sum(data['long_pnl'])
            total_short_pnl = sum(data['short_pnl'])
            
            # Определяем сигнал
            signal = self._get_signal(long_percent, short_percent)
            
            consensus = SymbolConsensus(
                symbol=symbol,
                long_count=long_count,
                short_count=short_count,
                total_count=total,
                long_percent=long_percent,
                short_percent=short_percent,
                avg_leverage_long=avg_leverage_long,
                avg_leverage_short=avg_leverage_short,
                total_long_pnl=total_long_pnl,
                total_short_pnl=total_short_pnl,
                signal=signal
            )
            consensus_list.append(consensus)
        
        # Сортируем по общему числу трейдеров (популярность)
        consensus_list.sort(key=lambda x: x.total_count, reverse=True)
        
        return consensus_list
    
    def _get_signal(self, long_percent: float, short_percent: float) -> str:
        """
        Определяет сигнал на основе процентов
        
        Returns:
            STRONG_BUY, BUY, NEUTRAL, SELL, STRONG_SELL
        """
        if long_percent >= 70:
            return "STRONG_BUY"
        elif long_percent >= self.min_consensus:
            return "BUY"
        elif short_percent >= 70:
            return "STRONG_SELL"
        elif short_percent >= self.min_consensus:
            return "SELL"
        else:
            return "NEUTRAL"
    
    def get_strong_signals(self, consensus_list: List[SymbolConsensus]) -> List[SymbolConsensus]:
        """Возвращает только сильные сигналы (BUY/SELL)"""
        return [c for c in consensus_list if c.signal in ["STRONG_BUY", "BUY", "STRONG_SELL", "SELL"]]
    
    def format_consensus_report(self, consensus_list: List[SymbolConsensus]) -> str:
        """Форматирует отчёт о консенсусе для Telegram"""
        if not consensus_list:
            return "📊 Нет данных о позициях"
        
        lines = ["📊 *BINANCE CONSENSUS REPORT*", ""]
        
        strong_signals = self.get_strong_signals(consensus_list)
        
        if strong_signals:
            lines.append("🚨 *СИГНАЛЫ:*")
            lines.append("")
            
            for c in strong_signals[:5]:  # Топ-5 сигналов
                if c.signal in ["STRONG_BUY", "BUY"]:
                    emoji = "🟢"
                    direction = "LONG"
                else:
                    emoji = "🔴"
                    direction = "SHORT"
                
                lines.append(
                    f"{emoji} *{c.symbol}* — {c.signal}\n"
                    f"▫️ {direction}: {c.long_percent if direction == 'LONG' else c.short_percent:.1f}%\n"
                    f"▫️ Трейдеров: {c.total_count} ({c.long_count} LONG / {c.short_count} SHORT)"
                )
                lines.append("")
        else:
            lines.append("⚠️ Нет чёткого консенсуса (минимум 60% требуется)")
            lines.append("")
        
        # Топ-3 по активности
        lines.append("📈 *Самые обсуждаемые:*")
        lines.append("")
        for c in consensus_list[:3]:
            lines.append(
                f"▫️ {c.symbol}: {c.long_percent:.1f}% LONG ({c.total_count} трейдеров)"
            )
        
        return "\n".join(lines)
    
    def print_consensus(self, consensus_list: List[SymbolConsensus]):
        """Печатает консенсус в консоль"""
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📊 CONSENSUS REPORT{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
        
        for c in consensus_list[:10]:
            if c.signal == "STRONG_BUY":
                color = Fore.GREEN
                symbol = "🟢"
            elif c.signal == "BUY":
                color = Fore.LIGHTGREEN_EX
                symbol = "🟩"
            elif c.signal == "STRONG_SELL":
                color = Fore.RED
                symbol = "🔴"
            elif c.signal == "SELL":
                color = Fore.LIGHTRED_EX
                symbol = "🟥"
            else:
                color = Fore.WHITE
                symbol = "⚪"
            
            print(f"{color}{symbol} {c.symbol:10} {c.signal:12}{Style.RESET_ALL}")
            print(f"   LONG: {c.long_percent:5.1f}% ({c.long_count})")
            print(f"   SHORT: {c.short_percent:5.1f}% ({c.short_count})")
            print()


if __name__ == "__main__":
    # Тест
    from scraper import Trader, Position
    
    # Тестовые данные
    traders = [
        Trader("uid1", "Trader1", 1, 150.0, 60.0, 10000.0, 100, 90),
        Trader("uid2", "Trader2", 2, 120.0, 55.0, 8000.0, 80, 60),
    ]
    
    positions = {
        "uid1": [
            Position("BTCUSDT", "LONG", 40000, 41000, 1000, 2.5, 1234567890),
            Position("ETHUSDT", "LONG", 2500, 2600, 500, 2.0, 1234567890),
        ],
        "uid2": [
            Position("BTCUSDT", "LONG", 40500, 41000, 500, 1.5, 1234567890),
            Position("SOLUSDT", "SHORT", 100, 95, 200, 2.0, 1234567890),
        ],
    }
    
    engine = ConsensusEngine(min_consensus_percent=60.0)
    consensus = engine.calculate_consensus(traders, positions)
    
    engine.print_consensus(consensus)
