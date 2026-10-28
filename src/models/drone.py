from pydantic import BaseModel, Field
from typing import Any, Optional

class Connection(BaseModel):
    id: int
    max_link_capacity: int