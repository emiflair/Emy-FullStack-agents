"""
Feedback Loop System
Collects analytics and implements continuous improvement for the agent system
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
from enum import Enum
import threading
import json
import statistics
from collections import defaultdict


class MetricType(Enum):
    """Types of metrics collected"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    """A single metric data point"""
    name: str
    value: float
    metric_type: MetricType
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'value': self.value,
            'type': self.metric_type.value,
            'labels': self.labels,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class FeedbackEntry:
    """A feedback entry from system observation"""
    source: str  # agent_type, task_type, etc.
    feedback_type: str  # performance, error, success, etc.
    data: Dict[str, Any]
    impact_score: float = 0.0  # -1 to 1, negative is bad
    timestamp: datetime = field(default_factory=datetime.utcnow)
    processed: bool = False
    action_taken: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source': self.source,
            'feedback_type': self.feedback_type,
            'data': self.data,
            'impact_score': self.impact_score,
            'timestamp': self.timestamp.isoformat(),
            'processed': self.processed,
            'action_taken': self.action_taken,
        }


class AnalyticsCollector:
    """
    Collects and aggregates analytics from all agents
    """
    
    def __init__(self):
        self._metrics: Dict[str, List[Metric]] = defaultdict(list)
        self._aggregations: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        
        # Retention settings
        self._retention_period = timedelta(hours=24)
        self._aggregation_interval = timedelta(minutes=5)
    
    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        labels: Optional[Dict[str, str]] = None,
    ):
        """Record a metric value"""
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            labels=labels or {},
        )
        
        with self._lock:
            self._metrics[name].append(metric)
        
        # Trigger aggregation if needed
        self._maybe_aggregate(name)
    
    def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
    ):
        """Increment a counter metric"""
        self.record_metric(name, value, MetricType.COUNTER, labels)
    
    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ):
        """Set a gauge metric"""
        self.record_metric(name, value, MetricType.GAUGE, labels)
    
    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ):
        """Observe a value for histogram"""
        self.record_metric(name, value, MetricType.HISTOGRAM, labels)
    
    def _maybe_aggregate(self, name: str):
        """Check if aggregation is needed and run it"""
        last_aggregation = self._aggregations.get(name, {}).get('last_aggregation')
        
        if not last_aggregation or \
           datetime.utcnow() - last_aggregation > self._aggregation_interval:
            self._aggregate(name)
    
    def _aggregate(self, name: str):
        """Aggregate metrics for a given name"""
        with self._lock:
            metrics = self._metrics.get(name, [])
            
            if not metrics:
                return
            
            # Calculate aggregations
            values = [m.value for m in metrics]
            
            self._aggregations[name] = {
                'count': len(values),
                'sum': sum(values),
                'min': min(values),
                'max': max(values),
                'avg': statistics.mean(values),
                'stddev': statistics.stdev(values) if len(values) > 1 else 0,
                'p50': statistics.median(values),
                'p95': self._percentile(values, 95),
                'p99': self._percentile(values, 99),
                'last_aggregation': datetime.utcnow(),
            }
    
    def _percentile(self, values: List[float], p: int) -> float:
        """Calculate percentile"""
        sorted_values = sorted(values)
        index = (len(sorted_values) - 1) * p / 100
        lower = int(index)
        upper = lower + 1
        
        if upper >= len(sorted_values):
            return sorted_values[-1]
        
        weight = index - lower
        return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight
    
    def get_metrics(
        self,
        name: str,
        since: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Get raw metrics"""
        metrics = self._metrics.get(name, [])
        
        if since:
            metrics = [m for m in metrics if m.timestamp >= since]
        
        return [m.to_dict() for m in metrics]
    
    def get_aggregation(self, name: str) -> Dict[str, Any]:
        """Get aggregated metrics"""
        self._aggregate(name)  # Ensure fresh aggregation
        return self._aggregations.get(name, {})
    
    def get_all_aggregations(self) -> Dict[str, Dict[str, Any]]:
        """Get all aggregations"""
        for name in self._metrics.keys():
            self._aggregate(name)
        return dict(self._aggregations)
    
    def cleanup_old_metrics(self):
        """Remove metrics older than retention period"""
        cutoff = datetime.utcnow() - self._retention_period
        
        with self._lock:
            for name in self._metrics:
                self._metrics[name] = [
                    m for m in self._metrics[name]
                    if m.timestamp >= cutoff
                ]


class FeedbackLoop:
    """
    Feedback loop system for continuous improvement
    Analyzes feedback and triggers optimization actions
    """
    
    def __init__(self, analytics: AnalyticsCollector):
        self.analytics = analytics
        self._feedback_queue: List[FeedbackEntry] = []
        self._feedback_history: List[FeedbackEntry] = []
        self._rules: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        
        # Learning parameters
        self._learning_rate = 0.1
        self._adaptation_threshold = 0.5
        
        # Pattern detection
        self._patterns: Dict[str, Dict[str, Any]] = {}
        self._pattern_actions: Dict[str, Callable] = {}
        
        # Initialize default rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default feedback rules"""
        self._rules = [
            {
                'name': 'high_error_rate',
                'condition': lambda f: f.feedback_type == 'error' and f.impact_score < -0.5,
                'action': 'reduce_load',
                'cooldown': timedelta(minutes=5),
                'last_triggered': None,
            },
            {
                'name': 'slow_performance',
                'condition': lambda f: f.feedback_type == 'performance' and f.data.get('latency', 0) > 5,
                'action': 'scale_up',
                'cooldown': timedelta(minutes=2),
                'last_triggered': None,
            },
            {
                'name': 'consistent_success',
                'condition': lambda f: f.feedback_type == 'success' and f.impact_score > 0.8,
                'action': 'maintain_or_scale_down',
                'cooldown': timedelta(minutes=10),
                'last_triggered': None,
            },
            {
                'name': 'task_completion_failure',
                'condition': lambda f: f.feedback_type == 'task_failure',
                'action': 'retry_with_adjustment',
                'cooldown': timedelta(seconds=30),
                'last_triggered': None,
            },
        ]
    
    def submit_feedback(
        self,
        source: str,
        feedback_type: str,
        data: Dict[str, Any],
        impact_score: float = 0.0,
    ):
        """Submit feedback to the loop"""
        feedback = FeedbackEntry(
            source=source,
            feedback_type=feedback_type,
            data=data,
            impact_score=impact_score,
        )
        
        with self._lock:
            self._feedback_queue.append(feedback)
        
        # Record analytics
        self.analytics.increment_counter(
            f'feedback_{feedback_type}_count',
            labels={'source': source}
        )
        
        if impact_score != 0:
            self.analytics.observe_histogram(
                'feedback_impact_score',
                impact_score,
                labels={'source': source, 'type': feedback_type}
            )
    
    def process_feedback(self) -> List[Dict[str, Any]]:
        """Process pending feedback and return actions to take"""
        actions = []
        
        with self._lock:
            pending = list(self._feedback_queue)
            self._feedback_queue.clear()
        
        for feedback in pending:
            # Evaluate against rules
            for rule in self._rules:
                if self._should_trigger_rule(rule, feedback):
                    action = self._create_action(rule, feedback)
                    if action:
                        actions.append(action)
                        feedback.processed = True
                        feedback.action_taken = rule['action']
                        rule['last_triggered'] = datetime.utcnow()
            
            # Detect patterns
            self._update_patterns(feedback)
            
            # Archive feedback
            self._feedback_history.append(feedback)
        
        # Check for pattern-based actions
        pattern_actions = self._check_patterns()
        actions.extend(pattern_actions)
        
        return actions
    
    def _should_trigger_rule(self, rule: Dict, feedback: FeedbackEntry) -> bool:
        """Check if a rule should be triggered"""
        # Check cooldown
        if rule['last_triggered']:
            if datetime.utcnow() - rule['last_triggered'] < rule['cooldown']:
                return False
        
        # Check condition
        try:
            return rule['condition'](feedback)
        except Exception:
            return False
    
    def _create_action(
        self,
        rule: Dict,
        feedback: FeedbackEntry,
    ) -> Optional[Dict[str, Any]]:
        """Create an action from a rule and feedback"""
        action_type = rule['action']
        
        action = {
            'type': action_type,
            'rule': rule['name'],
            'source': feedback.source,
            'feedback_type': feedback.feedback_type,
            'timestamp': datetime.utcnow().isoformat(),
            'parameters': {},
        }
        
        if action_type == 'reduce_load':
            action['parameters'] = {
                'rate_limit_reduction': 0.5,
                'target': feedback.source,
            }
        
        elif action_type == 'scale_up':
            action['parameters'] = {
                'worker_increase': 1,
                'target': feedback.source,
            }
        
        elif action_type == 'maintain_or_scale_down':
            action['parameters'] = {
                'worker_decrease': 1,
                'target': feedback.source,
                'condition': 'if_utilization_below_50_percent',
            }
        
        elif action_type == 'retry_with_adjustment':
            action['parameters'] = {
                'retry': True,
                'priority_boost': 1,
                'task_data': feedback.data,
            }
        
        return action
    
    def _update_patterns(self, feedback: FeedbackEntry):
        """Update pattern detection with new feedback"""
        key = f"{feedback.source}:{feedback.feedback_type}"
        
        if key not in self._patterns:
            self._patterns[key] = {
                'count': 0,
                'recent_impacts': [],
                'first_seen': feedback.timestamp,
                'last_seen': feedback.timestamp,
            }
        
        pattern = self._patterns[key]
        pattern['count'] += 1
        pattern['recent_impacts'].append(feedback.impact_score)
        pattern['recent_impacts'] = pattern['recent_impacts'][-100:]  # Keep last 100
        pattern['last_seen'] = feedback.timestamp
    
    def _check_patterns(self) -> List[Dict[str, Any]]:
        """Check for patterns that require action"""
        actions = []
        
        for key, pattern in self._patterns.items():
            # Check for repeated negative pattern
            if len(pattern['recent_impacts']) >= 10:
                avg_impact = sum(pattern['recent_impacts'][-10:]) / 10
                
                if avg_impact < -0.3:
                    source, feedback_type = key.split(':')
                    actions.append({
                        'type': 'pattern_detected',
                        'pattern': 'repeated_negative_feedback',
                        'source': source,
                        'feedback_type': feedback_type,
                        'avg_impact': avg_impact,
                        'count': pattern['count'],
                        'parameters': {
                            'investigation_required': True,
                            'suggested_action': 'review_agent_implementation',
                        },
                    })
        
        return actions
    
    def add_rule(
        self,
        name: str,
        condition: Callable[[FeedbackEntry], bool],
        action: str,
        cooldown: timedelta = timedelta(minutes=5),
    ):
        """Add a custom feedback rule"""
        self._rules.append({
            'name': name,
            'condition': condition,
            'action': action,
            'cooldown': cooldown,
            'last_triggered': None,
        })
    
    def register_pattern_action(self, pattern_name: str, action_func: Callable):
        """Register a custom action for a pattern"""
        self._pattern_actions[pattern_name] = action_func
    
    def get_feedback_summary(
        self,
        since: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get a summary of recent feedback"""
        feedback = self._feedback_history
        
        if since:
            feedback = [f for f in feedback if f.timestamp >= since]
        
        if not feedback:
            return {'message': 'No feedback data available'}
        
        # Group by type
        by_type: Dict[str, List[FeedbackEntry]] = defaultdict(list)
        for f in feedback:
            by_type[f.feedback_type].append(f)
        
        summary = {
            'total_feedback': len(feedback),
            'by_type': {},
            'avg_impact': sum(f.impact_score for f in feedback) / len(feedback),
            'positive_ratio': sum(1 for f in feedback if f.impact_score > 0) / len(feedback),
            'actions_taken': sum(1 for f in feedback if f.processed),
        }
        
        for feedback_type, entries in by_type.items():
            summary['by_type'][feedback_type] = {
                'count': len(entries),
                'avg_impact': sum(e.impact_score for e in entries) / len(entries),
            }
        
        return summary
    
    def get_patterns(self) -> Dict[str, Any]:
        """Get detected patterns"""
        result = {}
        
        for key, pattern in self._patterns.items():
            recent = pattern['recent_impacts'][-10:] if pattern['recent_impacts'] else []
            
            result[key] = {
                'total_count': pattern['count'],
                'avg_recent_impact': sum(recent) / len(recent) if recent else 0,
                'first_seen': pattern['first_seen'].isoformat(),
                'last_seen': pattern['last_seen'].isoformat(),
                'trend': self._calculate_trend(pattern['recent_impacts']),
            }
        
        return result
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend from values"""
        if len(values) < 5:
            return 'insufficient_data'
        
        recent = values[-5:]
        older = values[-10:-5] if len(values) >= 10 else values[:5]
        
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)
        
        diff = recent_avg - older_avg
        
        if diff > 0.1:
            return 'improving'
        elif diff < -0.1:
            return 'degrading'
        return 'stable'
    
    def clear_history(self, older_than: Optional[timedelta] = None):
        """Clear feedback history"""
        if older_than:
            cutoff = datetime.utcnow() - older_than
            self._feedback_history = [
                f for f in self._feedback_history
                if f.timestamp >= cutoff
            ]
        else:
            self._feedback_history.clear()


# Integration with agents
def create_feedback_reporter(
    feedback_loop: FeedbackLoop,
    agent_type: str,
) -> Callable:
    """Create a feedback reporter function for an agent"""
    
    def report(feedback_type: str, data: Dict[str, Any], impact: float = 0.0):
        feedback_loop.submit_feedback(
            source=agent_type,
            feedback_type=feedback_type,
            data=data,
            impact_score=impact,
        )
    
    return report
