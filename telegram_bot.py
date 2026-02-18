"""
Telegram Bot для управления и получения сигналов
"""

import asyncio
import logging
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from colorama import Fore, Style

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class ConsensusBot:
    """Telegram бот для консенсус-трейдера"""
    
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.application = Application.builder().token(token).build()
        self.is_running = False
        self.last_consensus = None
        self.last_message_id = None
        
        # Регистрируем команды
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Настройка обработчиков команд"""
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        self.application.add_handler(CommandHandler("status", self.cmd_status))
        self.application.add_handler(CommandHandler("consensus", self.cmd_consensus))
        self.application.add_handler(CommandHandler("top", self.cmd_top))
        self.application.add_handler(CommandHandler("stop", self.cmd_stop))
        
        # Callback для кнопок
        self.application.add_handler(CommandHandler("refresh", self.cmd_refresh))
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        welcome_text = (
            "🐋 *Binance Consensus Trader*\n\n"
            "Я сканирую топовых трейдеров Binance и определяю консенсус.\n\n"
            "*Команды:*\n"
            "📊 /consensus — Текущий консенсус\n"
            "🏆 /top — Топ трейдеров\n"
            "ℹ️ /status — Статус мониторинга\n"
            "🔄 /refresh — Обновить данные\n"
            "❓ /help — Помощь\n\n"
            "🚀 Мониторинг запущен!"
        )
        
        keyboard = [
            [InlineKeyboardButton("📊 Консенсус", callback_data='consensus')],
            [InlineKeyboardButton("🏆 Топ трейдеров", callback_data='top')],
            [InlineKeyboardButton("🔄 Обновить", callback_data='refresh')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        help_text = (
            "*🐋 Binance Consensus Trader — Помощь*\n\n"
            "*Как это работает:*\n"
            "1️⃣ Я сканирую топ-100 трейдеров Binance Futures Leaderboard\n"
            "2️⃣ Собираю их открытые позиции (LONG/SHORT)\n"
            "3️⃣ Считаю консенсус для каждой монеты\n"
            "4️⃣ Если 60%+ трейдеров в одну сторону — шлю сигнал\n\n"
            "*Команды:*\n"
            "• /consensus — Текущая ситуация по всем монетам\n"
            "• /top — Список лучших трейдеров\n"
            "• /status — Проверка работы бота\n"
            "• /refresh — Принудительное обновление\n\n"
            "*Сигналы:*\n"
            "🟢 STRONG_BUY — 70%+ трейдеров LONG\n"
            "🟩 BUY — 60-70% LONG\n"
            "🟥 SELL — 60-70% SHORT\n"
            "🔴 STRONG_SELL — 70%+ SHORT\n\n"
            "⚠️ *Важно:* Это не финансовый совет! Используй как подтверждение."
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /status"""
        status = "🟢 Работает" if self.is_running else "🔴 Остановлен"
        
        status_text = (
            f"*📊 Статус:* {status}\n\n"
            f"📈 Последнее обновление: {self.last_consensus or 'Н/Д'}\n"
            f"⏱ Интервал: 15 минут\n"
            f"🎯 Минимальный консенсус: 60%\n"
            f"👥 Трейдеров в базе: ~100"
        )
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    async def cmd_consensus(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /consensus — показать текущий консенсус"""
        await update.message.reply_text(
            "⏳ Обновляю данные... Это займет 1-2 минуты",
            parse_mode='Markdown'
        )
        # Данные обновятся через основной цикл
    
    async def cmd_top(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /top — показать топ трейдеров"""
        await update.message.reply_text(
            "⏳ Загружаю список топовых трейдеров...",
            parse_mode='Markdown'
        )
        # Данные будут загружены
    
    async def cmd_refresh(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /refresh — принудительное обновление"""
        await update.message.reply_text(
            "🔄 Запускаю принудительное обновление...",
            parse_mode='Markdown'
        )
    
    async def cmd_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /stop"""
        await update.message.reply_text(
            "🛑 Бот остановлен. Используй /start для запуска",
            parse_mode='Markdown'
        )
    
    async def send_consensus_alert(self, consensus_text: str):
        """
        Отправляет сигнал консенсуса в Telegram
        
        Args:
            consensus_text: Текст сигнала
        """
        try:
            keyboard = [
                [InlineKeyboardButton("🔄 Обновить", callback_data='refresh')],
                [InlineKeyboardButton("📊 Подробнее", callback_data='details')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = await self.application.bot.send_message(
                chat_id=self.chat_id,
                text=consensus_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            self.last_message_id = message.message_id
            print(f"{Fore.GREEN}✅ Сигнал отправлен в Telegram{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Ошибка отправки в Telegram: {e}{Style.RESET_ALL}")
    
    async def send_strong_signal(self, symbol: str, signal: str, details: dict):
        """
        Отправляет сильный сигнал (BUY/SELL)
        
        Args:
            symbol: Монета (BTCUSDT)
            signal: STRONG_BUY, BUY, SELL, STRONG_SELL
            details: Детали сигнала
        """
        if signal == "STRONG_BUY":
            emoji = "🚀"
            color = "🟢"
            text = f"*{color} STRONG BUY СИГНАЛ* {emoji}"
        elif signal == "BUY":
            emoji = "📈"
            color = "🟩"
            text = f"*{color} BUY СИГНАЛ* {emoji}"
        elif signal == "STRONG_SELL":
            emoji = "🚨"
            color = "🔴"
            text = f"*{color} STRONG SELL СИГНАЛ* {emoji}"
        else:
            emoji = "📉"
            color = "🟥"
            text = f"*{color} SELL СИГНАЛ* {emoji}"
        
        signal_text = (
            f"{text}\n\n"
            f"💎 *{symbol}*\n\n"
            f"📊 *Консенсус:*\n"
            f"🟢 LONG: {details.get('long_percent', 0):.1f}% ({details.get('long_count', 0)} трейдеров)\n"
            f"🔴 SHORT: {details.get('short_percent', 0):.1f}% ({details.get('short_count', 0)} трейдеров)\n\n"
            f"💰 *Общий PNL:\n"
            f"LONG: ${details.get('long_pnl', 0):,.2f}\n"
            f"SHORT: ${details.get('short_pnl', 0):,.2f}\n\n"
            f"⚠️ *Это не финансовый совет!*"
        )
        
        await self.send_consensus_alert(signal_text)
    
    def run(self):
        """Запускает бота"""
        print(f"{Fore.GREEN}🤖 Telegram бот запущен{Style.RESET_ALL}")
        self.is_running = True
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    async def start_async(self):
        """Асинхронный запуск"""
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        self.is_running = True
        print(f"{Fore.GREEN}🤖 Telegram бот запущен (async){Style.RESET_ALL}")
    
    async def stop_async(self):
        """Асинхронная остановка"""
        self.is_running = False
        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()


if __name__ == "__main__":
    import config
    
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        print(f"{Fore.RED}❌ Укажите TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID в .env{Style.RESET_ALL}")
        exit(1)
    
    bot = ConsensusBot(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)
    bot.run()
