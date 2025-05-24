"""Add subforums

Revision ID: 09b7e4a7127c
Revises: 1e7bc669ef9d
Create Date: 2022-09-14 01:20:21.773715

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '09b7e4a7127c'
down_revision = '1e7bc669ef9d'
branch_labels = ()
depends_on = None


def upgrade():
    with op.batch_alter_table('forums', schema=None) as batch_op:
        batch_op.add_column(sa.Column('parent_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(batch_op.f('fk_forums_parent_id_forums'), 'forums', ['parent_id'], ['id'], ondelete='CASCADE')


def downgrade():
    with op.batch_alter_table('forums', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('fk_forums_parent_id_forums'), type_='foreignkey')
        batch_op.drop_column('parent_id')
