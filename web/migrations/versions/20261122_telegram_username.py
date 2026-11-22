"""Store Telegram usernames."""

import sqlalchemy as sa
from alembic import op

revision = "20261122_telegram_username"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # New installations already have the column through create_all().
    columns = sa.inspect(op.get_bind()).get_columns("telegram_user")
    if not any(column["name"] == "username" for column in columns):
        op.add_column("telegram_user", sa.Column("username", sa.String(32)))


def downgrade():
    op.drop_column("telegram_user", "username")
