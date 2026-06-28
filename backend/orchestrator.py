import asyncio
import json
from typing import Dict, Any, List
from models import Plan, TaskDef
from agents import PlannerAgent, RetrieverAgent, AnalyzerAgent, WriterAgent

class Orchestrator:
    def __init__(self):
        self.planner = PlannerAgent()
        self.agents = {
            "Retriever": RetrieverAgent(),
            "Analyzer": AnalyzerAgent(),
            "Writer": WriterAgent()
        }
        self.results: Dict[str, Any] = {}
        self.event_queue = asyncio.Queue()
    
    async def run(self, user_request: str):
        await self.event_queue.put({"type": "status", "message": "Planning..."})
        try:
            plan = await self.planner.plan(user_request)
            await self.event_queue.put({"type": "plan", "data": plan.model_dump()})
        except Exception as e:
            await self.event_queue.put({"type": "error", "message": f"Planning failed: {str(e)}"})
            return

        pending_tasks = plan.tasks.copy()
        completed_tasks = set()

        while pending_tasks:
            # Find tasks with all dependencies met
            ready_tasks = [t for t in pending_tasks if all(d in completed_tasks for d in t.dependencies)]
            
            if not ready_tasks:
                if pending_tasks:
                    await self.event_queue.put({"type": "error", "message": "Deadlock detected. Unmet dependencies."})
                break

            await self.event_queue.put({
                "type": "status", 
                "message": f"Executing batch of {len(ready_tasks)} tasks concurrently: {[t.id for t in ready_tasks]}"
            })

            # Execute batch concurrently
            tasks_to_run = [self.execute_task(t) for t in ready_tasks]
            batch_results = await asyncio.gather(*tasks_to_run, return_exceptions=True)

            for task, result in zip(ready_tasks, batch_results):
                pending_tasks.remove(task)
                if isinstance(result, Exception):
                    await self.event_queue.put({"type": "error", "message": f"Task {task.id} failed: {str(result)}"})
                    return # Halt execution on failure for safety
                else:
                    completed_tasks.add(task.id)
                    self.results[task.id] = result
                    await self.event_queue.put({
                        "type": "task_complete", 
                        "task_id": task.id, 
                        "result": result
                    })

        await self.event_queue.put({"type": "status", "message": "All tasks completed."})
        await self.event_queue.put({"type": "done", "data": self.results})

    async def execute_task(self, task: TaskDef):
        agent = self.agents.get(task.assigned_agent)
        if not agent:
            raise Exception(f"Agent '{task.assigned_agent}' not found.")
        
        # Build context from dependencies
        context = {d: self.results[d] for d in task.dependencies if d in self.results}
        
        prompt = f"Task: {task.description}\n\nContext from previous tasks:\n{json.dumps(context)}"
        
        await self.event_queue.put({"type": "task_start", "task_id": task.id, "agent": task.assigned_agent})
        
        # The execute method handles retries
        result = await agent.execute(prompt)
        return result

    async def stream_events(self):
        while True:
            event = await self.event_queue.get()
            yield json.dumps(event)
            if event["type"] in ["done", "error"]:
                break
