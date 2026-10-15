import hashlib
import hmac

from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from models.base import PersistenceMixin, utc_now
from models.task import Task

ROLE_USER = 'user'
ROLE_ADMIN = 'admin'
ROLE_MANAGER = 'manager'
USER_ROLES = (ROLE_USER, ROLE_ADMIN, ROLE_MANAGER)
MIN_PASSWORD_LENGTH = 4
HASH_PREFIXES = ('scrypt:', 'pbkdf2:')


class User(PersistenceMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=ROLE_USER)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        # Never expose the password hash
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        if self.password.startswith(HASH_PREFIXES):
            return check_password_hash(self.password, raw_password)
        legacy_hash = hashlib.md5(raw_password.encode()).hexdigest()  # legacy rows only, upgraded on success
        if hmac.compare_digest(self.password, legacy_hash):
            self.set_password(raw_password)
            return True
        return False

    def delete_with_tasks(self):
        """Deletes the user and every task assigned to it in one transaction."""
        for task in Task.by_user(self.id):
            db.session.delete(task)
        self.delete()

    @classmethod
    def find_by_email(cls, email):
        return db.session.scalars(db.select(cls).filter_by(email=email)).first()

    @classmethod
    def task_counts(cls):
        """Returns {user_id: number of tasks} in a single GROUP BY query."""
        return Task.count_by(Task.user_id)
