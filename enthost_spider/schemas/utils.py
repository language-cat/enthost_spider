from pydantic import BaseModel, Field
from typing import Optional


class KwargsSchema(BaseModel):
    """
    用于接收kwargs参数设置默认值，作统一处理
    """
    is_async: Optional[bool] = Field(default=False)
    is_truncate_bloomfilter: Optional[bool] = Field(default=False)
