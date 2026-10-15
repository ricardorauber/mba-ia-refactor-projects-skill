"""Input validation shared by create and update use cases; every failure raises ValidationError (400)."""
import re
from datetime import datetime

from middlewares.errors import NotFoundError, ValidationError
from models.task import (DUE_DATE_FORMAT, MAX_PRIORITY, MAX_TITLE_LENGTH, MIN_PRIORITY, MIN_TITLE_LENGTH,
                         TAG_SEPARATOR, TASK_STATUSES)
from models.user import MIN_PASSWORD_LENGTH, USER_ROLES

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')
INVALID_DATA_MESSAGE = 'Dados inválidos'


def require_object(payload):
    if not isinstance(payload, dict):
        raise ValidationError(INVALID_DATA_MESSAGE)
    return payload


def require_payload(payload):
    if not payload:
        raise ValidationError(INVALID_DATA_MESSAGE)
    return require_object(payload)


def ensure_scalar(value, message=INVALID_DATA_MESSAGE):
    if isinstance(value, (dict, list)):
        raise ValidationError(message)
    return value


def validate_title(title):
    if not isinstance(title, str):
        raise ValidationError('Título inválido')
    if len(title) < MIN_TITLE_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > MAX_TITLE_LENGTH:
        raise ValidationError('Título muito longo')
    return title


def validate_status(status):
    if ensure_scalar(status, 'Status inválido') not in TASK_STATUSES:
        raise ValidationError('Status inválido')
    return status


def validate_priority(priority):
    if not isinstance(priority, (int, float)) or not MIN_PRIORITY <= priority <= MAX_PRIORITY:
        raise ValidationError(f'Prioridade deve ser entre {MIN_PRIORITY} e {MAX_PRIORITY}')
    return priority


def parse_due_date(value, message):
    if not isinstance(value, str):
        raise ValidationError(message)
    try:
        return datetime.strptime(value, DUE_DATE_FORMAT)
    except ValueError:
        raise ValidationError(message) from None


def normalize_tags(tags):
    if isinstance(tags, list):
        if not all(isinstance(tag, str) for tag in tags):
            raise ValidationError('Tags inválidas')
        return TAG_SEPARATOR.join(tags)
    return ensure_scalar(tags, 'Tags inválidas')


def find_reference(model, entity_id, not_found_message):
    """Returns the referenced row; a falsy id means 'no reference', as in the original API."""
    if not entity_id:
        return None
    entity = model.get_by_id(ensure_scalar(entity_id))
    if entity is None:
        raise NotFoundError(not_found_message)
    return entity


def validate_email(email):
    if not isinstance(email, str) or not EMAIL_PATTERN.match(email):
        raise ValidationError('Email inválido')
    return email


def validate_password(password, too_short_message):
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(too_short_message)
    return password


def validate_role(role):
    if ensure_scalar(role, 'Role inválido') not in USER_ROLES:
        raise ValidationError('Role inválido')
    return role


def validate_active(active):
    if active is not None and active not in (True, False):
        raise ValidationError('Campo active inválido')
    return active


def parse_optional_int(value, message):
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        raise ValidationError(message) from None
