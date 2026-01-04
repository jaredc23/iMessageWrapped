import sqlite3
import json
import os
from datetime import datetime, timezone, date
from pathlib import Path
import html
import re
from collections import defaultdict

# ================================================
# CONFIGURATION
# ================================================
SMS_DB_PATH = "data/chat.db"
CONTACTS_DB_PATH = "data/contacts_db.abcddb"
OUTPUT_DIR = "exports"
Path(OUTPUT_DIR).mkdir(exist_ok=True)

def export_messages(SMS_DB_PATH=SMS_DB_PATH, CONTACTS_DB_PATH=CONTACTS_DB_PATH, OUTPUT_DIR=OUTPUT_DIR, chats_selection="all", start_date="2025-01-01", end_date="2025-12-31"):
    # Ensure output directory exists for provided OUTPUT_DIR
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # ================================================
    # REACTION TYPE MAPPING
    # ================================================
    REACTION_TYPES = {
        2000: "loved",
        2001: "liked",
        2002: "disliked",
        2003: "laughed",
        2004: "emphasized",
        2005: "questioned",
        3000: "removed_love",
        3001: "removed_like",
        3002: "removed_dislike",
        3003: "removed_laugh",
        3004: "removed_emphasis",
        3005: "removed_question"
    }

    # ================================================
    # HELPERS
    # ================================================
    guid_pattern = re.compile(r"(?::|\/)(.*)$")
    def clean_up_guid(guid):
        return guid.split(":")[-1].split("/")[-1]

    def extract_text_from_attributed_body(attributed_body):
        """
        Extract plain text from NSAttributedString binary data.
        
        NSAttributedString is stored as a binary plist with the actual text
        typically after specific markers. This function uses multiple strategies
        to reliably extract the text content.
        """
        if not attributed_body:
            return None
        
        try:
            # Strategy 1: Look for text between __kIMMessagePartAttributeName markers
            # The actual message text usually appears after this marker
            decoded = attributed_body.decode('utf-8', errors='ignore')
            
            # Pattern 1: Text after __kIMMessagePartAttributeName
            # The format is often: __kIMMessagePartAttributeName...NSNumber...NSValue...[ACTUAL TEXT]
            pattern1 = r'__kIMMessagePartAttributeName.*?NSValue[^\x00-\x1f]*?([\x20-\x7e\s]+?)(?:\x00|streamtyped|NSString|NSDictionary|$)'
            match1 = re.search(pattern1, decoded, re.DOTALL)
            if match1:
                text = match1.group(1).strip()
                # Clean up any remaining artifacts
                text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
                text = text.strip()
                if len(text) > 2 and not all(c in 'NSObjectNSStringNSDictionaryNSNumberNSValue' for c in text.split()):
                    return text
            
            # Strategy 2: Look for the pattern before "streamtyped"
            # Sometimes the text appears just before this marker
            pattern2 = r'NSValue[^\x00-\x1f]*?([\x20-\x7e\s]+?)(?:streamtyped|NSString|$)'
            match2 = re.search(pattern2, decoded, re.DOTALL)
            if match2:
                text = match2.group(1).strip()
                text = re.sub(r'\s+', ' ', text)
                # Filter out common artifacts
                artifacts = ['NSObject', 'NSString', 'NSDictionary', 'NSNumber', 'NSValue', '__kIMMessagePartAttributeName']
                words = text.split()
                cleaned_words = [w for w in words if w not in artifacts and len(w) > 0]
                if cleaned_words:
                    text = ' '.join(cleaned_words)
                    if len(text) > 2:
                        return text
            
            # Strategy 3: Binary plist format - look for text after specific byte sequences
            # NSAttributedString often has the text after a length indicator
            # Try to find sections with concentrated printable ASCII
            chunks = decoded.split('NSString')
            for chunk in chunks[1:]:  # Skip first chunk which is usually headers
                # Look for continuous readable text
                readable = re.search(r'([a-zA-Z0-9\s\.\,\!\?\'\"\-\:\;]{8,})', chunk)
                if readable:
                    text = readable.group(1).strip()
                    # Make sure it's not just artifact strings
                    if not re.match(r'^(NSObject|NSDictionary|NSNumber|NSValue|__kIM)+', text):
                        text = re.sub(r'\s+', ' ', text)
                        if len(text) > 2:
                            return text
            
            # Strategy 4: Look between null bytes for text sections
            # Split on null bytes and find the chunk with the most readable content
            parts = attributed_body.split(b'\x00')
            best_text = ""
            best_score = 0
            
            for part in parts:
                try:
                    text = part.decode('utf-8', errors='ignore').strip()
                    # Skip known artifact strings
                    if any(artifact in text for artifact in ['streamtyped', '__kIMMessagePartAttributeName', 'typedstream']):
                        continue
                    # Score based on alphanumeric content and reasonable length
                    score = sum(c.isalnum() or c.isspace() for c in text)
                    if score > best_score and len(text) > 2 and len(text) < 1000:
                        best_score = score
                        best_text = text
                except:
                    continue
            
            if best_text and best_score > 5:
                # Clean up the best candidate
                best_text = re.sub(r'\s+', ' ', best_text)
                # Remove leading/trailing non-alphanumeric characters
                best_text = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9\.\!\?]+$', '', best_text)
                return best_text if best_text else None
                
        except Exception as e:
            print(f"Error extracting text from attributedBody: {e}")
        
        return None

    def apple_time_to_datetime(apple_time):
        if apple_time is None:
            return None
        ts = apple_time
        if ts > 1e12:
            ts = ts / 1_000_000_000
        return datetime.fromtimestamp(ts + 978307200, tz=timezone.utc)

    # Parse optional date range inputs into UTC datetimes (inclusive)
    def _parse_date_input(val, is_end=False):
        """Accepts None, date/datetime, or ISO string. Returns a timezone-aware datetime in UTC.

        If `is_end` is True, the time is set to the end of the day for date inputs
        to make the range inclusive.
        """
        if val is None:
            return None

        # If already a datetime or date
        if isinstance(val, datetime):
            dt = val
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)

        if isinstance(val, date):
            if is_end:
                return datetime(val.year, val.month, val.day, 23, 59, 59, 999999, tzinfo=timezone.utc)
            else:
                return datetime(val.year, val.month, val.day, 0, 0, 0, 0, tzinfo=timezone.utc)

        # Try parsing from ISO string
        try:
            parsed = datetime.fromisoformat(str(val))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except Exception:
            # Fallback: try parsing YYYY-MM-DD
            try:
                parts = str(val).split('T')[0].split('-')
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                if is_end:
                    return datetime(y, m, d, 23, 59, 59, 999999, tzinfo=timezone.utc)
                else:
                    return datetime(y, m, d, 0, 0, 0, 0, tzinfo=timezone.utc)
            except Exception:
                return None

    START_DT = _parse_date_input(start_date, is_end=False)
    END_DT = _parse_date_input(end_date, is_end=True)

    def normalize_contact_number(number):
        if not number:
            return None
        digits = re.sub(r"[^\d]", "", number)
        if len(digits) == 10:
            digits = "+1" + digits
        elif len(digits) == 11 and digits.startswith("1"):
            digits = "+" + digits
        elif not digits.startswith("+"):
            digits = "+" + digits
        return digits

    def normalize_handle(handle):
        if not handle:
            return None
        handle = handle.strip()
        if re.fullmatch(r"[\d\+\-\(\) ]+", handle):
            return normalize_contact_number(handle)
        return handle.lower()

    def is_reply(assoc_type):
        """
        Check if the associated_message_type indicates a reply.
        Type 2 appears to be thread replies (they show as special characters).
        """
        return assoc_type == 2

    def is_reaction(assoc_type):
        """
        Check if the associated_message_type indicates a reaction.
        Types 2000-2007 are reactions (love, like, dislike, laugh, emphasize, question, emoji, sticker)
        Types 3000-3005 are removed reactions
        """
        return assoc_type in REACTION_TYPES or assoc_type in [2006, 2007]

    def get_reaction_type(assoc_type, text, emoji):
        """
        Determine the type of reaction based on associated_message_type and text.
        Returns a dict with reaction details.
        """
        reaction_info = {
            "type": "unknown",
            "emoji": None,
            "display": text or ""
        }
        
        # Standard emoji reactions (like, love, laugh, etc.)
        if assoc_type in REACTION_TYPES:
            reaction_info["type"] = REACTION_TYPES[assoc_type]
            reaction_info["display"] = REACTION_TYPES[assoc_type].replace("_", " ").title()
            
            # Try to extract emoji from text if present
            if text:
                # Common patterns: "Loved "message"" or just the emoji
                emoji_match = re.search(r'^(❤️|👍|👎|😂|‼️|❓|❤|😆|🤣|💕|💖|💗|💓|💘|💙|💚|💛|🧡|💜|🖤|🤍|🤎)', text)
                if emoji_match:
                    reaction_info["emoji"] = emoji_match.group(1)
        
        # Check if it's a sticker reaction (has attachments or special formatting)
        elif text and ("sticker" in text.lower() or text.startswith("￼")):
            reaction_info["type"] = "sticker"
            reaction_info["display"] = "Sticker reaction"
        
        # Custom emoji or unicode emoji reaction
        elif emoji:
            reaction_info["type"] = "emoji"
            reaction_info["emoji"] = emoji
            reaction_info["display"] = emoji
        
        # Fallback to parsing text for emoji
        elif text:
            # Check if text is just an emoji (or starts with one)
            emoji_pattern = re.compile(
                "["
                "\U0001F600-\U0001F64F"  # emoticons
                "\U0001F300-\U0001F5FF"  # symbols & pictographs
                "\U0001F680-\U0001F6FF"  # transport & map symbols
                "\U0001F1E0-\U0001F1FF"  # flags (iOS)
                "\U00002702-\U000027B0"
                "\U000024C2-\U0001F251"
                "\U0001F900-\U0001F9FF"  # supplemental symbols
                "]+", flags=re.UNICODE
            )
            emoji_match = emoji_pattern.search(text)
            if emoji_match:
                reaction_info["type"] = "emoji"
                reaction_info["emoji"] = emoji_match.group(0)
                reaction_info["display"] = emoji_match.group(0)
        
        return reaction_info

    # ================================================
    # LOAD CONTACTS
    # ================================================
    def load_contacts(db_path):
        db_path = str(db_path)
        
        if not os.path.exists(db_path):
            print(f"ERROR: Contacts database not found at {db_path}")
            return {}
        
        try:
            conn = sqlite3.connect(db_path)
        except sqlite3.Error as e:
            print(f"ERROR: Could not connect to contacts database at {db_path}")
            print(f"Error: {e}")
            return {}
        
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cur.fetchall()]
        print("Tables in Contacts DB:", tables)

        contacts = {}

        if "ZCONTACT" in tables:
            phone_tables = ["ZPHONE", "ZABCDPHONENUMBER", "ZABCDRECORD"]
            email_tables = ["ZEMAILADDRESS", "ZABCDEMAILADDRESS"]
            
            phone_table = None
            email_table = None
            
            for pt in phone_tables:
                if pt in tables:
                    phone_table = pt
                    break
            
            for et in email_tables:
                if et in tables:
                    email_table = et
                    break
            
            print(f"Using phone table: {phone_table}")
            print(f"Using email table: {email_table}")
            
            try:
                if phone_table:
                    if phone_table == "ZPHONE":
                        query = """
                            SELECT ZCONTACT.ZFIRSTNAME, ZCONTACT.ZLASTNAME, ZPHONE.ZFULLNUMBER
                            FROM ZCONTACT
                            LEFT JOIN ZPHONE ON ZPHONE.ZCONTACT = ZCONTACT.Z_PK
                            WHERE ZPHONE.ZFULLNUMBER IS NOT NULL;
                        """
                    else:
                        query = f"""
                            SELECT ZCONTACT.ZFIRSTNAME, ZCONTACT.ZLASTNAME, {phone_table}.ZFULLNUMBER
                            FROM ZCONTACT
                            LEFT JOIN {phone_table} ON {phone_table}.ZOWNER = ZCONTACT.Z_PK
                            WHERE {phone_table}.ZFULLNUMBER IS NOT NULL;
                        """
                    
                    cur.execute(query)
                    rows = cur.fetchall()
                    print(f"Loaded {len(rows)} phone contacts")
                    
                    for first, last, phone in rows:
                        name = " ".join(filter(None, [first, last])).strip()
                        if name and phone:
                            normalized = normalize_contact_number(phone)
                            contacts[normalized] = name
                
                if email_table:
                    if email_table == "ZEMAILADDRESS":
                        query = """
                            SELECT ZCONTACT.ZFIRSTNAME, ZCONTACT.ZLASTNAME, ZEMAILADDRESS.ZADDRESS
                            FROM ZCONTACT
                            LEFT JOIN ZEMAILADDRESS ON ZEMAILADDRESS.ZCONTACT = ZCONTACT.Z_PK
                            WHERE ZEMAILADDRESS.ZADDRESS IS NOT NULL;
                        """
                    else:
                        query = f"""
                            SELECT ZCONTACT.ZFIRSTNAME, ZCONTACT.ZLASTNAME, {email_table}.ZADDRESS
                            FROM ZCONTACT
                            LEFT JOIN {email_table} ON {email_table}.ZOWNER = ZCONTACT.Z_PK
                            WHERE {email_table}.ZADDRESS IS NOT NULL;
                        """
                    
                    cur.execute(query)
                    rows = cur.fetchall()
                    print(f"Loaded {len(rows)} email contacts")
                    
                    for first, last, email in rows:
                        name = " ".join(filter(None, [first, last])).strip()
                        if name and email:
                            normalized = email.lower()
                            contacts[normalized] = name
                            
            except sqlite3.OperationalError as e:
                print(f"Error loading modern schema: {e}")
        
        elif "ZABCDRECORD" in tables:
            try:
                cur.execute("""
                    SELECT r.ZFIRSTNAME, r.ZLASTNAME, p.ZFULLNUMBER
                    FROM ZABCDRECORD r
                    JOIN ZABCDPHONENUMBER p ON p.ZOWNER = r.Z_PK
                    WHERE p.ZFULLNUMBER IS NOT NULL;
                """)
                rows = cur.fetchall()
                print(f"Loaded {len(rows)} phone contacts from old schema.")
                
                for first, last, phone in rows:
                    name = " ".join(filter(None, [first, last])).strip()
                    if name and phone:
                        normalized = normalize_contact_number(phone)
                        contacts[normalized] = name
                
                cur.execute("""
                    SELECT r.ZFIRSTNAME, r.ZLASTNAME, e.ZADDRESS
                    FROM ZABCDRECORD r
                    JOIN ZABCDEMAILADDRESS e ON e.ZOWNER = r.Z_PK
                    WHERE e.ZADDRESS IS NOT NULL;
                """)
                rows = cur.fetchall()
                print(f"Loaded {len(rows)} email contacts from old schema.")
                
                for first, last, email in rows:
                    name = " ".join(filter(None, [first, last])).strip()
                    if name and email:
                        normalized = email.lower()
                        contacts[normalized] = name
            except sqlite3.OperationalError as e:
                print(f"Error loading old schema: {e}")

        elif "ABPerson" in tables:
            # Apple AddressBook (older/newer) schema: ABPerson + ABMultiValue stores phones/emails
            try:
                cur.execute("SELECT p.First, p.Last, m.value FROM ABPerson p JOIN ABMultiValue m ON m.record_id = p.ROWID WHERE m.value IS NOT NULL;")
                rows = cur.fetchall()
                print(f"Loaded {len(rows)} multi-value contact entries from ABPerson schema.")
                for first, last, value in rows:
                    name = " ".join(filter(None, [first, last])).strip()
                    if not name or not value:
                        continue
                    value = value.strip()
                    # Heuristic: emails contain '@', phones contain digits
                    if "@" in value:
                        contacts[value.lower()] = name
                    else:
                        normalized = normalize_contact_number(value)
                        if normalized:
                            contacts[normalized] = name
            except sqlite3.OperationalError as e:
                print(f"Error loading ABPerson schema: {e}")

        conn.close()
        print(f"\nTotal unique contacts loaded: {len(contacts)}")
        return contacts

    # If provided contacts DB is missing or empty, try common alternatives in the same folder
    contacts_db_path = str(CONTACTS_DB_PATH)
    try_paths = [contacts_db_path]
    base_dir = os.path.dirname(contacts_db_path) or "."
    try_paths += [
        os.path.join(base_dir, "AddressBook.sqlitedb"),
        os.path.join(base_dir, "AddressBookImages.sqlitedb"),
        os.path.join(base_dir, "contacts.db"),
        os.path.join(base_dir, "AddressBook.db"),
    ]

    resolved = None
    for p in try_paths:
        if os.path.exists(p) and os.path.getsize(p) > 0:
            resolved = p
            break

    if resolved is None:
        print(f"WARNING: contacts DB not found or empty at {CONTACTS_DB_PATH}; tried: {try_paths}")
        contacts = {}
    else:
        if resolved != contacts_db_path:
            print(f"Using contacts DB: {resolved}")
        contacts = load_contacts(resolved)

    # ================================================
    # CONNECT TO SMS.DB
    # ================================================
    conn = sqlite3.connect(SMS_DB_PATH)
    cur = conn.cursor()

    # ================================================
    # LIST CHATS
    # ================================================
    query_chats = """
    SELECT 
        chat.ROWID,
        chat.display_name,
        group_concat(handle.id, ',') as participants
    FROM chat
    LEFT JOIN chat_handle_join ON chat_handle_join.chat_id = chat.ROWID
    LEFT JOIN handle ON handle.ROWID = chat_handle_join.handle_id
    GROUP BY chat.ROWID
    ORDER BY chat.ROWID;
    """
    cur.execute(query_chats)
    chats = cur.fetchall()

    print("\n=== Available Chats ===\n")
    for rowid, display_name, raw_participants in chats:
        if raw_participants:
            participants = ", ".join(
                contacts.get(normalize_handle(p), p) for p in raw_participants.split(",")
            )
        else:
            participants = "<unknown>"
        name = display_name if display_name else participants
        print(f"{rowid}: {name}")
    print()

    # ================================================
    # SELECT CHATS
    # ================================================
    selection = chats_selection#"432,573,12,297,60,179" #432, 573, 12, 297, 60, 179 #all
    if selection.lower() == "all":
        chat_ids = [c[0] for c in chats]
    else:
        chat_ids = [int(x.strip()) for x in selection.split(",")]

    print(f"\nExporting chats: {chat_ids}\n")

    # ================================================
    # EXPORT EACH CHAT WITH REACTIONS AND REPLIES
    # ================================================
    chat_name_mapping = {}

    for chat_id in chat_ids:
        # Get chat display name for mapping file
        chat_info = next((c for c in chats if c[0] == chat_id), None)
        if chat_info:
            display_name, raw_participants = chat_info[1], chat_info[2]
            if display_name:
                chat_name = display_name
            elif raw_participants:
                # Use contact names if available
                participant_names = [
                    contacts.get(normalize_handle(p), p) 
                    for p in raw_participants.split(",")
                ]
                chat_name = ", ".join(participant_names)
            else:
                chat_name = "Unknown"
        else:
            chat_name = "Unknown"
        
        # Store mapping with an `include` flag (default true) for future filtering
        # mark chats as excluded if the chat name is just a phone number (or only '+' and digits)
        def _is_phone_like(s):
            if not s:
                return False
            s = s.strip()
            # Only plus and digits
            if re.fullmatch(r"\+?\d+", s):
                return True
            # Allow common phone formatting characters and require at least one digit
            if re.fullmatch(r"[+\d\-\(\) \.]+", s) and re.search(r"\d", s):
                digits = re.sub(r"\D", "", s)
                return len(digits) > 0
            return False

        # determine message count for this chat and set mapping (exclude if phone-like or zero messages)
        try:
            cur.execute("""
            SELECT COUNT(m.ROWID)
            FROM chat_message_join cmj
            JOIN message m ON m.ROWID = cmj.message_id
            WHERE cmj.chat_id = ? AND (m.item_type IS NULL OR m.item_type = 0)
            """, (chat_id,))
            num_msgs = cur.fetchone()[0] or 0
        except Exception:
            num_msgs = 0

        # capture normalized participant handles for grouping/merging later
        participants_handles = []
        if chat_info and raw_participants:
            for p in raw_participants.split(','):
                nh = normalize_handle(p)
                if nh:
                    participants_handles.append(nh)

        chat_name_mapping[f"chat_{chat_id}.json"] = {
            "name": chat_name,
            "num_msgs": num_msgs,
            "include": False if _is_phone_like(chat_name) or num_msgs == 0 else True,
            "participants_handles": participants_handles
        }
        
        print(f"Exporting chat {chat_id} ({chat_name})...")

        # UPDATED QUERY: Include date_edited, date_retracted, and item_type
        query_messages = """
        SELECT
            m.ROWID,
            m.guid,
            m.text,
            m.attributedBody,
            m.date,
            m.is_from_me,
            h.id AS sender,
            GROUP_CONCAT(a.filename, '|||') AS attachments,
            m.associated_message_type,
            m.associated_message_guid,
            m.associated_message_emoji,
            m.thread_originator_guid,
            m.thread_originator_part,
            m.date_edited,
            m.date_retracted,
            m.item_type
        FROM chat_message_join cmj
        JOIN message m ON m.ROWID = cmj.message_id
        LEFT JOIN handle h ON h.ROWID = m.handle_id
        LEFT JOIN message_attachment_join maj ON maj.message_id = m.ROWID
        LEFT JOIN attachment a ON a.ROWID = maj.attachment_id
        WHERE cmj.chat_id = ?
        GROUP BY m.ROWID
        ORDER BY m.date ASC;
        """
        cur.execute(query_messages, (chat_id,))
        rows = cur.fetchall()

        messages = []
        message_index = {}
        pending_reactions = defaultdict(list)
        pending_replies = defaultdict(list)
        unique_senders = set()
        skipped_system_messages = 0

        # Process all messages
        all_messages = {}
        for row in rows:
            (message_id, guid, text, attributed_body, msg_date, is_from_me, sender, attachments_str,
            assoc_type, assoc_guid, assoc_emoji, thread_orig_guid, thread_orig_part,
            date_edited, date_retracted, item_type) = row

            # Skip system/special messages (group changes, name changes, etc.)
            # item_type 0 = regular message, 1+ = system events
            if item_type != 0:
                skipped_system_messages += 1
                continue

            if sender:
                unique_senders.add(sender)

            if is_from_me == 1:
                sender_name = "You"
                sender = "You"
            else:
                normalized_sender = normalize_handle(sender) if sender else None
                sender_name = contacts.get(normalized_sender, sender or "Unknown")

            timestamp = apple_time_to_datetime(msg_date)
            # If date range filtering is requested, skip messages outside the inclusive range
            if (START_DT or END_DT) and timestamp is not None:
                if START_DT and timestamp < START_DT:
                    continue
                if END_DT and timestamp > END_DT:
                    continue
            elif (START_DT or END_DT) and timestamp is None:
                # If filtering by date but message has no timestamp, skip it
                continue

            timestamp_iso = timestamp.isoformat() if timestamp else None
            
            # Check if message was edited or unsent
            edited_timestamp = apple_time_to_datetime(date_edited) if date_edited else None
            retracted_timestamp = apple_time_to_datetime(date_retracted) if date_retracted else None
            
            # Determine if message was unsent/retracted
            is_unsent = False
            if date_retracted is not None and date_retracted > 0:
                is_unsent = True
            elif date_edited is not None and date_edited > 0:
                # Message was edited - check if it became empty (which means unsent)
                if not text and not attributed_body and not attachments_str:
                    is_unsent = True

            # Parse attachments from concatenated string
            if attachments_str:
                attachment_list = [a for a in attachments_str.split('|||') if a]
            else:
                attachment_list = []

            # Extract text - use text field first, fall back to attributedBody
            message_text = text
            if not message_text and attributed_body:
                message_text = extract_text_from_attributed_body(attributed_body)

            is_reaction_msg = assoc_guid is not None and is_reaction(assoc_type)
            # A message is only a "reply" if it's in a thread but NOT a reaction
            is_reply_msg = thread_orig_guid is not None and thread_orig_guid != "" and not is_reaction_msg

            all_messages[message_id] = {
                "id": message_id,
                "guid": guid,
                "timestamp": timestamp_iso,
                "sender": sender,
                "sender_name": sender_name,
                "text": message_text,
                "attachments": attachment_list,
                "is_reaction": is_reaction_msg,
                "is_reply": is_reply_msg,
                "is_unsent": is_unsent,
                "date_edited": edited_timestamp.isoformat() if edited_timestamp else None,
                "has_replies": False,
                "reactions": [],
                "reply_guids": [],
                "assoc_type": assoc_type,
                "assoc_guid": assoc_guid,
                "assoc_emoji": assoc_emoji,
                "thread_originator_guid": thread_orig_guid
            }

        # Get the messages to export (adjust range as needed)
        sorted_messages = sorted(all_messages.values(), key=lambda m: m["timestamp"] or "")
        recent_messages = sorted_messages  # Remove slice or adjust as needed

        # Build messages list and index
        for msg_obj in recent_messages:
            if len(msg_obj["attachments"]) == 0:
                msg_obj["attachment"] = None
            elif len(msg_obj["attachments"]) == 1:
                msg_obj["attachment"] = msg_obj["attachments"][0]
            else:
                msg_obj["attachment"] = msg_obj["attachments"]
            
            assoc_type = msg_obj.pop("assoc_type", None)
            assoc_emoji = msg_obj.pop("assoc_emoji", None)
            assoc_guid = msg_obj.get("assoc_guid")
            thread_orig_guid = msg_obj.get("thread_originator_guid")
            del msg_obj["attachments"]
            
            messages.append(msg_obj)
            message_index[msg_obj["guid"]] = msg_obj

            # If this is a reaction, attach it to parent message
            if msg_obj["is_reaction"] and assoc_guid:
                reaction_type_info = get_reaction_type(assoc_type, msg_obj["text"], assoc_emoji)
                
                reaction_entry = {
                    "reactor": msg_obj["sender"],
                    "reactor_name": msg_obj["sender_name"],
                    "reaction_type": reaction_type_info["type"],
                    "emoji": reaction_type_info["emoji"],
                    "display": reaction_type_info["display"],
                    "raw_text": msg_obj["text"],
                    "timestamp": msg_obj["timestamp"]
                }
                
                # Remove prefix from guid (e.g., "bp:" or "p:")
                clean_guid = clean_up_guid(assoc_guid)
                msg_obj["assoc_guid"] = clean_guid
                
                parent = message_index.get(clean_guid)
                if parent:
                    parent["reactions"].append(reaction_entry)
                else:
                    pending_reactions[clean_guid].append(reaction_entry)
            
            # If this is a reply, attach it to parent message using thread_originator_guid
            if msg_obj["is_reply"] and thread_orig_guid:
                # Remove prefix from guid if present
                clean_guid = clean_up_guid(thread_orig_guid)
                msg_obj["thread_originator_guid"] = clean_guid
                
                parent = message_index.get(clean_guid)
                if parent:
                    parent["has_replies"] = True
                    # Append to maintain chronological order (first reply at index 0)
                    parent["reply_guids"].append(msg_obj["guid"])
                else:
                    pending_replies[clean_guid].append(msg_obj["guid"])

        # Attach pending reactions and replies
        for guid, reactions_list in pending_reactions.items():
            parent = message_index.get(guid)
            if parent:
                parent["reactions"].extend(reactions_list)
        
        for guid, reply_guid_list in pending_replies.items():
            parent = message_index.get(guid)
            if parent:
                parent["has_replies"] = True
                # Extend to maintain chronological order
                parent["reply_guids"].extend(reply_guid_list)

        # ----------------------
        # EXPORT JSON
        # ----------------------
        json_path = f"{OUTPUT_DIR}/chat_{chat_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)

        print(f"✔ JSON saved to {json_path}")
        print(f"  Total messages exported: {len(messages)}")
        if skipped_system_messages > 0:
            print(f"  Skipped {skipped_system_messages} system messages")
        print()

    # ----------------------
    # MERGE CHATS WITH IDENTICAL PARTICIPANTS
    # ----------------------
    # Build groups keyed by the sorted tuple of normalized participant handles
    groups = {}
    for filename, meta in chat_name_mapping.items():
        participants = meta.get('participants_handles')
        if not participants:
            continue
        key = tuple(sorted(participants))
        groups.setdefault(key, []).append(filename)

    # For any group with more than one file, merge into the first file and remove duplicates
    for key, files in groups.items():
        if len(files) <= 1:
            continue
        files = sorted(files)
        target = files[0]
        merged_messages = []
        seen_guids = set()

        for fname in files:
            path = os.path.join(OUTPUT_DIR, fname)
            if not os.path.exists(path):
                continue
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    arr = json.load(f) or []
            except Exception:
                arr = []
            for m in arr:
                guid = m.get('guid')
                if guid and guid in seen_guids:
                    continue
                if guid:
                    seen_guids.add(guid)
                merged_messages.append(m)

        # sort merged messages by timestamp (ISO strings), fallback to guid
        def _ts_key(m):
            ts = m.get('timestamp')
            if not ts:
                return datetime.min
            try:
                return datetime.fromisoformat(ts)
            except Exception:
                try:
                    return datetime.fromisoformat(ts.replace('Z', '+00:00'))
                except Exception:
                    return datetime.min

        merged_messages.sort(key=_ts_key)

        # write merged to target file
        target_path = os.path.join(OUTPUT_DIR, target)
        try:
            with open(target_path, 'w', encoding='utf-8') as f:
                json.dump(merged_messages, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

        # determine include flag for merged file (based on any source mapping)
        include_flag = any(chat_name_mapping.get(f, {}).get('include', False) for f in files)

        # remove the other files and delete mapping entries for them
        for fname in files[1:]:
            path = os.path.join(OUTPUT_DIR, fname)
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass
            # remove from mapping
            if fname in chat_name_mapping:
                del chat_name_mapping[fname]

        # update target metadata
        chat_name_mapping[target]['num_msgs'] = len(merged_messages)
        chat_name_mapping[target]['include'] = include_flag
        chat_name_mapping[target]['merged_from'] = files

    # ================================================
    # EXPORT CHAT NAME MAPPING
    # ================================================
    mapping_path = f"{OUTPUT_DIR}/number_to_name.json"
    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(chat_name_mapping, f, indent=2, ensure_ascii=False)

    print(f"✔ Chat name mapping saved to {mapping_path}")
    print("All exports complete!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Export iMessage chats to JSON files")
    parser.add_argument("--sms-db-path", dest="sms_db_path", default=SMS_DB_PATH,
                        help="Path to the SMS chat database (defaults to data/chat.db)")
    parser.add_argument("--contacts-db-path", dest="contacts_db_path", default=CONTACTS_DB_PATH,
                        help="Path to the contacts database (defaults to data/contacts_db.abcddb)")
    parser.add_argument("--output-dir", dest="output_dir", default=OUTPUT_DIR,
                        help="Directory to write exported JSON files (defaults to exports)")
    parser.add_argument("--chats-selection", dest="chats_selection", default="all",
                        help="Comma-separated chat ROWIDs to export, or 'all' (default: all)")
    parser.add_argument("--start-date", dest="start_date", default="2025-01-01",
                        help="Optional start date (YYYY-MM-DD or ISO). Inclusive. (default: 2025-01-01)")
    parser.add_argument("--end-date", dest="end_date", default="2025-12-31",
                        help="Optional end date (YYYY-MM-DD or ISO). Inclusive. (default: 2025-12-31)")

    args = parser.parse_args()

    export_messages(
        SMS_DB_PATH=args.sms_db_path,
        CONTACTS_DB_PATH=args.contacts_db_path,
        OUTPUT_DIR=args.output_dir,
        chats_selection=args.chats_selection,
        start_date=args.start_date,
        end_date=args.end_date,
    )