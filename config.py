"""
Configuration settings for the Telegram bot
"""

import os

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Spam detection settings
FLOOD_LIMIT = int(os.getenv("FLOOD_LIMIT", "5"))  # Max messages per minute
SPAM_THRESHOLD = int(os.getenv("SPAM_THRESHOLD", "3"))  # Similar messages threshold
MESSAGE_SIMILARITY_THRESHOLD = float(os.getenv("MESSAGE_SIMILARITY_THRESHOLD", "0.8"))

# Mute duration (in seconds)
DEFAULT_MUTE_DURATION = int(os.getenv("DEFAULT_MUTE_DURATION", "300"))  # 5 minutes

# Advanced filtering settings
ENABLE_MEDIA_FILTERING = os.getenv("ENABLE_MEDIA_FILTERING", "true").lower() == "true"
ENABLE_LINK_FILTERING = os.getenv("ENABLE_LINK_FILTERING", "true").lower() == "true"
ENABLE_BANNED_WORDS = os.getenv("ENABLE_BANNED_WORDS", "true").lower() == "true"

# Captcha settings
CAPTCHA_TIMEOUT = int(os.getenv("CAPTCHA_TIMEOUT", "300"))  # 5 minutes
CAPTCHA_DIFFICULTY = os.getenv("CAPTCHA_DIFFICULTY", "medium")  # easy, medium, hard

# Channel subscription settings
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "")  # Channel username without @
CHECK_SUBSCRIPTION = os.getenv("CHECK_SUBSCRIPTION", "false").lower() == "true"

# External logging
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID", "")  # Channel ID for logging
ENABLE_EXTERNAL_LOGGING = os.getenv("ENABLE_EXTERNAL_LOGGING", "false").lower() == "true"

# Warning system
MAX_WARNINGS = int(os.getenv("MAX_WARNINGS", "3"))
WARNING_ACTIONS = {
    1: "warn",     # First warning
    2: "mute",     # Second warning - mute for 10 minutes  
    3: "ban"       # Third warning - ban
}

# Escalating punishment durations (in seconds)
MUTE_DURATIONS = {
    1: 600,    # 10 minutes
    2: 3600,   # 1 hour
    3: 86400   # 24 hours
}

# Data file paths
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
GROUPS_FILE = os.path.join(DATA_DIR, "groups.json")
SPAM_DATA_FILE = os.path.join(DATA_DIR, "spam_data.json")

# Welcome message template
DEFAULT_WELCOME_MESSAGE = """
🎉 Welcome to {group_name}, {user_name}!

Please read our group rules and enjoy your stay. If you need help, use /help command.

This group is protected by anti-spam measures. Please be respectful to other members.
"""

# Bot commands help text
HELP_TEXT = """
🤖 **Advanced Group Management Bot Commands**

**General Commands:**
/start - Start the bot
/help - Show this help message

**Moderation Commands (Admin only):**
/ban @user [reason] - Ban a user from the group
/kick @user [reason] - Remove user (can rejoin)
/mute @user [duration] - Mute user for specified time
/unban @user - Unban a previously banned user
/info @user - Get user information
/resetwarnings @user - Reset warnings for a user

**Content Filtering (Admin only):**
/addword <word> - Add banned word/phrase
/removeword <word> - Remove banned word/phrase
/settings - Configure bot settings for this group

**Security Features (Admin only):**
/captcha on|off - Enable/disable captcha for new members
/channels add|remove @channel - Manage required channels
/setuplog @channel - Setup external logging channel

**Advanced Features:**
🛡️ **Content Filtering:**
• Banned words detection and removal
• Suspicious link filtering (URL shorteners, adult sites)
• Media content restrictions
• Forward message filtering

🔐 **Security Systems:**
• Math and text captcha verification for new users
• Channel subscription requirements
• Warning system with escalating punishments
• Advanced spam detection with AI-like filtering

📊 **Monitoring & Logging:**
• Comprehensive external logging to dedicated channels
• Real-time moderation action tracking
• User activity monitoring
• Automated threat detection

⚡ **Automated Moderation:**
• Smart flood protection
• Content similarity detection
• Progressive warning system (warn → mute → ban)
• Automatic punishment escalation

Need more help? Contact the bot administrator.
"""
