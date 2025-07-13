from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from database.controller import get_tasks
from deps import user_role


router = APIRouter()


@router.get("/list")
async def list_tasks(id: int | None = None, limit: int | None = None, offset: int = 0,):
    # if user_role != "ROLE_USER":
    #     raise HTTPException(status_code=403, detail="Forbidden.")
    tasks = await get_tasks(task_id=id, limit=limit, offset=offset)
    return tasks