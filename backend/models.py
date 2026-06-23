from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class TaskDef(BaseModel):
    id: str = Field(description="Unique task ID, e.g., task_1")
    description: str = Field(description="Detailed description of what needs to be done")
    assigned_agent: str = Field(description="Agent to handle this: 'Retriever', 'Analyzer', or 'Writer'")
    dependencies: List[str] = Field(default_factory=list, description="List of task IDs that must complete before this one")

class Plan(BaseModel):
    tasks: List[TaskDef] = Field(description="List of tasks representing the full execution plan")

class AgentResult(BaseModel):
    task_id: str
    status: str
    output: Any
    error: Optional[str] = None
