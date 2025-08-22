"""
Advanced content filtering system
Handles banned words, links, media, and other content restrictions
"""

import re
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from telegram import Message
from bot.storage import storage
from config import ENABLE_MEDIA_FILTERING, ENABLE_LINK_FILTERING, ENABLE_BANNED_WORDS

logger = logging.getLogger(__name__)

class ContentFilter:
    """Advanced content filtering system"""
    
    def __init__(self):
        # Predefined lists of suspicious/harmful content
        self.suspicious_domains = {
            'shorteners': [
                'bit.ly', 'tinyurl.com', 'shorturl.at', 'ow.ly', 't.co', 
                'goo.gl', 'buff.ly', 'tiny.cc', 'is.gd', 'v.gd'
            ],
            'gambling': [
                'bet365.com', 'pokerstars.com', '888casino.com', 'betfair.com',
                'williamhill.com', 'ladbrokes.com', 'bwin.com'
            ],
            'adult': [
                'pornhub.com', 'xvideos.com', 'xnxx.com', 'redtube.com',
                'youporn.com', 'tube8.com', 'spankbang.com'
            ],
            'scam': [
                'earn-money-fast.com', 'free-bitcoin.com', 'get-rich-quick.net',
                'miracle-cure.org', 'weight-loss-secret.com'
            ]
        }
        
        self.default_banned_words = [
            # Profanity and offensive terms
            'spam', 'scam', 'fake', 'fraud', 'cheat', 'hack',
            # Promotional terms that might indicate spam
            'buy now', 'limited time', 'act fast', 'exclusive offer',
            'free money', 'easy money', 'guaranteed profit',
            # Adult content indicators
            'porn', 'xxx', 'adult', 'nsfw', 'nude',
            # Gambling terms
            'bet', 'casino', 'poker', 'gambling', 'lottery'
        ]
        
        # Common file extensions for different media types
        self.media_extensions = {
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'],
            'videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'],
            'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma'],
            'documents': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'],
            'archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2']
        }
    
    def check_banned_words(self, group_id: int, text: str) -> Dict[str, Any]:
        """Check if text contains banned words"""
        if not ENABLE_BANNED_WORDS:
            return {"violation": False, "reasons": []}
        
        group_data = storage.get_group_data(group_id)
        banned_words = group_data.get("banned_words", self.default_banned_words)
        
        text_lower = text.lower()
        found_words = []
        
        for word in banned_words:
            if word.lower() in text_lower:
                found_words.append(word)
        
        if found_words:
            logger.info(f"Banned words detected in group {group_id}: {found_words}")
            return {
                "violation": True,
                "reasons": [f"Contains banned word(s): {', '.join(found_words)}"],
                "words": found_words,
                "action": "delete"
            }
        
        return {"violation": False, "reasons": []}
    
    def check_links(self, group_id: int, text: str) -> Dict[str, Any]:
        """Check for suspicious or unwanted links"""
        if not ENABLE_LINK_FILTERING:
            return {"violation": False, "reasons": []}
        
        group_data = storage.get_group_data(group_id)
        link_policy = group_data.get("link_policy", "moderate")  # strict, moderate, permissive
        
        # Extract URLs from text
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, text)
        
        # Also check for domain mentions without protocol
        domain_pattern = r'(?:^|\s)([a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}'
        potential_domains = re.findall(domain_pattern, text)
        
        violations = []
        suspicious_urls = []
        
        # Check URLs
        for url in urls:
            try:
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                
                # Check against suspicious domain lists
                for category, domains in self.suspicious_domains.items():
                    if any(suspicious in domain for suspicious in domains):
                        violations.append(f"Suspicious {category} link: {domain}")
                        suspicious_urls.append(url)
                        break
                
                # Additional checks based on policy
                if link_policy == "strict":
                    # Block all external links except whitelisted
                    whitelist = group_data.get("whitelisted_domains", [])
                    if not any(allowed in domain for allowed in whitelist):
                        violations.append(f"External link not whitelisted: {domain}")
                        suspicious_urls.append(url)
                
            except Exception as e:
                logger.error(f"Error parsing URL {url}: {e}")
        
        # Check potential domains (without protocol)
        for domain in potential_domains:
            domain = domain.lower().strip('.')
            for category, domains in self.suspicious_domains.items():
                if any(suspicious in domain for suspicious in domains):
                    violations.append(f"Suspicious {category} domain mentioned: {domain}")
                    break
        
        if violations:
            logger.info(f"Link violations detected in group {group_id}: {violations}")
            action = "delete" if link_policy == "strict" else "warn"
            return {
                "violation": True,
                "reasons": violations,
                "urls": suspicious_urls,
                "action": action
            }
        
        return {"violation": False, "reasons": []}
    
    def check_media_content(self, group_id: int, message: Message) -> Dict[str, Any]:
        """Check media content restrictions"""
        if not ENABLE_MEDIA_FILTERING:
            return {"violation": False, "reasons": []}
        
        group_data = storage.get_group_data(group_id)
        media_policy = group_data.get("media_policy", {})
        
        violations = []
        
        # Check if media is allowed at all
        if media_policy.get("block_all_media", False):
            if (message.photo or message.video or message.audio or 
                message.document or message.animation or message.sticker):
                violations.append("Media content not allowed in this group")
        else:
            # Check specific media types
            if message.photo and media_policy.get("block_images", False):
                violations.append("Images not allowed")
            
            if message.video and media_policy.get("block_videos", False):
                violations.append("Videos not allowed")
            
            if message.audio and media_policy.get("block_audio", False):
                violations.append("Audio files not allowed")
            
            if message.document and media_policy.get("block_documents", False):
                violations.append("Documents not allowed")
            
            if message.sticker and media_policy.get("block_stickers", False):
                violations.append("Stickers not allowed")
            
            if message.animation and media_policy.get("block_gifs", False):
                violations.append("GIFs/animations not allowed")
        
        # Check file size limits
        if message.document:
            file_size = getattr(message.document, 'file_size', 0)
            max_size = media_policy.get("max_file_size", 20 * 1024 * 1024)  # 20MB default
            
            if file_size > max_size:
                violations.append(f"File too large: {file_size / 1024 / 1024:.1f}MB (max: {max_size / 1024 / 1024}MB)")
        
        # Check for potentially harmful file types
        if message.document:
            file_name = getattr(message.document, 'file_name', '').lower()
            dangerous_extensions = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.com', '.jar', '.sh']
            
            if any(file_name.endswith(ext) for ext in dangerous_extensions):
                violations.append(f"Potentially harmful file type: {file_name}")
        
        if violations:
            logger.info(f"Media violations detected in group {group_id}: {violations}")
            return {
                "violation": True,
                "reasons": violations,
                "action": "delete"
            }
        
        return {"violation": False, "reasons": []}
    
    def check_forwarded_content(self, group_id: int, message: Message) -> Dict[str, Any]:
        """Check restrictions on forwarded messages"""
        group_data = storage.get_group_data(group_id)
        forward_policy = group_data.get("forward_policy", "allow")  # allow, restrict, block
        
        if not message.forward_date or forward_policy == "allow":
            return {"violation": False, "reasons": []}
        
        violations = []
        
        if forward_policy == "block":
            violations.append("Forwarded messages not allowed")
        elif forward_policy == "restrict":
            # Check forwarded from channels/bots
            if message.forward_from_chat:
                if message.forward_from_chat.type == "channel":
                    violations.append("Messages forwarded from channels not allowed")
                elif message.forward_from_chat.type in ["group", "supergroup"]:
                    violations.append("Messages forwarded from other groups not allowed")
            
            if message.forward_from and message.forward_from.is_bot:
                violations.append("Messages forwarded from bots not allowed")
        
        if violations:
            logger.info(f"Forward violations detected in group {group_id}: {violations}")
            return {
                "violation": True,
                "reasons": violations,
                "action": "delete"
            }
        
        return {"violation": False, "reasons": []}
    
    async def comprehensive_content_check(self, group_id: int, message: Message) -> Dict[str, Any]:
        """Perform comprehensive content filtering"""
        all_violations = []
        actions = set()
        
        # Check text content if present
        if message.text:
            # Banned words check
            banned_result = self.check_banned_words(group_id, message.text)
            if banned_result["violation"]:
                all_violations.extend(banned_result["reasons"])
                actions.add(banned_result["action"])
            
            # Links check
            link_result = self.check_links(group_id, message.text)
            if link_result["violation"]:
                all_violations.extend(link_result["reasons"])
                actions.add(link_result["action"])
        
        # Media content check
        media_result = self.check_media_content(group_id, message)
        if media_result["violation"]:
            all_violations.extend(media_result["reasons"])
            actions.add(media_result["action"])
        
        # Forwarded content check
        forward_result = self.check_forwarded_content(group_id, message)
        if forward_result["violation"]:
            all_violations.extend(forward_result["reasons"])
            actions.add(forward_result["action"])
        
        # Determine final action (prioritize more severe actions)
        final_action = "warn"
        if "delete" in actions:
            final_action = "delete"
        elif "mute" in actions:
            final_action = "mute"
        
        return {
            "violation": len(all_violations) > 0,
            "reasons": all_violations,
            "action": final_action,
            "violation_count": len(all_violations)
        }

# Global content filter instance
content_filter = ContentFilter()