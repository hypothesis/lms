"""
Add ApplicationInstance.settings and Course.settings server defaults and make them not-nullable.

Revision ID: 5086e8b137b9
Revises: 7f9824ded172
Create Date: 2020-07-16 10:23:06.469812

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import sessionmaker

revision = "5086e8b137b9"
down_revision = "7f9824ded172"


Base = declarative_base()
Session = sessionmaker()


class ApplicationInstance(Base):
    __tablename__ = "application_instances"
    id = sa.Column(sa.Integer, primary_key=True)
    settings = sa.Column(MutableDict.as_mutable(JSONB))


def upgrade():
    session = Session(bind=op.get_bind())

    for ai in session.query(ApplicationInstance).filter_by(settings=None):
        ai.settings = {}

    session.commit()

    op.alter_column("application_instances", "settings", nullable=False)
    op.alter_column(
        "application_instances", "settings", server_default=sa.text("'{}'::jsonb")
    )
    op.alter_column("course", "settings", server_default=sa.text("'{}'::jsonb"))


def downgrade():
    op.alter_column("application_instances", "settings", nullable=True)
    op.alter_column("application_instances", "settings", server_default=None)
    op.alter_column("course", "settings", server_default=None)
