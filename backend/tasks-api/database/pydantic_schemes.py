from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any
from database.enums import TaskCategoryEnum


class TaskModel(BaseModel):
    id: Optional[int] = None
    assigned_user_id: Optional[int]
    category: TaskCategoryEnum
    data_json: dict[str, Any]

    ai_pred: Optional[str] = None

    file_key_1: Optional[str]
    file_key_2: Optional[str]

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class TaskFilterModel(BaseModel):
    id: Optional[int] = None
    assigned_user_id: Optional[int] = None
    category: Optional[TaskCategoryEnum] = None
    data_json: Optional[dict[str, Any]] = None

    ai_pred: Optional[str] = None

    file_key_1: Optional[str] = None
    file_key_2: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class TaskKafkaModel(BaseModel):
    id: int
    assigned_user_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)