from controllers import validators
from middlewares.errors import NotFoundError, ValidationError
from models.category import DEFAULT_COLOR, Category
from models.task import Task

CATEGORY_NOT_FOUND = 'Categoria não encontrada'
EDITABLE_FIELDS = ('name', 'description', 'color')


def get_category_or_404(category_id):
    category = Category.get_by_id(category_id)
    if category is None:
        raise NotFoundError(CATEGORY_NOT_FOUND)
    return category


def list_categories():
    task_counts = Task.count_by(Task.category_id)
    return [{**category.to_dict(), 'task_count': task_counts.get(category.id, 0)} for category in Category.all()]


def create_category(payload):
    data = validators.require_payload(payload)
    name = validators.ensure_scalar(data.get('name'))
    if not name:
        raise ValidationError('Nome é obrigatório')

    category = Category(
        name=name,
        description=validators.ensure_scalar(data.get('description', '')),
        color=validators.ensure_scalar(data.get('color', DEFAULT_COLOR)),
    )
    return category.save().to_dict()


def update_category(category_id, payload):
    category = get_category_or_404(category_id)
    data = validators.require_object(payload)
    for field in EDITABLE_FIELDS:
        if field in data:
            setattr(category, field, validators.ensure_scalar(data[field]))
    return category.save().to_dict()


def delete_category(category_id):
    # SQLAlchemy sets category_id to NULL on the tasks of the deleted category in the same transaction
    get_category_or_404(category_id).delete()
    return {'message': 'Categoria deletada'}
