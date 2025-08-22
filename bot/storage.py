"""
Data storage management for the bot
Handles JSON file operations for users, groups, and spam data
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class StorageManager:
    """Manages data storage in JSON files"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, "users.json")
        self.groups_file = os.path.join(data_dir, "groups.json")
        self.spam_file = os.path.join(data_dir, "spam_data.json")
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize files if they don't exist
        self._init_files()
    
    def _init_files(self):
        """Initialize JSON files with empty structures"""
        files_structure = {
            self.users_file: {},
            self.groups_file: {},
            self.spam_file: {}
        }
        
        for file_path, default_structure in files_structure.items():
            if not os.path.exists(file_path):
                self._write_json(file_path, default_structure)
    
    def _read_json(self, file_path: str) -> Dict[str, Any]:
        """Read JSON data from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error reading {file_path}: {e}")
            return {}
    
    def _write_json(self, file_path: str, data: Dict[str, Any]):
        """Write JSON data to file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error writing {file_path}: {e}")
    
    def get_user_data(self, user_id: int) -> Dict[str, Any]:
        """Get user data by user ID"""
        users = self._read_json(self.users_file)
        return users.get(str(user_id), {})
    
    def save_user_data(self, user_id: int, user_data: Dict[str, Any]):
        """Save user data"""
        users = self._read_json(self.users_file)
        users[str(user_id)] = user_data
        self._write_json(self.users_file, users)
    
    def get_group_data(self, group_id: int) -> Dict[str, Any]:
        """Get group data by group ID"""
        groups = self._read_json(self.groups_file)
        default_group = {
            "welcome_message": None,
            "settings": {
                "anti_spam_enabled": True,
                "welcome_enabled": True,
                "flood_protection": True
            },
            "admins": [],
            "banned_words": []
        }
        return groups.get(str(group_id), default_group)
    
    def save_group_data(self, group_id: int, group_data: Dict[str, Any]):
        """Save group data"""
        groups = self._read_json(self.groups_file)
        groups[str(group_id)] = group_data
        self._write_json(self.groups_file, groups)
    
    def get_spam_data(self, user_id: int, group_id: int) -> Dict[str, Any]:
        """Get spam detection data for user in group"""
        spam_data = self._read_json(self.spam_file)
        key = f"{group_id}_{user_id}"
        return spam_data.get(key, {
            "message_count": 0,
            "last_message_time": 0,
            "recent_messages": [],
            "warnings": 0
        })
    
    def save_spam_data(self, user_id: int, group_id: int, data: Dict[str, Any]):
        """Save spam detection data"""
        spam_data = self._read_json(self.spam_file)
        key = f"{group_id}_{user_id}"
        spam_data[key] = data
        self._write_json(self.spam_file, spam_data)
    
    def log_action(self, group_id: int, admin_id: int, action: str, target_user: int, reason: str = ""):
        """Log moderation actions"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "admin_id": admin_id,
            "action": action,
            "target_user": target_user,
            "reason": reason
        }
        
        groups = self._read_json(self.groups_file)
        group_data = groups.get(str(group_id), {})
        
        if "action_log" not in group_data:
            group_data["action_log"] = []
        
        group_data["action_log"].append(log_entry)
        
        # Keep only last 100 entries
        group_data["action_log"] = group_data["action_log"][-100:]
        
        groups[str(group_id)] = group_data
        self._write_json(self.groups_file, groups)
        
        logger.info(f"Action logged: {action} by {admin_id} on {target_user} in group {group_id}")

# Global storage instance
storage = StorageManager()
