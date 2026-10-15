from database import db
from models.base import PersistenceMixin, format_datetime, utc_now

STATUS_PENDING = 'pending'
STATUS_IN_PROGRESS = 'in_progress'
STATUS_DONE = 'done'
STATUS_CANCELLED = 'cancelled'
TASK_STATUSES = (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)
CLOSED_STATUSES = (STATUS_DONE, STATUS_CANCELLED)

MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
DUE_DATE_FORMAT = '%Y-%m-%d'
TAG_SEPARATOR = ','


def completion_rate(done, total):
    return round((done / total) * 100, 2) if total > 0 else 0


class Task(PersistenceMixin, db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=STATUS_PENDING)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': format_datetime(self.due_date),
            'tags': self.tags.split(TAG_SEPARATOR) if self.tags else [],
        }

    def to_detail_dict(self):
        return {**self.to_dict(), 'overdue': self.is_overdue()}

    def to_list_dict(self):
        return {
            **self.to_detail_dict(),
            'user_name': self.user.name if self.user else None,
            'category_name': self.category.name if self.category else None,
        }

    def to_user_task_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': str(self.created_at),
            'due_date': format_datetime(self.due_date),
            'overdue': self.is_overdue(),
        }

    def is_overdue(self, now=None):
        now = now or utc_now()
        return bool(self.due_date) and self.due_date < now and self.status not in CLOSED_STATUSES

    def days_overdue(self, now=None):
        return ((now or utc_now()) - self.due_date).days

    @classmethod
    def all_with_relations(cls):
        query = db.select(cls).options(db.joinedload(cls.user), db.joinedload(cls.category))
        return db.session.scalars(query).unique().all()

    @classmethod
    def by_user(cls, user_id):
        return db.session.scalars(db.select(cls).filter_by(user_id=user_id)).all()

    @classmethod
    def search(cls, text=None, status=None, priority=None, user_id=None):
        query = db.select(cls)
        if text:
            pattern = f'%{text}%'
            query = query.where(db.or_(cls.title.like(pattern), cls.description.like(pattern)))
        if status:
            query = query.where(cls.status == status)
        if priority is not None:
            query = query.where(cls.priority == priority)
        if user_id is not None:
            query = query.where(cls.user_id == user_id)
        return db.session.scalars(query).all()

    @classmethod
    def count_by(cls, column):
        """Returns {value: count} for one column, in a single GROUP BY query."""
        rows = db.session.execute(db.select(column, db.func.count(cls.id)).group_by(column))
        return dict(rows.all())

    @classmethod
    def count_created_since(cls, moment):
        return db.session.scalar(db.select(db.func.count(cls.id)).where(cls.created_at >= moment))

    @classmethod
    def count_done_since(cls, moment):
        query = db.select(db.func.count(cls.id)).where(cls.status == STATUS_DONE, cls.updated_at >= moment)
        return db.session.scalar(query)
