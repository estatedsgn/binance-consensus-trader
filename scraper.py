"""
Binance Leaderboard Scraper
Получает список топовых трейдеров и их открытые позиции
"""

import requests
import json
import time
from typing import List, Dict, Optional
from dataclasses import dataclass
from colorama import Fore, Style


@dataclass
class Trader:
    """Структура данных трейдера"""
    encrypted_uid: str
    nick_name: str
    rank: int
    roi: float
    win_rate: float
    pnl: float
    following_count: int
    trade_period_days: int


@dataclass
class Position:
    """Структура данных позиции"""
    symbol: str
    side: str  # LONG или SHORT
    entry_price: float
    mark_price: float
    pnl: float
    roe: float
    leverage: int
    update_time: int


class BinanceScraper:
    """Скрейпер Binance Futures Leaderboard"""
    
    def __init__(self, cookies: str):
        self.cookies = cookies
        self.base_url = "https://www.binance.com"
        self.headers = {
            'authority': 'www.binance.com',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'client-type': 'web',
            'content-type': 'application/json',
            'cookie': cookies,
            'lang': 'en',
            'origin': 'https://www.binance.com',
            'referer': 'https://www.binance.com/en/futures-activity/leaderboard',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def get_top_traders(self, limit: int = 100) -> List[Trader]:
        """
        Получает список топовых трейдеров с лидерборда
        
        Args:
            limit: Сколько трейдеров получить (макс ~200)
        
        Returns:
            Список объектов Trader
        """
        url = f"{self.base_url}/bapi/futures/v1/public/future/leaderboard/getLeaderboard"
        
        payload = {
            "isShared": True,
            "isTrader": False,
            "periodType": "ALL",
            "sortType": "ROI",
            "sortOrder": "DESC",
            "limit": limit,
            "offset": 0
        }
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"{Fore.RED}❌ Ошибка получения лидерборда: {response.status_code}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Ответ: {response.text[:500]}{Style.RESET_ALL}")
                return []
            
            data = response.json()
            
            if not data.get('data') or not data['data'].get('list'):
                print(f"{Fore.YELLOW}⚠️ Нет данных в ответе{Style.RESET_ALL}")
                return []
            
            traders = []
            for idx, item in enumerate(data['data']['list'], 1):
                trader = Trader(
                    encrypted_uid=item.get('encryptedUid', ''),
                    nick_name=item.get('nickName', 'Unknown'),
                    rank=idx,
                    roi=float(item.get('roi', 0)),
                    win_rate=float(item.get('winRate', 0)),
                    pnl=float(item.get('pnl', 0)),
                    following_count=int(item.get('followingCount', 0)),
                    trade_period_days=int(item.get('tradePeriodDays', 0))
                )
                traders.append(trader)
            
            print(f"{Fore.GREEN}✅ Получено {len(traders)} трейдеров{Style.RESET_ALL}")
            return traders
            
        except Exception as e:
            print(f"{Fore.RED}❌ Ошибка: {e}{Style.RESET_ALL}")
            return []
    
    def get_trader_positions(self, encrypted_uid: str) -> List[Position]:
        """
        Получает открытые позиции конкретного трейдера
        
        Args:
            encrypted_uid: ID трейдера
        
        Returns:
            Список позиций
        """
        url = f"{self.base_url}/bapi/futures/v1/public/future/leaderboard/getOtherPosition"
        
        payload = {
            "encryptedUid": encrypted_uid,
            "tradeType": "PERPETUAL"
        }
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"{Fore.YELLOW}⚠️ Ошибка получения позиций для {encrypted_uid[:10]}...{Style.RESET_ALL}")
                return []
            
            data = response.json()
            
            if not data.get('data') or not data['data'].get('otherPositionRetList'):
                return []
            
            positions = []
            for pos in data['data']['otherPositionRetList']:
                # Определяем направление (LONG/SHORT)
                amount = float(pos.get('amount', 0))
                side = "LONG" if amount > 0 else "SHORT"
                
                position = Position(
                    symbol=pos.get('symbol', ''),
                    side=side,
                    entry_price=float(pos.get('entryPrice', 0)),
                    mark_price=float(pos.get('markPrice', 0)),
                    pnl=float(pos.get('pnl', 0)),
                    roe=float(pos.get('roe', 0)),
                    leverage=int(pos.get('leverage', 1)),
                    update_time=int(pos.get('updateTime', 0))
                )
                positions.append(position)
            
            return positions
            
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Ошибка получения позиций: {e}{Style.RESET_ALL}")
            return []
    
    def get_all_positions(self, traders: List[Trader], delay: float = 1.0) -> Dict[str, List[Position]]:
        """
        Получает позиции для всех трейдеров с задержкой между запросами
        
        Args:
            traders: Список трейдеров
            delay: Задержка между запросами (сек)
        
        Returns:
            Словарь {trader_uid: [positions]}
        """
        all_positions = {}
        
        print(f"{Fore.CYAN}📊 Получаем позиции для {len(traders)} трейдеров...{Style.RESET_ALL}")
        
        for i, trader in enumerate(traders):
            positions = self.get_trader_positions(trader.encrypted_uid)
            if positions:
                all_positions[trader.encrypted_uid] = positions
                print(f"{Fore.GREEN}  ✓ {trader.nick_name}: {len(positions)} позиций{Style.RESET_ALL}")
            
            # Задержка чтобы не забанили
            if i < len(traders) - 1:
                time.sleep(delay)
        
        print(f"{Fore.GREEN}✅ Получены позиции для {len(all_positions)} трейдеров{Style.RESET_ALL}")
        return all_positions


if __name__ == "__main__":
    # Тест
    import config
    
    if not config.BINANCE_COOKIES:
        print(f"{Fore.RED}❌ Укажите BINANCE_COOKIES в .env{Style.RESET_ALL}")
        exit(1)
    
    scraper = BinanceScraper(config.BINANCE_COOKIES)
    
    # Получаем топ-10 для теста
    traders = scraper.get_top_traders(10)
    
    print(f"\n{Fore.CYAN}👥 Топ-10 трейдеров:{Style.RESET_ALL}")
    for t in traders:
        print(f"  {t.rank}. {t.nick_name} (ROI: {t.roi:.2f}%, WinRate: {t.win_rate:.1f}%)")
    
    # Получаем позиции первого трейдера
    if traders:
        print(f"\n{Fore.CYAN}📈 Позиции {traders[0].nick_name}:{Style.RESET_ALL}")
        positions = scraper.get_trader_positions(traders[0].encrypted_uid)
        for p in positions:
            print(f"  {p.symbol}: {p.side} @ {p.entry_price:.2f} (PNL: {p.pnl:.2f}$)")
