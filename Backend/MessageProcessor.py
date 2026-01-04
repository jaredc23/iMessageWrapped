import emoji
from iMessage import iMessage

def extract_emojis(msg: iMessage):
    """
    Extracts all emojis using the emoji library.
    
    Args:
        text (str): The input text containing emojis
        
    Returns:
        list: A list of all emojis found in the text
    """
    if(msg.is_unsent):
        return []
    else:
        try:
            return [char for char in msg.text if char in emoji.EMOJI_DATA]
        except:
            print(msg, msg.id, msg.message_dict)
            return []
