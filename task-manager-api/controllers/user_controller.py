import logging

from controllers import validators
from middlewares.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from models.task import Task
from models.user import ROLE_USER, User

USER_NOT_FOUND = 'Usuário não encontrado'
EMAIL_TAKEN = 'Email já cadastrado'
INVALID_CREDENTIALS = 'Credenciais inválidas'
# The original API never verifies this token; kept as-is to preserve the contract.
LOGIN_TOKEN_PREFIX = 'fake-jwt-token-'

logger = logging.getLogger(__name__)


def get_user_or_404(user_id):
    user = User.get_by_id(user_id)
    if user is None:
        raise NotFoundError(USER_NOT_FOUND)
    return user


def list_users():
    task_counts = User.task_counts()
    return [{**user.to_dict(), 'task_count': task_counts.get(user.id, 0)} for user in User.all()]


def get_user(user_id):
    user = get_user_or_404(user_id)
    return {**user.to_dict(), 'tasks': [task.to_dict() for task in Task.by_user(user_id)]}


def create_user(payload):
    data = validators.require_payload(payload)
    name = validators.ensure_scalar(data.get('name'))
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', ROLE_USER)

    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')
    validators.validate_email(email)
    validators.validate_password(password, 'Senha deve ter no mínimo 4 caracteres')
    if User.find_by_email(email):
        raise ConflictError(EMAIL_TAKEN)
    validators.validate_role(role)

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    user.save()
    logger.info('User created: id=%s', user.id)
    return user.to_dict()


def update_user(user_id, payload):
    user = get_user_or_404(user_id)
    data = validators.require_payload(payload)

    if 'name' in data:
        if data['name'] is None:
            raise ValidationError('Nome é obrigatório')
        user.name = validators.ensure_scalar(data['name'])
    if 'email' in data:
        email = validators.validate_email(data['email'])
        existing = User.find_by_email(email)
        if existing and existing.id != user_id:
            raise ConflictError(EMAIL_TAKEN)
        user.email = email
    if 'password' in data:
        user.set_password(validators.validate_password(data['password'], 'Senha muito curta'))
    if 'role' in data:
        user.role = validators.validate_role(data['role'])
    if 'active' in data:
        user.active = validators.validate_active(data['active'])

    user.save()
    return user.to_dict()


def delete_user(user_id):
    get_user_or_404(user_id).delete_with_tasks()
    logger.info('User deleted: id=%s', user_id)
    return {'message': 'Usuário deletado com sucesso'}


def list_user_tasks(user_id):
    get_user_or_404(user_id)
    return [task.to_user_task_dict() for task in Task.by_user(user_id)]


def login(payload):
    data = validators.require_payload(payload)
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')

    user = User.find_by_email(validators.ensure_scalar(email))
    if not user:
        raise UnauthorizedError(INVALID_CREDENTIALS)
    if not isinstance(password, str):
        raise ValidationError(validators.INVALID_DATA_MESSAGE)
    if not user.check_password(password):
        raise UnauthorizedError(INVALID_CREDENTIALS)
    user.save()  # persists the upgraded hash of a legacy MD5 row
    if not user.active:
        raise ForbiddenError('Usuário inativo')

    return {
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': LOGIN_TOKEN_PREFIX + str(user.id),
    }
