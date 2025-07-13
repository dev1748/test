from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, Annotated, Union
from database.enums import TaskCategoryEnum
from database.controller import create_task, insert_prediction_into_task
from database.pydantic_schemes import TaskModel, TaskKafkaModel
import httpx
import json
import asyncio
# from faststream import FastStream, Context
# from faststream.kafka import KafkaBroker
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from deps import user_role


URL = "http://upload-api:5050"
AI_URL = "http://tasks-ai-api:7070"

router = APIRouter(prefix="/upload")

producer = None

async def get_producer():
    global producer
    if producer is None:
        producer = AIOKafkaProducer(bootstrap_servers="kafka:9092")
        await producer.start()
    return producer


class PredictionModel(BaseModel):
    task_id: int
    prediction: str

    model_config = ConfigDict(from_attributes=True)


async def consume_messages():
    print("Trying to initialize consumer")
    consumer = AIOKafkaConsumer(
        "ai_predictions",
        bootstrap_servers="kafka:9092",
        group_id='ai-predictions-processor'
    )
    await consumer.start()
    print("Started consuming")
    try:
        async for msg in consumer:
            message_data = json.loads(msg.value.decode('utf-8'))
            prediction = PredictionModel(**message_data)
            await insert_prediction_into_task(task_id=prediction.task_id, prediction=prediction.prediction)
    finally:
        print("Shutting consumer down")
        await consumer.stop()


@router.on_event("startup")
async def startup_event():
    await get_producer()  # Initialize producer on startup
    asyncio.create_task(consume_messages())

@router.on_event("shutdown")
async def shutdown_event():
    if producer:
        await producer.stop()


async def publish_to_tasks(message: str):
    try:
        producer = await get_producer()
        await producer.send("tasks", message.encode('utf-8'))
        print(f"✅ Published message: {message[:100]}...")  # Debug log
    except Exception as e:
        print(f"❌ Publish failed: {e}")
        raise HTTPException(500, "Message publishing failed")


# broker = KafkaBroker(bootstrap_servers="kafka:9092")
# stream = FastStream(broker=broker)

# to_tasks = broker.publisher("tasks")

# @broker.publisher("tasks")
# async def publish_to_tasks(msg: str):
#     return msg

# @broker.subscriber("tasks", no_ack=True)
# async def dummy_consumer(msg: str):
#     print(f"Received test message: {msg[:100]}...")

# @router.on_event("startup")
# async def startup():
#     await broker.start()

# @router.on_event("shutdown")
# async def shutdown():
#     await broker.close()

class TaskRequestModel(BaseModel):
    assigned_user_id: Optional[int] = None
    category: TaskCategoryEnum
    data_json: dict[str, Any]
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

async def get_task_data(task: str = Form(...)):
    return TaskRequestModel(**json.loads(task))

@router.post("/image")
async def upload_task_with_image(task: TaskRequestModel = Depends(get_task_data), file: UploadFile = File(...),
                                second_file: Annotated[Union[UploadFile, None], File()] = None,
                                user_role: str = Depends(user_role)):
    print(user_role)
    if user_role != "ROLE_ADMIN":
        raise HTTPException(status_code=403, detail="Forbidden.")
    upload_url = f"{URL}/upload/images"
    file_bytes = await file.read()
    file_key_2 = None
    files = {
        "file": (file.filename, file_bytes, file.content_type)
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url=upload_url, files=files)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code)
        file_key_1 = response.json()["file_key"]
    if second_file:
        second_file_bytes = await second_file.read()
        files_2 = {
            "file": (second_file.filename, second_file_bytes,
                    second_file.content_type)
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url=upload_url, files=files_2)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code)
            file_key_2 = response.json()["file_key"]
    new_task = await create_task(task_category=task.category,
                     data_json=task.data_json,
                     user_id=task.assigned_user_id,
                     file_key_1=file_key_1, file_key_2=file_key_2 if file_key_2 else None)
    task_to_send = TaskKafkaModel.model_validate(new_task)
    if task_to_send.assigned_user_id:
        message = task_to_send.model_dump_json()
        await publish_to_tasks(message=message)
    return "OK"


@router.post("/text")
async def upload_task_with_text(task: TaskRequestModel = Depends(get_task_data),
                                user_role: str = Depends(user_role)):
    print(user_role)
    # if user_role != "ROLE_USER":
    #     raise HTTPException(status_code=403, detail="Forbidden.")
    new_task = await create_task(task_category=task.category,
                     data_json=task.data_json,
                     user_id=task.assigned_user_id)
    task_to_send = TaskKafkaModel.model_validate(new_task)
    task_send_to_ai = TaskModel.model_validate(new_task)
    if task_to_send.assigned_user_id:
        message = task_to_send.model_dump_json()
        await publish_to_tasks(message=message)
    async with httpx.AsyncClient() as client:
        await client.post(f"{AI_URL}/pred", json=task_send_to_ai.model_dump())
    return "OK"


# @router.post("/image")
# async def upload_image(file: UploadFile = File(...)):
#     file_bytes = await file.read()
#     files = {
#         "file": (file.filename, file_bytes, file.content_type)
#     }
#     async with httpx.AsyncClient() as client:
#         response = await client.post(url=f"{URL}/upload/images", files=files)
    
#     return {
#         "status_code": response.status_code,
#         "response": response.json() if response.headers.get("content-type") == "application/json" \
#              else response.text
#     }

# @router.post("/text")
# async def upload_image(file: UploadFile = File(...)):
#     file_bytes = await file.read()
#     files = {
#         "file": (file.filename, file_bytes, file.content_type)
#     }
#     async with httpx.AsyncClient() as client:
#         response = await client.post(url=f"{URL}/upload/text", files=files)
    
#     return {
#         "status_code": response.status_code,
#         "response": response.json() if response.headers.get("content-type") == "application/json" \
#              else response.text
#     }