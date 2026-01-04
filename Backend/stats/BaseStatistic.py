from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime, time, timedelta

class BaseStatistic(ABC):
    """Abstract base class for all conversation statistics."""
    
    def __init__(self):
        self.timeline = defaultdict(int)  # {datetime: count}
        self.timeline_by_sender = defaultdict(lambda: defaultdict(int))  # {sender: {datetime: count}}
        self.by_hour = defaultdict(int)  # {hour: count}
        self.by_hour_by_sender = defaultdict(lambda: defaultdict(int))  # {sender: {hour: count}}
    
    @abstractmethod
    def record(self, msg):
        """Record a message. Must be implemented by subclasses."""
        pass
    
    def _record_base(self, sender, date, hour):
        """Common recording logic for timeline and hour tracking."""
        # Store by datetime (date + hour) for hourly support
        datetime_key = datetime.combine(date, time(hour=hour))
        
        self.timeline[datetime_key] += 1
        self.timeline_by_sender[sender][datetime_key] += 1
        self.by_hour[hour] += 1
        self.by_hour_by_sender[sender][hour] += 1
    
    def get_timeline(self, sender_number=None, period='week'):
        """
        Returns data over time.
        
        Parameters:
        - sender_number: Specific sender to filter by, or None for all senders
        - period: 'hour', 'day', 'week', 'month', or 'year' for aggregation
        
        Returns:
        {
            'dates': [list of dates/datetimes],
            'counts': [counts]
        }
        """
        # Choose data source
        if sender_number is not None:
            if sender_number not in self.timeline_by_sender:
                return {'dates': [], 'counts': []}
            timeline_data = self.timeline_by_sender[sender_number]
        else:
            timeline_data = self.timeline
        
        # Aggregate by period
        aggregated = defaultdict(int)
        
        for dt, count in timeline_data.items():
            key = self._get_period_key(dt, period)
            aggregated[key] += count
        
        # Sort by date/datetime
        sorted_data = sorted(aggregated.items())
        
        return {
            'dates': [d for d, _ in sorted_data],
            'counts': [c for _, c in sorted_data]
        }
    
    def get_by_hour(self, sender_number=None):
        """
        Returns data by hour of day.
        
        Parameters:
        - sender_number: Specific sender to filter by, or None for all senders
        
        Returns:
        {
            'hours': [0, 1, 2, ..., 23],
            'counts': [counts for each hour]
        }
        """
        # Choose data source
        if sender_number is not None:
            if sender_number not in self.by_hour_by_sender:
                return {'hours': list(range(24)), 'counts': [0] * 24}
            hour_data = self.by_hour_by_sender[sender_number]
        else:
            hour_data = self.by_hour
        
        return {
            'hours': list(range(24)),
            'counts': [hour_data.get(hour, 0) for hour in range(24)]
        }
    
    @staticmethod
    def _get_period_key(dt, period):
        """Convert a datetime to the appropriate period key."""
        if period == 'hour':
            # Round down to the hour
            return dt.replace(minute=0, second=0, microsecond=0)
        elif period == 'day':
            return dt.date()
        elif period == 'week':
            date = dt.date()
            return date - timedelta(days=date.weekday())
        elif period == 'month':
            return dt.date().replace(day=1)
        elif period == 'year':
            return dt.date().replace(month=1, day=1)
        else:
            raise ValueError(f"Invalid period: {period}. Use 'hour', 'day', 'week', 'month', or 'year'.")