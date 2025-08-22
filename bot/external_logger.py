"""
External logging system for comprehensive activity monitoring
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from telegram import Update, User, Chat
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from bot.storage import storage
from config import LOG_CHANNEL_ID, ENABLE_EXTERNAL_LOGGING

logger = logging.getLogger(__name__)

class ExternalLogger:
    """Handles comprehensive logging to external channels"""
    
    def __init__(self):
        self.log_channel_id = LOG_CHANNEL_ID
        self.enabled = ENABLE_EXTERNAL_LOGGING and bool(LOG_CHANNEL_ID)
    
    async def log_moderation_action(self, action: str, admin: User, target: Optional[User], 
                                  chat: Chat, reason: str, context: ContextTypes.DEFAULT_TYPE, 
                                  additional_info: str = ""):
        """Log moderation actions to external channel"""
        if not self.enabled:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Format admin info
            admin_info = f"@{admin.username}" if admin.username else f"{admin.full_name} (ID: {admin.id})"
            
            # Format target info
            if target:
                target_info = f"@{target.username}" if target.username else f"{target.full_name} (ID: {target.id})"
            else:
                target_info = "Unknown user"
            
            # Format chat info
            chat_info = f"{chat.title} ({chat.type}, ID: {chat.id})"
            
            log_message = f"""
🔨 **MODERATION ACTION**

**Action:** {action.upper()}
**Admin:** {admin_info}
**Target:** {target_info}
**Chat:** {chat_info}
**Reason:** {reason}
**Time:** {timestamp}
            """
            
            if additional_info:
                log_message += f"\n**Additional Info:** {additional_info}"
            
            await context.bot.send_message(
                chat_id=self.log_channel_id,
                text=log_message,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error logging moderation action: {e}")
    
    async def log_spam_detection(self, user: User, chat: Chat, message_text: str, 
                                spam_reasons: list, action_taken: str, 
                                context: ContextTypes.DEFAULT_TYPE):
        """Log spam detection events"""
        if not self.enabled:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            user_info = f"@{user.username}" if user.username else f"{user.full_name} (ID: {user.id})"
            chat_info = f"{chat.title} (ID: {chat.id})"
            
            # Truncate message for logging
            truncated_message = message_text[:100] + "..." if len(message_text) > 100 else message_text
            
            log_message = f"""
🚨 **SPAM DETECTED**

**User:** {user_info}
**Chat:** {chat_info}
**Reasons:** {', '.join(spam_reasons)}
**Action:** {action_taken.upper()}
**Message:** "{truncated_message}"
**Time:** {timestamp}
            """
            
            await context.bot.send_message(
                chat_id=self.log_channel_id,
                text=log_message,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error logging spam detection: {e}")
    
    async def log_new_member(self, user: User, chat: Chat, context: ContextTypes.DEFAULT_TYPE, 
                           verification_status: str = "pending"):
        """Log new member joins"""
        if not self.enabled:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            user_info = f"@{user.username}" if user.username else f"{user.full_name} (ID: {user.id})"
            chat_info = f"{chat.title} (ID: {chat.id})"
            
            status_emoji = {
                "verified": "✅",
                "pending": "🔄",
                "failed": "❌"
            }.get(verification_status, "❓")
            
            log_message = f"""
👋 **NEW MEMBER**

**User:** {user_info}
**Chat:** {chat_info}
**Status:** {status_emoji} {verification_status.title()}
**Time:** {timestamp}
            """
            
            await context.bot.send_message(
                chat_id=self.log_channel_id,
                text=log_message,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error logging new member: {e}")
    
    async def log_warning_escalation(self, user: User, chat: Chat, warning_count: int, 
                                   action_taken: str, context: ContextTypes.DEFAULT_TYPE):
        """Log warning system escalations"""
        if not self.enabled:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            user_info = f"@{user.username}" if user.username else f"{user.full_name} (ID: {user.id})"
            chat_info = f"{chat.title} (ID: {chat.id})"
            
            log_message = f"""
⚠️ **WARNING ESCALATION**

**User:** {user_info}
**Chat:** {chat_info}
**Warning Count:** {warning_count}
**Action Taken:** {action_taken.upper()}
**Time:** {timestamp}
            """
            
            await context.bot.send_message(
                chat_id=self.log_channel_id,
                text=log_message,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error logging warning escalation: {e}")
    
    async def log_captcha_event(self, user: User, chat: Chat, event_type: str, 
                              context: ContextTypes.DEFAULT_TYPE, details: str = ""):
        """Log captcha-related events"""
        if not self.enabled:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            user_info = f"@{user.username}" if user.username else f"{user.full_name} (ID: {user.id})"
            chat_info = f"{chat.title} (ID: {chat.id})"
            
            event_emoji = {
                "created": "🔐",
                "solved": "✅",
                "failed": "❌",
                "expired": "⏰"
            }.get(event_type, "❓")
            
            log_message = f"""
{event_emoji} **CAPTCHA EVENT**

**Event:** {event_type.upper()}
**User:** {user_info}
**Chat:** {chat_info}
**Time:** {timestamp}
            """
            
            if details:
                log_message += f"\n**Details:** {details}"
            
            await context.bot.send_message(
                chat_id=self.log_channel_id,
                text=log_message,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error logging captcha event: {e}")
    
    async def log_subscription_event(self, user: User, chat: Chat, event_type: str, 
                                   channel: str, context: ContextTypes.DEFAULT_TYPE):
        """Log subscription verification events"""
        if not self.enabled:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            user_info = f"@{user.username}" if user.username else f"{user.full_name} (ID: {user.id})"
            chat_info = f"{chat.title} (ID: {chat.id})"
            
            event_emoji = {
                "required": "📢",
                "verified": "✅",
                "failed": "❌"
            }.get(event_type, "❓")
            
            log_message = f"""
{event_emoji} **SUBSCRIPTION EVENT**

**Event:** {event_type.upper()}
**User:** {user_info}
**Chat:** {chat_info}
**Channel:** @{channel.lstrip('@')}
**Time:** {timestamp}
            """
            
            await context.bot.send_message(
                chat_id=self.log_channel_id,
                text=log_message,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error logging subscription event: {e}")
    
    async def log_content_filter(self, user: User, chat: Chat, violations: list, 
                               action_taken: str, context: ContextTypes.DEFAULT_TYPE):
        """Log content filtering events"""
        if not self.enabled:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            user_info = f"@{user.username}" if user.username else f"{user.full_name} (ID: {user.id})"
            chat_info = f"{chat.title} (ID: {chat.id})"
            
            log_message = f"""
🛡️ **CONTENT FILTERED**

**User:** {user_info}
**Chat:** {chat_info}
**Violations:** {', '.join(violations)}
**Action:** {action_taken.upper()}
**Time:** {timestamp}
            """
            
            await context.bot.send_message(
                chat_id=self.log_channel_id,
                text=log_message,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error logging content filter: {e}")
    
    async def log_system_event(self, event_type: str, chat: Chat, details: str, 
                             context: ContextTypes.DEFAULT_TYPE):
        """Log general system events"""
        if not self.enabled:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            chat_info = f"{chat.title} (ID: {chat.id})" if chat else "System"
            
            log_message = f"""
⚙️ **SYSTEM EVENT**

**Event:** {event_type.upper()}
**Chat:** {chat_info}
**Details:** {details}
**Time:** {timestamp}
            """
            
            await context.bot.send_message(
                chat_id=self.log_channel_id,
                text=log_message,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Error logging system event: {e}")

# Global external logger instance
external_logger = ExternalLogger()