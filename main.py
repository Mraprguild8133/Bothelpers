#!/usr/bin/env python3
"""
Telegram Group Management Bot
Main entry point for the bot application
"""

import os
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ChatMemberHandler, CallbackQueryHandler
from bot.handlers import (
    start_command, help_command, ban_command, mute_command, kick_command, 
    unban_command, info_command, settings_command, handle_new_members,
    handle_messages, error_handler, add_banned_word_command, remove_banned_word_command,
    set_captcha_command, manage_channels_command, reset_warnings_command,
    setup_logging_command, handle_callback_query
)
from config import BOT_TOKEN, LOG_LEVEL

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL.upper()),
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Start the bot"""
    logger.info("Starting Telegram Group Management Bot...")
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("mute", mute_command))
    application.add_handler(CommandHandler("kick", kick_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("settings", settings_command))
    
    # Advanced feature commands
    application.add_handler(CommandHandler("addword", add_banned_word_command))
    application.add_handler(CommandHandler("removeword", remove_banned_word_command))
    application.add_handler(CommandHandler("captcha", set_captcha_command))
    application.add_handler(CommandHandler("channels", manage_channels_command))
    application.add_handler(CommandHandler("resetwarnings", reset_warnings_command))
    application.add_handler(CommandHandler("setuplog", setup_logging_command))
    
    # Member status change handler
    application.add_handler(ChatMemberHandler(handle_new_members, ChatMemberHandler.CHAT_MEMBER))
    
    # Callback query handler for inline keyboards
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Message handler for spam detection (handles all message types)
    application.add_handler(MessageHandler(~filters.COMMAND, handle_messages))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Run the bot
    logger.info("Bot started successfully. Polling for updates...")
    application.run_polling(allowed_updates=["message", "chat_member"])

if __name__ == '__main__':
    main()
