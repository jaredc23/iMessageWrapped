from stats.BaseStatistic import BaseStatistic
from Message import Message

class AttachmentStatistic(BaseStatistic):
    """Tracks attachment count over time."""
    
    def record(self, msg):
        """Record a message with attachment."""
        if isinstance(msg, Message) and msg.has_attachment:
            date = msg.timestamp.date()
            hour = msg.timestamp.hour
            self._record_base(msg.sender, date, hour)