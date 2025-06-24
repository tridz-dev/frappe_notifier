import re

def normalize_topic_name(topic_name: str) -> str:
    """
    Normalizes a topic name to be Firebase-compatible:
    - Removes spaces
    - Replaces invalid characters with hyphens
    - Ensures only allowed characters (A-Z, a-z, 0-9, _, -, ~)
    """
    # Remove leading/trailing whitespace
    topic_name = topic_name.strip()
    # Replace all whitespace characters (space, tabs, etc.) with a dash
    topic_name = re.sub(r'\s+', '', topic_name)
    # Remove all characters that are not allowed in Firebase topic names
    topic_name = re.sub(r'[^a-zA-Z0-9_\-~]', '', topic_name)
    return topic_name
