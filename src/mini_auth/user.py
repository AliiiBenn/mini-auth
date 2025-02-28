import datetime
from typing import Final


class User:
    id: Final[int]
    email: Final[str]
    name: Final[str]
    created_at: Final[datetime.datetime]
    updated_at: Final[datetime.datetime]

    
