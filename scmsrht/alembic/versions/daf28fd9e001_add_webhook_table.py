"""Add webhook table

Revision ID: daf28fd9e001
Revises: bfcdce82e0fc
Create Date: 2017-09-19 20:53:10.516308

"""

# revision identifiers, used by Alembic.
revision = 'daf28fd9e001'
down_revision = 'bfcdce82e0fc'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('webhook',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('created', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('updated', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('description', sa.VARCHAR(length=1024), autoincrement=False, nullable=True),
    sa.Column('oauth_token_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('repo_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('url', sa.VARCHAR(length=2048), autoincrement=False, nullable=False),
    sa.Column('validate_ssl', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['oauth_token_id'], ['oauthtoken.id'], name='webhook_oauth_token_id_fkey'),
    sa.ForeignKeyConstraint(['repo_id'], ['repository.id'], name='webhook_repo_id_fkey'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='webhook_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='webhook_pkey')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('webhook')
    # ### end Alembic commands ###