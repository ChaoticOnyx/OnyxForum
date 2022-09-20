"""add community rating and uploads

Revision ID: 099c4dfd37c1
Revises: 09b7e4a7127c
Create Date: 2022-09-20 17:11:58.473465

"""
from alembic import op
import sqlalchemy as sa
import flaskbb


# revision identifiers, used by Alembic.
revision = '099c4dfd37c1'
down_revision = '09b7e4a7127c'
branch_labels = ()
depends_on = None


def upgrade():
    op.create_table('community_rating',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('change', sa.Integer(), nullable=False),
    sa.Column('datetime', flaskbb.utils.database.UTCDateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_community_rating_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_community_rating'))
    )
    with op.batch_alter_table('community_rating', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_community_rating_user_id'), ['user_id'], unique=False)

    op.create_table('uploaded_files',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('datetime', flaskbb.utils.database.UTCDateTime(timezone=True), nullable=True),
    sa.Column('current_name', sa.Text(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('original_name', sa.Text(), nullable=True),
    sa.Column('file_size', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_uploaded_files_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_uploaded_files'))
    )
    with op.batch_alter_table('groups', schema=None) as batch_op:
        batch_op.add_column(sa.Column('upload_size_limit', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('uploads_total_size_limit', sa.Integer(), nullable=False))

    with op.batch_alter_table('post_rate', schema=None) as batch_op:
        batch_op.add_column(sa.Column('community_rating_record', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_post_rate_community_rating_record'), ['community_rating_record'], unique=False)
        batch_op.create_foreign_key(batch_op.f('fk_post_rate_community_rating_record_community_rating'), 'community_rating', ['community_rating_record'], ['id'], ondelete='CASCADE')


def downgrade():
    with op.batch_alter_table('post_rate', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('fk_post_rate_community_rating_record_community_rating'), type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_post_rate_community_rating_record'))
        batch_op.drop_column('community_rating_record')

    with op.batch_alter_table('groups', schema=None) as batch_op:
        batch_op.drop_column('uploads_total_size_limit')
        batch_op.drop_column('upload_size_limit')

    op.drop_table('uploaded_files')
    with op.batch_alter_table('community_rating', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_community_rating_user_id'))

    op.drop_table('community_rating')
