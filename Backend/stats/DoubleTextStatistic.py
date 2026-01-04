from stats.BaseStatistic import BaseStatistic
from collections import defaultdict
from datetime import timedelta, datetime, time
from Message import Message
import logging

class DoubleTextStatistic(BaseStatistic):
    """Tracks double texting patterns (when same sender sends 2+ messages in a row)."""
    
    def __init__(self, log_file=None):
        super().__init__()
        # Track time between double texts - now using datetime keys for consistency
        self.time_between_timeline = defaultdict(lambda: defaultdict(list))  # {sender: {datetime: [time_diffs]}}
        self.time_between_by_hour = defaultdict(lambda: defaultdict(list))  # {sender: {hour: [time_diffs]}}
        
        # Track sent vs received ratio
        self.sent_timeline = defaultdict(lambda: defaultdict(int))  # {sender: {datetime: count}}
        self.received_timeline = defaultdict(lambda: defaultdict(int))  # {sender: {datetime: count}}
        
        # Track state for detecting double texts
        self.last_message_sender = None
        self.last_message_time = None
        self.last_message_text = None
        self.current_streak_start = None  # Track when double text streak started
        self.current_streak_start_text = None
        
        # Set up logging
        self.logger = logging.getLogger('DoubleTextStatistic')
        self.logger.propagate = True  # Ensure it respects the root logger's level

        if log_file:
            file_handler = logging.FileHandler(log_file, mode='w')
            file_handler.setLevel(logging.DEBUG)
            
            # Create formatter
            formatter = logging.Formatter('%(message)s')
            file_handler.setFormatter(formatter)
            
            # Add handler to logger
            self.logger.addHandler(file_handler)
        
        self.logger.info("=" * 80)
        self.logger.info("DOUBLE TEXT LOG")
        self.logger.info("=" * 80)
        self.logger.info("")
    
    def record(self, msg):
        """Record and detect double texts."""
        from Reaction import Reaction
        
        # Skip reactions - they don't count for double texting
        if isinstance(msg, Reaction):
            return
        
        # Only process Message objects
        if not isinstance(msg, Message):
            return
        
        date = msg.timestamp.date()
        hour = msg.timestamp.hour
        datetime_key = datetime.combine(date, time(hour=hour))
        
        # Record sent/received for this message
        self.sent_timeline[msg.sender][datetime_key] += 1
        
        # Record this as "received" for all other senders (whoever wasn't the sender)
        # This will be populated as we process messages
        
        # Get message text for logging (handle None case)
        current_text = msg.text if msg.text else "[No text content]"
        
        # Check if this is a double text
        if self.last_message_sender == msg.sender and self.last_message_sender is not None:
            # This is a double text!
            self._record_base(msg.sender, date, hour)
            
            # Log the double text
            self.logger.info("-" * 80)
            self.logger.info(f"DOUBLE TEXT DETECTED")
            self.logger.info(f"Sender: {msg.sender_name} ({msg.sender})")
            self.logger.info(f"Date: {msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info("")
            self.logger.info("Previous message (anchor):")
            self.logger.info(f"  Time: {self.last_message_time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info(f"  Text: {self.last_message_text[:100]}{'...' if len(self.last_message_text) > 100 else ''}")
            self.logger.info("")
            self.logger.info("Current message (double text):")
            self.logger.info(f"  Time: {msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info(f"  Text: {current_text[:100]}{'...' if len(current_text) > 100 else ''}")
            
            # Calculate time between this message and the start of the streak
            if self.current_streak_start is not None:
                time_diff = (msg.timestamp - self.current_streak_start).total_seconds() / 60  # in minutes
                
                self.logger.info("")
                self.logger.info(f"Time since streak start: {time_diff:.2f} minutes")
                
                if self.current_streak_start != self.last_message_time:
                    self.logger.info("(Part of a longer streak)")
                    self.logger.info(f"Streak started with:")
                    self.logger.info(f"  Time: {self.current_streak_start.strftime('%Y-%m-%d %H:%M:%S')}")
                    self.logger.info(f"  Text: {self.current_streak_start_text[:100]}{'...' if len(self.current_streak_start_text) > 100 else ''}")
                
                # Record time between double texts
                self.time_between_timeline[msg.sender][datetime_key].append(time_diff)
                self.time_between_by_hour[msg.sender][hour].append(time_diff)
            
            self.logger.info("")
            
            # Update streak start to previous message (for next double text in streak)
            self.current_streak_start = self.last_message_time
            self.current_streak_start_text = self.last_message_text
        else:
            # New sender, potential end of previous streak
            if self.last_message_sender is not None:
                self.logger.info(f"[Sender changed from {self.last_message_sender} to {msg.sender} at {msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')}]")
                self.logger.info("")
            
            # Start potential new streak
            self.current_streak_start = msg.timestamp
            self.current_streak_start_text = current_text
        
        # Update last message tracking
        self.last_message_sender = msg.sender
        self.last_message_time = msg.timestamp
        self.last_message_text = current_text
    
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
    
    def get_sent_received_ratio_timeline(self, sender_number, period='week'):
        """
        Returns the ratio of messages sent vs received over time.
        Ratio = sent / (sent + received)
        - 0.5 means equal sending/receiving
        - > 0.5 means sending more than receiving (you're double texting more)
        - < 0.5 means receiving more than sending (they're double texting more)
        
        Parameters:
        - sender_number: Specific sender to get ratio for
        - period: 'hour', 'day', 'week', 'month', or 'year' for aggregation
        
        Returns:
        {
            'dates': [list of dates],
            'ratios': [ratio values 0-1],
            'sent_counts': [messages sent],
            'received_counts': [messages received]
        }
        """
        if sender_number not in self.sent_timeline:
            return {'dates': [], 'ratios': [], 'sent_counts': [], 'received_counts': []}
        
        # Get sent data for this sender
        sent_data = self.sent_timeline[sender_number]
        
        # Calculate received data (all messages NOT from this sender)
        received_data = defaultdict(int)
        for sender, timeline in self.sent_timeline.items():
            if sender != sender_number:
                for dt, count in timeline.items():
                    received_data[dt] += count
        
        # Aggregate by period
        sent_aggregated = defaultdict(int)
        received_aggregated = defaultdict(int)
        
        for dt, count in sent_data.items():
            key = self._get_period_key(dt, period)
            sent_aggregated[key] += count
        
        for dt, count in received_data.items():
            key = self._get_period_key(dt, period)
            received_aggregated[key] += count
        
        # Get all unique dates
        all_dates = sorted(set(list(sent_aggregated.keys()) + list(received_aggregated.keys())))
        
        # Calculate ratios
        ratios = []
        sent_counts = []
        received_counts = []
        
        for date in all_dates:
            sent = sent_aggregated.get(date, 0)
            received = received_aggregated.get(date, 0)
            total = sent + received
            
            if total > 0:
                ratio = sent / total
            else:
                ratio = 0.5  # Default to neutral if no messages
            
            ratios.append(ratio)
            sent_counts.append(sent)
            received_counts.append(received)
        
        return {
            'dates': all_dates,
            'ratios': ratios,
            'sent_counts': sent_counts,
            'received_counts': received_counts
        }
    
    def get_avg_time_between_timeline(self, sender_number=None, period='week', use_median=True):
        """
        Returns time between double texts over time (using median by default).
        
        Parameters:
        - sender_number: Specific sender to filter by, or None for all senders
        - period: 'hour', 'day', 'week', 'month', or 'year' for aggregation
        - use_median: If True, use median (default, more robust). If False, use mean.
        
        Returns:
        {
            'dates': [list of dates],
            'avg_minutes': [time between double texts in minutes - median or mean]
        }
        """
        # Choose data source
        if sender_number is not None:
            if sender_number not in self.time_between_timeline:
                return {'dates': [], 'avg_minutes': []}
            timeline_data = self.time_between_timeline[sender_number]
        else:
            # Aggregate across all senders
            timeline_data = defaultdict(list)
            for sender_data in self.time_between_timeline.values():
                for dt, times in sender_data.items():
                    timeline_data[dt].extend(times)
        
        # Aggregate by period
        aggregated = defaultdict(list)
        
        for dt, time_diffs in timeline_data.items():
            key = self._get_period_key(dt, period)
            aggregated[key].extend(time_diffs)
        
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
    
    def get_avg_time_between_by_hour(self, sender_number=None, use_median=True):
        """
        Returns time between double texts by hour of day (using median by default).
        
        Parameters:
        - sender_number: Specific sender to filter by, or None for all senders
        - use_median: If True, use median (default, more robust). If False, use mean.
        
        Returns:
        {
            'hours': [0, 1, 2, ..., 23],
            'avg_minutes': [time between double texts for each hour - median or mean]
        }
        """
        # Choose data source
        if sender_number is not None:
            if sender_number not in self.time_between_by_hour:
                return {'hours': list(range(24)), 'avg_minutes': [0] * 24}
            hour_data = self.time_between_by_hour[sender_number]
        else:
            # Aggregate across all senders
            hour_data = defaultdict(list)
            for sender_data in self.time_between_by_hour.values():
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