import secrets
import uuid
from datetime import datetime, UTC

def generate_project_api_key() -> str:
    """Generate a secure API key for projects."""
    # Format: ma_[timestamp]_[random]
    timestamp = int(datetime.now(UTC).timestamp())
    random_part = secrets.token_urlsafe(32)
    return f"ma_{timestamp}_{random_part}"

def validate_project_api_key(api_key: str) -> bool:
    """Validate the format of a project API key."""
    try:
        prefix, timestamp, random_part = api_key.split("_")
        return (
            prefix == "ma" and
            timestamp.isdigit() and
            len(random_part) > 0
        )
    except ValueError:
        return False 