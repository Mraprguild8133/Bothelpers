"""
Spam detection and flood protection system
"""

import time
import re
import logging
from typing import List, Dict, Any
from difflib import SequenceMatcher
from bot.storage import storage
from bot.content_filter import content_filter
from config import FLOOD_LIMIT, SPAM_THRESHOLD, MESSAGE_SIMILARITY_THRESHOLD, MAX_WARNINGS

logger = logging.getLogger(__name__)

class SpamDetector:
    """Handles spam detection and flood protection"""
    
    def __init__(self):
        self.flood_limit = FLOOD_LIMIT
        self.spam_threshold = SPAM_THRESHOLD
        self.similarity_threshold = MESSAGE_SIMILARITY_THRESHOLD
    
    def is_flood(self, user_id: int, group_id: int) -> bool:
        """Check if user is flooding (too many messages in short time)"""
        current_time = time.time()
        spam_data = storage.get_spam_data(user_id, group_id)
        
        # Reset counter if more than a minute has passed
        if current_time - spam_data.get("last_message_time", 0) > 60:
            spam_data["message_count"] = 1
        else:
            spam_data["message_count"] = spam_data.get("message_count", 0) + 1
        
        spam_data["last_message_time"] = current_time
        storage.save_spam_data(user_id, group_id, spam_data)
        
        return spam_data["message_count"] > self.flood_limit
    
    def is_spam_message(self, user_id: int, group_id: int, message_text: str) -> bool:
        """Check if message is spam (repeated content)"""
        spam_data = storage.get_spam_data(user_id, group_id)
        recent_messages = spam_data.get("recent_messages", [])
        
        # Clean message text for comparison
        cleaned_message = self._clean_message(message_text)
        
        # Check similarity with recent messages
        similar_count = 0
        for old_message in recent_messages:
            similarity = SequenceMatcher(None, cleaned_message, old_message).ratio()
            if similarity >= self.similarity_threshold:
                similar_count += 1
        
        # Add current message to recent messages
        recent_messages.append(cleaned_message)
        
        # Keep only last 10 messages
        recent_messages = recent_messages[-10:]
        spam_data["recent_messages"] = recent_messages
        
        storage.save_spam_data(user_id, group_id, spam_data)
        
        return similar_count >= self.spam_threshold
    
    def contains_banned_words(self, group_id: int, message_text: str) -> bool:
        """Check if message contains banned words"""
        group_data = storage.get_group_data(group_id)
        banned_words = group_data.get("banned_words", [])
        
        message_lower = message_text.lower()
        for word in banned_words:
            if word.lower() in message_lower:
                logger.info(f"Banned word '{word}' detected in group {group_id}")
                return True
        
        return False
    
    def has_suspicious_links(self, message_text: str) -> bool:
        """Check for suspicious links (basic implementation)"""
        # Simple regex for URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, message_text)
        
        # Check for suspicious domains (basic list)
        suspicious_domains = [
            'bit.ly', 'tinyurl.com', 'shorturl.at', 'ow.ly',
            't.co', 'goo.gl', 'buff.ly'  # Common URL shorteners
        ]
        
        for url in urls:
            for domain in suspicious_domains:
                if domain in url:
                    logger.info(f"Suspicious link detected: {url}")
                    return True
        
        return False
    
    def _clean_message(self, message: str) -> str:
        """Clean message text for comparison"""
        # Remove extra whitespace, emojis, and normalize
        cleaned = re.sub(r'\s+', ' ', message.strip().lower())
        # Remove common punctuation for better comparison
        cleaned = re.sub(r'[!@#$%^&*(),.?":{}|<>]', '', cleaned)
        return cleaned
    
    async def check_message(self, user_id: int, group_id: int, message_text: str, message = None) -> Dict[str, Any]:
        """
        Comprehensive spam check for a message
        Returns dict with detection results
        """
        result = {
            "is_spam": False,
            "reasons": [],
            "action_recommended": None
        }
        
        # Check flood protection
        if self.is_flood(user_id, group_id):
            result["is_spam"] = True
            result["reasons"].append("flooding")
            result["action_recommended"] = "mute"
        
        # Check for repeated content
        if self.is_spam_message(user_id, group_id, message_text):
            result["is_spam"] = True
            result["reasons"].append("repeated_content")
            result["action_recommended"] = "warn"
        
        # Check banned words
        if self.contains_banned_words(group_id, message_text):
            result["is_spam"] = True
            result["reasons"].append("banned_words")
            result["action_recommended"] = "delete"
        
        # Check suspicious links
        if self.has_suspicious_links(message_text):
            result["is_spam"] = True
            result["reasons"].append("suspicious_links")
            result["action_recommended"] = "warn"
        
        # Use advanced content filtering if message object is provided
        if message:
            content_result = await content_filter.comprehensive_content_check(group_id, message)
            if content_result["violation"]:
                result["is_spam"] = True
                result["reasons"].extend(content_result["reasons"])
                # Use the most severe action recommended
                if content_result["action"] == "delete" or result["action_recommended"] == "mute":
                    result["action_recommended"] = content_result["action"]
                elif not result["action_recommended"]:
                    result["action_recommended"] = content_result["action"]
        
        return result
    
    def increment_warnings(self, user_id: int, group_id: int) -> int:
        """Increment user warnings and return total count"""
        spam_data = storage.get_spam_data(user_id, group_id)
        warnings = spam_data.get("warnings", 0) + 1
        spam_data["warnings"] = warnings
        storage.save_spam_data(user_id, group_id, spam_data)
        return warnings
    
    def get_warning_action(self, warning_count: int) -> str:
        """Get recommended action based on warning count"""
        if warning_count >= MAX_WARNINGS:
            return "ban"
        elif warning_count >= 2:
            return "mute"
        else:
            return "warn"
    
    def reset_warnings(self, user_id: int, group_id: int):
        """Reset user warnings"""
        spam_data = storage.get_spam_data(user_id, group_id)
        spam_data["warnings"] = 0
        storage.save_spam_data(user_id, group_id, spam_data)

# Global spam detector instance
spam_detector = SpamDetector()
