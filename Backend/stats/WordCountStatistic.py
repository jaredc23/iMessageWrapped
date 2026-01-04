from stats.BaseStatistic import BaseStatistic
from collections import defaultdict
from datetime import datetime, time

class WordCountStatistic(BaseStatistic):
    """Tracks word count patterns in messages."""
    
    def __init__(self):
        super().__init__()
        # Track word counts per message
        self.words_per_message_timeline = defaultdict(lambda: defaultdict(list))  # {sender: {datetime: [word_counts]}}
        self.words_per_message_by_hour = defaultdict(lambda: defaultdict(list))  # {sender: {hour: [word_counts]}}
        
        # Track total words (for words over time graph)
        self.total_words_timeline = defaultdict(lambda: defaultdict(int))  # {sender: {datetime: total_words}}
        self.total_words_by_hour = defaultdict(lambda: defaultdict(int))  # {sender: {hour: total_words}}
        
        # Debug counters
        self.debug_total_messages = 0
        self.debug_messages_with_text = 0
        self.debug_messages_recorded = 0
    
    def record(self, msg):
        """Record word count from a message."""
        from Message import Message
        from Reaction import Reaction
        
        self.debug_total_messages += 1
        
        # Skip reactions - only count actual messages
        if isinstance(msg, Reaction):
            return
        
        # Only process Message objects
        if not isinstance(msg, Message):
            return
        
        # Check if message has text
        if not msg.text:
            return
        
        self.debug_messages_with_text += 1
        
        # Count words (split by whitespace and filter empty strings)
        words = [w for w in msg.text.split() if w.strip()]
        word_count = len(words)
        
        # Skip messages with no words
        if word_count == 0:
            return
        
        self.debug_messages_recorded += 1
        
        date = msg.timestamp.date()
        hour = msg.timestamp.hour
        
        # Create datetime key
        datetime_key = datetime.combine(date, time(hour=hour))
        
        # Record word count per message
        self.words_per_message_timeline[msg.sender][datetime_key].append(word_count)
        self.words_per_message_by_hour[msg.sender][hour].append(word_count)
        
        # Record total words
        self.total_words_timeline[msg.sender][datetime_key] += word_count
        self.total_words_by_hour[msg.sender][hour] += word_count
        
        # Also record in base class for counting messages with text
        self._record_base(msg.sender, date, hour)
    
    def print_debug_info(self):
        """Print debug information about what was recorded."""
        print(f"\n=== WordCountStatistic Debug Info ===")
        print(f"Total messages processed: {self.debug_total_messages}")
        print(f"Messages with text: {self.debug_messages_with_text}")
        print(f"Messages recorded (word count > 0): {self.debug_messages_recorded}")
        print(f"Unique senders with word data: {len(self.words_per_message_timeline)}")
        
        if self.words_per_message_timeline:
            print(f"\nSenders tracked:")
            for sender in self.words_per_message_timeline.keys():
                total_messages = sum(len(counts) for counts in self.words_per_message_timeline[sender].values())
                print(f"  - {sender}: {total_messages} messages with text")
    
    @staticmethod
    def _median(lst):
        """Calculate median of a list."""
        if not lst:
            return 0
        sorted_lst = sorted(lst)
        n = len(sorted_lst)
        if n % 2 == 0:
            return (sorted_lst[n//2 - 1] + sorted_lst[n//2]) / 2
        else:
            return sorted_lst[n//2]
    
    def get_total_words_timeline(self, sender_number=None, period='week'):
        """
        Returns total word count over time.
        
        Parameters:
        - sender_number: Specific sender to filter by, or None for all senders
        - period: 'hour', 'day', 'week', 'month', or 'year' for aggregation
        
        Returns:
        {
            'dates': [list of dates/datetimes],
            'counts': [total words for each period]
        }
        """
        # Choose data source
        if sender_number is not None:
            if sender_number not in self.total_words_timeline:
                return {'dates': [], 'counts': []}
            timeline_data = self.total_words_timeline[sender_number]
        else:
            # Aggregate across all senders
            timeline_data = defaultdict(int)
            for sender_data in self.total_words_timeline.values():
                for dt, count in sender_data.items():
                    timeline_data[dt] += count
        
        # Aggregate by period
        aggregated = defaultdict(int)
        
        for dt, count in timeline_data.items():
            key = self._get_period_key(dt, period)
            aggregated[key] += count
        
        # Sort by date
        sorted_data = sorted(aggregated.items())
        
        return {
            'dates': [d for d, _ in sorted_data],
            'counts': [c for _, c in sorted_data]
        }
    
    def get_words_per_message_timeline(self, sender_number=None, period='week', use_median=True):
        """
        Returns average words per message over time.
        
        Parameters:
        - sender_number: Specific sender to filter by, or None for all senders
        - period: 'hour', 'day', 'week', 'month', or 'year' for aggregation
        - use_median: If True, use median (default). If False, use mean.
        
        Returns:
        {
            'dates': [list of dates/datetimes],
            'avg_words': [average words per message - median or mean]
        }
        """
        # Choose data source
        if sender_number is not None:
            if sender_number not in self.words_per_message_timeline:
                return {'dates': [], 'avg_words': []}
            timeline_data = self.words_per_message_timeline[sender_number]
        else:
            # Aggregate across all senders
            timeline_data = defaultdict(list)
            for sender_data in self.words_per_message_timeline.values():
                for dt, counts in sender_data.items():
                    timeline_data[dt].extend(counts)
        
        # Aggregate by period
        aggregated = defaultdict(list)
        
        for dt, word_counts in timeline_data.items():
            key = self._get_period_key(dt, period)
            aggregated[key].extend(word_counts)
        
        # Calculate median or mean
        sorted_data = sorted(aggregated.items())
        
        if use_median:
            avg_values = [self._median(counts) for _, counts in sorted_data]
        else:
            avg_values = [sum(counts) / len(counts) if counts else 0 for _, counts in sorted_data]
        
        return {
            'dates': [d for d, _ in sorted_data],
            'avg_words': avg_values
        }
    
    def get_words_per_message_by_hour(self, sender_number=None, use_median=True):
        """
        Returns average words per message by hour of day.
        
        Parameters:
        - sender_number: Specific sender to filter by, or None for all senders
        - use_median: If True, use median (default). If False, use mean.
        
        Returns:
        {
            'hours': [0, 1, 2, ..., 23],
            'avg_words': [average words per message for each hour - median or mean]
        }
        """
        # Choose data source
        if sender_number is not None:
            if sender_number not in self.words_per_message_by_hour:
                return {'hours': list(range(24)), 'avg_words': [0] * 24}
            hour_data = self.words_per_message_by_hour[sender_number]
        else:
            # Aggregate across all senders
            hour_data = defaultdict(list)
            for sender_data in self.words_per_message_by_hour.values():
                for hour, counts in sender_data.items():
                    hour_data[hour].extend(counts)
        
        # Calculate median or mean for each hour
        avg_words = []
        for hour in range(24):
            counts = hour_data.get(hour, [])
            if use_median:
                avg_words.append(self._median(counts))
            else:
                avg_words.append(sum(counts) / len(counts) if counts else 0)
        
        return {
            'hours': list(range(24)),
            'avg_words': avg_words
        }
    
    def get_overall_avg_words_per_message(self, sender_number=None, use_median=True):
        """
        Returns the overall average words per message across all time.
        
        Parameters:
        - sender_number: Specific sender to filter by, or None for all senders
        - use_median: If True, use median (default). If False, use mean.
        
        Returns:
        float: Average words per message
        """
        # Choose data source
        if sender_number is not None:
            if sender_number not in self.words_per_message_timeline:
                return 0
            timeline_data = self.words_per_message_timeline[sender_number]
        else:
            # Aggregate across all senders
            timeline_data = defaultdict(list)
            for sender_data in self.words_per_message_timeline.values():
                for dt, counts in sender_data.items():
                    timeline_data[dt].extend(counts)
        
        # Collect all word counts
        all_counts = []
        for counts in timeline_data.values():
            all_counts.extend(counts)
        
        if not all_counts:
            return 0
        
        if use_median:
            return self._median(all_counts)
        else:
            return sum(all_counts) / len(all_counts)