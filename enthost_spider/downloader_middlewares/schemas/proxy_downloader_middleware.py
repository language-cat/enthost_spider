from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProxyInfoSchema(BaseModel):
    id: Optional[str]
    user: str
    proxy: str
    counter: Optional[str] = Field(default=1)
    proxy_time_out: Optional[str] = Field(default=0)
    create_time: Optional[datetime] = Field(default=datetime.now)
    modify_date: Optional[datetime] = Field(default=datetime.now)
