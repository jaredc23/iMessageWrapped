from stats.BaseStatistic import BaseStatistic
from Message import Message
from Reaction import Reaction

class MessageStatistic(BaseStatistic):
    """Tracks message count (including reactions) over time."""
    
    def record(self, msg):
        """Record a message or reaction."""
        date = msg.timestamp.date()
        hour = msg.timestamp.hour
        self._record_base(msg.sender, date, hour)