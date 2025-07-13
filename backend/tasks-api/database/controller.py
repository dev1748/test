import asyncio
from datetime import datetime
from database.dao.basedao import BaseDAO
from database.dao.session_maker import connection
from database.models import Task
from database.enums import TaskCategoryEnum
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, create_model
from typing import List, Optional, Any
from database.pydantic_schemes import TaskModel, TaskFilterModel


class TaskDAO(BaseDAO[Task]):
    model = Task


default_order_lmbd = lambda a: a.created_at.desc()


@connection(commit=False)
async def get_tasks(session: AsyncSession, task_id: int | None = None,
                    user_id: int | None = None,
                    task_category: TaskCategoryEnum | None = None,
                    limit: int | None = None,
                    offset: int = 0):
    data = await TaskDAO.find_all(session=session, filters=TaskFilterModel(
        id=task_id,
        assigned_user_id=user_id,
        category=task_category,
    ), order_by_lmbd=default_order_lmbd, limit=limit, offset=offset)
    validated_data = [TaskModel.model_validate(i) for i in data]
    return validated_data

@connection(commit=True)
async def create_task(session: AsyncSession, task_category: TaskCategoryEnum, 
                    data_json: dict[str, Any],
                    user_id: int | None = None,
                    file_key_1: str | None = None,
                    file_key_2: str | None = None,):
    task = await TaskDAO.add(session=session, values=TaskModel(
        assigned_user_id = user_id,
        category = task_category,
        data_json=data_json,
        file_key_1=file_key_1,
        file_key_2=file_key_2
    ))
    return TaskModel.model_validate(task)

@connection(commit=True)
async def assign_task_to_user(session: AsyncSession, task_id: int, user_id: int):
    await TaskDAO.update_one_by_id(session=session, data_id=task_id, values=TaskFilterModel(
        assigned_user_id=user_id
    ))

@connection(commit=True)
async def insert_prediction_into_task(session: AsyncSession, task_id: int, prediction: str):
    await TaskDAO.update_one_by_id(session=session, data_id=task_id, values=TaskFilterModel(
        ai_pred=prediction
    ))
