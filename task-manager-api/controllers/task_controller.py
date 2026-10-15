import logging

from controllers import validators
from middlewares.errors import NotFoundError, ValidationError
from models.base import utc_now
from models.category import Category
from models.task import (DEFAULT_PRIORITY, STATUS_CANCELLED, STATUS_DONE, STATUS_IN_PROGRESS, STATUS_PENDING, Task,
                         completion_rate)
from models.user import User

TASK_NOT_FOUND = 'Task não encontrada'
USER_NOT_FOUND = 'Usuário não encontrado'
CATEGORY_NOT_FOUND = 'Categoria não encontrada'

logger = logging.getLogger(__name__)


def get_task_or_404(task_id):
    task = Task.get_by_id(task_id)
    if task is None:
        raise NotFoundError(TASK_NOT_FOUND)
    return task


def list_tasks():
    return [task.to_list_dict() for task in Task.all_with_relations()]


def get_task(task_id):
    return get_task_or_404(task_id).to_detail_dict()


def create_task(payload):
    data = validators.require_payload(payload)
    title = data.get('title')
    if not title:
        raise ValidationError('Título é obrigatório')

    task = Task()
    task.title = validators.validate_title(title)
    task.description = validators.ensure_scalar(data.get('description', ''))
    task.status = validators.validate_status(data.get('status', STATUS_PENDING))
    task.priority = validators.validate_priority(data.get('priority', DEFAULT_PRIORITY))
    validators.find_reference(User, data.get('user_id'), USER_NOT_FOUND)
    validators.find_reference(Category, data.get('category_id'), CATEGORY_NOT_FOUND)
    task.user_id = data.get('user_id')
    task.category_id = data.get('category_id')

    if data.get('due_date'):
        task.due_date = validators.parse_due_date(data['due_date'], 'Formato de data inválido. Use YYYY-MM-DD')
    if data.get('tags'):
        task.tags = validators.normalize_tags(data['tags'])

    task.save()
    logger.info('Task created: id=%s', task.id)
    return task.to_dict()


def update_task(task_id, payload):
    task = get_task_or_404(task_id)
    data = validators.require_payload(payload)

    if 'title' in data:
        task.title = validators.validate_title(data['title'])
    if 'description' in data:
        task.description = validators.ensure_scalar(data['description'])
    if 'status' in data:
        task.status = validators.validate_status(data['status'])
    if 'priority' in data:
        task.priority = validators.validate_priority(data['priority'])
    if 'user_id' in data:
        validators.find_reference(User, data['user_id'], USER_NOT_FOUND)
        task.user_id = data['user_id']
    if 'category_id' in data:
        validators.find_reference(Category, data['category_id'], CATEGORY_NOT_FOUND)
        task.category_id = data['category_id']
    if 'due_date' in data:
        due_date = data['due_date']
        task.due_date = validators.parse_due_date(due_date, 'Formato de data inválido') if due_date else None
    if 'tags' in data:
        task.tags = validators.normalize_tags(data['tags'])

    task.updated_at = utc_now()
    task.save()
    logger.info('Task updated: id=%s', task.id)
    return task.to_dict()


def delete_task(task_id):
    get_task_or_404(task_id).delete()
    logger.info('Task deleted: id=%s', task_id)
    return {'message': 'Task deletada com sucesso'}


def search_tasks(args):
    tasks = Task.search(
        text=args.get('q', ''),
        status=args.get('status', ''),
        priority=validators.parse_optional_int(args.get('priority', ''), 'Prioridade inválida'),
        user_id=validators.parse_optional_int(args.get('user_id', ''), 'Usuário inválido'),
    )
    return [task.to_dict() for task in tasks]


def task_stats():
    by_status = Task.count_by(Task.status)
    total = sum(by_status.values())
    done = by_status.get(STATUS_DONE, 0)
    now = utc_now()
    return {
        'total': total,
        'pending': by_status.get(STATUS_PENDING, 0),
        'in_progress': by_status.get(STATUS_IN_PROGRESS, 0),
        'done': done,
        'cancelled': by_status.get(STATUS_CANCELLED, 0),
        'overdue': sum(1 for task in Task.all() if task.is_overdue(now)),
        'completion_rate': completion_rate(done, total),
    }
