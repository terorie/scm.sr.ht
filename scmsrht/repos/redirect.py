import sqlalchemy as sa
import sqlalchemy_utils as sau
from sqlalchemy.ext.declarative import declared_attr
from enum import Enum

class BaseRedirectMixin:
    @declared_attr
    def __tablename__(cls):
        return "redirect"

    id = sa.Column(sa.Integer, primary_key=True)
    created = sa.Column(sa.DateTime, nullable=False)
    name = sa.Column(sa.Unicode(256), nullable=False)
    path = sa.Column(sa.Unicode(1024))

    @declared_attr
    def owner_id(cls):
        return sa.Column(sa.Integer, sa.ForeignKey('user.id'), nullable=False)

    @declared_attr
    def owner(cls):
        return sa.orm.relationship('User')

    @declared_attr
    def new_repo_id(cls):
        return sa.Column(
            sa.Integer,
            sa.ForeignKey('repository.id', ondelete="CASCADE"),
            nullable=False)

    @declared_attr
    def new_repo(cls):
        return sa.orm.relationship('Repository')
