
import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
import asyncio

# Load environment variables from .env file
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Telegram Bot Token from environment variable
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN environment variable not set.")
    exit(1)

# XT.com API Base URL
XT_API_BASE_URL = "https://sapi.xt.com/v4/public"

# User's Telegram Chat ID (This will be set dynamically after the first /start command)
USER_CHAT_ID = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message on /start command."""
    global USER_CHAT_ID
    USER_CHAT_ID = update.effective_chat.id
    await update.message.reply_text(
        'سلام! من ربات نظارت بر صرافی XT.com هستم. هر ساعت اطلاعات بازار را برای شما ارسال خواهم کرد.'
    )
    logger.info(f"Bot started by user {update.effective_user.id}. Chat ID: {USER_CHAT_ID}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message on /help command."""
    await update.message.reply_text('برای شروع، از دستور /start استفاده کنید. من هر ساعت اطلاعات بازار را برای شما ارسال خواهم کرد.')

async def get_all_symbols():
    """Fetches all trading symbols from XT.com."""
    try:
        response = requests.get(f"{XT_API_BASE_URL}/symbol")
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        if data and data.get("rc") == 0 and data.get("result"):
            return data["result"]["symbols"]
        else:
            logger.error(f"Error fetching symbols: {data.get('mc', 'Unknown error')}")
            return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to get_all_symbols failed: {e}")
        return []

async def get_ticker(symbol: str):
    """Fetches ticker information for a given symbol from XT.com."""
    try:
        response = requests.get(f"{XT_API_BASE_URL}/ticker?symbol={symbol}")
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        if data and data.get("rc") == 0 and data.get("result") and data["result"]:
            return data["result"][0] # The API returns a list, we need the first element
        else:
            logger.warning(f"No ticker data for {symbol}: {data.get('mc', 'Unknown error')}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to get_ticker for {symbol} failed: {e}")
        return None

async def get_depth_data(symbol: str, limit: int = 10):
    """Fetches order book depth for a given symbol from XT.com."""
    try:
        response = requests.get(f"{XT_API_BASE_URL}/depth?symbol={symbol}&limit={limit}")
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        if data and data.get("rc") == 0 and data.get("result"):
            return data["result"]
        else:
            logger.warning(f"No depth data for {symbol}: {data.get('mc', 'Unknown error')}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to get_depth_data for {symbol} failed: {e}")
        return None

async def monitor_xt_market(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Monitors the XT.com market for anomalies and sends reports."""
    if not USER_CHAT_ID:
        logger.warning("USER_CHAT_ID is not set. Cannot send market updates.")
        return

    logger.info("Starting market monitoring...")
    message_parts = []

    all_symbols_info = await get_all_symbols()
    if not all_symbols_info:
        await context.bot.send_message(chat_id=USER_CHAT_ID, text="خطا در دریافت لیست جفت ارزها از XT.com.")
        return

    # Filter for ONLINE and openapiEnabled symbols
    active_symbols = [s for s in all_symbols_info if s.get("state") == "ONLINE" and s.get("openapiEnabled") == True]
    
    # Identify "Hidden" or new tokens (e.g., not commonly traded or recently added)
    hidden_tokens = [s["symbol"].upper() for s in all_symbols_info if s.get("state") == "ONLINE" and not s.get("openapiEnabled")]
    logger.info(f"Found {len(active_symbols)} active symbols and {len(hidden_tokens)} hidden symbols.")

    # Example: Check for low liquidity (simplified: small order book or wide spread)
    # and no order book (empty bids/asks)
    low_liquidity_tokens = []
    no_order_book_tokens = []
    wide_spread_tokens = []
    price_discrepancy_tokens = [] # For btc/usdq type discrepancies

    for symbol_info in active_symbols:
        symbol = symbol_info["symbol"]
        ticker = await get_ticker(symbol)
        depth = await get_depth_data(symbol, limit=5) # Get top 5 bids/asks

        if ticker:
            best_bid_price = float(ticker.get("bp", 0)) if ticker.get("bp") else 0
            best_ask_price = float(ticker.get("ap", 0)) if ticker.get("ap") else 0

            if best_bid_price > 0 and best_ask_price > 0:
                spread = (best_ask_price - best_bid_price) / best_bid_price * 100
                if spread > 0.5:  # Example threshold for wide spread (0.5%)
                    link = f"https://www.xt.com/en/trade/{symbol.upper()}"
                    wide_spread_tokens.append(f"[{symbol.upper()}]({link}) (اسپرد: {spread:.2f}%) - خرید: {best_bid_price}, فروش: {best_ask_price}")
            
            # Check for price discrepancies (e.g., BTC/USDQ vs BTC/USDT)
            if "_usdq" in symbol.lower():
                base_coin = symbol.split("_")[0]
                usdt_pair = f"{base_coin}_usdt"
                usdt_ticker = await get_ticker(usdt_pair)
                if usdt_ticker:
                    usdt_price = float(usdt_ticker.get("c", 0))
                    usdq_price = float(ticker.get("c", 0))
                    if usdt_price > 0 and abs(usdq_price - usdt_price) / usdt_price > 0.05: # 5% discrepancy
                        link = f"https://www.xt.com/en/trade/{symbol.upper()}"
                        price_discrepancy_tokens.append(f"[{symbol.upper()}]({link}) ({usdq_price}) vs {usdt_pair.upper()} ({usdt_price})")

        if depth:
            bids = depth.get("bids", [])
            asks = depth.get("asks", [])

            link = f"https://www.xt.com/en/trade/{symbol.upper()}"
            if not bids and not asks:
                no_order_book_tokens.append(f"[{symbol.upper()}]({link})")
            elif len(bids) < 3 or len(asks) < 3: # Simplified low liquidity check
                low_liquidity_tokens.append(f"[{symbol.upper()}]({link})")

    if wide_spread_tokens:
        message_parts.append("\n*اسپردهای شدید (بالاتر از ۰.۵٪):*\n" + "\n".join(wide_spread_tokens))
    if low_liquidity_tokens:
        message_parts.append("\n*توکن‌های با نقدینگی کم (اوردر بوک کم عمق):*\n" + "\n".join(low_liquidity_tokens))
    if no_order_book_tokens:
        message_parts.append("\n*توکن‌های بدون اوردر بوک:*\n" + "\n".join(no_order_book_tokens))
    if price_discrepancy_tokens:
        message_parts.append("\n*اختلاف قیمت شدید (بیش از ۵٪):*\n" + "\n".join(price_discrepancy_tokens))
    
    if hidden_tokens:
        hidden_links = [f"[{s}](https://www.xt.com/en/trade/{s})" for s in hidden_tokens[:20]]
        message_parts.append("\n*توکن‌های مخفی (غیرفعال در API عمومی):*\n" + ", ".join(hidden_links) + (f" (+{len(hidden_tokens)-20} مورد دیگر)" if len(hidden_tokens) > 20 else ""))

    if not message_parts:
        final_message = "هیچ مورد خاصی در بازار XT.com شناسایی نشد."
    else:
        final_message = "*گزارش بازار XT.com: *\n" + "\n".join(message_parts)

    await context.bot.send_message(chat_id=USER_CHAT_ID, text=final_message, parse_mode='Markdown')
    logger.info("Market monitoring report sent.")

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually trigger the market check."""
    global USER_CHAT_ID
    USER_CHAT_ID = update.effective_chat.id
    await update.message.reply_text('در حال بررسی بازار... لطفا کمی صبر کنید.')
    await monitor_xt_market(context)

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("check", check_command))

    # Schedule the monitoring task to run every hour
    job_queue = application.job_queue
    job_queue.run_repeating(monitor_xt_market, interval=3600, first=10) # Run every hour, first run after 10 seconds

    # Run the bot until the user presses Ctrl-C
    logger.info("Bot is polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
