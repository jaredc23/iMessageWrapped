from stats.BaseStatistic import BaseStatistic
from collections import defaultdict
from datetime import datetime, time
from Message import Message
from Reaction import Reaction

class ResponseTimeStatistic(BaseStatistic):
    """Tracks response time patterns (time between receiving and sending messages)."""
    
    def __init__(self):
        super().__init__()
        # Track response times
        self.response_time_timeline = defaultdict(lambda: defaultdict(list))  # {sender: {datetime: [response_times]}}
        self.response_time_by_hour = defaultdict(lambda: defaultdict(list))  # {sender: {hour: [response_times]}}
        
        # Track state for detecting responses
        self.last_message_sender = None
        self.last_message_time = None
        self.last_message_date = None
        self.last_message_hour = None
    
    def record(self, msg):
        """Record message and calculate response time if applicable."""
        # Process both Messages and Reactions
        if not isinstance(msg, (Message, Reaction)):
            return
        
        current_sender = msg.sender
        current_time = msg.timestamp
        current_date = current_time.date()
        current_hour = current_time.hour
        
        # Check if this is a response (different sender than last message)
        if self.last_message_sender is not None and self.last_message_sender != current_sender:
            # This is a response!
            response_time_minutes = (current_time - self.last_message_time).total_seconds() / 60
            
            # Create datetime key for the ORIGINAL message time (when it was sent, not when response came)
            datetime_key = datetime.combine(self.last_message_date, time(hour=self.last_message_hour))
            
            # Record response time at the time the ORIGINAL message was sent
            self.response_time_timeline[current_sender][datetime_key].append(response_time_minutes)
            self.response_time_by_hour[current_sender][self.last_message_hour].append(response_time_minutes)
            
            # Also record in base class for counting responses
            self._record_base(current_sender, self.last_message_date, self.last_message_hour)
        
        # Update last message tracking
        self.last_message_sender = current_sender
        self.last_message_time = current_time
        self.last_message_date = current_date
        self.last_message_hour = current_hour
    
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
    
    def get_response_time_timeline(self, sender_number=None, period='week', use_median=True):
        """
        Returns response time over time (using median by default for robustness).
        
        Parameters:
        - sender_number: Specific sender to filter by (whose responses to measure), or None for all
        - period: 'hour', 'day', 'week', 'month', or 'year' for aggregation
        - use_median: If True, use median (default, more robust). If False, use mean.
        
        Returns:
        {
            'dates': [list of dates/datetimes],
            'avg_minutes': [response time in minutes - median or mean]
        }
        """
        # Choose data source
        if sender_number is not None:
            if sender_number not in self.response_time_timeline:
                return {'dates': [], 'avg_minutes': []}
            timeline_data = self.response_time_timeline[sender_number]
        else:
            # Aggregate across all senders
            timeline_data = defaultdict(list)
            for sender_data in self.response_time_timeline.values():
                for dt, times in sender_data.items():
                    timeline_data[dt].extend(times)
        
        # Aggregate by period
        aggregated = defaultdict(list)
        
        for dt, response_times in timeline_data.items():
            key = self._get_period_key(dt, period)
            aggregated[key].extend(response_times)
        
        # Calculate median or mean
        sorted_data = sorted(aggregated.items())
        
        if use_median:
            avg_values = [self._median(times) for _, times in sorted_data]
        else:
            avg_values = [sum(times) / len(times) if times else 0 for _, times in sorted_data]
        
        return {
            'dates': [d for d, _ in sorted_data],
            'avg_minutes': avg_values
        }
    
    def get_response_time_by_hour(self, sender_number=None, use_median=True):
        """
        Returns response time by hour of day (hour when original message was sent).
        Uses median by default for robustness to outliers.
        
        Parameters:
        - sender_number: Specific sender to filter by (whose responses to measure), or None for all
        - use_median: If True, use median (default, more robust). If False, use mean.
        
        Returns:
        {
            'hours': [0, 1, 2, ..., 23],
            'avg_minutes': [response time for each hour - median or mean]
        }
        """
        # Choose data source
        if sender_number is not None:
            if sender_number not in self.response_time_by_hour:
                return {'hours': list(range(24)), 'avg_minutes': [0] * 24}
            hour_data = self.response_time_by_hour[sender_number]
        else:
            # Aggregate across all senders
            hour_data = defaultdict(list)
            for sender_data in self.response_time_by_hour.values():
                for hour, times in sender_data.items():
                    hour_data[hour].extend(times)
        
        # Calculate median or mean for each hour
        avg_minutes = []
        for hour in range(24):
            times = hour_data.get(hour, [])
            if use_median:
                avg_minutes.append(self._median(times))
            else:
                avg_minutes.append(sum(times) / len(times) if times else 0)
        
        return {
            'hours': list(range(24)),
            'avg_minutes': avg_minutes
        }