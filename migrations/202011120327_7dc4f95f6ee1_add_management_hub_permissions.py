"""add management hub permissions

Revision ID: 7dc4f95f6ee1
Revises: ba063d7df9ca
Create Date: 2020-11-12 03:27:29.404131

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '7dc4f95f6ee1'
down_revision = 'ba063d7df9ca'
branch_labels = ()
depends_on = None


def upgrade():
    with op.batch_alter_table('groups', schema=None) as batch_op:
        batch_op.add_column(sa.Column('dragon_management', sa.Boolean(), nullable=False))
        batch_op.add_column(sa.Column('eos_management', sa.Boolean(), nullable=False))
        batch_op.add_column(sa.Column('onyx_management', sa.Boolean(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('groups', schema=None) as batch_op:
        batch_op.drop_column('onyx_management')
        batch_op.drop_column('eos_management')
        batch_op.drop_column('dragon_management')
    # ### end Alembic commands ###
