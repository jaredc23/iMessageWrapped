from datetime import datetime
from zoneinfo import ZoneInfo

class iMessage:
    """
    Base class for iMessage messages and reactions.
    Contains all shared attributes and functionality.
    """
    
    def __init__(self, message_dict):
        """
        Initialize an iMessage from a message dictionary.
        
        Args:
            message_dict: Dictionary containing message data from export
        """
        self.message_dict = message_dict
        self.id = message_dict["id"]
        self.guid = message_dict["guid"]
        self.timestamp = datetime.fromisoformat(message_dict["timestamp"]).astimezone(ZoneInfo("America/New_York"))
        self.sender = message_dict["sender"]
        self.sender_name = message_dict["sender_name"]
        self.text = message_dict["text"]
        self.is_reaction = message_dict.get("is_reaction", False)
        self.is_unsent = message_dict["is_unsent"]
    
    def __str__(self):
        """String representation of the iMessage."""
        return f"<iMessage ({self.sender_name}: {self.timestamp.strftime('%m/%d/%Y %H:%M')}): {self.text}>"
    
    def __repr__(self):
        """Representation of the iMessage."""
        return self.__str__()
    
    def to_dict(self):
        """
        Convert iMessage to dictionary format.
        Subclasses should override to add specific fields.
        """
        return {
            "id": self.id,
            "guid": self.guid,
            "timestamp": self.timestamp.isoformat(),
            "sender": self.sender,
            "sender_name": self.sender_name,
            "text": self.text,
            "is_reaction": self.is_reaction
        }


if __name__ == "__main__":
    # Test with example data
    test_message = {
        "id": 372484,
        "guid": "8ED96FF7-A080-4CF7-B49E-80C537DD2ED4",
        "timestamp": "2025-11-09T04:35:20.907900+00:00",
        "sender": None,
        "sender_name": "You",
        "text": "And I stg if a bed bug even thinks abt it",
        "is_reaction": False
    }
    
    msg = iMessage(test_message)
    print(msg)
    print(f"ID: {msg.id}")
    print(f"Sender: {msg.sender_name}")
    print(f"Time: {msg.timestamp}")
    print(f"Is reaction: {msg.is_reaction}")