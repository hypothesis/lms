"""
DB migration to back-fill organizations.

Revision ID: 52755322151e
Revises: 79eda94de79f
Create Date: 2022-09-07 18:11:19.706885

"""

import itertools
from base64 import urlsafe_b64encode
from collections import Counter
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy.orm import declarative_base

# revision identifiers, used by Alembic.
revision = "52755322151e"
down_revision = "79eda94de79f"

Base = declarative_base()


class ApplicationInstance(Base):
    """Class to represent a single lms install."""

    __tablename__ = "application_instances"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    #: A unique identifier for the LMS instance.
    tool_consumer_instance_guid = sa.Column(sa.UnicodeText, nullable=True)

    #: The name of the LMS instance, e.g. "HypothesisU".
    tool_consumer_instance_name = sa.Column(sa.UnicodeText, nullable=True)

    organization_id = sa.Column(
        sa.Integer(), sa.ForeignKey("organization.id"), nullable=True
    )
    organization = sa.orm.relationship("Organization")
    """The organization this application instance belongs to."""


class CreatedUpdatedMixin:
    created = sa.Column(sa.DateTime(), server_default=sa.func.now(), nullable=False)
    updated = sa.Column(
        sa.DateTime(),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )


class Organization(CreatedUpdatedMixin, Base):
    """Model for Organizations comprised of application instances."""

    __tablename__ = "organization"

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)

    name = sa.Column(sa.UnicodeText(), nullable=False)
    """Human readable name for the organization."""

    enabled = sa.Column(sa.Boolean(), nullable=False, default=True)
    """Is this organization allowed to use LMS?"""

    _public_id = sa.Column(
        "public_id",
        sa.UnicodeText(),
        nullable=False,
        unique=True,
        # We don't use a standard UUID-4 format here as they are common in Tool
        # Consumer Instance GUIDs, and might be confused for them. These also
        # happen to be shorter and guaranteed URL safe.
        default=lambda: urlsafe_b64encode(uuid4().bytes).decode("ascii").rstrip("="),
    )
    """
    A human readable URL safe public id.

    Although this is a GUID the DB can only enforce that this is only locally
    unique to the LMS instance. For this reason the `public_id()` accessor
    should be used instead which provides a fully qualified id.
    """

    application_instances = sa.orm.relationship(
        "ApplicationInstance", back_populates="organization"
    )
    """Get any application instances associated with this organization."""


# This code is lifted straight from Sparky
def connected_subgraphs(edges):
    """
    Get a list of sets of nodes which form connected sub-graphs.

    * All edges are assumed to be bidirectional
    * All items in a set are guaranteed to be at least indirectly connected
    * No items in different sets should be connected even indirectly
    """

    # Put every node in a group on its own
    group_to_nodes = {node: {node} for node in itertools.chain(*edges)}
    # ... and record it's location (which will change)
    node_to_group = {node: node for node in group_to_nodes.keys()}

    # Repeatedly merge groups if they are joined by an edge
    for left_node, right_node in edges:
        left_group, right_group = node_to_group[left_node], node_to_group[right_node]

        if left_group == right_group:
            # Nothing to do, they are already in the same group
            continue

        # Merge the right group into the left and update the lookups
        for node in group_to_nodes.pop(right_group):
            group_to_nodes[left_group].add(node)
            node_to_group[node] = left_group

    # Discard our internal ids for the sub-graphs as they have no meaning
    # outside this method. Sort them to make it easier on the eye.
    return sorted(sorted(nodes) for nodes in group_to_nodes.values())


def pick_name(names):
    """Pick the most common or the longest non-empty name."""

    names = [name.strip() for name in names if name and name.strip()]
    if not names:
        return None

    if len(names) == 1:
        return names[0]

    most_common = Counter()
    longest_name = ""
    for name in names:
        most_common[name] += 1
        if len(name) > len(longest_name):
            longest_name = name

    for name, count in most_common.most_common(1):
        if count > 1:
            return name

    return longest_name


def upgrade():
    db_session = sa.orm.Session(bind=op.get_bind())

    print("Clearing old organizations...")
    op.execute("UPDATE application_instances SET organization_id = NULL")
    op.execute("DELETE FROM organization")

    with open(__file__.replace(".py", ".sql"), encoding="utf-8") as handle:
        query = handle.read()

    print("Detecting GUIDs...")
    edges = list(db_session.execute(query))

    print("Grouping GUIDs...")
    grouped_guids = connected_subgraphs(edges)

    print("Creating new organizations...")
    total = 0

    for ai_ids in grouped_guids:
        ais = (
            db_session.query(ApplicationInstance)
            .filter(ApplicationInstance.id.in_(ai_ids))
            .all()
        )
        if not ais:
            continue

        organization = Organization(
            name=pick_name([ai.tool_consumer_instance_name for ai in ais])
        )
        total += 1
        print(
            f"\tCreating '{organization.name}' for {len(ais)} application instance(s)"
        )
        for ai in ais:
            ai.organization = organization

        db_session.add(organization)

    print(f"Created {total} organization(s). Done")


def downgrade():
    op.execute("UPDATE application_instances SET organization_id = NULL")
    op.execute("DELETE FROM organization")
