"""
Captcha verification system for new users
"""

import random
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.storage import storage
from config import CAPTCHA_TIMEOUT, CAPTCHA_DIFFICULTY

logger = logging.getLogger(__name__)

class CaptchaManager:
    """Manages captcha verification for new users"""
    
    def __init__(self):
        self.pending_users = {}  # user_id: {chat_id, question, answer, expires}
        self.difficulty_settings = {
            "easy": {"type": "math", "max_num": 10},
            "medium": {"type": "math", "max_num": 50}, 
            "hard": {"type": "mixed", "max_num": 100}
        }
    
    def generate_captcha(self, difficulty: str = "medium") -> tuple[str, str]:
        """Generate a captcha question and answer"""
        settings = self.difficulty_settings.get(difficulty, self.difficulty_settings["medium"])
        
        if settings["type"] == "math":
            return self._generate_math_captcha(settings["max_num"])
        elif settings["type"] == "mixed":
            if random.choice([True, False]):
                return self._generate_math_captcha(settings["max_num"])
            else:
                return self._generate_text_captcha()
        else:
            return self._generate_math_captcha(settings["max_num"])
    
    def _generate_math_captcha(self, max_num: int) -> tuple[str, str]:
        """Generate a math captcha"""
        operations = ["+", "-", "*"]
        operation = random.choice(operations)
        
        if operation == "+":
            a = random.randint(1, max_num)
            b = random.randint(1, max_num)
            answer = a + b
            question = f"What is {a} + {b}?"
        elif operation == "-":
            a = random.randint(max_num//2, max_num)
            b = random.randint(1, a)
            answer = a - b
            question = f"What is {a} - {b}?"
        else:  # multiplication
            a = random.randint(1, min(max_num//10, 12))
            b = random.randint(1, min(max_num//10, 12))
            answer = a * b
            question = f"What is {a} × {b}?"
        
        return question, str(answer)
    
    def _generate_text_captcha(self) -> tuple[str, str]:
        """Generate a text-based captcha"""
        questions = [
            ("What is the capital of France?", "paris"),
            ("How many days are in a week?", "7"),
            ("What color do you get when you mix red and blue?", "purple"),
            ("What is the largest planet in our solar system?", "jupiter"),
            ("How many legs does a spider have?", "8"),
            ("What is 2 to the power of 3?", "8"),
            ("In which month does the year start?", "january"),
            ("What do bees make?", "honey"),
        ]
        
        question, answer = random.choice(questions)
        return question, answer.lower()
    
    async def create_captcha_for_user(self, user_id: int, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Create and send captcha to new user"""
        try:
            # Generate captcha
            question, answer = self.generate_captcha(CAPTCHA_DIFFICULTY)
            
            # Store captcha data
            expires = datetime.now() + timedelta(seconds=CAPTCHA_TIMEOUT)
            self.pending_users[user_id] = {
                "chat_id": chat_id,
                "question": question,
                "answer": answer,
                "expires": expires
            }
            
            # Create inline keyboard with options
            if question.startswith("What is") and any(op in question for op in ["+", "-", "×"]):
                # Math captcha - generate multiple choice
                correct_answer = int(answer)
                options = [correct_answer]
                
                # Generate wrong answers
                while len(options) < 4:
                    wrong = correct_answer + random.randint(-10, 10)
                    if wrong != correct_answer and wrong not in options and wrong >= 0:
                        options.append(wrong)
                
                random.shuffle(options)
                
                keyboard = []
                for i in range(0, len(options), 2):
                    row = []
                    for j in range(2):
                        if i + j < len(options):
                            option = options[i + j]
                            row.append(InlineKeyboardButton(
                                str(option),
                                callback_data=f"captcha_{user_id}_{option}"
                            ))
                    keyboard.append(row)
            else:
                # Text captcha - user needs to type answer
                keyboard = [[InlineKeyboardButton(
                    "I'll type my answer",
                    callback_data=f"captcha_text_{user_id}"
                )]]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send captcha message
            captcha_text = f"""
🔐 **Security Verification**

Welcome! To join this group, please solve this captcha:

**{question}**

⏰ You have {CAPTCHA_TIMEOUT // 60} minutes to complete this verification.
❌ Failure to complete will result in removal from the group.
            """
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=captcha_text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            
            # Mute user until verification
            await context.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=context.bot.get_chat(chat_id).permissions._replace(
                    can_send_messages=False,
                    can_send_media_messages=False,
                    can_send_other_messages=False
                )
            )
            
            logger.info(f"Captcha created for user {user_id} in chat {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating captcha for user {user_id}: {e}")
            return False
    
    async def verify_captcha(self, user_id: int, answer: str, context: ContextTypes.DEFAULT_TYPE) -> tuple[bool, str]:
        """Verify captcha answer"""
        if user_id not in self.pending_users:
            return False, "No pending captcha found."
        
        captcha_data = self.pending_users[user_id]
        
        # Check if expired
        if datetime.now() > captcha_data["expires"]:
            del self.pending_users[user_id]
            return False, "Captcha expired."
        
        # Check answer
        correct_answer = captcha_data["answer"].lower().strip()
        user_answer = answer.lower().strip()
        
        if user_answer == correct_answer:
            # Correct answer - remove restrictions
            chat_id = captcha_data["chat_id"]
            
            try:
                # Restore full permissions
                await context.bot.restrict_chat_member(
                    chat_id=chat_id,
                    user_id=user_id,
                    permissions=context.bot.get_chat(chat_id).permissions
                )
                
                # Remove from pending
                del self.pending_users[user_id]
                
                # Log successful verification
                logger.info(f"User {user_id} successfully completed captcha in chat {chat_id}")
                
                return True, "✅ Captcha solved! Welcome to the group!"
                
            except Exception as e:
                logger.error(f"Error removing restrictions for user {user_id}: {e}")
                return False, "Error updating permissions."
        else:
            return False, f"❌ Incorrect answer. Try again.\nCorrect answer was: {correct_answer}"
    
    async def cleanup_expired_captchas(self, context: ContextTypes.DEFAULT_TYPE):
        """Remove users who failed to complete captcha in time"""
        current_time = datetime.now()
        expired_users = []
        
        for user_id, data in self.pending_users.items():
            if current_time > data["expires"]:
                expired_users.append((user_id, data["chat_id"]))
        
        for user_id, chat_id in expired_users:
            try:
                # Remove user from group
                await context.bot.ban_chat_member(chat_id, user_id)
                await context.bot.unban_chat_member(chat_id, user_id)  # Allow rejoin
                
                # Send notification
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ User {user_id} was removed for failing to complete captcha verification."
                )
                
                # Remove from pending
                del self.pending_users[user_id]
                
                logger.info(f"Removed user {user_id} from chat {chat_id} for expired captcha")
                
            except Exception as e:
                logger.error(f"Error removing expired captcha user {user_id}: {e}")

# Global captcha manager instance
captcha_manager = CaptchaManager()