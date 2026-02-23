"""
Priority Task Queue System
Manages task prioritization and queue distribution
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from enum import IntEnum
from datetime import datetime, timedelta
import heapq
import threading
import uuid
import json
import redis


class TaskPriority(IntEnum):
    """Task priority levels"""
    CRITICAL = 10
    HIGH = 7
    MEDIUM = 5
    LOW = 3
    BACKGROUND = 1


@dataclass
class QueuedTask:
    """Task in the priority queue"""
    task_id: str
    task_name: str
    priority: TaskPriority
    payload: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other):
        """Compare tasks by priority (higher priority = earlier execution)"""
        if self.priority != other.priority:
            return self.priority > other.priority
        return self.created_at < other.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'task_name': self.task_name,
            'priority': self.priority.value,
            'payload': self.payload,
            'created_at': self.created_at.isoformat(),
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'dependencies': self.dependencies,
            'metadata': self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueuedTask':
        return cls(
            task_id=data['task_id'],
            task_name=data['task_name'],
            priority=TaskPriority(data['priority']),
            payload=data['payload'],
            created_at=datetime.fromisoformat(data['created_at']),
            scheduled_at=datetime.fromisoformat(data['scheduled_at']) if data.get('scheduled_at') else None,
            deadline=datetime.fromisoformat(data['deadline']) if data.get('deadline') else None,
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', 3),
            dependencies=data.get('dependencies', []),
            metadata=data.get('metadata', {}),
        )


class PriorityTaskQueue:
    """
    Priority-based task queue with Redis backing
    Supports task prioritization, scheduling, and dependency management
    """
    
    def __init__(self, redis_url: str = 'redis://localhost:6379/2'):
        self._local_queue: List[QueuedTask] = []
        self._lock = threading.Lock()
        self._redis_client: Optional[redis.Redis] = None
        self._redis_url = redis_url
        self._completed_tasks: Dict[str, datetime] = {}
        self._pending_dependencies: Dict[str, List[str]] = {}
        
        self._connect_redis()
    
    def _connect_redis(self):
        """Connect to Redis for persistent queue storage"""
        try:
            self._redis_client = redis.from_url(self._redis_url)
            self._redis_client.ping()
        except Exception as e:
            print(f"Warning: Redis connection failed: {e}. Using local queue only.")
            self._redis_client = None
    
    def enqueue(
        self,
        task_name: str,
        payload: Dict[str, Any],
        priority: TaskPriority = TaskPriority.MEDIUM,
        scheduled_at: Optional[datetime] = None,
        deadline: Optional[datetime] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add a task to the priority queue"""
        task_id = str(uuid.uuid4())
        
        task = QueuedTask(
            task_id=task_id,
            task_name=task_name,
            priority=priority,
            payload=payload,
            scheduled_at=scheduled_at,
            deadline=deadline,
            dependencies=dependencies or [],
            metadata=metadata or {},
        )
        
        # Check if task has unmet dependencies
        if task.dependencies:
            unmet = [dep for dep in task.dependencies if dep not in self._completed_tasks]
            if unmet:
                self._pending_dependencies[task_id] = unmet
                self._store_pending_task(task)
                return task_id
        
        self._add_to_queue(task)
        return task_id
    
    def _add_to_queue(self, task: QueuedTask):
        """Add task to both local and Redis queues"""
        with self._lock:
            heapq.heappush(self._local_queue, task)
        
        if self._redis_client:
            queue_name = self._get_queue_name(task.priority)
            self._redis_client.zadd(
                queue_name,
                {json.dumps(task.to_dict()): -task.priority.value}
            )
    
    def _store_pending_task(self, task: QueuedTask):
        """Store task waiting for dependencies"""
        if self._redis_client:
            self._redis_client.hset(
                'pending_tasks',
                task.task_id,
                json.dumps(task.to_dict())
            )
    
    def _get_queue_name(self, priority: TaskPriority) -> str:
        """Get Redis queue name for priority level"""
        priority_names = {
            TaskPriority.CRITICAL: 'queue:critical',
            TaskPriority.HIGH: 'queue:high',
            TaskPriority.MEDIUM: 'queue:medium',
            TaskPriority.LOW: 'queue:low',
            TaskPriority.BACKGROUND: 'queue:background',
        }
        return priority_names.get(priority, 'queue:medium')
    
    def dequeue(self, timeout: float = 0) -> Optional[QueuedTask]:
        """Get the highest priority task from the queue"""
        now = datetime.utcnow()
        
        with self._lock:
            # Filter out tasks not yet scheduled
            ready_tasks = [
                t for t in self._local_queue
                if not t.scheduled_at or t.scheduled_at <= now
            ]
            
            if not ready_tasks:
                return None
            
            # Get highest priority task
            task = heapq.heappop(self._local_queue)
            
            # Skip if scheduled for later
            if task.scheduled_at and task.scheduled_at > now:
                heapq.heappush(self._local_queue, task)
                return None
            
            # Remove from Redis
            if self._redis_client:
                queue_name = self._get_queue_name(task.priority)
                self._redis_client.zrem(queue_name, json.dumps(task.to_dict()))
            
            return task
    
    def dequeue_batch(self, batch_size: int = 10) -> List[QueuedTask]:
        """Get multiple tasks from the queue"""
        tasks = []
        for _ in range(batch_size):
            task = self.dequeue()
            if task:
                tasks.append(task)
            else:
                break
        return tasks
    
    def mark_completed(self, task_id: str):
        """Mark a task as completed and check pending dependencies"""
        self._completed_tasks[task_id] = datetime.utcnow()
        
        # Update pending tasks
        tasks_to_enqueue = []
        for pending_id, deps in list(self._pending_dependencies.items()):
            if task_id in deps:
                deps.remove(task_id)
                if not deps:
                    # All dependencies met, move to queue
                    del self._pending_dependencies[pending_id]
                    task_data = self._get_pending_task(pending_id)
                    if task_data:
                        tasks_to_enqueue.append(task_data)
        
        for task in tasks_to_enqueue:
            self._add_to_queue(task)
    
    def _get_pending_task(self, task_id: str) -> Optional[QueuedTask]:
        """Retrieve a pending task from storage"""
        if self._redis_client:
            data = self._redis_client.hget('pending_tasks', task_id)
            if data:
                self._redis_client.hdel('pending_tasks', task_id)
                return QueuedTask.from_dict(json.loads(data))
        return None
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get statistics about the queue"""
        stats = {
            'local_queue_size': len(self._local_queue),
            'pending_tasks': len(self._pending_dependencies),
            'completed_tasks': len(self._completed_tasks),
            'priority_breakdown': {},
        }
        
        for task in self._local_queue:
            priority_name = task.priority.name
            stats['priority_breakdown'][priority_name] = \
                stats['priority_breakdown'].get(priority_name, 0) + 1
        
        if self._redis_client:
            for priority in TaskPriority:
                queue_name = self._get_queue_name(priority)
                stats['priority_breakdown'][f'redis_{priority.name}'] = \
                    self._redis_client.zcard(queue_name)
        
        return stats
    
    def requeue_task(self, task: QueuedTask, delay: int = 60):
        """Requeue a failed task with delay"""
        task.retry_count += 1
        if task.retry_count <= task.max_retries:
            task.scheduled_at = datetime.utcnow() + timedelta(seconds=delay)
            self._add_to_queue(task)
            return True
        return False
    
    def clear_queue(self, priority: Optional[TaskPriority] = None):
        """Clear tasks from the queue"""
        with self._lock:
            if priority:
                self._local_queue = [t for t in self._local_queue if t.priority != priority]
                heapq.heapify(self._local_queue)
                
                if self._redis_client:
                    queue_name = self._get_queue_name(priority)
                    self._redis_client.delete(queue_name)
            else:
                self._local_queue = []
                if self._redis_client:
                    for p in TaskPriority:
                        self._redis_client.delete(self._get_queue_name(p))
    
    def peek(self) -> Optional[QueuedTask]:
        """Peek at the highest priority task without removing it"""
        with self._lock:
            if self._local_queue:
                return self._local_queue[0]
        return None
    
    def get_task_position(self, task_id: str) -> Optional[int]:
        """Get the position of a task in the queue"""
        with self._lock:
            sorted_queue = sorted(self._local_queue)
            for i, task in enumerate(sorted_queue):
                if task.task_id == task_id:
                    return i
        return None
    
    def update_priority(self, task_id: str, new_priority: TaskPriority) -> bool:
        """Update the priority of a queued task"""
        with self._lock:
            for task in self._local_queue:
                if task.task_id == task_id:
                    # Remove and re-add with new priority
                    old_task_dict = task.to_dict()
                    self._local_queue.remove(task)
                    task.priority = new_priority
                    heapq.heappush(self._local_queue, task)
                    
                    if self._redis_client:
                        old_queue = self._get_queue_name(TaskPriority(old_task_dict['priority']))
                        new_queue = self._get_queue_name(new_priority)
                        self._redis_client.zrem(old_queue, json.dumps(old_task_dict))
                        self._redis_client.zadd(
                            new_queue,
                            {json.dumps(task.to_dict()): -new_priority.value}
                        )
                    return True
        return False


class TaskScheduler:
    """Schedules tasks for future execution"""
    
    def __init__(self, queue: PriorityTaskQueue):
        self.queue = queue
        self._scheduled_jobs: Dict[str, Dict[str, Any]] = {}
    
    def schedule_once(
        self,
        task_name: str,
        payload: Dict[str, Any],
        run_at: datetime,
        priority: TaskPriority = TaskPriority.MEDIUM,
    ) -> str:
        """Schedule a task for one-time execution"""
        return self.queue.enqueue(
            task_name=task_name,
            payload=payload,
            priority=priority,
            scheduled_at=run_at,
        )
    
    def schedule_recurring(
        self,
        task_name: str,
        payload: Dict[str, Any],
        interval: timedelta,
        priority: TaskPriority = TaskPriority.MEDIUM,
        start_at: Optional[datetime] = None,
    ) -> str:
        """Schedule a recurring task"""
        job_id = str(uuid.uuid4())
        
        self._scheduled_jobs[job_id] = {
            'task_name': task_name,
            'payload': payload,
            'interval': interval.total_seconds(),
            'priority': priority,
            'next_run': start_at or datetime.utcnow(),
        }
        
        # Schedule first execution
        self.queue.enqueue(
            task_name=task_name,
            payload={**payload, '_job_id': job_id, '_recurring': True},
            priority=priority,
            scheduled_at=start_at,
        )
        
        return job_id
    
    def cancel_recurring(self, job_id: str) -> bool:
        """Cancel a recurring job"""
        if job_id in self._scheduled_jobs:
            del self._scheduled_jobs[job_id]
            return True
        return False
    
    def handle_recurring_completion(self, job_id: str):
        """Schedule next execution of recurring job"""
        if job_id in self._scheduled_jobs:
            job = self._scheduled_jobs[job_id]
            next_run = datetime.utcnow() + timedelta(seconds=job['interval'])
            job['next_run'] = next_run
            
            self.queue.enqueue(
                task_name=job['task_name'],
                payload={**job['payload'], '_job_id': job_id, '_recurring': True},
                priority=job['priority'],
                scheduled_at=next_run,
            )
