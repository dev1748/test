from fastapi import APIRouter
from database.controller import assign_task_to_user


router = APIRouter()


@router.post("/assign")
async def assign_task_route(id_task: int, id_user: int):
    await assign_task_to_user(task_id=id_task, user_id=id_user)
    return "OK"