#!/usr/bin/env python3
"""
Telegram Group Management Bot - Working Version
Main application with web interface and bot functionality
"""

import os
import logging
import threading
import asyncio
from flask import Flask

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Flask web interface
app = Flask(__name__)

@app.route('/')
def dashboard():
    bot_token = os.getenv('BOT_TOKEN')
    bot_status = "✅ Active" if bot_token else "❌ Missing BOT_TOKEN"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Telegram Group Management Bot</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .status {{ padding: 10px; border-radius: 5px; margin: 10px 0; }}
            .active {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
            .inactive {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
            .feature {{ background: #e7f3ff; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }}
            .commands {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Telegram Group Management Bot</h1>
            
            <div class="status {'active' if bot_token else 'inactive'}">
                <strong>Bot Status:</strong> {bot_status}
            </div>
            
            <h2>🚀 Advanced Features</h2>
            
            <div class="feature">
                <h3>🛡️ Content Filtering & Spam Protection</h3>
                <p>• Advanced spam detection with flood protection<br>
                • Banned word filtering with regex patterns<br>
                • Media restrictions (file types, sizes)<br>
                • Link and forwarded message control</p>
            </div>
            
            <div class="feature">
                <h3>🔐 Multi-Level Captcha System</h3>
                <p>• Easy: Simple math problems<br>
                • Medium: Pattern recognition<br>
                • Hard: Complex verification challenges<br>
                • Automatic user restriction until verification</p>
            </div>
            
            <div class="feature">
                <h3>📺 Channel Subscription Verification</h3>
                <p>• Require users to subscribe to specific channels<br>
                • Automatic verification with inline buttons<br>
                • Configurable required channels per group<br>
                • Integration with captcha system</p>
            </div>
            
            <div class="feature">
                <h3>📝 External Logging & Transparency</h3>
                <p>• All moderation actions logged to external channels<br>
                • Comprehensive audit trail<br>
                • Configurable log channels per group<br>
                • Real-time transparency reporting</p>
            </div>
            
            <div class="feature">
                <h3>⚠️ Progressive Warning System</h3>
                <p>• Escalating consequences for violations<br>
                • Configurable warning thresholds<br>
                • Automatic temporary restrictions<br>
                • Warning reset capabilities</p>
            </div>
            
            <h2>🎛️ Available Commands</h2>
            <div class="commands">
                <strong>Moderation:</strong> /ban, /mute, /kick, /unban, /info<br>
                <strong>Settings:</strong> /settings, /addword, /removeword, /captcha<br>
                <strong>Channels:</strong> /channels (add/remove/list)<br>
                <strong>Logging:</strong> /setuplog<br>
                <strong>Warnings:</strong> /resetwarnings<br>
                <strong>Help:</strong> /start, /help
            </div>
            
            <h2>📊 System Information</h2>
            <p>✅ Web Interface: Active<br>
            ✅ Storage System: JSON-based with backup<br>
            ✅ Port Configuration: Render.com ready (Port 5000)<br>
            ✅ All Bot Modules: Loaded and Ready</p>
            
            {'<p><strong>⚡ Ready to manage your Telegram groups!</strong></p>' if bot_token else '<p><strong>🔧 Waiting for BOT_TOKEN to activate...</strong></p>'}
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    return {"status": "healthy", "service": "telegram-group-management-bot"}

@app.route('/stats')
def stats():
    return {
        "bot_active": bool(os.getenv('BOT_TOKEN')),
        "features": {
            "content_filtering": True,
            "spam_protection": True,
            "captcha_system": True,
            "channel_verification": True,
            "external_logging": True,
            "warning_system": True
        },
        "deployment": "render_ready"
    }

def run_telegram_bot():
    """Initialize and run the Telegram bot"""
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.warning("BOT_TOKEN not found. Bot functionality disabled.")
        return
    
    try:
        # Import telegram modules only when token is available
        from telegram.ext import Application, CommandHandler, MessageHandler, filters, ChatMemberHandler, CallbackQueryHandler
        from bot.handlers import (
            start_command, help_command, ban_command, mute_command, kick_command,
            unban_command, info_command, settings_command, handle_new_members,
            handle_messages, error_handler, add_banned_word_command, remove_banned_word_command,
            set_captcha_command, manage_channels_command, reset_warnings_command,
            setup_logging_command, handle_callback_query
        )
        
        logger.info("Starting Telegram Group Management Bot...")
        
        # Create the Application
        application = Application.builder().token(bot_token).build()
        
        # Add command handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("ban", ban_command))
        application.add_handler(CommandHandler("mute", mute_command))
        application.add_handler(CommandHandler("kick", kick_command))
        application.add_handler(CommandHandler("unban", unban_command))
        application.add_handler(CommandHandler("info", info_command))
        application.add_handler(CommandHandler("settings", settings_command))
        application.add_handler(CommandHandler("addword", add_banned_word_command))
        application.add_handler(CommandHandler("removeword", remove_banned_word_command))
        application.add_handler(CommandHandler("captcha", set_captcha_command))
        application.add_handler(CommandHandler("channels", manage_channels_command))
        application.add_handler(CommandHandler("resetwarnings", reset_warnings_command))
        application.add_handler(CommandHandler("setuplog", setup_logging_command))
        
        # Add message and member handlers
        application.add_handler(MessageHandler(filters.ALL, handle_messages))
        application.add_handler(ChatMemberHandler(handle_new_members, ChatMemberHandler.CHAT_MEMBER))
        application.add_handler(CallbackQueryHandler(handle_callback_query))
        
        # Add error handler
        application.add_error_handler(error_handler)
        
        # Run the bot
        logger.info("Bot started successfully. Running polling...")
        application.run_polling(allowed_updates=["message", "chat_member", "callback_query"])
        
    except ImportError as e:
        logger.error(f"Telegram import error: {str(e)}")
        logger.warning("Running in web-only mode. Bot functionality disabled.")
    except Exception as e:
        logger.error(f"Bot startup error: {str(e)}")

def main():
    """Main application entry point"""
    logger.info("Starting Telegram Group Management Bot Application...")
    
    # Start Flask web interface
    flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False))
    flask_thread.daemon = True
    flask_thread.start()
    
    # Start Telegram bot in main thread
    run_telegram_bot()

if __name__ == '__main__':
    main()
