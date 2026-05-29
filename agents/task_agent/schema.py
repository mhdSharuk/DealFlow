from pydantic import BaseModel, Field
from typing import List, Optional

class TaskItem(BaseModel):
    assignee: str = Field(description='Name of the internal employee responsible for the task')
    action_items: str = Field(description='Clear task definition for the JIRA tickets')
    blocker: Optional[str] = Field(default=None, 
                                   description = 'Dependencies or blocker for finishing the task, if any')
    

class TaskOutput(BaseModel):
    tasks: List[TaskItem] = Field(description='List of tasks with assignees, action items, and blockers if any')
    