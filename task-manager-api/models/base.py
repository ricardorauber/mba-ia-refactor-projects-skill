from datetime import datetime, timezone

from database import db


def utc_now():
    # Naive UTC keeps the stored format of existing rows
    return datetime.now(timezone.utc).replace(tzinfo=None)


def format_datetime(value):
    return str(value) if value else None


class PersistenceMixin:
    """Data access shared by every model; each call is one transaction."""

    @classmethod
    def get_by_id(cls, entity_id):
        return db.session.get(cls, entity_id)

    @classmethod
    def all(cls):
        return db.session.scalars(db.select(cls)).all()

    @classmethod
    def count(cls):
        return db.session.scalar(db.select(db.func.count()).select_from(cls))

    def save(self):
        db.session.add(self)
        self.commit()
        return self

    def delete(self):
        db.session.delete(self)
        self.commit()

    @staticmethod
    def commit():
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
