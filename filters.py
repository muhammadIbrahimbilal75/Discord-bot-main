import re
from typing import List, Set
from config import BotConfig

class MessageFilter:
    """Message filtering and content moderation utilities"""
    
    def __init__(self):
        # Load filtered words from config
        self.filtered_words: Set[str] = set()
        for word in BotConfig.FILTERED_WORDS:
            self.filtered_words.add(word.lower())
        
        # Common patterns to detect
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        
        self.invite_pattern = re.compile(
            r'(discord\.gg\/|discord\.com\/invite\/|discordapp\.com\/invite\/)[a-zA-Z0-9]+'
        )
        
        # Excessive caps detection
        self.caps_threshold = 0.7  # 70% uppercase letters
        
        # Excessive repeated characters
        self.repeat_pattern = re.compile(r'(.)\1{4,}')  # 5 or more repeated characters
    
    def contains_filtered_words(self, message: str) -> bool:
        """Check if message contains filtered words"""
        if not self.filtered_words:
            return False
        
        # Convert to lowercase for checking
        message_lower = message.lower()
        
        # Remove common punctuation for better detection
        cleaned_message = re.sub(r'[^\w\s]', ' ', message_lower)
        
        # Split into words
        words = cleaned_message.split()
        
        # Check each word
        for word in words:
            if word in self.filtered_words:
                return True
        
        # Check for partial matches in filtered words
        for filtered_word in self.filtered_words:
            if filtered_word in message_lower:
                return True
        
        return False
    
    def contains_discord_invite(self, message: str) -> bool:
        """Check if message contains Discord invite links"""
        return bool(self.invite_pattern.search(message))
    
    def contains_external_links(self, message: str) -> bool:
        """Check if message contains external URLs"""
        return bool(self.url_pattern.search(message))
    
    def is_excessive_caps(self, message: str) -> bool:
        """Check if message has excessive capital letters"""
        if len(message) < 10:  # Skip short messages
            return False
        
        # Count letters only
        letters = [c for c in message if c.isalpha()]
        if len(letters) < 5:  # Need at least 5 letters to check
            return False
        
        caps_count = sum(1 for c in letters if c.isupper())
        caps_ratio = caps_count / len(letters)
        
        return caps_ratio > self.caps_threshold
    
    def has_excessive_repeats(self, message: str) -> bool:
        """Check if message has excessive repeated characters"""
        return bool(self.repeat_pattern.search(message))
    
    def is_spam_like(self, message: str) -> bool:
        """Check if message appears to be spam-like"""
        # Check multiple spam indicators
        spam_indicators = 0
        
        if self.is_excessive_caps(message):
            spam_indicators += 1
        
        if self.has_excessive_repeats(message):
            spam_indicators += 1
        
        if len(message.split()) < 3 and len(message) > 50:  # Long message with few words
            spam_indicators += 1
        
        # Check for excessive emojis
        emoji_count = len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', message))
        if emoji_count > 5:
            spam_indicators += 1
        
        return spam_indicators >= 2
    
    def get_filter_reason(self, message: str) -> List[str]:
        """Get list of reasons why message was filtered"""
        reasons = []
        
        if self.contains_filtered_words(message):
            reasons.append("Contains inappropriate content")
        
        if self.contains_discord_invite(message):
            reasons.append("Contains Discord invite link")
        
        if self.is_excessive_caps(message):
            reasons.append("Excessive capital letters")
        
        if self.has_excessive_repeats(message):
            reasons.append("Excessive repeated characters")
        
        if self.is_spam_like(message):
            reasons.append("Appears to be spam")
        
        return reasons
    
    def clean_message(self, message: str) -> str:
        """Clean message by removing filtered content"""
        # Remove excessive repeated characters
        cleaned = self.repeat_pattern.sub(r'\1\1', message)
        
        # Remove Discord invites
        cleaned = self.invite_pattern.sub('[INVITE_REMOVED]', cleaned)
        
        return cleaned
    
    def add_filtered_word(self, word: str):
        """Add a word to the filter list"""
        self.filtered_words.add(word.lower())
    
    def remove_filtered_word(self, word: str):
        """Remove a word from the filter list"""
        self.filtered_words.discard(word.lower())
    
    def get_filtered_words(self) -> List[str]:
        """Get list of currently filtered words"""
        return sorted(list(self.filtered_words))
