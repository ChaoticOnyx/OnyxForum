"""add ignorekarma user flag

Revision ID: 28e774f9972f
Revises: 34b4f4dc375c
Create Date: 2021-06-20 06:34:25.772649

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '28e774f9972f'
down_revision = '34b4f4dc375c'
branch_labels = ()
depends_on = None


def upgrade():
    with op.batch_alter_table('groups', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ignorekarma', sa.Boolean(), nullable=False))


def downgrade():
    with op.batch_alter_table('groups', schema=None) as batch_op:
        batch_op.drop_column('ignorekarma')
