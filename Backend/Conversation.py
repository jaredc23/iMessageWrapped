import json
import re
from pathlib import Path
from Message import Message
from Reaction import Reaction
from iMessage import iMessage

from stats.MessageStatistic import MessageStatistic
from stats.AttachmentStatistic import AttachmentStatistic
from stats.EmojiStatistic import EmojiStatistic
from stats.DoubleTextStatistic import DoubleTextStatistic
from stats.ResponseTimeStatistic import ResponseTimeStatistic
from stats.WordCountStatistic import WordCountStatistic

class Conversation:

    def __init__(self, json_path, chat_name_dict=None):
        self.filepath = json_path  # Add this line
        with open(json_path, "r") as f:
            self.json_data = json.load(f)

        self.thread: list[iMessage] = []
        self.messages: dict[str, Message] = {}
        self.reactions: dict[str, Reaction] = {}

        self.skipped_count = 0

        if(chat_name_dict is None):
            matches = re.findall(r"chat_.*\.json", json_path)
            self.chat_name = matches[0] if matches else Path(json_path).stem
        else:
            key_matches = re.findall(r"chat_.*\.json", json_path)
            key = key_matches[0] if key_matches else Path(json_path).name
            # prefer user-provided mapping, fallback to the filename key
            mapped = chat_name_dict.get(key, key)
            # mapping may be either a string (legacy) or an object {"name": ..., "include": ...}
            if isinstance(mapped, dict):
                self.chat_name = mapped.get('name', key)
            else:
                self.chat_name = mapped

        for item in self.json_data:
            if(item["is_reaction"]):
                try:
                    self.reactions[item["guid"]] = Reaction(item)
                    self.thread.append(self.reactions[item["guid"]])
                    self.messages[self.reactions[item["guid"]].assoc_guid].addReaction(self.reactions[item["guid"]])
                except Exception as e:
                    self.skipped_count += 1
            else:
                self.messages[item["guid"]] = Message(item)
                self.thread.append(self.messages[item["guid"]])

    def calculate_statistics(self, show_progress=False, pbar_position=None):
        """Calculate median/average statistics for this conversation.

        If `show_progress` is True and `tqdm` is available, show a small progress
        bar while iterating through messages. `pbar_position` specifies the
        tqdm position so multiple bars can be displayed concurrently.
        """
        from collections import defaultdict
        try:
            if show_progress:
                try:
                    from tqdm import tqdm
                    pbar = tqdm(self.thread, desc=f"Processing {self.chat_name}", position=pbar_position, leave=False)
                    iterator = pbar
                except Exception:
                    iterator = self.thread
            else:
                iterator = self.thread

            # Initialize statistic trackers
            self.message_stats = MessageStatistic()
            self.attachment_stats = AttachmentStatistic()
            self.emoji_stats = EmojiStatistic()
            self.double_text_stats = DoubleTextStatistic()
            self.response_time_stats = ResponseTimeStatistic()
            self.word_count_stats = WordCountStatistic()
        
            # Dictionary of unique senders
            self.senders = {}

            # Process all messages
            for msg in iterator:
                # Track unique senders
                if msg.sender not in self.senders:
                    self.senders[msg.sender] = {
                        "name": msg.sender_name,
                        "messages_sent": 0,
                        "reactions_sent": 0,
                        "messages_unsent": 0,
                        "attachments_sent": 0
                    }
        
                # Update sender counts
                if type(msg) is Reaction:
                    self.senders[msg.sender]["reactions_sent"] += 1
                else:
                    self.senders[msg.sender]["messages_sent"] += 1
        
                if msg.is_unsent:
                    self.senders[msg.sender]["messages_unsent"] += 1
        
                if type(msg) is Message and msg.has_attachment:
                    self.senders[msg.sender]["attachments_sent"] += 1
        
                # Record in statistics
                self.message_stats.record(msg)
                self.attachment_stats.record(msg)
                self.emoji_stats.record(msg)
                self.double_text_stats.record(msg)
                self.response_time_stats.record(msg)
                self.word_count_stats.record(msg)

        except Exception as e:
            print(f"Error calculating statistics for {getattr(self, 'chat_name', '<unknown>')}: {e}")
            import traceback
            traceback.print_exc()
    
    # Convenience methods for backward compatibility
    def get_emoji_totals(self, sender_number):
        """Returns emoji totals for a sender in [[emoji list][count]] format."""
        return self.emoji_stats.get_totals(sender_number)
    
    def get_emoji_timeline(self, sender_number=None, period='week', top_n=15, include_all=False):
        """Returns emoji usage over time."""
        return self.emoji_stats.get_item_timeline(sender_number, period, top_n, include_all)
    
    def get_emoji_by_hour(self, sender_number=None, top_n=15, include_all=False):
        """Returns emoji usage by hour."""
        return self.emoji_stats.get_item_by_hour(sender_number, top_n, include_all)
    
    def get_messages_timeline(self, sender_number=None, period='week'):
        """Returns message count over time."""
        return self.message_stats.get_timeline(sender_number, period)
    
    def get_messages_by_hour(self, sender_number=None):
        """Returns message count by hour."""
        return self.message_stats.get_by_hour(sender_number)
    
    def get_attachments_timeline(self, sender_number=None, period='week'):
        """Returns attachment count over time."""
        return self.attachment_stats.get_timeline(sender_number, period)
    
    def get_attachments_by_hour(self, sender_number=None):
        """Returns attachment count by hour."""
        return self.attachment_stats.get_by_hour(sender_number)
    
    def get_double_texts_timeline(self, sender_number=None, period='week'):
        """Returns double text count over time."""
        return self.double_text_stats.get_timeline(sender_number, period)

    def get_double_texts_by_hour(self, sender_number=None):
        """Returns double text count by hour."""
        return self.double_text_stats.get_by_hour(sender_number)

    def get_avg_time_between_double_texts_timeline(self, sender_number=None, period='week', use_median=True):
        """Returns time between double texts over time (median by default, use_median=False for mean)."""
        return self.double_text_stats.get_avg_time_between_timeline(sender_number, period, use_median)

    def get_avg_time_between_double_texts_by_hour(self, sender_number=None, use_median=True):
        """Returns time between double texts by hour (median by default, use_median=False for mean)."""
        return self.double_text_stats.get_avg_time_between_by_hour(sender_number, use_median)
    
    def get_response_times_timeline(self, sender_number=None, period='week'):
        """Returns response time count over time."""
        return self.response_time_stats.get_timeline(sender_number, period)

    def get_response_times_by_hour(self, sender_number=None):
        """Returns response time count by hour."""
        return self.response_time_stats.get_by_hour(sender_number)

    def get_avg_response_time_timeline(self, sender_number=None, period='week', use_median=True):
        """Returns response time over time (median by default, use_median=False for mean)."""
        return self.response_time_stats.get_response_time_timeline(sender_number, period, use_median)

    def get_avg_response_time_by_hour(self, sender_number=None, use_median=True):
        """Returns response time by hour (median by default, use_median=False for mean)."""
        return self.response_time_stats.get_response_time_by_hour(sender_number, use_median)

    def get_total_words_timeline(self, sender_number=None, period='week'):
        """Returns total word count over time."""
        return self.word_count_stats.get_total_words_timeline(sender_number, period)

    def get_words_per_message_timeline(self, sender_number=None, period='week', use_median=True):
        """Returns average words per message over time (median by default)."""
        return self.word_count_stats.get_words_per_message_timeline(sender_number, period, use_median)

    def get_words_per_message_by_hour(self, sender_number=None, use_median=True):
        """Returns average words per message by hour (median by default)."""
        return self.word_count_stats.get_words_per_message_by_hour(sender_number, use_median)

    def get_overall_avg_words_per_message(self, sender_number=None, use_median=True):
        """Returns overall average words per message across all time (median by default)."""
        return self.word_count_stats.get_overall_avg_words_per_message(sender_number, use_median)

    def __str__(self):
        return f"<Conversation ({len(self.thread)} messages)>"

    def printConvo(self):
        for item in self.thread:
            print(item)

    def delete_json_file(self):
        """Delete the underlying conversation JSON file from disk.

        Returns True if the file was deleted, False if the file did not
        exist or an error occurred.
        """
        try:
            p = Path(self.filepath)
        except Exception:
            return False

        try:
            if p.exists():
                p.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting conversation file {p}: {e}")
            return False

if __name__ == "__main__":
    name_dict = {}
    with open("exports/number_to_name.json", "r") as f:
        name_dict = json.load(f)
    c = Conversation("exports/chat_576.json", chat_name_dict=name_dict)
    #c.calculate_statistics()
    #print(c.senders)
    #print(c.get_emoji_totals("You"))
    print(name_dict)
    print(c.chat_name)