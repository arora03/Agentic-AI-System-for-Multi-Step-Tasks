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
    def __init__(self, name: str, system_prompt: str, model: str = "llama-3.3-70b-versatile"):
        self.name = name
        self.system_prompt = system_prompt
        self.model = model

    async def execute(self, prompt: str, retries: int = 3, json_mode: bool = False) -> str:
        client = get_groq_client()
        
        kwargs = {
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            "model": self.model,
            "temperature": 0.2
        }
        
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        for attempt in range(retries):
            try:
                response = await client.chat.completions.create(**kwargs)
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
        response = await self.execute(f"Create a plan for: {user_request}", json_mode=True)
        # Clean up if markdown backticks are present (JSON mode usually avoids this, but just in case)
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:-3].strip()
        elif response.startswith("```"):
            response = response[3:-3].strip()
        
        try:
            data = json.loads(response)
            return Plan(**data)
        except Exception as e:
            import re
            # Fallback aggressive JSON repair
            try:
                match = re.search(r'\[.*\]', response, re.DOTALL)
                if match:
                    cleaned = re.sub(r',\s*([\]}])', r'\1', match.group(0))
                    tasks_list = json.loads(cleaned)
                    return Plan(tasks=tasks_list)
            except:
                pass
            raise Exception(f"Planner failed to parse JSON: {e}\nRaw output: {response}")

class RetrieverAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Retriever",
            system_prompt="You are a Retriever Agent. Your job is to extract the main search query from the task description. Reply with ONLY the search query term, nothing else."
        )

    async def execute(self, prompt: str, retries: int = 3) -> str:
        # Step 1: Get the search query from LLM
        query = await super().execute(prompt, retries)
        query = query.strip().strip('"').strip("'")
        
        # Step 2: Use Wikipedia API to fetch real data
        import urllib.request
        import urllib.parse
        try:
            search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&utf8=&format=json"
            req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
            
            # Using run_in_executor for blocking urllib call to not block the event loop
            loop = asyncio.get_event_loop()
            def fetch(url):
                with urllib.request.urlopen(req) as response:
                    return json.loads(response.read().decode('utf-8'))
            
            search_data = await loop.run_in_executor(None, fetch, search_url)
            
            if not search_data['query']['search']:
                return f"Real Tool Execution: No Wikipedia results found for '{query}'."
                
            best_title = search_data['query']['search'][0]['title']
            summary_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&explaintext&titles={urllib.parse.quote(best_title)}&format=json"
            
            req2 = urllib.request.Request(summary_url, headers={'User-Agent': 'Mozilla/5.0'})
            def fetch2(url):
                with urllib.request.urlopen(req2) as response:
                    return json.loads(response.read().decode('utf-8'))
                    
            summary_data = await loop.run_in_executor(None, fetch2, summary_url)
            pages = summary_data['query']['pages']
            extract = list(pages.values())[0].get('extract', 'No content found.')
            
            return f"Real Tool Execution (Wikipedia - {best_title}):\n{extract[:1500]}..." # Limit context size
            
        except Exception as e:
            # Fallback to hallucination if internet/wiki fails
            fallback_prompt = "You are a helpful assistant. Provide a comprehensive summary based on your internal knowledge. " + prompt
            return f"Tool Execution Failed: {str(e)}. Fallback to internal knowledge: " + await super().execute(fallback_prompt, retries)

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
