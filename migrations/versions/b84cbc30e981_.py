"""empty message

Revision ID: b84cbc30e981
Revises: cb3cdf248718
Create Date: 2019-07-31 11:19:01.122554

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b84cbc30e981'
down_revision = 'cb3cdf248718'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('rss_feed', sa.Column('favicon', sa.String(length=128), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('rss_feed', 'favicon')
    # ### end Alembic commands ###
