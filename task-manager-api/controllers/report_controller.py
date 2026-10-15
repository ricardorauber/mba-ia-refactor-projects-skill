from collections import Counter
from datetime import timedelta

from controllers.user_controller import get_user_or_404
from models.base import utc_now
from models.category import Category
from models.task import STATUS_DONE, TASK_STATUSES, Task, completion_rate
from models.user import User

RECENT_ACTIVITY_DAYS = 7
HIGH_PRIORITY_MAX = 2  # priorities 1 and 2 count as high priority
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}


def summary_report():
    now = utc_now()
    tasks = Task.all()
    by_status = Task.count_by(Task.status)
    by_priority = Task.count_by(Task.priority)
    recent_since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
    overdue_tasks = [task for task in tasks if task.is_overdue(now)]

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': len(tasks),
            'total_users': User.count(),
            'total_categories': Category.count(),
        },
        'tasks_by_status': _status_counts(by_status),
        'tasks_by_priority': {label: by_priority.get(priority, 0) for priority, label in PRIORITY_LABELS.items()},
        'overdue': {
            'count': len(overdue_tasks),
            'tasks': [
                {'id': task.id, 'title': task.title, 'due_date': str(task.due_date),
                 'days_overdue': task.days_overdue(now)}
                for task in overdue_tasks
            ],
        },
        'recent_activity': {
            'tasks_created_last_7_days': Task.count_created_since(recent_since),
            'tasks_completed_last_7_days': Task.count_done_since(recent_since),
        },
        'user_productivity': _user_productivity(tasks),
    }


def user_report(user_id):
    user = get_user_or_404(user_id)
    tasks = Task.by_user(user_id)
    now = utc_now()
    by_status = Counter(task.status for task in tasks)
    done = by_status[STATUS_DONE]

    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': len(tasks),
            **_status_counts(by_status),
            'overdue': sum(1 for task in tasks if task.is_overdue(now)),
            'high_priority': sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_MAX),
            'completion_rate': completion_rate(done, len(tasks)),
        },
    }


def _status_counts(by_status):
    return {status: by_status.get(status, 0) for status in TASK_STATUSES}


def _user_productivity(tasks):
    totals = Counter(task.user_id for task in tasks)
    completed = Counter(task.user_id for task in tasks if task.status == STATUS_DONE)
    return [
        {
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': totals[user.id],
            'completed_tasks': completed[user.id],
            'completion_rate': completion_rate(completed[user.id], totals[user.id]),
        }
        for user in User.all()
    ]
