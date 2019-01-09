import sqlalchemy as sa
import sqlalchemy_utils as sau
from sqlalchemy.ext.declarative import declared_attr
from enum import Enum

class RepoVisibility(Enum):
    autocreated = 'autocreated'
    """Used for repositories that were created automatically on push"""
    public = 'public'
    private = 'private'
    unlisted = 'unlisted'

class BaseRepositoryMixin:
    @declared_attr
    def __tablename__(cls):
        return "repository"

    id = sa.Column(sa.Integer, primary_key=True)
    created = sa.Column(sa.DateTime, nullable=False)
    updated = sa.Column(sa.DateTime, nullable=False)
    name = sa.Column(sa.Unicode(256), nullable=False)
    description = sa.Column(sa.Unicode(1024))
    path = sa.Column(sa.Unicode(1024))
    visibility = sa.Column(
            sau.ChoiceType(RepoVisibility, impl=sa.String()),
            nullable=False,
            default=RepoVisibility.public)

    @declared_attr
    def owner_id(cls):
        return sa.Column(sa.Integer, sa.ForeignKey('user.id'), nullable=False)

    @declared_attr
    def owner(cls):
        return sa.orm.relationship('User', backref=sa.orm.backref('repos'))
