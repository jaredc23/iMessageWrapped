from datetime import datetime
from zoneinfo import ZoneInfo
import re
from iMessage import iMessage

class Reaction(iMessage):
    """
    Represents a reaction to an iMessage.
    Inherits from iMessage and adds reaction-specific functionality.
    Can be initialized from the message export format where is_reaction=True.
    """
    
    # Mapping of reaction text patterns to reaction types
    REACTION_PATTERNS = {
        r"^Loved": "loved",
        r"^Liked": "liked",
        r"^Disliked": "disliked",
        r"^Laughed at": "laughed",
        r"^Emphasized": "emphasized",
        r"^Questioned": "questioned",
        r"^Removed a heart from": "removed_love",
        r"^Removed a like from": "removed_like",
        r"^Removed a dislike from": "removed_dislike",
        r"^Removed a laugh from": "removed_laugh",
        r"^Removed an emphasis from": "removed_emphasis",
        r"^Removed a question mark from": "removed_question"
    }
    
    # Emoji mapping for reaction types
    REACTION_EMOJIS = {
        "loved": "❤️",
        "liked": "👍",
        "disliked": "👎",
        "laughed": "😂",
        "emphasized": "‼️",
        "questioned": "❓",
        "removed_love": "💔",
        "removed_like": "👎",
        "removed_dislike": "👍",
        "removed_laugh": "😐",
        "removed_emphasis": "➖",
        "removed_question": "❔"
    }

    def __init__(self, message_dict):
        """
        Initialize a Reaction from a message dictionary where is_reaction=True.
        
        Args:
            message_dict: Dictionary containing reaction data from message export
        """
        if not message_dict.get("is_reaction", False):
            raise ValueError("Message dictionary must have is_reaction=True")
        
        # Call parent constructor
        super().__init__(message_dict)
        
        # Reaction-specific attributes
        self.raw_text = self.text
        self.assoc_guid = message_dict["assoc_guid"]
        
        # Parse reaction type and emoji from text
        self.reaction_type = self._parse_reaction_type()
        self.emoji = self._extract_emoji()
        self.display = self._create_display()
        
        # Extract the original message text that was reacted to
        self.reacted_to_text = self._extract_reacted_to_text()
    
    def _parse_reaction_type(self):
        """Parse the reaction type from the text."""
        if not self.text:
            return "unknown"
        
        for pattern, reaction_type in self.REACTION_PATTERNS.items():
            if re.match(pattern, self.text, re.IGNORECASE):
                return reaction_type
        
        # Check if it's just an emoji
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001F900-\U0001F9FF"  # supplemental symbols
            "]+", flags=re.UNICODE
        )
        if emoji_pattern.match(self.text):
            return "emoji"
        
        return "unknown"
    
    def _extract_emoji(self):
        """Extract emoji from the text or use default for reaction type."""
        if not self.text:
            return None
        
        # Try to extract emoji from text
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001F900-\U0001F9FF"
            "]+", flags=re.UNICODE
        )
        
        emoji_match = emoji_pattern.search(self.text)
        if emoji_match:
            return emoji_match.group(0)
        
        # Use default emoji for known reaction types
        return self.REACTION_EMOJIS.get(self.reaction_type)
    
    def _extract_reacted_to_text(self):
        """Extract the original message text from reaction text like 'Loved "message"'."""
        if not self.text:
            return None
        
        # Pattern to match quoted text: "text"
        quoted_match = re.search(r'"([^"]+)"', self.text)
        if quoted_match:
            return quoted_match.group(1)
        
        # Pattern to match text after "Loved/Liked/etc "
        for pattern in self.REACTION_PATTERNS.keys():
            match = re.match(f"{pattern}\\s+(.+)", self.text, re.IGNORECASE)
            if match:
                text = match.group(1)
                # Remove quotes if present
                return text.strip('"')
        
        return None
    
    def _create_display(self):
        """Create a user-friendly display string for the reaction."""
        if self.reaction_type in self.REACTION_PATTERNS.values():
            return self.reaction_type.replace("_", " ").title()
        elif self.reaction_type == "emoji":
            return self.emoji or "Emoji reaction"
        else:
            return self.text or "Reaction"
    
    def __str__(self):
        """String representation of the Reaction."""
        emoji_str = f"{self.emoji} " if self.emoji else ""
        return f"<Reaction ({self.sender_name}: {self.timestamp.strftime('%m/%d/%Y %H:%M')}): {emoji_str}{self.display}>"
    
    def __repr__(self):
        """Representation of the Reaction."""
        return self.__str__()
    
    def to_dict(self):
        """Convert reaction back to dictionary format."""
        # Get base dictionary from parent
        base_dict = super().to_dict()
        
        # Add reaction-specific fields
        base_dict.update({
            "reaction_type": self.reaction_type,
            "emoji": self.emoji,
            "display": self.display,
            "raw_text": self.raw_text,
            "reacted_to_text": self.reacted_to_text,
            "assoc_guid": self.assoc_guid
        })
        
        return base_dict

    
if __name__ == "__main__":
    from unused.zz_deprecated_Conversation import Conversation
    c = Conversation("exports/chat_573.json")
    m = Reaction(c.json_data[2])
    print(m)