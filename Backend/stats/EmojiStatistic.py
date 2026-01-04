from stats.BaseStatistic import BaseStatistic
from collections import defaultdict
from datetime import timedelta, datetime
from Message import Message
from MessageProcessor import extract_emojis

class EmojiStatistic(BaseStatistic):
    """Tracks emoji usage over time."""
    
    def __init__(self):
        super().__init__()
        # Item-specific tracking (emojis are items, not just counts)
        self.item_timeline = defaultdict(lambda: defaultdict(int))  # {emoji: {date: count}}
        self.item_timeline_by_sender = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))  # {sender: {emoji: {date: count}}}
        self.item_by_hour = defaultdict(lambda: defaultdict(int))  # {emoji: {hour: count}}
        self.item_by_hour_by_sender = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))  # {sender: {emoji: {hour: count}}}
        
        # Legacy format for backward compatibility
        self.emojis_by_sender = {}  # {sender: {emoji: {"total": count, timestamp: count}}}
    
    def record(self, msg):
        """Record emojis from a message."""
        if not isinstance(msg, Message):
            return
        
        emojis = extract_emojis(msg)
        if not emojis:
            return
        
        date = msg.timestamp.date()
        hour = msg.timestamp.hour
        
        # Initialize sender if needed
        if msg.sender not in self.emojis_by_sender:
            self.emojis_by_sender[msg.sender] = {}
        
        for emoji in emojis:
            # Track in item structures
            self.item_timeline[emoji][date] += 1
            self.item_timeline_by_sender[msg.sender][emoji][date] += 1
            self.item_by_hour[emoji][hour] += 1
            self.item_by_hour_by_sender[msg.sender][emoji][hour] += 1
            
            # Legacy format
            if emoji not in self.emojis_by_sender[msg.sender]:
                self.emojis_by_sender[msg.sender][emoji] = {"total": 0}
            if msg.timestamp not in self.emojis_by_sender[msg.sender][emoji]:
                self.emojis_by_sender[msg.sender][emoji][msg.timestamp] = 0
            self.emojis_by_sender[msg.sender][emoji][msg.timestamp] += 1
            self.emojis_by_sender[msg.sender][emoji]["total"] += 1
    
    def get_totals(self, sender_number):
        """Returns emoji totals for a sender in [[emoji list][count]] format."""
        if sender_number not in self.emojis_by_sender:
            return [[], []]
        
        emojis = []
        counts = []
        for emoji, data in self.emojis_by_sender[sender_number].items():
            emojis.append(emoji)
            counts.append(data["total"])
        
        return [emojis, counts]
    
    def get_item_timeline(self, sender_number=None, period='week', top_n=15, include_all=False):
        """
        Returns emoji usage over time for line graphing.
        
        Parameters:
        - sender_number: Specific sender to filter by, or None for all senders
        - period: 'day', 'week', 'month', or 'year' for aggregation
        - top_n: Number of top emojis to include (default 15)
        - include_all: If True, includes all emojis regardless of top_n
        
        Returns:
        {
            'dates': [list of dates in chronological order],
            'emojis': {
                'emoji1': [counts corresponding to dates],
                'emoji2': [counts corresponding to dates],
                ...
            }
        }
        """
        # Choose the right data source
        if sender_number is not None:
            if sender_number not in self.item_timeline_by_sender:
                return {'dates': [], 'emojis': {}}
            timeline_data = self.item_timeline_by_sender[sender_number]
        else:
            timeline_data = self.item_timeline
        
        # Aggregate by period
        aggregated = defaultdict(lambda: defaultdict(int))
        
        for emoji, dates in timeline_data.items():
            for date, count in dates.items():
                # Convert date to datetime for _get_period_key
                dt = datetime.combine(date, datetime.min.time())
                key = self._get_period_key(dt, period)
                aggregated[emoji][key] += count
        
        # Select emojis
        if include_all:
            selected_emojis = list(aggregated.keys())
        else:
            # Calculate which emojis were "top" for the most time periods
            all_dates = sorted(set(date for emoji_dates in aggregated.values() for date in emoji_dates.keys()))
            
            emoji_top_count = defaultdict(int)
            
            for date in all_dates:
                date_counts = [(emoji, aggregated[emoji].get(date, 0)) for emoji in aggregated.keys()]
                date_counts.sort(key=lambda x: x[1], reverse=True)
                top_n_this_date = [emoji for emoji, _ in date_counts[:top_n]]
                
                for emoji in top_n_this_date:
                    emoji_top_count[emoji] += 1
            
            selected_emojis = sorted(emoji_top_count.keys(), 
                                    key=lambda e: emoji_top_count[e], 
                                    reverse=True)[:top_n]
        
        # Get all unique dates across selected emojis
        all_dates = sorted(set(
            date for emoji in selected_emojis 
            for date in aggregated[emoji].keys()
        ))
        
        # Build the return structure
        result = {
            'dates': all_dates,
            'emojis': {}
        }
        
        for emoji in selected_emojis:
            counts = [aggregated[emoji].get(date, 0) for date in all_dates]
            result['emojis'][emoji] = counts
        
        return result
    
    def get_item_by_hour(self, sender_number=None, top_n=15, include_all=False):
        """
        Returns emoji usage by hour of day.
        
        Parameters:
        - sender_number: Specific sender to filter by, or None for all senders
        - top_n: Number of top emojis to include (default 15)
        - include_all: If True, includes all emojis regardless of top_n
        
        Returns:
        {
            'hours': [0, 1, 2, ..., 23],
            'emojis': {
                'emoji1': [counts for each hour 0-23],
                'emoji2': [counts for each hour 0-23],
                ...
            }
        }
        """
        # Choose the right data source
        if sender_number is not None:
            if sender_number not in self.item_by_hour_by_sender:
                return {'hours': list(range(24)), 'emojis': {}}
            hour_data = self.item_by_hour_by_sender[sender_number]
        else:
            hour_data = self.item_by_hour
        
        # Select emojis
        if include_all:
            selected_emojis = list(hour_data.keys())
        else:
            emoji_totals = {emoji: sum(hours.values()) for emoji, hours in hour_data.items()}
            selected_emojis = sorted(emoji_totals.keys(), 
                                    key=lambda e: emoji_totals[e], 
                                    reverse=True)[:top_n]
        
        # Build result with all 24 hours
        result = {
            'hours': list(range(24)),
            'emojis': {}
        }
        
        for emoji in selected_emojis:
            counts = [hour_data[emoji].get(hour, 0) for hour in range(24)]
            result['emojis'][emoji] = counts
        
        return result