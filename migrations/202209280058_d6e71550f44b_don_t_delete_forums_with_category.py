"""Don't delete forums with category

Revision ID: d6e71550f44b
Revises: 099c4dfd37c1
Create Date: 2022-09-28 00:58:23.158083

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'd6e71550f44b'
down_revision = '099c4dfd37c1'
branch_labels = ()
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('forums', schema=None) as batch_op:
        batch_op.alter_column('category_id',
               existing_type=mysql.INTEGER(),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('forums', schema=None) as batch_op:
        batch_op.alter_column('category_id',
               existing_type=mysql.INTEGER(),
               nullable=False)

    # ### end Alembic commands ###
