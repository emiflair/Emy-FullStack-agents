"""
System Optimizer
Optimization strategies for the Emy-FullStack system
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Tuple
from enum import Enum
from datetime import datetime, timedelta
import json
import math
from collections import defaultdict


class OptimizationStrategy(Enum):
    """Available optimization strategies"""
    LOAD_BALANCE = "load_balance"
    PRIORITY_BASED = "priority_based"
    DEADLINE_DRIVEN = "deadline_driven"
    COST_OPTIMIZED = "cost_optimized"
    THROUGHPUT_MAXIMIZED = "throughput_maximized"
    LATENCY_MINIMIZED = "latency_minimized"


@dataclass
class OptimizationResult:
    """Result of an optimization operation"""
    strategy: OptimizationStrategy
    success: bool
    changes_made: List[Dict[str, Any]]
    metrics_before: Dict[str, Any]
    metrics_after: Dict[str, Any]
    improvement: float  # Percentage improvement
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'strategy': self.strategy.value,
            'success': self.success,
            'changes_made': self.changes_made,
            'metrics_before': self.metrics_before,
            'metrics_after': self.metrics_after,
            'improvement': self.improvement,
            'timestamp': self.timestamp.isoformat(),
        }


class SystemOptimizer:
    """
    System-wide optimizer for the Emy-FullStack agent system
    Implements various optimization strategies
    """
    
    def __init__(self):
        self.current_strategy = OptimizationStrategy.LOAD_BALANCE
        self._optimization_history: List[OptimizationResult] = []
        self._metrics_cache: Dict[str, Any] = {}
        self._agent_capabilities: Dict[str, Dict[str, Any]] = {}
        self._resource_costs: Dict[str, float] = {}
        
        # Strategy weights for multi-objective optimization
        self._strategy_weights = {
            'throughput': 0.3,
            'latency': 0.3,
            'cost': 0.2,
            'reliability': 0.2,
        }
    
    def set_strategy(self, strategy: OptimizationStrategy):
        """Set the current optimization strategy"""
        self.current_strategy = strategy
    
    def optimize(
        self,
        system_state: Dict[str, Any],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> OptimizationResult:
        """Run optimization with current strategy"""
        metrics_before = self._collect_metrics(system_state)
        
        # Select optimization method based on strategy
        optimizers = {
            OptimizationStrategy.LOAD_BALANCE: self._optimize_load_balance,
            OptimizationStrategy.PRIORITY_BASED: self._optimize_priority_based,
            OptimizationStrategy.DEADLINE_DRIVEN: self._optimize_deadline_driven,
            OptimizationStrategy.COST_OPTIMIZED: self._optimize_cost,
            OptimizationStrategy.THROUGHPUT_MAXIMIZED: self._optimize_throughput,
            OptimizationStrategy.LATENCY_MINIMIZED: self._optimize_latency,
        }
        
        optimizer = optimizers.get(self.current_strategy, self._optimize_load_balance)
        changes = optimizer(system_state, constraints or {})
        
        # Apply changes and collect new metrics
        self._apply_changes(changes)
        metrics_after = self._collect_metrics(system_state)
        
        # Calculate improvement
        improvement = self._calculate_improvement(metrics_before, metrics_after)
        
        result = OptimizationResult(
            strategy=self.current_strategy,
            success=improvement >= 0,
            changes_made=changes,
            metrics_before=metrics_before,
            metrics_after=metrics_after,
            improvement=improvement,
        )
        
        self._optimization_history.append(result)
        return result
    
    def _collect_metrics(self, system_state: Dict) -> Dict[str, Any]:
        """Collect current system metrics"""
        return {
            'throughput': system_state.get('tasks_per_minute', 0),
            'avg_latency': system_state.get('avg_task_latency', 0),
            'queue_depth': system_state.get('total_queue_depth', 0),
            'worker_utilization': system_state.get('avg_worker_utilization', 0),
            'error_rate': system_state.get('error_rate', 0),
            'timestamp': datetime.utcnow().isoformat(),
        }
    
    def _apply_changes(self, changes: List[Dict[str, Any]]):
        """Apply optimization changes"""
        from task_queue import WorkerManager, PriorityTaskQueue
        
        worker_manager = WorkerManager()
        queue = PriorityTaskQueue()
        
        for change in changes:
            change_type = change.get('type')
            
            if change_type == 'scale_workers':
                worker_manager.scale_pool(
                    change['queue'],
                    change['target_workers'],
                )
            
            elif change_type == 'update_priority':
                queue.update_priority(
                    change['task_id'],
                    change['new_priority'],
                )
            
            elif change_type == 'redistribute_tasks':
                # Implementation for task redistribution
                pass
    
    def _calculate_improvement(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any],
    ) -> float:
        """Calculate improvement percentage"""
        improvements = []
        
        # Throughput (higher is better)
        if before.get('throughput', 0) > 0:
            throughput_change = (after.get('throughput', 0) - before['throughput']) / before['throughput']
            improvements.append(throughput_change * self._strategy_weights['throughput'])
        
        # Latency (lower is better)
        if before.get('avg_latency', 0) > 0:
            latency_change = (before['avg_latency'] - after.get('avg_latency', 0)) / before['avg_latency']
            improvements.append(latency_change * self._strategy_weights['latency'])
        
        # Error rate (lower is better)
        if before.get('error_rate', 0) > 0:
            error_change = (before['error_rate'] - after.get('error_rate', 0)) / before['error_rate']
            improvements.append(error_change * self._strategy_weights['reliability'])
        
        return sum(improvements) * 100 if improvements else 0.0
    
    # ========== Optimization Strategies ==========
    
    def _optimize_load_balance(
        self,
        state: Dict[str, Any],
        constraints: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Optimize for even load distribution across workers"""
        changes = []
        
        queue_loads = state.get('queue_loads', {})
        
        if not queue_loads:
            return changes
        
        avg_load = sum(queue_loads.values()) / len(queue_loads)
        
        for queue, load in queue_loads.items():
            if load > avg_load * 1.5:
                # Queue is overloaded, scale up
                current_workers = state.get('workers', {}).get(queue, 1)
                changes.append({
                    'type': 'scale_workers',
                    'queue': queue,
                    'target_workers': current_workers + 1,
                    'reason': f'Load {load} exceeds average {avg_load}',
                })
            
            elif load < avg_load * 0.3:
                # Queue is underutilized, scale down
                current_workers = state.get('workers', {}).get(queue, 1)
                if current_workers > 1:
                    changes.append({
                        'type': 'scale_workers',
                        'queue': queue,
                        'target_workers': current_workers - 1,
                        'reason': f'Load {load} below threshold',
                    })
        
        return changes
    
    def _optimize_priority_based(
        self,
        state: Dict[str, Any],
        constraints: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Optimize based on task priorities"""
        changes = []
        
        pending_tasks = state.get('pending_tasks', [])
        
        # Sort tasks by priority
        sorted_tasks = sorted(pending_tasks, key=lambda t: t.get('priority', 5), reverse=True)
        
        # Ensure high-priority queues have enough workers
        high_priority_count = sum(1 for t in sorted_tasks if t.get('priority', 5) >= 7)
        
        if high_priority_count > 10:
            current_critical_workers = state.get('workers', {}).get('critical', 2)
            changes.append({
                'type': 'scale_workers',
                'queue': 'critical',
                'target_workers': min(current_critical_workers + 2, 6),
                'reason': f'{high_priority_count} high-priority tasks pending',
            })
        
        return changes
    
    def _optimize_deadline_driven(
        self,
        state: Dict[str, Any],
        constraints: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Optimize to meet task deadlines"""
        changes = []
        now = datetime.utcnow()
        
        pending_tasks = state.get('pending_tasks', [])
        
        for task in pending_tasks:
            deadline_str = task.get('deadline')
            if not deadline_str:
                continue
            
            deadline = datetime.fromisoformat(deadline_str)
            time_remaining = (deadline - now).total_seconds()
            estimated_time = task.get('estimated_duration', 300)  # Default 5 min
            
            if time_remaining < estimated_time * 1.5:
                # At risk of missing deadline, boost priority
                changes.append({
                    'type': 'update_priority',
                    'task_id': task['task_id'],
                    'new_priority': 10,  # Critical
                    'reason': f'Deadline risk: {time_remaining}s remaining',
                })
        
        return changes
    
    def _optimize_cost(
        self,
        state: Dict[str, Any],
        constraints: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Optimize for minimum resource cost"""
        changes = []
        
        workers = state.get('workers', {})
        queue_loads = state.get('queue_loads', {})
        
        budget = constraints.get('budget', float('inf'))
        current_cost = sum(
            self._resource_costs.get(q, 1.0) * w 
            for q, w in workers.items()
        )
        
        if current_cost > budget:
            # Need to reduce costs
            # Find least utilized queues
            utilizations = []
            for queue, worker_count in workers.items():
                load = queue_loads.get(queue, 0)
                utilization = load / worker_count if worker_count > 0 else 0
                utilizations.append((queue, utilization, worker_count))
            
            # Sort by utilization (lowest first)
            utilizations.sort(key=lambda x: x[1])
            
            for queue, util, count in utilizations:
                if count > 1 and current_cost > budget:
                    changes.append({
                        'type': 'scale_workers',
                        'queue': queue,
                        'target_workers': count - 1,
                        'reason': f'Cost reduction: utilization {util:.2%}',
                    })
                    current_cost -= self._resource_costs.get(queue, 1.0)
        
        return changes
    
    def _optimize_throughput(
        self,
        state: Dict[str, Any],
        constraints: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Optimize for maximum throughput"""
        changes = []
        
        queue_loads = state.get('queue_loads', {})
        workers = state.get('workers', {})
        throughputs = state.get('throughputs', {})
        
        # Scale up queues with high throughput potential
        for queue, load in queue_loads.items():
            if load > 0:
                current_workers = workers.get(queue, 1)
                current_throughput = throughputs.get(queue, 0)
                
                # Estimate throughput increase
                estimated_new_throughput = current_throughput * (current_workers + 1) / current_workers
                
                if estimated_new_throughput > current_throughput * 1.2:
                    max_workers = constraints.get('max_workers', {}).get(queue, 10)
                    if current_workers < max_workers:
                        changes.append({
                            'type': 'scale_workers',
                            'queue': queue,
                            'target_workers': current_workers + 1,
                            'reason': f'Throughput optimization: estimated {estimated_new_throughput:.1f}/min',
                        })
        
        return changes
    
    def _optimize_latency(
        self,
        state: Dict[str, Any],
        constraints: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Optimize for minimum latency"""
        changes = []
        
        latencies = state.get('latencies', {})
        workers = state.get('workers', {})
        target_latency = constraints.get('target_latency', 1.0)  # seconds
        
        for queue, latency in latencies.items():
            if latency > target_latency:
                current_workers = workers.get(queue, 1)
                
                # Estimate workers needed
                workers_needed = math.ceil(current_workers * (latency / target_latency))
                max_workers = constraints.get('max_workers', {}).get(queue, 10)
                
                new_workers = min(workers_needed, max_workers)
                
                if new_workers > current_workers:
                    changes.append({
                        'type': 'scale_workers',
                        'queue': queue,
                        'target_workers': new_workers,
                        'reason': f'Latency reduction: {latency:.2f}s → {target_latency:.2f}s',
                    })
        
        return changes
    
    # ========== Analysis ==========
    
    def analyze_bottlenecks(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify system bottlenecks"""
        bottlenecks = []
        
        queue_loads = state.get('queue_loads', {})
        workers = state.get('workers', {})
        latencies = state.get('latencies', {})
        error_rates = state.get('error_rates', {})
        
        for queue in set(queue_loads.keys()) | set(workers.keys()):
            load = queue_loads.get(queue, 0)
            worker_count = workers.get(queue, 1)
            latency = latencies.get(queue, 0)
            error_rate = error_rates.get(queue, 0)
            
            utilization = load / worker_count if worker_count > 0 else 0
            
            if utilization > 0.9:
                bottlenecks.append({
                    'queue': queue,
                    'type': 'high_utilization',
                    'severity': 'high',
                    'value': utilization,
                    'recommendation': 'Scale up workers',
                })
            
            if latency > 5.0:  # 5 seconds
                bottlenecks.append({
                    'queue': queue,
                    'type': 'high_latency',
                    'severity': 'medium',
                    'value': latency,
                    'recommendation': 'Add more workers or optimize tasks',
                })
            
            if error_rate > 0.1:  # 10%
                bottlenecks.append({
                    'queue': queue,
                    'type': 'high_error_rate',
                    'severity': 'high',
                    'value': error_rate,
                    'recommendation': 'Investigate and fix errors',
                })
        
        return bottlenecks
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate an optimization report"""
        if not self._optimization_history:
            return {'message': 'No optimization history available'}
        
        recent = self._optimization_history[-10:]
        
        return {
            'total_optimizations': len(self._optimization_history),
            'recent_optimizations': [r.to_dict() for r in recent],
            'avg_improvement': sum(r.improvement for r in recent) / len(recent),
            'most_common_strategy': max(
                set(r.strategy for r in self._optimization_history),
                key=lambda s: sum(1 for r in self._optimization_history if r.strategy == s)
            ).value,
            'total_changes_made': sum(len(r.changes_made) for r in self._optimization_history),
        }
    
    def set_strategy_weights(self, weights: Dict[str, float]):
        """Set weights for multi-objective optimization"""
        total = sum(weights.values())
        self._strategy_weights = {k: v/total for k, v in weights.items()}
    
    def set_resource_costs(self, costs: Dict[str, float]):
        """Set resource costs for cost optimization"""
        self._resource_costs = costs
