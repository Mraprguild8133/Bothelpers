"""
Utility functions for the bot
"""

import logging
from typing import List, Optional
from telegram import Chat, ChatMember, User
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus

logger = logging.getLogger(__name__)

async def is_admin(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> bool:
    """Check if user is admin in the chat"""
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False

async def is_bot_admin(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> bool:
    """Check if bot has admin privileges in the chat"""
    try:
        bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
        return bot_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception as e:
        logger.error(f"Error checking bot admin status: {e}")
        return False

def extract_user_and_reason(args: List[str]) -> tuple[Optional[str], str]:
    """Extract username/user_id and reason from command arguments"""
    if not args:
        return None, ""
    
    username = args[0]
    reason = " ".join(args[1:]) if len(args) > 1 else "No reason provided"
    
    # Remove @ symbol if present
    if username.startswith('@'):
        username = username[1:]
    
    return username, reason

def format_user_info(user: User, member: ChatMember) -> str:
    """Format user information for display"""
    info_lines = [
        f"👤 **User Information**",
        f"Name: {user.full_name}",
        f"Username: @{user.username}" if user.username else "Username: Not set",
        f"User ID: `{user.id}`",
        f"Status: {member.status}",
    ]
    
    if user.is_bot:
        info_lines.append("Type: Bot")
    else:
        info_lines.append("Type: User")
    
    if hasattr(member, 'joined_date') and member.joined_date:
        info_lines.append(f"Joined: {member.joined_date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return "\n".join(info_lines)

def parse_duration(duration_str: str) -> int:
    """Parse duration string to seconds (e.g., '5m', '1h', '2d')"""
    if not duration_str:
        return 300  # Default 5 minutes
    
    duration_str = duration_str.lower().strip()
    
    # Extract number and unit
    import re
    match = re.match(r'(\d+)([smhd]?)', duration_str)
    if not match:
        return 300  # Default if parsing fails
    
    value, unit = match.groups()
    value = int(value)
    
    # Convert to seconds
    multipliers = {
        's': 1,        # seconds
        'm': 60,       # minutes
        'h': 3600,     # hours
        'd': 86400,    # days
        '': 60         # default to minutes if no unit
    }
    
    return value * multipliers.get(unit, 60)

def format_duration(seconds: int) -> str:
    """Format seconds into human readable duration"""
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''}"
    else:
        days = seconds // 86400
        return f"{days} day{'s' if days != 1 else ''}"

def escape_markdown(text: str) -> str:
    """Escape markdown special characters"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

async def get_user_from_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, username_or_id: str) -> Optional[User]:
    """Get user object from username or user ID"""
    try:
        # Try to parse as user ID first
        try:
            user_id = int(username_or_id)
            member = await context.bot.get_chat_member(chat_id, user_id)
            return member.user
        except ValueError:
            pass
        
        # Try to get user by username
        # Note: Telegram Bot API doesn't have direct username lookup
        # This would require maintaining a user database or using other methods
        logger.warning(f"Cannot resolve username {username_or_id} - consider using user ID or reply to message")
        return None
        
    except Exception as e:
        logger.error(f"Error getting user {username_or_id}: {e}")
        return None

def log_action(action: str, admin_user: User, target_user: Optional[User], chat_id: int, reason: str = ""):
    """Log moderation actions"""
    target_info = f"@{target_user.username} ({target_user.id})" if target_user else "Unknown user"
    admin_info = f"@{admin_user.username} ({admin_user.id})" if admin_user.username else f"User {admin_user.id}"
    
    log_message = f"{action.upper()}: {admin_info} performed {action} on {target_info} in chat {chat_id}"
    if reason:
        log_message += f" - Reason: {reason}"
    
    logger.info(log_message)
