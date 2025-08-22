# Telegram Group Management Bot

## Overview

This is a comprehensive Telegram bot designed for advanced group moderation and management. The bot provides anti-spam protection, user management capabilities, automated moderation features, advanced content filtering, captcha verification, channel subscription requirements, and comprehensive external logging for Telegram groups. It includes flood detection, spam message filtering, user banning/muting functionality, escalating warning systems, and welcome messages for new members. The bot is built using the python-telegram-bot library and uses JSON file storage for persistence.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Bot Framework
- **Technology**: Python with python-telegram-bot library
- **Architecture Pattern**: Handler-based event-driven architecture
- **Entry Point**: `main.py` sets up the Application with various command and message handlers

### Storage Layer
- **Storage Type**: JSON file-based persistence
- **Location**: Local `data/` directory with separate files for users, groups, and spam data
- **Storage Manager**: Centralized `StorageManager` class handles all file I/O operations
- **Data Files**:
  - `users.json` - User information and settings
  - `groups.json` - Group configurations and settings
  - `spam_data.json` - Spam detection metrics and user activity tracking

### Handler System
- **Command Handlers**: Process bot commands like `/ban`, `/mute`, `/kick`, `/unban`, `/info`, `/addword`, `/removeword`, `/captcha`, `/channels`, `/resetwarnings`, `/setuplog`
- **Message Handlers**: Monitor all message types (text, media, documents) for comprehensive content filtering
- **Member Handlers**: Track new member joins with captcha verification, subscription checks, and welcome messages
- **Callback Handlers**: Handle inline keyboard interactions for captcha responses and subscription verification
- **Error Handlers**: Centralized error logging and handling

### Advanced Content Filtering & Spam Detection Engine
- **Flood Protection**: Tracks message frequency per user (configurable limit)
- **Content Similarity**: Uses SequenceMatcher to detect repeated message patterns
- **Advanced Content Filter**: Comprehensive filtering for banned words, suspicious links, media restrictions, and forwarded messages
- **Link Analysis**: Detects and filters URL shorteners, gambling sites, adult content, and scam domains
- **Media Filtering**: Configurable restrictions on images, videos, documents, stickers, and file size limits
- **Banned Words System**: Customizable word/phrase blacklists with admin management
- **Threshold-based**: Configurable similarity thresholds and spam limits
- **Time-based Reset**: Automatic counter resets after time intervals

### Advanced Moderation & Security Systems
- **Permission Checks**: Validates admin status before executing moderation commands
- **User Management**: Ban, kick, mute, and unban functionality with reason logging
- **Duration Support**: Configurable mute durations with time parsing utilities
- **Warning System**: Progressive escalating punishments (warn → mute → ban) with configurable thresholds
- **Captcha Verification**: Math and text-based captcha challenges for new users with timeout enforcement
- **Subscription Requirements**: Channel subscription verification with automatic enforcement
- **Activity Logging**: Comprehensive logging of all moderation actions
- **External Logging**: Real-time logging to dedicated channels for transparency and monitoring

### Configuration Management
- **Environment Variables**: All settings configurable via environment variables including captcha settings, subscription requirements, and logging channels
- **Default Values**: Fallback configuration values for all settings
- **Centralized Config**: Single `config.py` file manages all application settings
- **Advanced Settings**: Media filtering controls, warning system thresholds, captcha difficulty levels, and punishment escalation timers

## External Dependencies

### Core Dependencies
- **python-telegram-bot**: Primary framework for Telegram Bot API integration (version 20.8)
- **Python Standard Library**: 
  - `json` for data persistence
  - `os` for environment variable handling
  - `logging` for application logging
  - `datetime` for time-based operations and captcha timeouts
  - `difflib.SequenceMatcher` for spam content similarity detection
  - `re` for pattern matching and content analysis
  - `random` for captcha generation
  - `urllib.parse` for URL analysis and link filtering

### Telegram Bot API
- **Bot Token**: Required environment variable for bot authentication
- **Chat Management**: Uses Telegram's chat member management APIs
- **Message Handling**: Processes incoming messages and commands through webhooks/polling

### File System & Data Storage
- **Local Storage**: Requires write access to local file system for data persistence
- **Data Directory**: Creates and manages `data/` directory structure
- **JSON Files**: Stores all persistent data in JSON format for simplicity
- **Modular Architecture**: Separate modules for captcha management, content filtering, subscription checking, and external logging
- **Storage Manager**: Centralized data management with automatic file initialization and error handling

### Runtime Environment
- **Python 3.x**: Modern Python version required for async/await support
- **Environment Variables**: Configurable through system environment or `.env` file
- **Logging**: File and console logging support for monitoring and debugging