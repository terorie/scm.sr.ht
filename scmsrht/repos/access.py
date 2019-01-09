import sqlalchemy as sa
import sqlalchemy_utils as sau
from sqlalchemy.ext.declarative import declared_attr
from enum import Enum

class AccessMode(Enum):
    ro = 'ro'
    rw = 'rw'

class BaseAccessMixin:
    @declared_attr
    def __tablename__(cls):
        return "access"

    id = sa.Column(sa.Integer, primary_key=True)
    created = sa.Column(sa.DateTime, nullable=False)
    updated = sa.Column(sa.DateTime, nullable=False)
    mode = sa.Column(sau.ChoiceType(AccessMode, impl=sa.String()),
            nullable=False, default=AccessMode.ro)

    @declared_attr
    def user_id(cls):
        return sa.Column(sa.Integer, sa.ForeignKey('user.id'), nullable=False)

    @declared_attr
    def user(cls):
        return sa.orm.relationship('User', backref='access_grants')

    @declared_attr
    def repo_id(cls):
        return sa.Column(sa.Integer,
            sa.ForeignKey('repository.id', ondelete="CASCADE"),
            nullable=False)

    @declared_attr
    def repo(cls):
        return  sa.orm.relationship('Repository',
            backref=sa.orm.backref('access_grants', cascade="all, delete"))

    def __repr__(self):
        return '<Access {} {}->{}:{}>'.format(
                self.id, self.user_id, self.repo_id, self.mode)
