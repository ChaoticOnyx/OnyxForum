"""Add PostRate

Revision ID: 55e110ae9db4
Revises: 28e774f9972f
Create Date: 2021-12-05 03:47:23.969683

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
import flaskbb

# revision identifiers, used by Alembic.
revision = '1e7bc669ef9d'
down_revision = '28e774f9972f'
branch_labels = ()
depends_on = None


def upgrade():
    op.create_table('post_rate',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('post', sa.Integer(), nullable=False),
    sa.Column('user', sa.Integer(), nullable=False),
    sa.Column('change', sa.Integer(), nullable=False),
    sa.Column('datetime', flaskbb.utils.database.UTCDateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['post'], ['posts.id'], name=op.f('fk_post_rate_post_posts')),
    sa.ForeignKeyConstraint(['user'], ['users.id'], name=op.f('fk_post_rate_user_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_post_rate'))
    )
    with op.batch_alter_table('post_rate', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_post_rate_post'), ['post'], unique=False)
        batch_op.create_index(batch_op.f('ix_post_rate_user'), ['user'], unique=False)

    op.drop_table('messages')
    op.drop_table('conversations')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('rate_weight', sa.Integer(), server_default=sa.text('1'), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('rate_weight')

    op.create_table('conversations',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('user_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('from_user_id', mysql.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('to_user_id', mysql.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('shared_id', sa.BINARY(length=16), nullable=False),
    sa.Column('subject', mysql.VARCHAR(charset='utf8', collation='utf8_general_ci', length=255), nullable=True),
    sa.Column('date_created', mysql.DATETIME(), nullable=False),
    sa.Column('date_modified', mysql.DATETIME(), nullable=False),
    sa.Column('trash', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    sa.Column('draft', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    sa.Column('unread', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    sa.CheckConstraint('(`draft` in (0,1))', name='conversations_chk_2'),
    sa.CheckConstraint('(`trash` in (0,1))', name='conversations_chk_1'),
    sa.CheckConstraint('(`unread` in (0,1))', name='conversations_chk_3'),
    sa.ForeignKeyConstraint(['from_user_id'], ['users.id'], name='fk_conversations_from_user_id_users', ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['to_user_id'], ['users.id'], name='fk_conversations_to_user_id_users', ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_conversations_user_id_users', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_table('messages',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('conversation_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('user_id', mysql.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('message', mysql.TEXT(charset='utf8', collation='utf8_general_ci'), nullable=False),
    sa.Column('date_created', mysql.DATETIME(), nullable=False),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], name='fk_messages_conversation_id_conversations', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_messages_user_id_users', ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    with op.batch_alter_table('post_rate', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_post_rate_user'))
        batch_op.drop_index(batch_op.f('ix_post_rate_post'))

    op.drop_table('post_rate')
    # ### end Alembic commands ###
