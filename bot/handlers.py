"""
Command and message handlers for the Telegram bot
"""

import logging
from datetime import datetime, timedelta
from telegram import Update, ChatMember, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.error import TelegramError

from bot.storage import storage
from bot.spam_detector import spam_detector
from bot.captcha import captcha_manager
from bot.content_filter import content_filter
from bot.subscription_checker import subscription_checker
from bot.external_logger import external_logger
from bot.utils import (
    is_admin, is_bot_admin, extract_user_and_reason, format_user_info,
    parse_duration, format_duration, get_user_from_message, log_action
)
from config import (
    HELP_TEXT, DEFAULT_WELCOME_MESSAGE, DEFAULT_MUTE_DURATION,
    CHECK_SUBSCRIPTION, CAPTCHA_TIMEOUT, MAX_WARNINGS, MUTE_DURATIONS
)

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    chat = update.effective_chat
    
    if chat.type == 'private':
        welcome_text = f"""
🤖 **Welcome to Group Management Bot!**

Hello {user.first_name}! I'm a comprehensive group management bot designed to help you moderate Telegram groups effectively.

**Key Features:**
• Anti-spam protection and flood detection
• User management (ban, mute, kick, unban)
• Welcome messages for new members
• Admin-only moderation commands
• Comprehensive activity logging

To get started, add me to your group and make me an administrator with the necessary permissions.

Use /help to see all available commands.

**Setup Instructions:**
1. Add me to your group
2. Promote me to administrator
3. Give me permissions to delete messages, ban users, etc.
4. Use /settings to configure group-specific options

Ready to make your group management easier! 🚀
        """
        await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)
    else:
        # In group
        await update.message.reply_text(
            f"👋 Hello! I'm ready to help manage this group. Use /help to see available commands.",
            parse_mode=ParseMode.MARKDOWN
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.MARKDOWN)

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ban command"""
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if command is used in a group
    if chat.type == 'private':
        await update.message.reply_text("❌ This command can only be used in groups.")
        return
    
    # Check if user is admin
    if not await is_admin(context, chat.id, user.id):
        await update.message.reply_text("❌ Only administrators can use this command.")
        return
    
    # Check if bot has admin privileges
    if not await is_bot_admin(context, chat.id):
        await update.message.reply_text("❌ I need administrator privileges to ban users.")
        return
    
    # Extract username and reason
    username, reason = extract_user_and_reason(context.args)
    
    if not username:
        await update.message.reply_text(
            "❌ Please specify a user to ban.\n"
            "Usage: `/ban @username [reason]` or `/ban user_id [reason]`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        # Get target user
        target_user = await get_user_from_message(context, chat.id, username)
        if not target_user:
            await update.message.reply_text(f"❌ User {username} not found.")
            return
        
        # Check if target is admin
        if await is_admin(context, chat.id, target_user.id):
            await update.message.reply_text("❌ Cannot ban administrators.")
            return
        
        # Ban the user
        await context.bot.ban_chat_member(chat.id, target_user.id)
        
        # Log the action
        storage.log_action(chat.id, user.id, "ban", target_user.id, reason)
        log_action("ban", user, target_user, chat.id, reason)
        
        success_message = f"✅ User {target_user.full_name} has been banned."
        if reason != "No reason provided":
            success_message += f"\n📝 Reason: {reason}"
        
        await update.message.reply_text(success_message)
        
    except TelegramError as e:
        logger.error(f"Error banning user: {e}")
        await update.message.reply_text(f"❌ Failed to ban user: {str(e)}")

async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /mute command"""
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if command is used in a group
    if chat.type == 'private':
        await update.message.reply_text("❌ This command can only be used in groups.")
        return
    
    # Check if user is admin
    if not await is_admin(context, chat.id, user.id):
        await update.message.reply_text("❌ Only administrators can use this command.")
        return
    
    # Check if bot has admin privileges
    if not await is_bot_admin(context, chat.id):
        await update.message.reply_text("❌ I need administrator privileges to mute users.")
        return
    
    # Parse arguments
    if not context.args:
        await update.message.reply_text(
            "❌ Please specify a user to mute.\n"
            "Usage: `/mute @username [duration] [reason]`\n"
            "Duration examples: 5m, 1h, 2d",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    username = context.args[0]
    duration_str = context.args[1] if len(context.args) > 1 else ""
    reason = " ".join(context.args[2:]) if len(context.args) > 2 else "No reason provided"
    
    # If second argument doesn't look like duration, treat it as reason
    if duration_str and not any(c in duration_str for c in 'smhd') and not duration_str.isdigit():
        reason = " ".join(context.args[1:])
        duration_str = ""
    
    duration_seconds = parse_duration(duration_str) if duration_str else DEFAULT_MUTE_DURATION
    
    try:
        # Remove @ if present
        if username.startswith('@'):
            username = username[1:]
        
        # Get target user
        target_user = await get_user_from_message(context, chat.id, username)
        if not target_user:
            await update.message.reply_text(f"❌ User {username} not found.")
            return
        
        # Check if target is admin
        if await is_admin(context, chat.id, target_user.id):
            await update.message.reply_text("❌ Cannot mute administrators.")
            return
        
        # Calculate mute until time
        mute_until = datetime.now() + timedelta(seconds=duration_seconds)
        
        # Mute the user
        await context.bot.restrict_chat_member(
            chat.id,
            target_user.id,
            permissions=context.bot.get_chat_permissions(chat.id),
            until_date=mute_until
        )
        
        # Log the action
        storage.log_action(chat.id, user.id, "mute", target_user.id, f"{reason} ({format_duration(duration_seconds)})")
        log_action("mute", user, target_user, chat.id, reason)
        
        success_message = f"🔇 User {target_user.full_name} has been muted for {format_duration(duration_seconds)}."
        if reason != "No reason provided":
            success_message += f"\n📝 Reason: {reason}"
        
        await update.message.reply_text(success_message)
        
    except TelegramError as e:
        logger.error(f"Error muting user: {e}")
        await update.message.reply_text(f"❌ Failed to mute user: {str(e)}")

async def kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /kick command"""
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if command is used in a group
    if chat.type == 'private':
        await update.message.reply_text("❌ This command can only be used in groups.")
        return
    
    # Check if user is admin
    if not await is_admin(context, chat.id, user.id):
        await update.message.reply_text("❌ Only administrators can use this command.")
        return
    
    # Check if bot has admin privileges
    if not await is_bot_admin(context, chat.id):
        await update.message.reply_text("❌ I need administrator privileges to kick users.")
        return
    
    # Extract username and reason
    username, reason = extract_user_and_reason(context.args)
    
    if not username:
        await update.message.reply_text(
            "❌ Please specify a user to kick.\n"
            "Usage: `/kick @username [reason]` or `/kick user_id [reason]`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        # Get target user
        target_user = await get_user_from_message(context, chat.id, username)
        if not target_user:
            await update.message.reply_text(f"❌ User {username} not found.")
            return
        
        # Check if target is admin
        if await is_admin(context, chat.id, target_user.id):
            await update.message.reply_text("❌ Cannot kick administrators.")
            return
        
        # Kick the user (ban then unban to allow rejoin)
        await context.bot.ban_chat_member(chat.id, target_user.id)
        await context.bot.unban_chat_member(chat.id, target_user.id)
        
        # Log the action
        storage.log_action(chat.id, user.id, "kick", target_user.id, reason)
        log_action("kick", user, target_user, chat.id, reason)
        
        success_message = f"👋 User {target_user.full_name} has been kicked (can rejoin)."
        if reason != "No reason provided":
            success_message += f"\n📝 Reason: {reason}"
        
        await update.message.reply_text(success_message)
        
    except TelegramError as e:
        logger.error(f"Error kicking user: {e}")
        await update.message.reply_text(f"❌ Failed to kick user: {str(e)}")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unban command"""
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if command is used in a group
    if chat.type == 'private':
        await update.message.reply_text("❌ This command can only be used in groups.")
        return
    
    # Check if user is admin
    if not await is_admin(context, chat.id, user.id):
        await update.message.reply_text("❌ Only administrators can use this command.")
        return
    
    # Check if bot has admin privileges
    if not await is_bot_admin(context, chat.id):
        await update.message.reply_text("❌ I need administrator privileges to unban users.")
        return
    
    # Extract username and reason
    username, reason = extract_user_and_reason(context.args)
    
    if not username:
        await update.message.reply_text(
            "❌ Please specify a user to unban.\n"
            "Usage: `/unban @username` or `/unban user_id`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        # Parse user ID or username
        try:
            user_id = int(username)
        except ValueError:
            await update.message.reply_text("❌ Please provide a valid user ID for unbanning.")
            return
        
        # Unban the user
        await context.bot.unban_chat_member(chat.id, user_id)
        
        # Log the action
        storage.log_action(chat.id, user.id, "unban", user_id, reason)
        logger.info(f"User {user.id} unbanned user {user_id} in chat {chat.id}")
        
        success_message = f"✅ User ID {user_id} has been unbanned."
        if reason != "No reason provided":
            success_message += f"\n📝 Reason: {reason}"
        
        await update.message.reply_text(success_message)
        
    except TelegramError as e:
        logger.error(f"Error unbanning user: {e}")
        await update.message.reply_text(f"❌ Failed to unban user: {str(e)}")

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /info command"""
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if command is used in a group
    if chat.type == 'private':
        await update.message.reply_text("❌ This command can only be used in groups.")
        return
    
    # Check if user is admin
    if not await is_admin(context, chat.id, user.id):
        await update.message.reply_text("❌ Only administrators can use this command.")
        return
    
    # Check if reply to message or username provided
    target_user = None
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    elif context.args:
        username = context.args[0]
        target_user = await get_user_from_message(context, chat.id, username)
    
    if not target_user:
        await update.message.reply_text(
            "❌ Please reply to a user's message or specify a username.\n"
            "Usage: `/info @username` or reply to a message with `/info`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        # Get chat member info
        member = await context.bot.get_chat_member(chat.id, target_user.id)
        
        # Format user information
        info_text = format_user_info(target_user, member)
        
        # Add spam data if available
        spam_data = storage.get_spam_data(target_user.id, chat.id)
        if spam_data.get("warnings", 0) > 0:
            info_text += f"\n⚠️ Warnings: {spam_data['warnings']}"
        
        await update.message.reply_text(info_text, parse_mode=ParseMode.MARKDOWN)
        
    except TelegramError as e:
        logger.error(f"Error getting user info: {e}")
        await update.message.reply_text(f"❌ Failed to get user information: {str(e)}")

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settings command"""
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if command is used in a group
    if chat.type == 'private':
        await update.message.reply_text("❌ This command can only be used in groups.")
        return
    
    # Check if user is admin
    if not await is_admin(context, chat.id, user.id):
        await update.message.reply_text("❌ Only administrators can use this command.")
        return
    
    group_data = storage.get_group_data(chat.id)
    settings = group_data.get("settings", {})
    
    # Create inline keyboard for settings
    keyboard = [
        [
            InlineKeyboardButton(
                f"Anti-spam: {'✅' if settings.get('anti_spam_enabled', True) else '❌'}",
                callback_data=f"toggle_antispam_{chat.id}"
            )
        ],
        [
            InlineKeyboardButton(
                f"Welcome messages: {'✅' if settings.get('welcome_enabled', True) else '❌'}",
                callback_data=f"toggle_welcome_{chat.id}"
            )
        ],
        [
            InlineKeyboardButton(
                f"Flood protection: {'✅' if settings.get('flood_protection', True) else '❌'}",
                callback_data=f"toggle_flood_{chat.id}"
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    settings_text = f"""
⚙️ **Group Settings for {chat.title}**

Current configuration:
• Anti-spam protection: {'Enabled' if settings.get('anti_spam_enabled', True) else 'Disabled'}
• Welcome messages: {'Enabled' if settings.get('welcome_enabled', True) else 'Disabled'}
• Flood protection: {'Enabled' if settings.get('flood_protection', True) else 'Disabled'}

Click the buttons below to toggle settings:
    """
    
    await update.message.reply_text(
        settings_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new members joining the group"""
    chat = update.effective_chat
    
    # Only process in groups
    if chat.type == 'private':
        return
    
    # Check if welcome messages are enabled
    group_data = storage.get_group_data(chat.id)
    if not group_data.get("settings", {}).get("welcome_enabled", True):
        return
    
    # Process new members
    for member_update in update.chat_member:
        if (member_update.new_chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED] and
            member_update.old_chat_member.status == ChatMemberStatus.LEFT):
            
            new_user = member_update.new_chat_member.user
            
            # Skip bots
            if new_user.is_bot:
                continue
            
            # Get welcome message
            welcome_msg = group_data.get("welcome_message") or DEFAULT_WELCOME_MESSAGE
            
            # Format welcome message
            formatted_msg = welcome_msg.format(
                group_name=chat.title,
                user_name=new_user.first_name,
                user_mention=f"@{new_user.username}" if new_user.username else new_user.first_name
            )
            
            try:
                await context.bot.send_message(
                    chat.id,
                    formatted_msg,
                    parse_mode=ParseMode.MARKDOWN
                )
                logger.info(f"Welcome message sent for user {new_user.id} in group {chat.id}")
            except TelegramError as e:
                logger.error(f"Error sending welcome message: {e}")

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages for spam detection"""
    chat = update.effective_chat
    user = update.effective_user
    message = update.message
    
    # Only process in groups, and handle all message types (not just text)
    if chat.type == 'private':
        return
    
    # Skip messages from admins
    if await is_admin(context, chat.id, user.id):
        return
    
    # Check if anti-spam is enabled
    group_data = storage.get_group_data(chat.id)
    if not group_data.get("settings", {}).get("anti_spam_enabled", True):
        return
    
    # Check for spam (now includes advanced content filtering)
    spam_result = await spam_detector.check_message(user.id, chat.id, message.text or "", message)
    
    if spam_result["is_spam"]:
        logger.info(f"Spam detected from user {user.id} in group {chat.id}: {spam_result['reasons']}")
        
        try:
            # Delete the message
            await message.delete()
            
            # Take action based on spam type
            action = spam_result.get("action_recommended", "warn")
            
            if action == "mute":
                # Mute for flooding
                await context.bot.restrict_chat_member(
                    chat.id,
                    user.id,
                    permissions=context.bot.get_chat_permissions(chat.id),
                    until_date=datetime.now() + timedelta(minutes=5)
                )
                
                await context.bot.send_message(
                    chat.id,
                    f"🔇 {user.first_name} has been muted for 5 minutes due to flooding."
                )
                
            elif action == "warn":
                # Increment warnings
                warnings = spam_detector.increment_warnings(user.id, chat.id)
                
                await context.bot.send_message(
                    chat.id,
                    f"⚠️ {user.first_name} received a warning for spam. "
                    f"Total warnings: {warnings}/3"
                )
                
                # Ban if too many warnings
                if warnings >= 3:
                    await context.bot.ban_chat_member(chat.id, user.id)
                    await context.bot.send_message(
                        chat.id,
                        f"🔨 {user.first_name} has been banned for repeated spam violations."
                    )
            
            # Log the action
            storage.log_action(
                chat.id, 
                context.bot.id, 
                f"spam_detection_{action}", 
                user.id, 
                f"Reasons: {', '.join(spam_result['reasons'])}"
            )
            
            # Log to external channel
            await external_logger.log_spam_detection(
                user, chat, message.text or "", 
                spam_result['reasons'], action, context
            )
            
        except TelegramError as e:
            logger.error(f"Error handling spam message: {e}")

async def add_banned_word_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a banned word to the group"""
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type == 'private':
        await update.message.reply_text("❌ This command can only be used in groups.")
        return
    
    if not await is_admin(context, chat.id, user.id):
        await update.message.reply_text("❌ Only administrators can use this command.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Please specify a word to ban.\n"
            "Usage: `/addword <word or phrase>`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    word = " ".join(context.args).lower()
    group_data = storage.get_group_data(chat.id)
    banned_words = group_data.get("banned_words", [])
    
    if word not in banned_words:
        banned_words.append(word)
        group_data["banned_words"] = banned_words
        storage.save_group_data(chat.id, group_data)
        
        await update.message.reply_text(f"✅ Added '{word}' to banned words list.")
        logger.info(f"Admin {user.id} added banned word '{word}' in group {chat.id}")
    else:
        await update.message.reply_text(f"⚠️ '{word}' is already in the banned words list.")

async def remove_banned_word_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove a banned word from the group"""
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type == 'private':
        await update.message.reply_text("❌ This command can only be used in groups.")
        return
    
    if not await is_admin(context, chat.id, user.id):
        await update.message.reply_text("❌ Only administrators can use this command.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Please specify a word to remove.\n"
            "Usage: `/removeword <word or phrase>`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    word = " ".join(context.args).lower()
    group_data = storage.get_group_data(chat.id)
    banned_words = group_data.get("banned_words", [])
    
    if word in banned_words:
        banned_words.remove(word)
        group_data["banned_words"] = banned_words
        storage.save_group_data(chat.id, group_data)
        
        await update.message.reply_text(f"✅ Removed '{word}' from banned words list.")
        logger.info(f"Admin {user.id} removed banned word '{word}' in group {chat.id}")
    else:
        await update.message.reply_text(f"⚠️ '{word}' is not in the banned words list.")

async def set_captcha_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enable/disable captcha for new members"""
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type == 'private':
        await update.message.reply_text("❌ This command can only be used in groups.")
        return
    
    if not await is_admin(context, chat.id, user.id):
        await update.message.reply_text("❌ Only administrators can use this command.")
        return
    
    if not context.args:
        # Show current status
        group_data = storage.get_group_data(chat.id)
        captcha_enabled = group_data.get("settings", {}).get("captcha_enabled", False)
        status = "enabled" if captcha_enabled else "disabled"
        
        await update.message.reply_text(
            f"🔐 **Captcha Status:** {status}\n\n"
            f"Usage: `/captcha on|off`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    setting = context.args[0].lower()
    group_data = storage.get_group_data(chat.id)
    
    if setting in ['on', 'enable', 'true']:
        group_data.setdefault("settings", {})["captcha_enabled"] = True
        storage.save_group_data(chat.id, group_data)
        await update.message.reply_text("✅ Captcha verification enabled for new members.")
    elif setting in ['off', 'disable', 'false']:
        group_data.setdefault("settings", {})["captcha_enabled"] = False
        storage.save_group_data(chat.id, group_data)
        await update.message.reply_text("❌ Captcha verification disabled.")
    else:
        await update.message.reply_text("❌ Invalid option. Use: on, off")

async def manage_channels_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage required channels for the group"""
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type == 'private':
        await update.message.reply_text("❌ This command can only be used in groups.")
        return
    
    if not await is_admin(context, chat.id, user.id):
        await update.message.reply_text("❌ Only administrators can use this command.")
        return
    
    if not context.args:
        # Show current channels
        channels = subscription_checker.get_required_channels(chat.id)
        if channels:
            channel_list = "\n".join([f"• @{channel}" for channel in channels])
            await update.message.reply_text(
                f"📢 **Required Channels:**\n{channel_list}\n\n"
                f"Usage: `/channels add|remove @channel`",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                "📢 No required channels set.\n\n"
                "Usage: `/channels add|remove @channel`",
                parse_mode=ParseMode.MARKDOWN
            )
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Invalid usage.\n"
            "Usage: `/channels add|remove @channel`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    action = context.args[0].lower()
    channel = context.args[1].lstrip('@')
    
    if action == 'add':
        subscription_checker.add_required_channel(chat.id, channel)
        await update.message.reply_text(f"✅ Added @{channel} to required channels.")
    elif action == 'remove':
        subscription_checker.remove_required_channel(chat.id, channel)
        await update.message.reply_text(f"✅ Removed @{channel} from required channels.")
    else:
        await update.message.reply_text("❌ Invalid action. Use 'add' or 'remove'.")

async def reset_warnings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset warnings for a user"""
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type == 'private':
        await update.message.reply_text("❌ This command can only be used in groups.")
        return
    
    if not await is_admin(context, chat.id, user.id):
        await update.message.reply_text("❌ Only administrators can use this command.")
        return
    
    # Check if reply to message or username provided
    target_user = None
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    elif context.args:
        username = context.args[0]
        target_user = await get_user_from_message(context, chat.id, username)
    
    if not target_user:
        await update.message.reply_text(
            "❌ Please reply to a user's message or specify a username.\n"
            "Usage: `/resetwarnings @username` or reply to a message",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    spam_detector.reset_warnings(target_user.id, chat.id)
    await update.message.reply_text(
        f"✅ Warnings reset for {target_user.full_name}."
    )
    
    # Log the action
    storage.log_action(chat.id, user.id, "reset_warnings", target_user.id, "Warnings cleared by admin")

async def setup_logging_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Setup external logging channel"""
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type == 'private':
        await update.message.reply_text("❌ This command can only be used in groups.")
        return
    
    if not await is_admin(context, chat.id, user.id):
        await update.message.reply_text("❌ Only administrators can use this command.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📊 **External Logging Setup**\n\n"
            "To enable external logging:\n"
            "1. Create a channel for logs\n"
            "2. Add this bot as admin to the channel\n"
            "3. Use `/setuplog @channel_username`\n\n"
            "To disable: `/setuplog off`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    setting = context.args[0].lower()
    group_data = storage.get_group_data(chat.id)
    
    if setting == 'off':
        group_data.pop("log_channel", None)
        storage.save_group_data(chat.id, group_data)
        await update.message.reply_text("❌ External logging disabled.")
    else:
        channel = setting.lstrip('@')
        group_data["log_channel"] = channel
        storage.save_group_data(chat.id, group_data)
        await update.message.reply_text(f"✅ External logging enabled for @{channel}")

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user = query.from_user
    
    try:
        if data.startswith("captcha_"):
            # Handle captcha responses
            if data.startswith("captcha_text_"):
                user_id = int(data.split("_")[2])
                if user_id == user.id:
                    await query.edit_message_text(
                        "🔐 Please type your answer in the chat."
                    )
            else:
                parts = data.split("_")
                if len(parts) >= 3:
                    user_id = int(parts[1])
                    answer = parts[2]
                    
                    if user_id == user.id:
                        success, message = await captcha_manager.verify_captcha(
                            user_id, answer, context
                        )
                        
                        if success:
                            await query.edit_message_text(message)
                            await external_logger.log_captcha_event(
                                user, query.message.chat, "solved", context
                            )
                        else:
                            await query.edit_message_text(message)
        
        elif data.startswith("verify_sub_"):
            # Handle subscription verification
            parts = data.split("_", 3)
            if len(parts) >= 4:
                user_id = int(parts[2])
                channel = parts[3]
                
                if user_id == user.id:
                    success, message = await subscription_checker.verify_subscription_callback(
                        user_id, channel, context
                    )
                    
                    if success:
                        await external_logger.log_subscription_event(
                            user, query.message.chat, "verified", channel, context
                        )
                    else:
                        await external_logger.log_subscription_event(
                            user, query.message.chat, "failed", channel, context
                        )
                    
                    await query.answer(message, show_alert=True)
        
        elif data.startswith("toggle_"):
            # Handle settings toggles
            if not await is_admin(context, query.message.chat.id, user.id):
                await query.answer("❌ Only administrators can change settings.", show_alert=True)
                return
            
            setting_type = data.split("_")[1]
            chat_id = int(data.split("_")[2])
            
            group_data = storage.get_group_data(chat_id)
            settings = group_data.get("settings", {})
            
            if setting_type == "antispam":
                settings["anti_spam_enabled"] = not settings.get("anti_spam_enabled", True)
            elif setting_type == "welcome":
                settings["welcome_enabled"] = not settings.get("welcome_enabled", True)
            elif setting_type == "flood":
                settings["flood_protection"] = not settings.get("flood_protection", True)
            
            group_data["settings"] = settings
            storage.save_group_data(chat_id, group_data)
            
            # Update the settings message by calling settings command
            await settings_command(update, context)
    
    except Exception as e:
        logger.error(f"Error handling callback query: {e}")
        await query.answer("❌ An error occurred processing your request.", show_alert=True)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    # Try to send error message to user if possible
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ An error occurred while processing your request. Please try again later."
            )
        except Exception:
            pass  # Ignore errors when sending error messages
