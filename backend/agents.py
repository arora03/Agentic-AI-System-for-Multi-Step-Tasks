import os
import json
import asyncio
from typing import Dict, Any
from groq import AsyncGroq
from models import TaskDef, Plan

# Try to get API key from environment, will be loaded from .env in main.py
def get_groq_client():
    return AsyncGroq(api_key=os.environ.get("GROQ_API_KEY", "dummy"))

class BaseAgent:
    def __init__(self, name: str, system_prompt: str, model: str = "llama3-70b-8192"):
        self.name = name
        self.system_prompt = system_prompt
        self.model = model

    async def execute(self, prompt: str, retries: int = 3) -> str:
        client = get_groq_client()
        for attempt in range(retries):
            try:
                response = await client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    model=self.model,
                    temperature=0.2
                )
                return response.choices[0].message.content
            except Exception as e:
                if attempt == retries - 1:
                    raise Exception(f"Agent {self.name} failed after {retries} attempts: {str(e)}")
                await asyncio.sleep(2 ** attempt) # Exponential backoff

class PlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Planner",
            system_prompt="""You are a Planner Agent. Your job is to break down complex requests into a sequence of smaller tasks.
Output MUST be valid JSON matching this schema:
{
  "tasks": [
    {
      "id": "task_1",
      "description": "...",
      "assigned_agent": "Retriever | Analyzer | Writer",
      "dependencies": []
    }
  ]
}
Return ONLY valid JSON, no other text."""
        )

    async def plan(self, user_request: str) -> Plan:
        response = await self.execute(f"Create a plan for: {user_request}")
        # Clean up if markdown backticks are present
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:-3].strip()
        elif response.startswith("```"):
            response = response[3:-3].strip()
        
        try:
            data = json.loads(response)
            return Plan(**data)
        except Exception as e:
            raise Exception(f"Planner failed to parse JSON: {e}\nRaw output: {response}")

class RetrieverAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Retriever",
            system_prompt="You are a Retriever Agent. Your job is to gather facts, simulate web searches, and provide context. Be concise and factual."
        )

class AnalyzerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Analyzer",
            system_prompt="You are an Analyzer Agent. Your job is to analyze data provided by the Retriever and extract key insights. If asked to simulate a failure, respond with explicitly malformed output."
        )

class WriterAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Writer",
            system_prompt="You are a Writer Agent. Your job is to take analyzed insights and draft a final, well-formatted response."
        )
