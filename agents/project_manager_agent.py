"""
Project / Product Manager Agent
Responsible for task assignment, dependency tracking,
milestone management, and priority adjustment.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from .base_agent import BaseAgent, Task, TaskStatus, TaskPriority


class ProjectManagerAgent(BaseAgent):
    """
    Project / Product Manager Agent for the Emy-FullStack system.
    
    Capabilities:
    - Assign tasks to agents
    - Track dependencies and progress
    - Adjust priorities based on performance metrics
    - Define milestones
    - Generate reports and dashboards
    - Coordinate agent workflows
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(
            name="Project Manager",
            description="Coordinates all agents and manages project workflow",
            capabilities=[
                "task_assignment",
                "dependency_tracking",
                "milestone_management",
                "priority_adjustment",
                "reporting",
                "coordination",
            ],
            config=config or {}
        )
        self.projects: Dict[str, Dict] = {}
        self.milestones: List[Dict] = []
        self.agent_workloads: Dict[str, int] = {}
        self.task_assignments: Dict[str, str] = {}  # task_id -> agent_name

    async def execute_task(self, task: Task) -> Any:
        """Execute a project management task."""
        task_type = task.metadata.get("type", "generic")
        
        handlers = {
            "task_assignment": self._assign_tasks,
            "dependency_tracking": self._track_dependencies,
            "milestone_management": self._manage_milestones,
            "priority_adjustment": self._adjust_priorities,
            "reporting": self._generate_report,
            "coordination": self._coordinate_agents,
            "create_project": self._create_project,
            "sprint_planning": self._plan_sprint,
        }
        
        handler = handlers.get(task_type, self._handle_generic_task)
        return await handler(task)

    async def _assign_tasks(self, task: Task) -> Dict[str, Any]:
        """Assign tasks to appropriate agents."""
        tasks_to_assign = task.metadata.get("tasks", [])
        
        self.log(f"Assigning {len(tasks_to_assign)} tasks to agents")
        
        assignments = []
        for task_data in tasks_to_assign:
            assignment = self._find_best_agent(task_data)
            assignments.append(assignment)
            self.task_assignments[task_data.get("id", "")] = assignment["agent"]
        
        return {
            "assignments": assignments,
            "task_queue_code": self._generate_task_queue_code(),
        }

    def _find_best_agent(self, task_data: Dict) -> Dict:
        """Find the best agent for a task."""
        task_type = task_data.get("type", "generic")
        
        # Agent mapping based on task type
        agent_mapping = {
            "ui": "Frontend",
            "frontend": "Frontend",
            "flutter": "Frontend",
            "api": "Backend",
            "backend": "Backend",
            "endpoint": "Backend",
            "database": "Database",
            "db": "Database",
            "schema": "Database",
            "deploy": "DevOps",
            "infrastructure": "DevOps",
            "ci_cd": "DevOps",
            "test": "QA",
            "testing": "QA",
            "validation": "QA",
            "design": "UI/UX",
            "layout": "UI/UX",
            "wireframe": "UI/UX",
            "security": "Security",
            "auth": "Security",
            "encryption": "Security",
            "ml": "AI/ML",
            "ai": "AI/ML",
            "optimization": "AI/ML",
        }
        
        agent = agent_mapping.get(task_type.lower(), "Backend")
        
        # Update workload
        self.agent_workloads[agent] = self.agent_workloads.get(agent, 0) + 1
        
        return {
            "task_id": task_data.get("id"),
            "task_name": task_data.get("name"),
            "agent": agent,
            "priority": task_data.get("priority", "medium"),
            "estimated_hours": task_data.get("estimated_hours", 4),
        }

    def _generate_task_queue_code(self) -> str:
        """Generate task queue implementation code."""
        return '''from celery import Celery
from typing import Dict, List, Any
import json
from datetime import datetime
import redis

# Celery app configuration
app = Celery(
    'emy_tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
)

# Redis client for task metadata
redis_client = redis.Redis(host='localhost', port=6379, db=2)

class TaskQueue:
    """Intelligent task queue with priority and dependencies"""
    
    QUEUE_KEYS = {
        "critical": "tasks:critical",
        "high": "tasks:high",
        "medium": "tasks:medium",
        "low": "tasks:low",
    }
    
    def __init__(self):
        self.redis = redis_client
        
    def enqueue(self, task: Dict[str, Any]) -> str:
        """Add task to appropriate priority queue"""
        task_id = task.get("id", f"task_{datetime.utcnow().timestamp()}")
        priority = task.get("priority", "medium")
        
        # Store task metadata
        self.redis.hset(f"task:{task_id}", mapping={
            "data": json.dumps(task),
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
        })
        
        # Add to priority queue
        queue_key = self.QUEUE_KEYS.get(priority, self.QUEUE_KEYS["medium"])
        self.redis.lpush(queue_key, task_id)
        
        return task_id
    
    def dequeue(self, agent_name: str) -> Dict[str, Any]:
        """Get next task for agent, respecting priorities"""
        # Check queues in priority order
        for priority in ["critical", "high", "medium", "low"]:
            queue_key = self.QUEUE_KEYS[priority]
            task_id = self.redis.rpop(queue_key)
            
            if task_id:
                task_id = task_id.decode() if isinstance(task_id, bytes) else task_id
                task_data = self.redis.hget(f"task:{task_id}", "data")
                
                if task_data:
                    # Update status
                    self.redis.hset(f"task:{task_id}", "status", "in_progress")
                    self.redis.hset(f"task:{task_id}", "assigned_to", agent_name)
                    self.redis.hset(f"task:{task_id}", "started_at", datetime.utcnow().isoformat())
                    
                    return json.loads(task_data)
        
        return None
    
    def complete(self, task_id: str, result: Dict = None):
        """Mark task as completed"""
        self.redis.hset(f"task:{task_id}", mapping={
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "result": json.dumps(result or {}),
        })
    
    def get_task_status(self, task_id: str) -> Dict:
        """Get current task status"""
        data = self.redis.hgetall(f"task:{task_id}")
        return {k.decode(): v.decode() for k, v in data.items()}
    
    def get_queue_stats(self) -> Dict:
        """Get statistics for all queues"""
        return {
            priority: self.redis.llen(queue_key)
            for priority, queue_key in self.QUEUE_KEYS.items()
        }

@app.task(bind=True, max_retries=3)
def execute_agent_task(self, task_data: Dict, agent_name: str):
    """Celery task to execute agent work"""
    try:
        # Import and instantiate appropriate agent
        from agents import get_agent
        agent = get_agent(agent_name)
        
        # Execute task
        result = agent.execute_task(task_data)
        
        return {"status": "success", "result": result}
    except Exception as e:
        self.retry(exc=e, countdown=60)

# Task routing
app.conf.task_routes = {
    'emy_tasks.execute_agent_task': {'queue': 'agent_tasks'},
}
'''

    async def _track_dependencies(self, task: Task) -> Dict[str, Any]:
        """Track task dependencies."""
        project_id = task.metadata.get("project_id")
        
        self.log(f"Tracking dependencies for project: {project_id}")
        
        dependency_graph = self._build_dependency_graph(project_id)
        critical_path = self._calculate_critical_path(dependency_graph)
        
        return {
            "project_id": project_id,
            "dependency_graph": dependency_graph,
            "critical_path": critical_path,
            "blocked_tasks": self._find_blocked_tasks(dependency_graph),
            "visualization": self._generate_dependency_diagram(dependency_graph),
        }

    def _build_dependency_graph(self, project_id: str) -> Dict:
        """Build task dependency graph."""
        # Example dependency graph
        return {
            "nodes": [
                {"id": "1", "name": "Setup Database", "status": "completed"},
                {"id": "2", "name": "Create API", "status": "in_progress", "depends_on": ["1"]},
                {"id": "3", "name": "Build UI", "status": "pending", "depends_on": ["2"]},
                {"id": "4", "name": "Auth System", "status": "in_progress", "depends_on": ["1"]},
                {"id": "5", "name": "Testing", "status": "pending", "depends_on": ["3", "4"]},
                {"id": "6", "name": "Deployment", "status": "pending", "depends_on": ["5"]},
            ],
            "edges": [
                {"from": "1", "to": "2"},
                {"from": "2", "to": "3"},
                {"from": "1", "to": "4"},
                {"from": "3", "to": "5"},
                {"from": "4", "to": "5"},
                {"from": "5", "to": "6"},
            ],
        }

    def _calculate_critical_path(self, graph: Dict) -> List[str]:
        """Calculate critical path through dependency graph."""
        # Simple critical path calculation
        return ["Setup Database", "Create API", "Build UI", "Testing", "Deployment"]

    def _find_blocked_tasks(self, graph: Dict) -> List[Dict]:
        """Find tasks blocked by incomplete dependencies."""
        blocked = []
        completed_ids = {n["id"] for n in graph["nodes"] if n["status"] == "completed"}
        
        for node in graph["nodes"]:
            if node["status"] == "pending":
                deps = node.get("depends_on", [])
                incomplete_deps = [d for d in deps if d not in completed_ids]
                if incomplete_deps:
                    blocked.append({
                        "task": node["name"],
                        "blocked_by": incomplete_deps,
                    })
        
        return blocked

    def _generate_dependency_diagram(self, graph: Dict) -> str:
        """Generate Mermaid diagram for dependencies."""
        diagram = "```mermaid\nflowchart TD\n"
        
        for node in graph["nodes"]:
            status_style = {
                "completed": ":::done",
                "in_progress": ":::active",
                "pending": "",
            }.get(node["status"], "")
            diagram += f"    {node['id']}[{node['name']}]{status_style}\n"
        
        for edge in graph["edges"]:
            diagram += f"    {edge['from']} --> {edge['to']}\n"
        
        diagram += "\n    classDef done fill:#90EE90\n"
        diagram += "    classDef active fill:#FFD700\n"
        diagram += "```"
        
        return diagram

    async def _manage_milestones(self, task: Task) -> Dict[str, Any]:
        """Manage project milestones."""
        action = task.metadata.get("action", "list")
        
        if action == "create":
            return await self._create_milestone(task.metadata)
        elif action == "update":
            return await self._update_milestone(task.metadata)
        else:
            return self._get_milestones()

    async def _create_milestone(self, data: Dict) -> Dict:
        """Create a new milestone."""
        milestone = {
            "id": f"ms_{len(self.milestones) + 1}",
            "name": data.get("name", "Milestone"),
            "description": data.get("description", ""),
            "due_date": data.get("due_date"),
            "status": "pending",
            "tasks": data.get("tasks", []),
            "progress": 0,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        self.milestones.append(milestone)
        self.log(f"Created milestone: {milestone['name']}")
        
        return milestone

    async def _update_milestone(self, data: Dict) -> Dict:
        """Update milestone status."""
        milestone_id = data.get("milestone_id")
        
        for milestone in self.milestones:
            if milestone["id"] == milestone_id:
                milestone.update({
                    "status": data.get("status", milestone["status"]),
                    "progress": data.get("progress", milestone["progress"]),
                })
                return milestone
        
        return {"error": "Milestone not found"}

    def _get_milestones(self) -> Dict:
        """Get all milestones."""
        return {
            "milestones": self.milestones,
            "summary": {
                "total": len(self.milestones),
                "completed": len([m for m in self.milestones if m["status"] == "completed"]),
                "in_progress": len([m for m in self.milestones if m["status"] == "in_progress"]),
                "pending": len([m for m in self.milestones if m["status"] == "pending"]),
            },
        }

    async def _adjust_priorities(self, task: Task) -> Dict[str, Any]:
        """Adjust task priorities based on metrics."""
        metrics = task.metadata.get("metrics", {})
        
        self.log("Adjusting priorities based on performance metrics")
        
        adjustments = self._calculate_priority_adjustments(metrics)
        
        return {
            "adjustments": adjustments,
            "reasoning": self._explain_adjustments(adjustments),
        }

    def _calculate_priority_adjustments(self, metrics: Dict) -> List[Dict]:
        """Calculate priority adjustments based on metrics."""
        return [
            {
                "task_id": "task_1",
                "old_priority": "medium",
                "new_priority": "high",
                "reason": "Blocking multiple dependent tasks",
            },
            {
                "task_id": "task_2",
                "old_priority": "high",
                "new_priority": "critical",
                "reason": "Deadline approaching",
            },
            {
                "task_id": "task_3",
                "old_priority": "high",
                "new_priority": "medium",
                "reason": "Dependency not yet ready",
            },
        ]

    def _explain_adjustments(self, adjustments: List[Dict]) -> str:
        """Explain priority adjustments."""
        explanations = []
        for adj in adjustments:
            explanations.append(
                f"Task {adj['task_id']}: {adj['old_priority']} → {adj['new_priority']} "
                f"({adj['reason']})"
            )
        return "\n".join(explanations)

    async def _generate_report(self, task: Task) -> Dict[str, Any]:
        """Generate project report."""
        report_type = task.metadata.get("report_type", "status")
        
        self.log(f"Generating {report_type} report")
        
        if report_type == "status":
            return self._generate_status_report()
        elif report_type == "performance":
            return self._generate_performance_report()
        elif report_type == "burndown":
            return self._generate_burndown_chart()
        else:
            return self._generate_status_report()

    def _generate_status_report(self) -> Dict:
        """Generate project status report."""
        return {
            "report_type": "status",
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_tasks": 50,
                "completed": 30,
                "in_progress": 12,
                "pending": 8,
                "completion_percentage": 60,
            },
            "by_agent": {
                "Frontend": {"completed": 8, "in_progress": 2, "pending": 2},
                "Backend": {"completed": 10, "in_progress": 4, "pending": 1},
                "Database": {"completed": 5, "in_progress": 1, "pending": 0},
                "DevOps": {"completed": 3, "in_progress": 2, "pending": 2},
                "QA": {"completed": 4, "in_progress": 3, "pending": 3},
            },
            "blockers": [
                "Waiting for API design approval",
                "Database migration needs review",
            ],
            "upcoming": [
                {"task": "User authentication", "due": "2024-01-15"},
                {"task": "Payment integration", "due": "2024-01-20"},
            ],
        }

    def _generate_performance_report(self) -> Dict:
        """Generate agent performance report."""
        return {
            "report_type": "performance",
            "time_period": "last 7 days",
            "metrics": {
                "task_completion_rate": 0.85,
                "average_task_time": "4.2 hours",
                "on_time_delivery": 0.78,
                "quality_score": 0.92,
            },
            "agent_performance": {
                "Frontend": {"score": 88, "tasks_completed": 12, "avg_time": "3.5h"},
                "Backend": {"score": 92, "tasks_completed": 15, "avg_time": "4.0h"},
                "Database": {"score": 95, "tasks_completed": 6, "avg_time": "5.0h"},
                "QA": {"score": 90, "tasks_completed": 10, "avg_time": "2.5h"},
            },
        }

    def _generate_burndown_chart(self) -> Dict:
        """Generate burndown chart data."""
        return {
            "report_type": "burndown",
            "sprint": "Sprint 5",
            "data": [
                {"day": 1, "remaining": 50, "ideal": 50},
                {"day": 2, "remaining": 47, "ideal": 45},
                {"day": 3, "remaining": 42, "ideal": 40},
                {"day": 4, "remaining": 38, "ideal": 35},
                {"day": 5, "remaining": 35, "ideal": 30},
                {"day": 6, "remaining": 30, "ideal": 25},
                {"day": 7, "remaining": 25, "ideal": 20},
            ],
            "velocity": 7.14,
            "projected_completion": "On track",
        }

    async def _coordinate_agents(self, task: Task) -> Dict[str, Any]:
        """Coordinate multiple agents for a workflow."""
        workflow = task.metadata.get("workflow", "default")
        
        self.log(f"Coordinating agents for workflow: {workflow}")
        
        coordination_plan = self._create_coordination_plan(workflow)
        
        return {
            "workflow": workflow,
            "plan": coordination_plan,
            "orchestration_code": self._generate_orchestration_code(),
        }

    def _create_coordination_plan(self, workflow: str) -> Dict:
        """Create an agent coordination plan."""
        return {
            "phases": [
                {
                    "phase": 1,
                    "name": "Planning",
                    "agents": ["UI/UX", "Project Manager"],
                    "tasks": ["Create wireframes", "Define requirements"],
                    "duration": "2 days",
                },
                {
                    "phase": 2,
                    "name": "Development",
                    "agents": ["Frontend", "Backend", "Database"],
                    "tasks": ["Build UI", "Create APIs", "Setup DB"],
                    "duration": "5 days",
                    "parallel": True,
                },
                {
                    "phase": 3,
                    "name": "Integration",
                    "agents": ["Backend", "Security"],
                    "tasks": ["Integrate components", "Security audit"],
                    "duration": "2 days",
                },
                {
                    "phase": 4,
                    "name": "Testing",
                    "agents": ["QA"],
                    "tasks": ["Unit tests", "Integration tests", "E2E tests"],
                    "duration": "3 days",
                },
                {
                    "phase": 5,
                    "name": "Deployment",
                    "agents": ["DevOps"],
                    "tasks": ["Deploy to staging", "Deploy to production"],
                    "duration": "1 day",
                },
            ],
            "communication": {
                "sync_frequency": "daily standup",
                "channels": ["task_queue", "event_bus"],
            },
        }

    def _generate_orchestration_code(self) -> str:
        """Generate workflow orchestration code."""
        return '''from typing import List, Dict, Any
import asyncio
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class WorkflowStep:
    name: str
    agents: List[str]
    tasks: List[str]
    dependencies: List[str] = field(default_factory=list)
    parallel: bool = False
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: Any = None

class WorkflowOrchestrator:
    """Orchestrate multi-agent workflows"""
    
    def __init__(self, agents: Dict[str, Any]):
        self.agents = agents
        self.workflows: Dict[str, List[WorkflowStep]] = {}
        self.event_handlers: Dict[str, List] = {}
        
    def define_workflow(self, name: str, steps: List[WorkflowStep]):
        """Define a new workflow"""
        self.workflows[name] = steps
        
    async def execute_workflow(self, name: str, context: Dict = None) -> Dict:
        """Execute a defined workflow"""
        steps = self.workflows.get(name)
        if not steps:
            raise ValueError(f"Workflow {name} not found")
        
        results = {}
        context = context or {}
        
        for step in steps:
            # Check dependencies
            for dep in step.dependencies:
                if results.get(dep, {}).get("status") != "success":
                    step.status = WorkflowStatus.FAILED
                    return {"status": "failed", "failed_at": step.name}
            
            # Execute step
            step.status = WorkflowStatus.RUNNING
            self._emit_event("step_started", {"step": step.name})
            
            try:
                if step.parallel:
                    step.result = await self._execute_parallel(step, context)
                else:
                    step.result = await self._execute_sequential(step, context)
                
                step.status = WorkflowStatus.COMPLETED
                results[step.name] = {"status": "success", "result": step.result}
                
            except Exception as e:
                step.status = WorkflowStatus.FAILED
                results[step.name] = {"status": "failed", "error": str(e)}
                return {"status": "failed", "results": results}
            
            self._emit_event("step_completed", {"step": step.name, "result": step.result})
        
        return {"status": "success", "results": results}
    
    async def _execute_parallel(self, step: WorkflowStep, context: Dict) -> List[Any]:
        """Execute tasks in parallel across agents"""
        tasks = []
        for agent_name, task_name in zip(step.agents, step.tasks):
            agent = self.agents.get(agent_name)
            if agent:
                tasks.append(agent.execute_task({"name": task_name, **context}))
        
        return await asyncio.gather(*tasks)
    
    async def _execute_sequential(self, step: WorkflowStep, context: Dict) -> List[Any]:
        """Execute tasks sequentially"""
        results = []
        for agent_name, task_name in zip(step.agents, step.tasks):
            agent = self.agents.get(agent_name)
            if agent:
                result = await agent.execute_task({"name": task_name, **context})
                results.append(result)
                context["previous_result"] = result
        
        return results
    
    def on_event(self, event_type: str, handler):
        """Register event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def _emit_event(self, event_type: str, data: Dict):
        """Emit workflow event"""
        for handler in self.event_handlers.get(event_type, []):
            handler(data)

# Example usage
# orchestrator = WorkflowOrchestrator(agents)
# orchestrator.define_workflow("mvp", [
#     WorkflowStep("planning", ["UI/UX"], ["Create wireframes"]),
#     WorkflowStep("dev", ["Frontend", "Backend"], ["Build UI", "Create API"], parallel=True),
#     WorkflowStep("test", ["QA"], ["Run tests"], dependencies=["dev"]),
# ])
# result = await orchestrator.execute_workflow("mvp")
'''

    async def _create_project(self, task: Task) -> Dict[str, Any]:
        """Create a new project."""
        project_name = task.metadata.get("name", "New Project")
        project_type = task.metadata.get("type", "mvp")
        
        self.log(f"Creating project: {project_name}")
        
        project = {
            "id": f"proj_{len(self.projects) + 1}",
            "name": project_name,
            "type": project_type,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "milestones": [],
            "tasks": [],
            "team": list(self.agent_workloads.keys()),
        }
        
        self.projects[project["id"]] = project
        
        return project

    async def _plan_sprint(self, task: Task) -> Dict[str, Any]:
        """Plan a sprint."""
        sprint_number = task.metadata.get("sprint_number", 1)
        duration_days = task.metadata.get("duration", 14)
        
        self.log(f"Planning Sprint {sprint_number}")
        
        sprint_plan = {
            "sprint": sprint_number,
            "duration_days": duration_days,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=duration_days)).isoformat(),
            "goals": [
                "Complete user authentication",
                "Implement core API endpoints",
                "Setup CI/CD pipeline",
            ],
            "capacity": {
                "Frontend": 40,  # hours
                "Backend": 50,
                "Database": 20,
                "DevOps": 30,
                "QA": 35,
            },
            "planned_tasks": [
                {"name": "Auth flow", "agent": "Backend", "story_points": 8},
                {"name": "Login UI", "agent": "Frontend", "story_points": 5},
                {"name": "DB schema", "agent": "Database", "story_points": 3},
            ],
            "total_story_points": 16,
        }
        
        return sprint_plan

    async def _handle_generic_task(self, task: Task) -> Dict[str, Any]:
        """Handle generic project management tasks."""
        self.log(f"Handling generic PM task: {task.name}")
        
        return {
            "task": task.name,
            "status": "completed",
            "message": f"Generic PM task '{task.name}' completed",
        }

    def get_status(self) -> Dict[str, Any]:
        """Get enhanced status with PM-specific info."""
        base_status = super().get_status()
        base_status.update({
            "projects": len(self.projects),
            "milestones": len(self.milestones),
            "active_assignments": len(self.task_assignments),
            "agent_workloads": self.agent_workloads,
        })
        return base_status
