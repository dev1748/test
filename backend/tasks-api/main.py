from fastapi import FastAPI
from uploads_router import router as uploads
from list_router import router as list_router
from assign_router import router as assign_router
from faststream.kafka import KafkaBroker
import uvicorn

# broker = KafkaBroker(bootstrap_servers="localhost:9092")

# @broker.subscriber("completed-tasks")
# async def complete_task(msg: str):
#     print(f"Recieved completed task: {msg}")

app = FastAPI()
app.include_router(uploads, prefix="/task")
app.include_router(list_router, prefix="/task")
app.include_router(assign_router, prefix="/task")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
