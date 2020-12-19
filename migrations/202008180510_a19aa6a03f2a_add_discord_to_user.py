"""Add discord to user

Revision ID: a19aa6a03f2a
Revises: 5945d8081a95
Create Date: 2020-08-18 05:10:58.562227

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'a19aa6a03f2a'
down_revision = '5945d8081a95'
branch_labels = ()
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('discord', sa.String(length=200), nullable=True))
        batch_op.alter_column('email',
               existing_type=mysql.VARCHAR(length=200),
               nullable=True)
        batch_op.alter_column('password',
               existing_type=mysql.VARCHAR(length=120),
               nullable=True)
        batch_op.alter_column('username',
               existing_type=mysql.VARCHAR(length=200),
               nullable=True)
        batch_op.create_unique_constraint(batch_op.f('uq_users_discord'), ['discord'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('uq_users_discord'), type_='unique')
        batch_op.alter_column('username',
               existing_type=mysql.VARCHAR(length=200),
               nullable=False)
        batch_op.alter_column('password',
               existing_type=mysql.VARCHAR(length=120),
               nullable=False)
        batch_op.alter_column('email',
               existing_type=mysql.VARCHAR(length=200),
               nullable=False)
        batch_op.drop_column('discord')

    # ### end Alembic commands ###