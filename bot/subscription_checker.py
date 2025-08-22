"""
Channel subscription verification system
"""

import logging
from typing import Optional, Dict, Any, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from bot.storage import storage
from config import REQUIRED_CHANNEL, CHECK_SUBSCRIPTION

logger = logging.getLogger(__name__)

class SubscriptionChecker:
    """Manages channel subscription requirements"""
    
    def __init__(self):
        self.pending_verification = {}  # user_id: {chat_id, message_id}
    
    async def check_user_subscription(self, user_id: int, channel_username: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check if user is subscribed to required channel"""
        try:
            # Add @ prefix if not present
            if not channel_username.startswith('@'):
                channel_username = f'@{channel_username}'
            
            # Get user's membership status in the channel
            member = await context.bot.get_chat_member(channel_username, user_id)
            
            # Consider user subscribed if they are member, administrator, or creator
            return member.status in ['member', 'administrator', 'creator']
            
        except TelegramError as e:
            logger.error(f"Error checking subscription for user {user_id} in channel {channel_username}: {e}")
            return False
    
    async def verify_new_member_subscription(self, user_id: int, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Verify subscription for new group member"""
        if not CHECK_SUBSCRIPTION or not REQUIRED_CHANNEL:
            return True  # No subscription required
        
        group_data = storage.get_group_data(chat_id)
        required_channels = group_data.get("required_channels", [])
        
        # Use global setting if no group-specific channels
        if not required_channels and REQUIRED_CHANNEL:
            required_channels = [REQUIRED_CHANNEL]
        
        if not required_channels:
            return True  # No channels to check
        
        # Check subscription to all required channels
        for channel in required_channels:
            is_subscribed = await self.check_user_subscription(user_id, channel, context)
            if not is_subscribed:
                await self.send_subscription_requirement(user_id, chat_id, channel, context)
                return False
        
        return True
    
    async def send_subscription_requirement(self, user_id: int, chat_id: int, channel_username: str, context: ContextTypes.DEFAULT_TYPE):
        """Send subscription requirement message to user"""
        try:
            # Mute user until they subscribe
            await context.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=context.bot.get_chat(chat_id).permissions._replace(
                    can_send_messages=False,
                    can_send_media_messages=False,
                    can_send_other_messages=False
                )
            )
            
            # Create subscription verification message
            channel_link = f"https://t.me/{channel_username.lstrip('@')}"
            
            keyboard = [
                [InlineKeyboardButton("📢 Subscribe to Channel", url=channel_link)],
                [InlineKeyboardButton("✅ I've Subscribed", callback_data=f"verify_sub_{user_id}_{channel_username}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            subscription_text = f"""
🔒 **Subscription Required**

To participate in this group, you must first subscribe to our channel:

**Channel:** @{channel_username.lstrip('@')}

📋 **Instructions:**
1. Click "Subscribe to Channel" below
2. Join the channel
3. Come back and click "I've Subscribed"

⚠️ **Note:** You cannot send messages until you complete this verification.
            """
            
            message = await context.bot.send_message(
                chat_id=chat_id,
                text=subscription_text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            
            # Store verification data
            self.pending_verification[user_id] = {
                "chat_id": chat_id,
                "message_id": message.message_id,
                "channel": channel_username
            }
            
            logger.info(f"Subscription requirement sent to user {user_id} in chat {chat_id}")
            
        except Exception as e:
            logger.error(f"Error sending subscription requirement to user {user_id}: {e}")
    
    async def verify_subscription_callback(self, user_id: int, channel_username: str, context: ContextTypes.DEFAULT_TYPE) -> tuple[bool, str]:
        """Handle subscription verification callback"""
        if user_id not in self.pending_verification:
            return False, "No pending verification found."
        
        verification_data = self.pending_verification[user_id]
        chat_id = verification_data["chat_id"]
        
        # Check if user is now subscribed
        is_subscribed = await self.check_user_subscription(user_id, channel_username, context)
        
        if is_subscribed:
            try:
                # Remove restrictions
                await context.bot.restrict_chat_member(
                    chat_id=chat_id,
                    user_id=user_id,
                    permissions=context.bot.get_chat(chat_id).permissions
                )
                
                # Delete verification message
                try:
                    await context.bot.delete_message(
                        chat_id=chat_id,
                        message_id=verification_data["message_id"]
                    )
                except:
                    pass  # Message might already be deleted
                
                # Send welcome message
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"✅ Thank you for subscribing! You can now participate in the group."
                )
                
                # Remove from pending
                del self.pending_verification[user_id]
                
                logger.info(f"User {user_id} successfully verified subscription in chat {chat_id}")
                return True, "Subscription verified successfully!"
                
            except Exception as e:
                logger.error(f"Error completing subscription verification for user {user_id}: {e}")
                return False, "Error updating permissions."
        else:
            return False, "❌ You are not subscribed to the required channel yet. Please subscribe first."
    
    async def check_periodic_subscription(self, context: ContextTypes.DEFAULT_TYPE):
        """Periodically check if users are still subscribed (optional enforcement)"""
        # This can be called periodically to ensure users remain subscribed
        # Implementation depends on how strict you want the enforcement to be
        pass
    
    def add_required_channel(self, group_id: int, channel_username: str):
        """Add a required channel for a group"""
        group_data = storage.get_group_data(group_id)
        required_channels = group_data.get("required_channels", [])
        
        # Clean channel username
        channel_username = channel_username.lstrip('@')
        
        if channel_username not in required_channels:
            required_channels.append(channel_username)
            group_data["required_channels"] = required_channels
            storage.save_group_data(group_id, group_data)
            logger.info(f"Added required channel @{channel_username} for group {group_id}")
    
    def remove_required_channel(self, group_id: int, channel_username: str):
        """Remove a required channel for a group"""
        group_data = storage.get_group_data(group_id)
        required_channels = group_data.get("required_channels", [])
        
        # Clean channel username
        channel_username = channel_username.lstrip('@')
        
        if channel_username in required_channels:
            required_channels.remove(channel_username)
            group_data["required_channels"] = required_channels
            storage.save_group_data(group_id, group_data)
            logger.info(f"Removed required channel @{channel_username} for group {group_id}")
    
    def get_required_channels(self, group_id: int) -> List[str]:
        """Get list of required channels for a group"""
        group_data = storage.get_group_data(group_id)
        return group_data.get("required_channels", [])

# Global subscription checker instance
subscription_checker = SubscriptionChecker()