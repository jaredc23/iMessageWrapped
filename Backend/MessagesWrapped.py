import json
import os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from concurrent.futures.process import BrokenProcessPool
from collections import defaultdict
from datetime import datetime, date, time
import multiprocessing
from Conversation import Conversation
import logging

def setup_logging(verbose_file=None):
    """Set up logging to console and optionally to a file."""
    log_format = "%(asctime)s - %(levelname)s - %(message)s"

    # Default console logging level is WARNING (suppress INFO logs)
    logging.basicConfig(level=logging.WARNING, format=log_format)

    # Explicitly set the root logger level to WARNING to suppress all INFO logs
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)

    if verbose_file:
        # Enable DEBUG level logging to the specified file
        file_handler = logging.FileHandler(verbose_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(file_handler)

        # Set console logging to INFO level for progress updates
        root_logger.setLevel(logging.INFO)
    else:
        # Ensure only progress bars are shown without verbose logging
        root_logger.setLevel(logging.WARNING)

def load_and_calculate_conversation(filepath, name_dict=None, show_progress=False, position=None):
    """
    Helper function to load and calculate statistics for a single conversation.
    This needs to be a top-level function for multiprocessing to work.
    """
    try:
        filepath = str(filepath)  # Ensure filepath is a string
        convo = Conversation(filepath, chat_name_dict=name_dict)
        # Calculate statistics, optionally showing per-conversation progress
        try:
            convo.calculate_statistics(show_progress=show_progress, pbar_position=position)
        except TypeError:
            # Backward compatibility if Conversation.calculate_statistics doesn't accept args
            convo.calculate_statistics()
        return convo
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return None

class MessagesWrapped:
    """
    Aggregates multiple conversations for overall statistics and comparisons.
    """
    
    def __init__(self, conversations_dir="exports", max_workers=None, use_processes=False, show_progress=True):
        """
        Initialize MessagesWrapped with conversations from a directory.
        
        Parameters:
        - conversations_dir: Directory containing conversation JSON files
        - max_workers: Maximum number of parallel workers (None = CPU count)
        - use_processes: If True, use ProcessPoolExecutor. If False, use ThreadPoolExecutor
        """
        self.conversations_dir = conversations_dir
        self.conversations = []
        self.conversation_metadata = {}

        self.name_dict = {} # Dictionary to convert filenames (chat_#.json) to get the user's chat name
        mapping_path = Path(self.conversations_dir) / "number_to_name.json"
        if mapping_path.exists():
            try:
                with open(mapping_path, "r", encoding="utf-8") as f:
                    self.name_dict = json.load(f)
            except Exception as e:
                print(f"Warning: failed to load mapping {mapping_path}: {e}")
                self.name_dict = {}
        else:
            # No mapping file found; initialize empty mapping
            self.name_dict = {}
        
        # Determine number of workers
        if max_workers is None:
            max_workers = multiprocessing.cpu_count()
        # Ensure max_workers is capped to avoid resource exhaustion
        if max_workers is None or max_workers > 10:
            max_workers = min(10, os.cpu_count() or 1)
        self.max_workers = max_workers
        # Prefer threads by default; on macOS process pools are often unstable
        import sys
        if use_processes and sys.platform == 'darwin':
            print("ProcessPoolExecutor disabled on macOS — using threads instead.")
            self.use_processes = False
        else:
            self.use_processes = use_processes
        # Whether to show a loading progress bar; can be disabled for CI or quiet runs
        self.show_progress = show_progress
        
        print(f"Initializing MessagesWrapped with {self.max_workers} workers...")
        self._load_conversations()
        self._calculate_metadata()
        print(f"Loaded {len(self.conversations)} conversations successfully!")
    
    def _load_conversations(self):
        """Load all conversation files in parallel."""
        # Find all JSON files in the directory
        json_files = list(Path(self.conversations_dir).glob("chat_*.json"))
        filtered_files = []
        skipped_files = []

        for p in json_files:
            key = p.name
            mapping = self.name_dict.get(key)
            try:
                if isinstance(mapping, dict) and mapping.get('include') is False:
                    skipped_files.append(p)
                    continue
            except Exception:
                pass
            filtered_files.append(p)

        if skipped_files:
            logging.info(f"Skipped {len(skipped_files)} files due to name_dict settings.")

        json_files = filtered_files

        if not json_files:
            logging.warning("No conversation files found after filtering.")
            return

        logging.info(f"Found {len(json_files)} conversation files.")
        logging.info(f"Using {'ProcessPoolExecutor' if self.use_processes else 'ThreadPoolExecutor'} with {self.max_workers} workers.")

        # Choose executor type
        ExecutorClass = ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor
        
        # Load conversations in parallel
        successful = 0
        failed = 0

        # Initialize progress bar if enabled
        use_tqdm = False
        pbar = None
        if self.show_progress:
            try:
                from tqdm import tqdm
                use_tqdm = True
                pbar = tqdm(total=len(json_files), desc="Loading chats")
            except Exception:
                print(f"Starting load of {len(json_files)} chats...")

        # Process files in smaller batches to avoid too many open files
        batch_size = 100  # Adjust batch size as needed
        for i in range(0, len(json_files), batch_size):
            batch = json_files[i:i + batch_size]
            logging.info(f"Processing batch {i // batch_size + 1} with {len(batch)} files.")

            with ExecutorClass(max_workers=self.max_workers) as executor:
                future_to_file = {executor.submit(load_and_calculate_conversation, file, self.name_dict, self.show_progress): file for file in batch}

                for future in as_completed(future_to_file):
                    file = future_to_file[future]
                    try:
                        convo = future.result()
                        if convo:
                            self.conversations.append(convo)
                            successful += 1
                            logging.debug(f"Successfully loaded conversation: {file}")
                        else:
                            failed += 1
                            logging.warning(f"Failed to load conversation: {file}")
                    except Exception as e:
                        failed += 1
                        logging.error(f"Error processing {file}: {e}")

            logging.info(f"Batch {i // batch_size + 1} complete: {successful} successful, {failed} failed so far.")

        logging.info(f"Loading complete: {successful} successful, {failed} failed.")

    
    def _calculate_metadata(self):
        """Calculate metadata for each conversation."""
        print("\nCalculating metadata for conversations...")
        
        for idx, convo in enumerate(self.conversations):
            try:
                # Extract conversation name from filepath (prefer mapped human name)
                if hasattr(convo, 'filepath'):
                    file_path = Path(convo.filepath)
                    file_stem = file_path.stem  # e.g., "chat_573"
                    file_name = file_path.name
                    # If a mapping exists in `self.name_dict`, prefer its `name` field
                    mapping = None
                    try:
                        mapping = self.name_dict.get(file_name) or self.name_dict.get(file_stem)
                    except Exception:
                        mapping = None

                    if isinstance(mapping, dict) and mapping.get('name'):
                        convo_name = mapping.get('name')
                    else:
                        convo_name = file_stem
                else:
                    convo_name = f"conversation_{idx}"
                
                # Count unique participants
                unique_senders = len(convo.senders)
                is_group_chat = unique_senders > 2
                
                # Get first and last message timestamps
                if convo.thread:
                    first_message = convo.thread[0].timestamp
                    last_message = convo.thread[-1].timestamp
                    duration_days = (last_message - first_message).days
                    if duration_days == 0:
                        duration_days = 1  # Avoid division by zero
                else:
                    first_message = None
                    last_message = None
                    duration_days = 1
                
                # Calculate summary statistics
                total_messages = sum(s["messages_sent"] for s in convo.senders.values())
                total_reactions = sum(s["reactions_sent"] for s in convo.senders.values())
                total_attachments = sum(s["attachments_sent"] for s in convo.senders.values())
                
                # Get participant names
                participant_names = [s["name"] for s in convo.senders.values()]
                
                # Store metadata
                self.conversation_metadata[id(convo)] = {
                    "name": convo_name,
                    "filepath": getattr(convo, 'filepath', 'unknown'),
                    "is_group_chat": is_group_chat,
                    "participant_count": unique_senders,
                    "participant_names": participant_names,
                    "total_messages": total_messages,
                    "total_reactions": total_reactions,
                    "total_attachments": total_attachments,
                    "first_message": first_message,
                    "last_message": last_message,
                    "duration_days": duration_days,
                    "messages_per_day": total_messages / duration_days if duration_days > 0 else 0,
                    # Messages sent by the user labeled 'You' (if present)
                    "messages_sent_you": convo.senders.get('You', {}).get('messages_sent', 0),
                    "messages_per_day_you": convo.senders.get('You', {}).get('messages_sent', 0) / duration_days if duration_days > 0 else 0,
                }
                
                # Calculate median statistics for this conversation
                self._calculate_conversation_statistics(convo)
                
                print(f"  ✓ Processed metadata for {convo_name}")
                
            except Exception as e:
                print(f"  ✗ Error calculating metadata for conversation {idx}: {e}")
                import traceback
                traceback.print_exc()

    def _calculate_conversation_statistics(self, convo):
        """Calculate median/average statistics for a single conversation."""
        convo_id = id(convo)
        metadata = self.conversation_metadata[convo_id]
        
        # Get overall averages for all senders combined
        metadata["avg_words_per_message"] = convo.get_overall_avg_words_per_message(use_median=True)
        metadata["mean_words_per_message"] = convo.get_overall_avg_words_per_message(use_median=False)
        
        # Get response time statistics (across all senders)
        response_time_data = convo.get_avg_response_time_timeline(period='day', use_median=True)
        if response_time_data['dates']:
            all_response_times = response_time_data['avg_minutes']
            non_zero_times = [t for t in all_response_times if t > 0]
            if non_zero_times:
                metadata["median_response_time_minutes"] = self._median(non_zero_times)
                metadata["mean_response_time_minutes"] = sum(non_zero_times) / len(non_zero_times)
            else:
                metadata["median_response_time_minutes"] = 0
                metadata["mean_response_time_minutes"] = 0
        else:
            metadata["median_response_time_minutes"] = 0
            metadata["mean_response_time_minutes"] = 0
        
        # Double text statistics
        double_text_data = convo.get_double_texts_timeline(period='day')
        if double_text_data['dates']:
            total_double_texts = sum(double_text_data['counts'])
            metadata["total_double_texts"] = total_double_texts
            metadata["double_texts_per_day"] = total_double_texts / metadata["duration_days"] if metadata["duration_days"] > 0 else 0
        else:
            metadata["total_double_texts"] = 0
            metadata["double_texts_per_day"] = 0
    
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
    
    def get_conversation_comparison(self, sort_by="total_messages", top_n=None):
        """
        Get a comparison of all conversations.
        
        Parameters:
        - sort_by: Metric to sort by (e.g., "total_messages", "messages_per_day", "participant_count")
        - top_n: If provided, only return top N conversations
        
        Returns:
        List of conversation metadata dictionaries, sorted by the specified metric
        """
        comparisons = []
        for convo_id, metadata in self.conversation_metadata.items():
            comparisons.append(metadata)
        
        # Check if we have any comparisons
        if not comparisons:
            return []
        
        # Sort by specified metric (descending)
        if sort_by in comparisons[0]:
            comparisons.sort(key=lambda x: x.get(sort_by, 0), reverse=True)
        
        if top_n:
            comparisons = comparisons[:top_n]
        
        return comparisons

    def _in_date_range(self, dt, start_date, end_date):
        """Return True if datetime/date `dt` falls within [start_date, end_date].

        `dt` may be a date or datetime. `start_date`/`end_date` may be None.
        """
        if dt is None:
            return False
        if isinstance(dt, datetime):
            d = dt.date()
        elif isinstance(dt, date):
            d = dt
        else:
            # Fallback: try to access .date()
            try:
                d = dt.date()
            except Exception:
                return False

        if start_date and d < start_date:
            return False
        if end_date and d > end_date:
            return False
        return True

    def _resolve_sender_key(self, convo, sender_label):
        """Resolve a human-friendly sender label (e.g., 'You') to the sender key
        used inside a Conversation's statistics (often phone number or None).

        If `sender_label` is None, returns None. If the label matches a sender
        key directly, returns it. Otherwise searches `convo.senders` for a
        sender whose `name` equals `sender_label` and returns that key.
        If no match, returns the original label for best-effort behavior.
        """
        if sender_label is None:
            return None
        # direct match
        try:
            if sender_label in getattr(convo, 'senders', {}):
                return sender_label
        except Exception:
            pass

        # find by display name
        for key, info in getattr(convo, 'senders', {}).items():
            if info.get('name') == sender_label:
                return key

        # fallback
        return sender_label

    def _is_group_convo(self, convo):
        """Determine whether a conversation is a group chat.

        Uses several heuristics in order:
        1. If a mapping exists in `self.name_dict` use the mapped name and
           consider it a group when it contains separators (commas, '+') or
           common group keywords.
        2. Fall back to the number of unique active senders seen in `convo.senders`.
        """
        try:
            # Prefer explicit metadata from mapping if available
            convo_fp = getattr(convo, 'filepath', None)
            file_name = None
            if convo_fp:
                file_name = Path(convo_fp).name
                file_stem = Path(convo_fp).stem
            else:
                file_stem = None

            mapping = None
            if file_name and file_name in self.name_dict:
                mapping = self.name_dict.get(file_name)
            elif file_stem and file_stem in self.name_dict:
                mapping = self.name_dict.get(file_stem)

            mapped_name = None
            if isinstance(mapping, dict):
                mapped_name = mapping.get('name')
            elif isinstance(mapping, str):
                mapped_name = mapping

            if isinstance(mapped_name, str) and mapped_name:
                lower = mapped_name.lower()
                # If there are commas or '+' signs it's almost certainly a group
                if ',' in mapped_name or '+' in mapped_name or ' & ' in mapped_name or ' and ' in lower:
                    return True
                # Common group-y names/keywords
                group_keywords = ['family', 'group', 'crew', 'squad', 'team', 'club', 'fam']
                for kw in group_keywords:
                    if kw in lower:
                        return True

            # Fallback: use number of unique senders recorded (active participants)
            unique_senders = len(getattr(convo, 'senders', {}) or {})
            return unique_senders > 2
        except Exception:
            # Conservative fallback: if anything goes wrong, treat as non-group
            try:
                return len(getattr(convo, 'senders', {}) or {}) > 2
            except Exception:
                return False

    def print_conversation_comparison(self, sort_by="total_messages", top_n=10):
        """Print a formatted comparison of conversations."""
        data = self.get_conversation_comparison_data(sort_by=sort_by, top_n=top_n)

        if not data:
            print("\nNo conversations loaded!")
            return

        print(f"\n{'='*80}")
        print(f"TOP {len(data)} CONVERSATIONS (sorted by {sort_by})")
        print(f"{'='*80}\n")

        for i, meta in enumerate(data, 1):
            print(f"{i}. {meta['name']}")
            print(f"   Participants: {', '.join(meta['participant_names'][:3])}{'...' if len(meta['participant_names']) > 3 else ''}")
            print(f"   Type: {'Group Chat' if meta['is_group_chat'] else '1-on-1'} ({meta['participant_count']} people)")
            # Show both overall and your messages/day when available
            print(f"   Messages: {meta['total_messages']:,} ({meta['messages_per_day']:.1f}/day)")
            if meta.get('messages_per_day_you') is not None:
                print(f"   Your messages/day: {meta['messages_per_day_you']:.2f}/day")
            print(f"   Duration: {meta['duration_days']} days")
            print(f"   Reactions: {meta['total_reactions']:,}")
            print(f"   Attachments: {meta['total_attachments']:,}")
            print(f"   Median words/message: {meta['avg_words_per_message']:.1f}")
            print(f"   Median response time: {meta['median_response_time_minutes']:.1f} minutes")
            print()

    def get_conversation_comparison_data(self, sort_by="total_messages", top_n=10, start_date=None, end_date=None):
        """Return conversation comparison data as a list of structured dicts.

        If `start_date`/`end_date` are provided, metrics such as
        `total_messages`, `messages_sent_you`, and `messages_per_day` are
        computed for that inclusive date range. Otherwise the conversation's
        precomputed metadata is used.
        """
        result = []

        for convo_id, meta in self.conversation_metadata.items():
            # find the conversation object
            convo = next((c for c in self.conversations if id(c) == convo_id), None)
            if convo is None:
                continue

            # Default to metadata values
            total_messages = meta.get('total_messages', 0)
            messages_sent_you = meta.get('messages_sent_you', 0)
            # duration_days here will be overridden when a date range is provided
            duration_days = meta.get('duration_days', 0)

            # If a date range is provided, compute totals from daily timelines
            if start_date or end_date:
                # overall messages (all senders)
                try:
                    all_data = convo.get_messages_timeline(sender_number=None, period='day')
                    dates = all_data.get('dates', [])
                    counts = all_data.get('counts', [])
                    filtered_dates = []
                    total_messages = 0
                    for dt, c in zip(dates, counts):
                        if not self._in_date_range(dt, start_date, end_date):
                            continue
                        total_messages += c
                        filtered_dates.append(dt)
                except Exception:
                    total_messages = 0
                    filtered_dates = []

                # messages sent by 'You' (resolve sender key)
                try:
                    you_key = self._resolve_sender_key(convo, 'You')
                    you_data = convo.get_messages_timeline(sender_number=you_key, period='day')
                    you_dates = you_data.get('dates', [])
                    you_counts = you_data.get('counts', [])
                    messages_sent_you = sum(c for dt, c in zip(you_dates, you_counts) if self._in_date_range(dt, start_date, end_date))
                except Exception:
                    messages_sent_you = 0

                # compute the active days for the selected range for this convo
                if start_date and end_date:
                    days_span = (end_date - start_date).days + 1
                elif filtered_dates:
                    min_d = min(filtered_dates)
                    max_d = max(filtered_dates)
                    days_span = (max_d - min_d).days + 1
                else:
                    days_span = 0

                duration_days = days_span if days_span > 0 else 0

                messages_per_day = (total_messages / duration_days) if duration_days > 0 else 0
                messages_per_day_you = (messages_sent_you / duration_days) if duration_days > 0 else 0
            else:
                # use precomputed metadata values
                messages_per_day = meta.get('messages_per_day', 0)
                messages_per_day_you = meta.get('messages_per_day_you', 0)

            entry = {
                'name': meta.get('name'),
                'participant_names': meta.get('participant_names', []),
                'is_group_chat': meta.get('is_group_chat', False),
                'participant_count': meta.get('participant_count', 0),
                'total_messages': total_messages,
                'messages_per_day': messages_per_day,
                'messages_sent_you': messages_sent_you,
                'messages_per_day_you': messages_per_day_you,
                'duration_days': duration_days,
                'total_reactions': meta.get('total_reactions', 0),
                'total_attachments': meta.get('total_attachments', 0),
                'avg_words_per_message': meta.get('avg_words_per_message', 0),
                'median_response_time_minutes': meta.get('median_response_time_minutes', 0),
            }
            result.append(entry)

        # If sorting by messages_per_day, exclude very short conversations (<5 days)
        if sort_by == 'messages_per_day':
            result = [r for r in result if r.get('duration_days', 0) >= 5]
            result.sort(key=lambda x: x.get('messages_per_day_you', x.get('messages_per_day', 0)), reverse=True)
        else:
            result.sort(key=lambda x: x.get(sort_by, 0), reverse=True)

        if top_n:
            return result[:top_n]
        return result
    
    # Aggregated timeline methods
    def get_combined_messages_timeline(self, sender_number=None, period='week', start_date=None, end_date=None):
        """Get combined message count across all conversations.

        Optional date filtering: pass `start_date` and/or `end_date` (date objects) to limit
        the data considered to a specific inclusive date range.
        """
        aggregated = defaultdict(int)
        for convo in self.conversations:
            resolved = self._resolve_sender_key(convo, sender_number)
            # When a date range is provided, request daily buckets and then
            # re-aggregate into the requested period. This avoids dropping
            # events where the period key (e.g., week start) falls outside
            # the date range even though some days in that period should be
            # included (e.g., a week that starts in June but contains July days).
            if (start_date or end_date) and period != 'day':
                data = convo.get_messages_timeline(sender_number=resolved, period='day')
                for dt, count in zip(data['dates'], data['counts']):
                    # dt here is a date object (day); filter by actual day
                    if start_date or end_date:
                        if not self._in_date_range(dt, start_date, end_date):
                            continue
                    # compute the aggregated period key using the conversation's statistic helper
                    # convert date -> datetime for _get_period_key
                    key = convo.message_stats._get_period_key(datetime.combine(dt if isinstance(dt, date) else dt.date(), time(hour=0)), period)
                    aggregated[key] += count
            else:
                data = convo.get_messages_timeline(sender_number=resolved, period=period)
                for dt, count in zip(data['dates'], data['counts']):
                    if start_date or end_date:
                        if not self._in_date_range(dt, start_date, end_date):
                            continue
                    aggregated[dt] += count

        sorted_data = sorted(aggregated.items())
        return {
            'dates': [d for d, _ in sorted_data],
            'counts': [c for _, c in sorted_data]
        }
    
    def get_combined_messages_by_hour(self, sender_number=None, use_median=True, start_date=None, end_date=None):
        """Get combined message activity by hour (average or median messages per hour).

        Accepts optional `start_date`/`end_date` to restrict which datetimes are
        considered. When a date range is provided we filter the per-hour slots
        by date before aggregating.
        """
        hour_values = defaultdict(list)  # hour -> list of counts (one per observed date-hour)

        for convo in self.conversations:
            # Choose timeline source for this conversation
            if sender_number is not None:
                resolved = self._resolve_sender_key(convo, sender_number)
                if resolved not in convo.message_stats.timeline_by_sender:
                    continue
                timeline = convo.message_stats.timeline_by_sender[resolved]
            else:
                timeline = defaultdict(int)
                for sender_data in convo.message_stats.timeline_by_sender.values():
                    for dt, count in sender_data.items():
                        timeline[dt] += count

            # timeline keys are datetimes (date+hour) representing a single hour slot
            for dt, count in timeline.items():
                if start_date or end_date:
                    if not self._in_date_range(dt, start_date, end_date):
                        continue
                hour = dt.hour
                hour_values[hour].append(count)

        # Compute median or mean per hour
        results = []
        for hour in range(24):
            values = hour_values.get(hour, [])
            if not values:
                results.append(0)
            else:
                if use_median:
                    results.append(self._median(values))
                else:
                    results.append(sum(values) / len(values))

        return {
            'hours': list(range(24)),
            'counts': results
        }
    
    def get_combined_emoji_totals(self, sender_number=None, top_n=15, start_date=None, end_date=None):
        """Get combined top emojis across all conversations.

        Optional date filtering: provide `start_date`/`end_date` (date objects).
        """
        emoji_counts = defaultdict(int)
        
        for convo in self.conversations:
            try:
                if start_date or end_date:
                    # Build totals from timeline so we can respect date range
                    resolved = self._resolve_sender_key(convo, sender_number)
                    data = convo.get_emoji_timeline(sender_number=resolved, period='day', include_all=True)
                    for emoji, counts in data['emojis'].items():
                        for dt, count in zip(data['dates'], counts):
                            if not self._in_date_range(dt, start_date, end_date):
                                continue
                            emoji_counts[emoji] += count
                else:
                    resolved = self._resolve_sender_key(convo, sender_number)
                    data = convo.get_emoji_totals(resolved)
                    for emoji, count in zip(data[0], data[1]):
                        emoji_counts[emoji] += count
            except:
                continue
        
        # Sort and get top N
        sorted_emojis = sorted(emoji_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        return [
            [emoji for emoji, _ in sorted_emojis],
            [count for _, count in sorted_emojis]
        ]
    
    def get_combined_emoji_timeline(self, sender_number=None, period='week', top_n=15, start_date=None, end_date=None):
        """Get combined emoji usage over time across all conversations."""
        # First, determine which emojis are top overall
        top_emojis_data = self.get_combined_emoji_totals(sender_number, top_n)
        top_emojis = set(top_emojis_data[0])
        
        # Aggregate timeline data for top emojis
        emoji_timelines = defaultdict(lambda: defaultdict(int))
        
        for convo in self.conversations:
            try:
                resolved = self._resolve_sender_key(convo, sender_number)
                data = convo.get_emoji_timeline(sender_number=resolved, period=period, include_all=True)
                for emoji, counts in data['emojis'].items():
                    if emoji in top_emojis:
                        for dt, count in zip(data['dates'], counts):
                            if start_date or end_date:
                                if not self._in_date_range(dt, start_date, end_date):
                                    continue
                            emoji_timelines[emoji][dt] += count
            except:
                continue
        
        # Get all unique dates
        all_dates = sorted(set(date for emoji_data in emoji_timelines.values() for date in emoji_data.keys()))
        
        # Build result
        result = {
            'dates': all_dates,
            'emojis': {}
        }
        
        for emoji in top_emojis:
            counts = [emoji_timelines[emoji].get(date, 0) for date in all_dates]
            result['emojis'][emoji] = counts
        
        return result

    def get_combined_emoji_by_hour(self, sender_number=None, top_n=15, include_all=False, start_date=None, end_date=None):
        """Get combined emoji usage by hour across all conversations."""
        # Determine top emojis overall (respect include_all)
        if include_all:
            top_emojis = None
        else:
            top_emojis_data = self.get_combined_emoji_totals(sender_number, top_n)
            top_emojis = set(top_emojis_data[0])

        # Aggregate per-emoji per-hour counts
        emoji_hour = defaultdict(lambda: defaultdict(int))

        for convo in self.conversations:
            try:
                resolved = self._resolve_sender_key(convo, sender_number)
                data = convo.get_emoji_by_hour(sender_number=resolved, top_n=top_n, include_all=True)
                for emoji, counts in data['emojis'].items():
                    if top_emojis is None or emoji in top_emojis:
                        for hour, count in enumerate(counts):
                            emoji_hour[emoji][hour] += count
            except:
                continue

        # Build result
        result = {
            'hours': list(range(24)),
            'emojis': {}
        }

        selected_emojis = list(emoji_hour.keys())
        for emoji in selected_emojis:
            result['emojis'][emoji] = [emoji_hour[emoji].get(hour, 0) for hour in range(24)]

        return result
    
    def get_combined_words_per_message_timeline(self, sender_number=None, period='week', use_median=True, start_date=None, end_date=None):
        """Get combined average words per message over time."""
        # Collect all word counts per period
        period_word_counts = defaultdict(list)
        
        for convo in self.conversations:
            # Get individual word counts (not averaged)
            resolved = self._resolve_sender_key(convo, sender_number)
            if sender_number is not None:
                if resolved not in convo.word_count_stats.words_per_message_timeline:
                    continue
                timeline_data = convo.word_count_stats.words_per_message_timeline[resolved]
            else:
                timeline_data = defaultdict(list)
                for sender_data in convo.word_count_stats.words_per_message_timeline.values():
                    for dt, counts in sender_data.items():
                        timeline_data[dt].extend(counts)
            
            # Aggregate by period
            for dt, word_counts in timeline_data.items():
                if start_date or end_date:
                    if not self._in_date_range(dt, start_date, end_date):
                        continue
                key = convo.word_count_stats._get_period_key(dt, period)
                period_word_counts[key].extend(word_counts)
        
        # Calculate median or mean for each period
        sorted_data = sorted(period_word_counts.items())
        
        if use_median:
            avg_values = [self._median(counts) for _, counts in sorted_data]
        else:
            avg_values = [sum(counts) / len(counts) if counts else 0 for _, counts in sorted_data]
        
        return {
            'dates': [d for d, _ in sorted_data],
            'avg_words': avg_values
        }

    def get_combined_total_words_timeline(self, sender_number=None, period='week', start_date=None, end_date=None):
        """Get combined total words over time across all conversations.

        Returns a dict with 'dates' and 'counts' like the individual statistic.
        """
        period_totals = defaultdict(int)

        for convo in self.conversations:
            # Choose data source for this conversation
            resolved = self._resolve_sender_key(convo, sender_number)
            # If filtering by date and requesting multi-day periods, pull daily data
            if (start_date or end_date) and period != 'day':
                # request daily totals so we can apply inclusive date filtering
                if resolved is not None:
                    # use the internal total_words_timeline if present
                    if resolved in convo.word_count_stats.total_words_timeline:
                        timeline = convo.word_count_stats.total_words_timeline[resolved]
                    else:
                        timeline = {}
                else:
                    # combine all senders daily totals
                    timeline = defaultdict(int)
                    for sender_data in convo.word_count_stats.total_words_timeline.values():
                        for dt, count in sender_data.items():
                            timeline[dt] = timeline.get(dt, 0) + count

                for dt, count in timeline.items():
                    if start_date or end_date:
                        if not self._in_date_range(dt, start_date, end_date):
                            continue
                    key = convo.word_count_stats._get_period_key(datetime.combine(dt if isinstance(dt, date) else dt.date(), time(hour=0)), period)
                    period_totals[key] += count
            else:
                if resolved is not None:
                    if resolved not in convo.word_count_stats.total_words_timeline:
                        continue
                    timeline_data = convo.word_count_stats.total_words_timeline[resolved]
                else:
                    timeline_data = defaultdict(int)
                    for sender_data in convo.word_count_stats.total_words_timeline.values():
                        for dt, count in sender_data.items():
                            timeline_data[dt] += count

                for dt, count in timeline_data.items():
                    if start_date or end_date:
                        if not self._in_date_range(dt, start_date, end_date):
                            continue
                    key = convo.word_count_stats._get_period_key(dt, period)
                    period_totals[key] += count

            # (Per-conversation aggregation handled above for each branch)

        # Sort and return
        sorted_data = sorted(period_totals.items())

        return {
            'dates': [d for d, _ in sorted_data],
            'counts': [c for _, c in sorted_data]
        }
    
    def get_combined_words_per_message_by_hour(self, sender_number=None, use_median=True, start_date=None, end_date=None):
        """Get combined average words per message by hour."""
        hour_word_counts = defaultdict(list)
        
        for convo in self.conversations:
            resolved = self._resolve_sender_key(convo, sender_number)
            if sender_number is not None:
                if resolved not in convo.word_count_stats.words_per_message_by_hour:
                    continue
                hour_data = convo.word_count_stats.words_per_message_by_hour[resolved]
            else:
                hour_data = defaultdict(list)
                for sender_data in convo.word_count_stats.words_per_message_by_hour.values():
                    for hour, counts in sender_data.items():
                        hour_data[hour].extend(counts)
            
            for hour, counts in hour_data.items():
                # per-hour lists don't contain date info, so start/end cannot filter here
                hour_word_counts[hour].extend(counts)
        
        # Calculate median or mean for each hour
        avg_words = []
        for hour in range(24):
            counts = hour_word_counts.get(hour, [])
            if use_median:
                avg_words.append(self._median(counts))
            else:
                avg_words.append(sum(counts) / len(counts) if counts else 0)
        
        return {
            'hours': list(range(24)),
            'avg_words': avg_words
        }
    
    def get_combined_response_time_timeline(self, sender_number=None, period='week', use_median=True, start_date=None, end_date=None):
        """Get combined response time over time."""
        period_response_times = defaultdict(list)
        
        for convo in self.conversations:
            resolved = self._resolve_sender_key(convo, sender_number)
            if sender_number is not None:
                if resolved not in convo.response_time_stats.response_time_timeline:
                    continue
                timeline_data = convo.response_time_stats.response_time_timeline[resolved]
            else:
                timeline_data = defaultdict(list)
                for sender_data in convo.response_time_stats.response_time_timeline.values():
                    for dt, times in sender_data.items():
                        timeline_data[dt].extend(times)
            
            # Aggregate by period
            for dt, response_times in timeline_data.items():
                if start_date or end_date:
                    if not self._in_date_range(dt, start_date, end_date):
                        continue
                key = convo.response_time_stats._get_period_key(dt, period)
                period_response_times[key].extend(response_times)
        
        # Calculate median or mean for each period
        sorted_data = sorted(period_response_times.items())
        
        if use_median:
            avg_values = [self._median(times) for _, times in sorted_data]
        else:
            avg_values = [sum(times) / len(times) if times else 0 for _, times in sorted_data]
        
        return {
            'dates': [d for d, _ in sorted_data],
            'avg_minutes': avg_values
        }
    
    def get_combined_response_time_by_hour(self, sender_number=None, use_median=True, start_date=None, end_date=None):
        """Get combined response time by hour.

        If `start_date`/`end_date` are provided, this will rebuild the per-hour
        buckets from the timeline (which includes datetime keys) so the
        date-range can be respected. Otherwise it uses the precomputed
        `response_time_by_hour` buckets for better performance.
        """
        hour_response_times = defaultdict(list)

        for convo in self.conversations:
            resolved = self._resolve_sender_key(convo, sender_number)

            # If filtering by date, rebuild per-hour lists from the timeline
            if start_date or end_date:
                if sender_number is not None:
                    if resolved not in convo.response_time_stats.response_time_timeline:
                        continue
                    timeline_data = convo.response_time_stats.response_time_timeline[resolved]
                else:
                    timeline_data = defaultdict(list)
                    for sender_data in convo.response_time_stats.response_time_timeline.values():
                        for dt, times in sender_data.items():
                            timeline_data[dt].extend(times)

                for dt, times in timeline_data.items():
                    if not self._in_date_range(dt, start_date, end_date):
                        continue
                    hour = dt.hour
                    hour_response_times[hour].extend(times)
            else:
                # No date filtering: use precomputed per-hour buckets
                if sender_number is not None:
                    if resolved not in convo.response_time_stats.response_time_by_hour:
                        continue
                    hour_data = convo.response_time_stats.response_time_by_hour[resolved]
                else:
                    hour_data = defaultdict(list)
                    for sender_data in convo.response_time_stats.response_time_by_hour.values():
                        for hour, times in sender_data.items():
                            hour_data[hour].extend(times)

                for hour, times in hour_data.items():
                    hour_response_times[hour].extend(times)

        # Calculate median or mean for each hour
        avg_minutes = []
        for hour in range(24):
            times = hour_response_times.get(hour, [])
            if use_median:
                avg_minutes.append(self._median(times))
            else:
                avg_minutes.append(sum(times) / len(times) if times else 0)

        return {
            'hours': list(range(24)),
            'avg_minutes': avg_minutes
        }
    
    def get_combined_double_texts_timeline(self, sender_number=None, period='week', start_date=None, end_date=None):
        """Get combined double text count over time."""
        aggregated = defaultdict(int)

        for convo in self.conversations:
            resolved = self._resolve_sender_key(convo, sender_number)
            data = convo.get_double_texts_timeline(sender_number=resolved, period=period)
            for dt, count in zip(data['dates'], data['counts']):
                if start_date or end_date:
                    if not self._in_date_range(dt, start_date, end_date):
                        continue
                aggregated[dt] += count

        sorted_data = sorted(aggregated.items())
        return {
            'dates': [d for d, _ in sorted_data],
            'counts': [c for _, c in sorted_data]
        }
    
    def get_combined_double_texts_by_hour(self, sender_number=None):
        """Get combined double text count by hour."""
        aggregated = defaultdict(int)
        
        for convo in self.conversations:
            resolved = self._resolve_sender_key(convo, sender_number)
            data = convo.get_double_texts_by_hour(sender_number=resolved)
            for hour, count in zip(data['hours'], data['counts']):
                aggregated[hour] += count
        
        return {
            'hours': list(range(24)),
            'counts': [aggregated[hour] for hour in range(24)]
        }

    def get_combined_attachments_timeline(self, sender_number=None, period='week', start_date=None, end_date=None):
        """Get combined attachment counts over time across all conversations."""
        aggregated = defaultdict(int)

        for convo in self.conversations:
            resolved = self._resolve_sender_key(convo, sender_number)
            data = convo.get_attachments_timeline(sender_number=resolved, period=period)
            for dt, count in zip(data['dates'], data['counts']):
                if start_date or end_date:
                    if not self._in_date_range(dt, start_date, end_date):
                        continue
                aggregated[dt] += count

        sorted_data = sorted(aggregated.items())
        return {
            'dates': [d for d, _ in sorted_data],
            'counts': [c for _, c in sorted_data]
        }

    def get_combined_attachments_by_hour(self, sender_number=None):
        """Get combined attachment counts by hour across all conversations."""
        aggregated = defaultdict(int)

        for convo in self.conversations:
            resolved = self._resolve_sender_key(convo, sender_number)
            data = convo.get_attachments_by_hour(sender_number=resolved)
            for hour, count in zip(data['hours'], data['counts']):
                aggregated[hour] += count

        return {
            'hours': list(range(24)),
            'counts': [aggregated[hour] for hour in range(24)]
        }

    def get_combined_avg_time_between_double_texts_timeline(self, sender_number=None, period='week', use_median=True, start_date=None, end_date=None):
        """Get combined average time between double texts over time.

        Accepts `start_date` and `end_date` to restrict which datetimes are considered.
        """
        period_times = defaultdict(list)

        for convo in self.conversations:
            try:
                # access raw times so we can filter by date
                resolved = self._resolve_sender_key(convo, sender_number)
                if sender_number is not None:
                    if resolved not in convo.double_text_stats.time_between_timeline:
                        continue
                    timeline_data = convo.double_text_stats.time_between_timeline[resolved]
                else:
                    timeline_data = defaultdict(list)
                    for sender_data in convo.double_text_stats.time_between_timeline.values():
                        for dt, times in sender_data.items():
                            timeline_data[dt].extend(times)

                for dt, times in timeline_data.items():
                    if start_date or end_date:
                        if not self._in_date_range(dt, start_date, end_date):
                            continue
                    key = convo.double_text_stats._get_period_key(dt, period)
                    period_times[key].extend(times)
            except:
                continue

        sorted_data = sorted(period_times.items())
        if use_median:
            avg_values = [self._median(times) for _, times in sorted_data]
        else:
            avg_values = [sum(times) / len(times) if times else 0 for _, times in sorted_data]

        return {
            'dates': [d for d, _ in sorted_data],
            'avg_minutes': avg_values
        }

    def get_combined_avg_time_between_double_texts_by_hour(self, sender_number=None, use_median=True, start_date=None, end_date=None):
        """Get combined average time between double texts by hour."""
        hour_times = defaultdict(list)

        for convo in self.conversations:
            resolved = self._resolve_sender_key(convo, sender_number)
            if sender_number is not None:
                if resolved not in convo.double_text_stats.time_between_by_hour:
                    continue
                hour_data = convo.double_text_stats.time_between_by_hour[resolved]
            else:
                hour_data = defaultdict(list)
                for sender_data in convo.double_text_stats.time_between_by_hour.values():
                    for hour, times in sender_data.items():
                        hour_data[hour].extend(times)

            for hour, times in hour_data.items():
                hour_times[hour].extend(times)

        avg_minutes = []
        for hour in range(24):
            times = hour_times.get(hour, [])
            if use_median:
                avg_minutes.append(self._median(times))
            else:
                avg_minutes.append(sum(times) / len(times) if times else 0)

        return {
            'hours': list(range(24)),
            'avg_minutes': avg_minutes
        }

    def get_combined_sent_received_ratio_timeline(self, sender_number, period='week'):
        """Get combined sent/received ratio across all conversations for a sender."""
        def _in_range_key(dt, start_date=None, end_date=None):
            return True

        sent_agg = defaultdict(int)
        recv_agg = defaultdict(int)

        for convo in self.conversations:
            # sent timeline for this convo
            sent_data = convo.double_text_stats.sent_timeline.get(sender_number, {})

            # received = sum of sent_timeline for other senders
            received_data = defaultdict(int)
            for sender, timeline in convo.double_text_stats.sent_timeline.items():
                if sender == sender_number:
                    continue
                for dt, count in timeline.items():
                    received_data[dt] += count

            for dt, count in sent_data.items():
                key = convo.double_text_stats._get_period_key(dt, period)
                sent_agg[key] += count

            for dt, count in received_data.items():
                key = convo.double_text_stats._get_period_key(dt, period)
                recv_agg[key] += count

        all_dates = sorted(set(list(sent_agg.keys()) + list(recv_agg.keys())))

        ratios = []
        sent_counts = []
        received_counts = []

        for date in all_dates:
            sent = sent_agg.get(date, 0)
            received = recv_agg.get(date, 0)
            total = sent + received
            ratio = (sent / total) if total > 0 else 0.5
            ratios.append(ratio)
            sent_counts.append(sent)
            received_counts.append(received)

        return {
            'dates': all_dates,
            'ratios': ratios,
            'sent_counts': sent_counts,
            'received_counts': received_counts
        }

    # ---------------------- New summary/stat helper methods ----------------------
    def total_messages_sent(self, sender_number='You', start_date=None, end_date=None):
        """Total number of messages sent by `sender_number` within optional date range."""
        # Fast path: if no date range is provided, we can use per-conversation
        # sender counts that are already accumulated in `convo.senders`.
        if start_date is None and end_date is None:
            total = 0
            for convo in self.conversations:
                try:
                    total += int(convo.senders.get(sender_number, {}).get('messages_sent', 0))
                except Exception:
                    continue
            return total

        # Fallback: when a date range is provided, aggregate per-day timelines
        total = 0
        for convo in self.conversations:
            try:
                data = convo.get_messages_timeline(sender_number=sender_number, period='day')
                for dt, count in zip(data['dates'], data['counts']):
                    if start_date or end_date:
                        if not self._in_date_range(dt, start_date, end_date):
                            continue
                    total += count
            except Exception:
                continue
        return total

    def count_non_group_chats_with_min_messages(self, sender_number='You', min_messages=2, start_date=None, end_date=None):
        """Count non-group (1-on-1) conversations where `sender_number` sent at least `min_messages` in range."""
        count = 0
        for convo in self.conversations:
            try:
                # determine if group chat
                if self._is_group_convo(convo):
                    continue

                convo_total = 0
                data = convo.get_messages_timeline(sender_number=sender_number, period='day')
                for dt, c in zip(data['dates'], data['counts']):
                    if start_date or end_date:
                        if not self._in_date_range(dt, start_date, end_date):
                            continue
                    convo_total += c

                if convo_total >= min_messages:
                    count += 1
            except Exception:
                continue
        return count

    def top_n_chats_by_messages_sent(self, sender_number='You', n=10, start_date=None, end_date=None):
        """Return top-n conversations sorted by total messages sent by `sender_number` in range.

        Returns list of tuples: [(conversation_label, count), ...]
        """
        convo_counts = []
        for convo in self.conversations:
            try:
                # Fast path: if no date range, use accumulated per-conversation sender counts
                if start_date is None and end_date is None:
                    total = int(convo.senders.get(sender_number, {}).get('messages_sent', 0))
                else:
                    data = convo.get_messages_timeline(sender_number=sender_number, period='day')
                    total = 0
                    for dt, c in zip(data['dates'], data['counts']):
                        if start_date or end_date:
                            if not self._in_date_range(dt, start_date, end_date):
                                continue
                        total += c

                meta_name = self.conversation_metadata.get(id(convo), {}).get('name')
                if meta_name:
                    label = meta_name
                else:
                    raw_label = getattr(convo, 'chat_name', None)
                    if isinstance(raw_label, str) and raw_label:
                        label = raw_label
                    else:
                        label = Path(getattr(convo, 'filepath', '')).stem
                convo_counts.append((label, total))
            except Exception:
                continue

        convo_counts.sort(key=lambda x: x[1], reverse=True)
        return [(label, cnt) for label, cnt in convo_counts[:n]]

    def top_n_chats_by_avg_messages_per_day(self, sender_number='You', n=10, start_date=None, end_date=None):
        """Return top-n non-group conversations sorted by average messages per day from `sender_number` in range.

        Returns list of tuples: [(conversation_label, avg_per_day), ...]
        """
        results = []
        for convo in self.conversations:
            try:
                # skip groups
                if self._is_group_convo(convo):
                    continue

                data = convo.get_messages_timeline(sender_number=sender_number, period='day')
                dates = []
                total = 0
                for dt, c in zip(data['dates'], data['counts']):
                    if start_date or end_date:
                        if not self._in_date_range(dt, start_date, end_date):
                            continue
                    dates.append(dt)
                    total += c

                if not dates:
                    continue

                # compute active days in the selected range for this convo
                min_d = min(dates)
                max_d = max(dates)
                days = (max_d - min_d).days + 1
                if days <= 0:
                    continue
                avg_per_day = total / days
                meta_name = self.conversation_metadata.get(id(convo), {}).get('name')
                if meta_name:
                    label = meta_name
                else:
                    raw_label = getattr(convo, 'chat_name', None)
                    if isinstance(raw_label, str) and raw_label:
                        label = raw_label
                    else:
                        label = Path(getattr(convo, 'filepath', '')).stem
                results.append((label, avg_per_day, total))
            except Exception:
                continue

        results.sort(key=lambda x: x[1], reverse=True)
        return [(label, avg) for label, avg, _ in results[:n]]

    def top_bottom_n_non_group_chats_by_response_time(self, sender_number='You', n=5, start_date=None, end_date=None, use_median=True):
        """Return top and bottom n non-group chats by average (or median) response time for `sender_number`.

        Returns dict: {'top': [(label, value), ...], 'bottom': [(label, value), ...]}
        """
        convo_times = []
        for convo in self.conversations:
            try:
                if self._is_group_convo(convo):
                    continue

                # collect response times for this sender
                timeline = convo.response_time_stats.response_time_timeline.get(sender_number, {}) if hasattr(convo, 'response_time_stats') else {}
                all_times = []
                for dt, times in timeline.items():
                    if start_date or end_date:
                        if not self._in_date_range(dt, start_date, end_date):
                            continue
                    all_times.extend(times)

                if not all_times:
                    continue
                value = self._median(all_times) if use_median else (sum(all_times) / len(all_times))
                meta_name = self.conversation_metadata.get(id(convo), {}).get('name')
                if meta_name:
                    label = meta_name
                else:
                    raw_label = getattr(convo, 'chat_name', None)
                    if isinstance(raw_label, str) and raw_label:
                        label = raw_label
                    else:
                        label = Path(getattr(convo, 'filepath', '')).stem
                convo_times.append((label, value))
            except Exception:
                continue

        if not convo_times:
            return {'top': [], 'bottom': []}

        convo_times.sort(key=lambda x: x[1], reverse=True)
        top = convo_times[:n]
        bottom = convo_times[-n:][::-1]
        return {'top': top, 'bottom': bottom}

    def top_n_chats_by_attachments_sent(self, sender_number='You', n=10, start_date=None, end_date=None):
        """Return top-n conversations sorted by attachments sent by `sender_number` in range."""
        convo_attach = []
        for convo in self.conversations:
            try:
                data = convo.get_attachments_timeline(sender_number=sender_number, period='day')
                total = 0
                for dt, c in zip(data['dates'], data['counts']):
                    if start_date or end_date:
                        if not self._in_date_range(dt, start_date, end_date):
                            continue
                    total += c
                meta_name = self.conversation_metadata.get(id(convo), {}).get('name')
                if meta_name:
                    label = meta_name
                else:
                    raw_label = getattr(convo, 'chat_name', None)
                    if isinstance(raw_label, str) and raw_label:
                        label = raw_label
                    else:
                        label = Path(getattr(convo, 'filepath', '')).stem
                convo_attach.append((label, total))
            except Exception:
                continue

        convo_attach.sort(key=lambda x: x[1], reverse=True)
        return convo_attach[:n]

    def get_top_chats_messages_timeline(self, sender_number='You', n=5, period='day', start_date=None, end_date=None):
        """For top-n chats by message count, return a timeline dict with dates and per-conversation counts.

        Returns: {
            'dates': [date1, date2, ...],
            'conversations': {label: [counts aligned to dates], ...}
        }
        """
        # find top n by message count in range
        convo_counts = []
        for convo in self.conversations:
            try:
                data = convo.get_messages_timeline(sender_number=sender_number, period=period)
                total = 0
                entries = []
                for dt, c in zip(data['dates'], data['counts']):
                    if start_date or end_date:
                        if not self._in_date_range(dt, start_date, end_date):
                            continue
                    entries.append((dt, c))
                    total += c
                if total == 0:
                    continue
                meta_name = self.conversation_metadata.get(id(convo), {}).get('name')
                if meta_name:
                    label = meta_name
                else:
                    raw_label = getattr(convo, 'chat_name', None)
                    if isinstance(raw_label, str) and raw_label:
                        label = raw_label
                    else:
                        label = Path(getattr(convo, 'filepath', '')).stem
                convo_counts.append((label, total, entries))
            except Exception:
                continue

        convo_counts.sort(key=lambda x: x[1], reverse=True)
        selected = convo_counts[:n]

        # collect all dates across selected convos
        all_dates = sorted(set(dt for _, _, entries in selected for dt, _ in entries))

        # build per-convo aligned lists
        conversations = {}
        for label, _, entries in selected:
            mapping = {dt: c for dt, c in entries}
            conversations[label] = [mapping.get(dt, 0) for dt in all_dates]

        return {'dates': all_dates, 'conversations': conversations}
    

    def get_2025_messages_wrapped(self):

        START_DATE = datetime(2025, 1, 1).date()
        END_DATE = datetime(2025, 12, 31).date()

        total_number_messages = self.total_messages_sent(sender_number='You', start_date=START_DATE, end_date=END_DATE) #Total messages sent
        #Total words texted:
        total_words_sent = 0
        total_words_data = self.get_combined_total_words_timeline(sender_number="You", period='week', start_date=START_DATE, end_date=END_DATE)
        for count in total_words_data['counts']:
            total_words_sent += count
        words_per_message_per_hour = self.get_combined_words_per_message_by_hour(sender_number="You", start_date=START_DATE, end_date=END_DATE, use_median=False) #Your words per message habits based on hour of the day
        non_gc_with_min2_msgs = self.count_non_group_chats_with_min_messages(sender_number='You', min_messages=1, start_date=START_DATE, end_date=END_DATE) #Total individuals messaged
        comp_data = self.get_conversation_comparison_data(sort_by="messages_per_day_you", top_n=10, start_date=START_DATE, end_date=END_DATE) #Rank chats based on messages you sent per day
        
        top_n_chats_by_messages = self.top_n_chats_by_messages_sent(sender_number='You', n=5, start_date=START_DATE, end_date=END_DATE) #Top chats based on number of messages you sent
        if top_n_chats_by_messages:
            names = [t[0] for t in top_n_chats_by_messages]
            # Build timeline (use same TOP_N and date range)
            top_chats_timeline = self.get_top_chats_messages_timeline(sender_number='You', n=10, period='day', start_date=START_DATE, end_date=END_DATE) #Timeline showing the people you messaged and when
        
        top_n_chats_by_attachments = self.top_n_chats_by_attachments_sent(sender_number='You', n=5, start_date=START_DATE, end_date=END_DATE) #Top chats based on attachments you sent
        

        top_emojis_data = self.get_combined_emoji_totals(sender_number="You", top_n=15, start_date=START_DATE, end_date=END_DATE) #Your top emojis used in 2025
        emoji_timeline = self.get_combined_emoji_timeline(sender_number="You", period="week", top_n=5, start_date=START_DATE, end_date=END_DATE) #Your top emojis timeline in 2025 on a weekly basis

        top_bottom_n_non_gc_by_response_time = self.top_bottom_n_non_group_chats_by_response_time(sender_number='You', n=5, start_date=START_DATE, end_date=END_DATE, use_median=True) #Top and bottom group chats based on your activity
        messages_sent_timeline = self.get_combined_messages_timeline(sender_number="You", period='week', start_date=START_DATE, end_date=END_DATE) #Your messages timeline in 2025 on a weekly basis
        messages_sent_by_hour = self.get_combined_messages_by_hour(sender_number="You", start_date=START_DATE, end_date=END_DATE, use_median=False) #Your messages habits based on hour of the day
        response_time_by_hour = self.get_combined_response_time_by_hour(sender_number="You", start_date=START_DATE, end_date=END_DATE, use_median=False) #Your response time habits based on hour of the day


        # Return all collected data as a dictionary
        return {
            'total_number_messages': total_number_messages, #
            'total_words_sent': total_words_sent, #
            'words_per_message_per_hour': words_per_message_per_hour, #
            'non_gc_with_min2_msgs': non_gc_with_min2_msgs, #
            'conversation_comparison': comp_data, #
            'top_n_chats_by_messages': top_n_chats_by_messages, #
            'top_n_chats_by_attachments': top_n_chats_by_attachments,#
            'top_chats_timeline': top_chats_timeline if top_n_chats_by_messages else None, #
            'top_emojis_data': top_emojis_data, #
            'emoji_timeline': emoji_timeline, #
            'top_bottom_n_non_gc_by_response_time': top_bottom_n_non_gc_by_response_time, #
            'messages_sent_timeline': messages_sent_timeline,
            'messages_sent_by_hour': messages_sent_by_hour,
            'response_time_by_hour': response_time_by_hour #
        }

    def export_2025_messages_wrapped(self, filepath='wrapped_2025.json'):
        """Generate the 2025 wrapped summary and write it to `filepath` as JSON.

        Dates and datetimes are converted to iso-8601 strings so the output
        is JSON-serializable.
        Returns the filepath on success.
        """
        data = self.get_2025_messages_wrapped()

        def _serialize(obj):
            # Convert date/datetime to isoformat, recurse into lists/dicts
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, date):
                return obj.isoformat()
            if isinstance(obj, dict):
                return {k: _serialize(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_serialize(v) for v in obj]
            return obj

        serializable = _serialize(data)

        # Write the entire dictionary as a single JSON object
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(serializable, f, ensure_ascii=False, indent=2)

        return filepath

    def cleanup_all_exports(self, delete_mapping=True, mapping_filename='number_to_name.json'):
        """Delete all conversation JSON files (calls each Conversation.delete_json_file())

        This will attempt to instantiate a `Conversation` for each `chat_*.json`
        file in `self.conversations_dir` and call its `delete_json_file()` method.

        If `delete_mapping` is True, also delete the mapping JSON file named
        `mapping_filename` inside `self.conversations_dir` (if present).

        This function will NOT delete any message database files.

        Returns a dict with summary: {'deleted_files': [...], 'failed': [...], 'mapping_deleted': bool}
        """
        from pathlib import Path
        results = {
            'deleted_files': [],
            'failed': [],
            'mapping_deleted': False
        }

        exports_dir = Path(self.conversations_dir)
        if not exports_dir.exists():
            print(f"Exports directory not found: {exports_dir}")
            return results

        # Iterate all chat_*.json files (including ones skipped earlier)
        for p in exports_dir.glob('chat_*.json'):
            try:
                # instantiate Conversation to use its delete helper (best-effort)
                try:
                    from Conversation import Conversation
                    convo = Conversation(str(p), chat_name_dict=self.name_dict)
                    deleted = convo.delete_json_file()
                    if deleted:
                        results['deleted_files'].append(str(p))
                    else:
                        results['failed'].append(str(p))
                except Exception:
                    # Fallback: attempt direct unlink if Conversation can't be instantiated
                    try:
                        p.unlink()
                        results['deleted_files'].append(str(p))
                    except Exception:
                        results['failed'].append(str(p))
            except Exception as e:
                results['failed'].append(str(p))

        # Delete mapping JSON if requested
        if delete_mapping:
            mapping_path = exports_dir / mapping_filename
            try:
                if mapping_path.exists():
                    mapping_path.unlink()
                    results['mapping_deleted'] = True
            except Exception as e:
                print(f"Error deleting mapping file {mapping_path}: {e}")

        print(f"Cleanup complete. Deleted: {len(results['deleted_files'])}, Failed: {len(results['failed'])}, Mapping deleted: {results['mapping_deleted']}")
        return results

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process exported conversation JSON files and produce a wrapped summary")
    parser.add_argument("--exports-dir", dest="exports_dir", default="exports",
                        help="Directory containing chat_*.json files and number_to_name.json (default: exports)")
    parser.add_argument("--max-workers", dest="max_workers", type=int, default=None,
                        help="Maximum number of workers for parallel loading (default: CPU count)")
    parser.add_argument("--use-processes", dest="use_processes", action="store_true",
                        help="Use ProcessPoolExecutor instead of ThreadPoolExecutor (disabled by default)")
    parser.add_argument("-v", dest="verbose_file", default=None,
                        help="Enable verbose logging to the specified file")

    args = parser.parse_args()

    setup_logging(verbose_file=args.verbose_file)

    wrapped = MessagesWrapped(conversations_dir=args.exports_dir, max_workers=args.max_workers, use_processes=args.use_processes)
    out_path = Path(args.exports_dir) / "wrapped_2025.imsgwrp"
    wrapped.export_2025_messages_wrapped(filepath=str(out_path))