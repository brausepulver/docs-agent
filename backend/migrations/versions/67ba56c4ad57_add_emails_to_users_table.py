"""add emails to users table

Revision ID: 67ba56c4ad57
Revises: faa5de1605d4
Create Date: 2024-11-10 23:33:54.979371

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67ba56c4ad57'
down_revision: Union[str, None] = 'faa5de1605d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('email', sa.String(), nullable=False))
    op.alter_column('users', 'auth0_id',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.create_unique_constraint(None, 'users', ['email'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'users', type_='unique')
    op.alter_column('users', 'auth0_id',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.drop_column('users', 'email')
    # ### end Alembic commands ###