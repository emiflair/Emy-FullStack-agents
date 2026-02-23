"""
Worker Manager
Manages Celery workers and worker pools for the agent system
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from datetime import datetime, timedelta
import threading
import subprocess
import os
import signal
import json
import uuid


class WorkerStatus(Enum):
    """Worker status states"""
    IDLE = "idle"
    BUSY = "busy"
    STARTING = "starting"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class WorkerInfo:
    """Information about a worker process"""
    worker_id: str
    queue: str
    status: WorkerStatus = WorkerStatus.STOPPED
    process_id: Optional[int] = None
    started_at: Optional[datetime] = None
    tasks_processed: int = 0
    tasks_failed: int = 0
    current_task: Optional[str] = None
    hostname: str = field(default_factory=lambda: os.uname().nodename)
    concurrency: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'worker_id': self.worker_id,
            'queue': self.queue,
            'status': self.status.value,
            'process_id': self.process_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'tasks_processed': self.tasks_processed,
            'tasks_failed': self.tasks_failed,
            'current_task': self.current_task,
            'hostname': self.hostname,
            'concurrency': self.concurrency,
        }


@dataclass
class WorkerPool:
    """Pool of workers for a specific queue"""
    queue: str
    min_workers: int = 1
    max_workers: int = 4
    scale_up_threshold: float = 0.8  # Queue utilization to trigger scale up
    scale_down_threshold: float = 0.2  # Queue utilization to trigger scale down
    workers: Dict[str, WorkerInfo] = field(default_factory=dict)
    
    @property
    def active_workers(self) -> int:
        return sum(1 for w in self.workers.values() 
                   if w.status in [WorkerStatus.IDLE, WorkerStatus.BUSY])
    
    @property
    def busy_workers(self) -> int:
        return sum(1 for w in self.workers.values() 
                   if w.status == WorkerStatus.BUSY)
    
    @property
    def utilization(self) -> float:
        if self.active_workers == 0:
            return 0.0
        return self.busy_workers / self.active_workers


class WorkerManager:
    """
    Manages Celery workers for the Emy-FullStack system
    Handles worker lifecycle, scaling, and monitoring
    """
    
    # Default pools for each agent type
    DEFAULT_POOLS = {
        'frontend': WorkerPool('frontend', min_workers=1, max_workers=3),
        'backend': WorkerPool('backend', min_workers=2, max_workers=5),
        'database': WorkerPool('database', min_workers=1, max_workers=3),
        'devops': WorkerPool('devops', min_workers=1, max_workers=2),
        'qa': WorkerPool('qa', min_workers=1, max_workers=4),
        'uiux': WorkerPool('uiux', min_workers=1, max_workers=2),
        'security': WorkerPool('security', min_workers=1, max_workers=2),
        'aiml': WorkerPool('aiml', min_workers=1, max_workers=3),
        'project_manager': WorkerPool('project_manager', min_workers=1, max_workers=2),
        'master_brain': WorkerPool('master_brain', min_workers=1, max_workers=1),
        'openclaw': WorkerPool('openclaw', min_workers=1, max_workers=3),
        'critical': WorkerPool('critical', min_workers=2, max_workers=6),
        'high': WorkerPool('high', min_workers=2, max_workers=4),
        'medium': WorkerPool('medium', min_workers=2, max_workers=4),
        'low': WorkerPool('low', min_workers=1, max_workers=2),
    }
    
    def __init__(self, celery_app_path: str = 'task_queue.celery_app:celery_app'):
        self.pools: Dict[str, WorkerPool] = dict(self.DEFAULT_POOLS)
        self.celery_app_path = celery_app_path
        self._processes: Dict[str, subprocess.Popen] = {}
        self._lock = threading.Lock()
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
    
    def start_worker(
        self,
        queue: str,
        concurrency: int = 1,
        worker_id: Optional[str] = None,
    ) -> Optional[WorkerInfo]:
        """Start a new Celery worker for a queue"""
        if queue not in self.pools:
            self.pools[queue] = WorkerPool(queue)
        
        pool = self.pools[queue]
        
        # Check if we've reached max workers
        if pool.active_workers >= pool.max_workers:
            return None
        
        worker_id = worker_id or f"{queue}-{uuid.uuid4().hex[:8]}"
        
        # Create worker info
        worker = WorkerInfo(
            worker_id=worker_id,
            queue=queue,
            status=WorkerStatus.STARTING,
            concurrency=concurrency,
        )
        
        # Build celery worker command
        cmd = [
            'celery',
            '-A', self.celery_app_path,
            'worker',
            '-Q', queue,
            '-n', f'{worker_id}@%h',
            '-c', str(concurrency),
            '--loglevel', 'INFO',
        ]
        
        try:
            # Start worker process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid,
            )
            
            worker.process_id = process.pid
            worker.started_at = datetime.utcnow()
            worker.status = WorkerStatus.IDLE
            
            with self._lock:
                self._processes[worker_id] = process
                pool.workers[worker_id] = worker
            
            return worker
            
        except Exception as e:
            worker.status = WorkerStatus.ERROR
            print(f"Failed to start worker {worker_id}: {e}")
            return None
    
    def stop_worker(self, worker_id: str, graceful: bool = True) -> bool:
        """Stop a worker"""
        with self._lock:
            if worker_id not in self._processes:
                return False
            
            process = self._processes[worker_id]
            
            # Find the worker and update status
            for pool in self.pools.values():
                if worker_id in pool.workers:
                    pool.workers[worker_id].status = WorkerStatus.STOPPING
                    break
            
            try:
                if graceful:
                    # Send SIGTERM for graceful shutdown
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    # Send SIGKILL for immediate shutdown
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                
                process.wait(timeout=30)
                
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            
            # Clean up
            del self._processes[worker_id]
            
            for pool in self.pools.values():
                if worker_id in pool.workers:
                    pool.workers[worker_id].status = WorkerStatus.STOPPED
                    break
            
            return True
    
    def stop_all_workers(self, graceful: bool = True):
        """Stop all workers"""
        worker_ids = list(self._processes.keys())
        for worker_id in worker_ids:
            self.stop_worker(worker_id, graceful)
    
    def scale_pool(self, queue: str, target_workers: int) -> List[WorkerInfo]:
        """Scale a worker pool to target number of workers"""
        if queue not in self.pools:
            return []
        
        pool = self.pools[queue]
        current = pool.active_workers
        
        # Constrain to min/max
        target = max(pool.min_workers, min(pool.max_workers, target_workers))
        
        result = []
        
        if target > current:
            # Scale up
            for _ in range(target - current):
                worker = self.start_worker(queue)
                if worker:
                    result.append(worker)
        
        elif target < current:
            # Scale down - stop idle workers first
            to_stop = current - target
            stopped = 0
            
            for worker_id, worker in list(pool.workers.items()):
                if stopped >= to_stop:
                    break
                if worker.status == WorkerStatus.IDLE:
                    if self.stop_worker(worker_id):
                        stopped += 1
        
        return result
    
    def auto_scale(self):
        """Automatically scale worker pools based on utilization"""
        for queue, pool in self.pools.items():
            utilization = pool.utilization
            
            if utilization >= pool.scale_up_threshold:
                # Scale up
                new_target = min(pool.active_workers + 1, pool.max_workers)
                self.scale_pool(queue, new_target)
            
            elif utilization <= pool.scale_down_threshold:
                # Scale down
                new_target = max(pool.active_workers - 1, pool.min_workers)
                self.scale_pool(queue, new_target)
    
    def start_monitoring(self, interval: float = 30.0):
        """Start background monitoring and auto-scaling"""
        if self._monitoring:
            return
        
        self._monitoring = True
        
        def monitor_loop():
            while self._monitoring:
                self._update_worker_stats()
                self.auto_scale()
                threading.Event().wait(interval)
        
        self._monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
    
    def _update_worker_stats(self):
        """Update worker statistics from Celery"""
        # In production, would query Celery inspect API
        # For now, check process status
        with self._lock:
            for worker_id, process in list(self._processes.items()):
                poll_result = process.poll()
                
                if poll_result is not None:
                    # Process has exited
                    for pool in self.pools.values():
                        if worker_id in pool.workers:
                            pool.workers[worker_id].status = WorkerStatus.STOPPED
                            pool.workers[worker_id].process_id = None
                            break
                    del self._processes[worker_id]
    
    def get_worker_stats(self, queue: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about workers"""
        stats = {
            'total_workers': 0,
            'active_workers': 0,
            'busy_workers': 0,
            'pools': {},
        }
        
        pools_to_check = {queue: self.pools[queue]} if queue and queue in self.pools else self.pools
        
        for q, pool in pools_to_check.items():
            pool_stats = {
                'min_workers': pool.min_workers,
                'max_workers': pool.max_workers,
                'active_workers': pool.active_workers,
                'busy_workers': pool.busy_workers,
                'utilization': pool.utilization,
                'workers': [w.to_dict() for w in pool.workers.values()],
            }
            stats['pools'][q] = pool_stats
            stats['total_workers'] += len(pool.workers)
            stats['active_workers'] += pool.active_workers
            stats['busy_workers'] += pool.busy_workers
        
        return stats
    
    def restart_worker(self, worker_id: str) -> Optional[WorkerInfo]:
        """Restart a worker"""
        # Get worker info before stopping
        worker_info = None
        queue = None
        concurrency = 1
        
        for q, pool in self.pools.items():
            if worker_id in pool.workers:
                worker_info = pool.workers[worker_id]
                queue = q
                concurrency = worker_info.concurrency
                break
        
        if not worker_info or not queue:
            return None
        
        # Stop and start
        self.stop_worker(worker_id)
        return self.start_worker(queue, concurrency, worker_id)
    
    def set_pool_config(
        self,
        queue: str,
        min_workers: Optional[int] = None,
        max_workers: Optional[int] = None,
        scale_up_threshold: Optional[float] = None,
        scale_down_threshold: Optional[float] = None,
    ):
        """Update pool configuration"""
        if queue not in self.pools:
            self.pools[queue] = WorkerPool(queue)
        
        pool = self.pools[queue]
        
        if min_workers is not None:
            pool.min_workers = min_workers
        if max_workers is not None:
            pool.max_workers = max_workers
        if scale_up_threshold is not None:
            pool.scale_up_threshold = scale_up_threshold
        if scale_down_threshold is not None:
            pool.scale_down_threshold = scale_down_threshold


class WorkerHealthChecker:
    """Monitors worker health and handles failures"""
    
    def __init__(self, worker_manager: WorkerManager):
        self.manager = worker_manager
        self.health_history: Dict[str, List[Dict[str, Any]]] = {}
        self.restart_counts: Dict[str, int] = {}
        self.max_restarts: int = 3
        self.restart_window: int = 300  # 5 minutes
    
    def check_health(self, worker_id: str) -> Dict[str, Any]:
        """Check health of a specific worker"""
        result = {
            'worker_id': worker_id,
            'healthy': True,
            'checks': [],
        }
        
        # Find worker
        worker = None
        for pool in self.manager.pools.values():
            if worker_id in pool.workers:
                worker = pool.workers[worker_id]
                break
        
        if not worker:
            result['healthy'] = False
            result['checks'].append({'check': 'exists', 'passed': False})
            return result
        
        # Check process is running
        if worker_id in self.manager._processes:
            process = self.manager._processes[worker_id]
            if process.poll() is not None:
                result['healthy'] = False
                result['checks'].append({'check': 'process_running', 'passed': False})
        else:
            result['checks'].append({'check': 'process_running', 'passed': True})
        
        # Check status
        if worker.status == WorkerStatus.ERROR:
            result['healthy'] = False
            result['checks'].append({'check': 'status', 'passed': False})
        else:
            result['checks'].append({'check': 'status', 'passed': True})
        
        # Record health check
        if worker_id not in self.health_history:
            self.health_history[worker_id] = []
        
        self.health_history[worker_id].append({
            'timestamp': datetime.utcnow().isoformat(),
            'healthy': result['healthy'],
        })
        
        # Keep only last 100 checks
        self.health_history[worker_id] = self.health_history[worker_id][-100:]
        
        return result
    
    def handle_unhealthy_worker(self, worker_id: str) -> bool:
        """Handle an unhealthy worker by restarting if possible"""
        # Check restart count
        if worker_id not in self.restart_counts:
            self.restart_counts[worker_id] = 0
        
        if self.restart_counts[worker_id] >= self.max_restarts:
            # Too many restarts, don't restart
            return False
        
        # Attempt restart
        new_worker = self.manager.restart_worker(worker_id)
        
        if new_worker:
            self.restart_counts[worker_id] += 1
            return True
        
        return False
    
    def run_health_checks(self) -> Dict[str, Any]:
        """Run health checks on all workers"""
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'healthy_count': 0,
            'unhealthy_count': 0,
            'workers': {},
        }
        
        for pool in self.manager.pools.values():
            for worker_id in pool.workers.keys():
                health = self.check_health(worker_id)
                results['workers'][worker_id] = health
                
                if health['healthy']:
                    results['healthy_count'] += 1
                else:
                    results['unhealthy_count'] += 1
                    self.handle_unhealthy_worker(worker_id)
        
        return results
