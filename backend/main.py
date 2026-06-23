from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import asyncio
from dotenv import load_dotenv

from orchestrator import Orchestrator

# Load environment variables from .env
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PromptRequest(BaseModel):
    prompt: str

@app.post("/api/orchestrate")
async def orchestrate(request: PromptRequest):
    orchestrator = Orchestrator()
    
    # Run the orchestrator in a background task so we can return the stream response immediately
    asyncio.create_task(orchestrator.run(request.prompt))
    
    return EventSourceResponse(orchestrator.stream_events())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
