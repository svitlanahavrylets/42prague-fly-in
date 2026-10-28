from pydantic import BaseModel, Field
from typing import Any, Optional

class Connection(BaseModel):
    zones: tuple[str, str]
    max_link_capacity: int

