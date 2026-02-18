#!/usr/bin/env python3
"""
🏃‍♂️ Главный скрипт Binance Consensus Trader
Оркестрирует сканирование, расчёт консенсуса и отправку сигналов
"""

import asyncio
import time
import signal
import sys
from datetime import datetime
from colorama import Fore, Style, init

import config
from scraper import BinanceScraper
from consensus import ConsensusEngine
from telegram_bot import ConsensusBot

# Инициализация colorama
init(autoreset=True)


class ConsensusTrader:
    """Главный класс приложения"""
    
    def __init__(self):
        self.scraper = None
        self.engine = None
        self.bot = None
        self.is_running = False
        self.last_update = None
        
        if config.BINANCE_COOKIES:
            self.scraper = BinanceScraper(config.BINANCE_COOKIES)
            self.engine = ConsensusEngine(config.MIN_CONSENSUS_PERCENT)
        
        if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
            self.bot = ConsensusBot(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)
    
    async def run_single_scan(self):
        """Один полный цикл сканирования"""
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🚀 ЗАПУСК СКАНИРОВАНИЯ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
        
        try:
            # 1. Получаем топовых трейдеров
            print(f"{Fore.YELLOW}📊 Получаем топ-{config.TOP_TRADERS_COUNT} трейдеров...{Style.RESET_ALL}")
            traders = self.scraper.get_top_traders(config.TOP_TRADERS_COUNT)
            
            if not traders:
                print(f"{Fore.RED}❌ Не удалось получить список трейдеров{Style.RESET_ALL}")
                return False
            
            print(f"{Fore.GREEN}✅ Получено {len(traders)} трейдеров{Style.RESET_ALL}")
            
            # Показываем топ-5
            print(f"\n{Fore.CYAN}🏆 Топ-5 трейдеров:{Style.RESET_ALL}")
            for i, t in enumerate(traders[:5], 1):
                print(f"   {i}. {t.nick_name} (ROI: {t.roi:.1f}%, WinRate: {t.win_rate:.1f}%)")
            
            # 2. Получаем позиции трейдеров
            print(f"\n{Fore.YELLOW}📈 Получаем позиции...{Style.RESET_ALL}")
            positions = self.scraper.get_all_positions(traders, delay=1.0)
            
            # 3. Рассчитываем консенсус
            print(f"\n{Fore.YELLOW}🧮 Рассчитываем консенсус...{Style.RESET_ALL}")
            consensus_list = self.engine.calculate_consensus(
                traders,
                positions,
                tracked_symbols=config.TRACKED_SYMBOLS
            )
            
            # 4. Показываем в консоли
            self.engine.print_consensus(consensus_list)
            
            # 5. Отправляем в Telegram
            if self.bot and self.bot.is_running:
                report = self.engine.format_consensus_report(consensus_list)
                await self.bot.send_consensus_alert(report)
                
                # Проверяем сильные сигналы
                strong_signals = self.engine.get_strong_signals(consensus_list)
                for sig in strong_signals:
                    if sig.signal in ["STRONG_BUY", "STRONG_SELL"]:
                        # Отправляем отдельный алерт
                        await self.bot.send_strong_signal(
                            sig.symbol,
                            sig.signal,
                            {
                                'long_percent': sig.long_percent,
                                'short_percent': sig.short_percent,
                                'long_count': sig.long_count,
                                'short_count': sig.short_count,
                                'long_pnl': sig.total_long_pnl,
                                'short_pnl': sig.total_short_pnl
                            }
                        )
            
            self.last_update = datetime.now()
            print(f"\n{Fore.GREEN}✅ Сканирование завершено!{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ Ошибка сканирования: {e}{Style.RESET_ALL}")
            import traceback
            traceback.print_exc()
            return False
    
    async def run_watch_mode(self):
        """Режим постоянного мониторинга"""
        print(f"{Fore.GREEN}👀 Запуск режима мониторинга (интервал: {config.UPDATE_INTERVAL_MINUTES} мин){Style.RESET_ALL}")
        
        self.is_running = True
        
        # Обработка Ctrl+C
        def signal_handler(sig, frame):
            print(f"\n{Fore.YELLOW}🛑 Остановка...{Style.RESET_ALL}")
            self.is_running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        while self.is_running:
            # Запускаем сканирование
            await self.run_single_scan()
            
            # Ждём до следующего цикла
            if self.is_running:
                next_run = datetime.now().strftime('%H:%M:%S')
                print(f"\n{Fore.CYAN}😴 Следующее сканирование через {config.UPDATE_INTERVAL_MINUTES} минут...{Style.RESET_ALL}")
                print(f"{Fore.CYAN}   (Нажми Ctrl+C для остановки){Style.RESET_ALL}\n")
                
                # Асинхронный сон с возможностью прерывания
                for _ in range(config.UPDATE_INTERVAL_MINUTES * 60):
                    if not self.is_running:
                        break
                    await asyncio.sleep(1)
        
        print(f"{Fore.GREEN}👋 Мониторинг остановлен{Style.RESET_ALL}")
    
    async def run(self):
        """Главный метод запуска"""
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🐋 BINANCE CONSENSUS TRADER{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
        
        # Проверка конфигурации
        if not config.BINANCE_COOKIES:
            print(f"{Fore.RED}❌ Ошибка: Не указан BINANCE_COOKIES{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}   Смотри README.md как получить cookies{Style.RESET_ALL}")
            return
        
        if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
            print(f"{Fore.YELLOW}⚠️ Предупреждение: Не указаны Telegram настройки{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}   Бот будет работать только в консольном режиме{Style.RESET_ALL}\n")
        
        # Запускаем бота если есть токен
        bot_task = None
        if self.bot:
            await self.bot.start_async()
        
        # Запускаем мониторинг
        try:
            await self.run_watch_mode()
        finally:
            # Останавливаем бота при выходе
            if self.bot:
                await self.bot.stop_async()


def main():
    """Точка входа"""
    trader = ConsensusTrader()
    
    try:
        asyncio.run(trader.run())
    except KeyboardInterrupt:
        print(f"\n{Fore.GREEN}👋 До свидания!{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Критическая ошибка: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
