from iMessage import iMessage
from typing import TYPE_CHECKING

# Avoid circular import for type hints
if TYPE_CHECKING:
    from Reaction import Reaction


class Message(iMessage):
    """
    Represents a standard iMessage (not a reaction).
    Inherits common functionality from iMessage base class.
    """

    def __init__(self, message_dict):
        # Initialize parent class with shared attributes
        super().__init__(message_dict)
        
        # Message-specific attributes
        self.has_attachment = message_dict["attachment"] is not None
        self.attachment = message_dict["attachment"]
        self.reaction_list_raw = message_dict.get("reactions", [])
        
        # Reaction tracking
        self.reactions: list["Reaction"] = []
        self.num_reactions = len(self.reaction_list_raw)
        self.all_reactions_added = self.num_reactions == len(self.reactions)

        self.is_reply = message_dict["is_reply"]
        self.has_replies = message_dict["has_replies"]
        self.reply_guids = message_dict["reply_guids"]
        self.thread_originator_guid = message_dict["thread_originator_guid"]

    def addReaction(self, reaction: "Reaction"):
        """
        Add a reaction to this message.
        
        Args:
            reaction: Reaction object to add
        """
        self.reactions.append(reaction)
        self.all_reactions_added = self.num_reactions == len(self.reactions)

    def __str__(self):
        return f"<Message ({self.sender_name}: {self.timestamp.strftime('%m/%d/%Y %H:%M')}): {self.text}>"
    
    def to_dict(self):
        """Convert message to dictionary format."""
        base_dict = super().to_dict()
        base_dict.update({
            "has_attachment": self.has_attachment,
            "attachment": self.attachment,
            "num_reactions": self.num_reactions,
            "reactions": [r.to_dict() for r in self.reactions]
        })
        return base_dict


if __name__ == "__main__":
    from unused.zz_deprecated_Conversation import Conversation
    from Reaction import Reaction
    
    c = Conversation("exports/chat_573.json")
    m = Message(c.json_data[1])
    print(m)
    
    r = Reaction(c.json_data[2])
    print(f"All reactions added: {m.all_reactions_added}")
    m.addReaction(r)
    print(f"All reactions added: {m.all_reactions_added}")
    print(f"Reactions: {m.reactions}")