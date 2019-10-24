"""
Disabled provisioning for non-whitelisted consumer keys.

Revision ID: b99c4d910801
Revises: 7e4124035651
Create Date: 2018-12-07 12:04:18.524467

"""
import logging

import sqlalchemy as sa
from alembic import op
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

log = logging.getLogger(__name__)


# revision identifiers, used by Alembic.
revision = "b99c4d910801"
down_revision = "7e4124035651"


Base = declarative_base()
Session = sessionmaker()


class ApplicationInstance(Base):
    __tablename__ = "application_instances"
    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    consumer_key = sa.Column(sa.String)
    provisioning = sa.Column(sa.Boolean())


def upgrade():
    session = Session(bind=op.get_bind())

    disabled = 0
    enabled = 0

    for ai in session.query(ApplicationInstance):
        if ai.consumer_key in WHITELISTED_CONSUMER_KEYS:
            enabled += 1
        else:
            ai.provisioning = False
            disabled += 1

    session.commit()

    log.info(
        "Disabled provisioning for %s non-whitelisted application instances", disabled
    )
    log.info(
        "Left provisioning enabled for %s whitelisted application instances", enabled
    )


def downgrade():
    pass


WHITELISTED_CONSUMER_KEYS = [
    # QA
    "Hypothesis7b5fb260f6d0db063da4e580a6b849f5",
    "Hypothesisecb311a8f8702321b0923f080985ac6b",
    "Hypothesis842477196a5fc5df347ccbbafe0e6ac8",
    "Hypothesisac612428af9ef362b6e18aec5a02b1f5",
    "Hypothesis466c9b1464a5f79ec85a8eaa87ceae36",
    "Hypothesisc6d3eb00fbe4bdf9ade70f4f330ebeed",
    # Production
    "Hypothesisf7fd048c074dc0dc88026e0bb8608acc",
    "Hypothesis4cc3079efeab2f1f5758ece8ff907608",
    "Hypothesise3ed5471002c49043502f69d2fb52f80",
    "Hypothesis4d5938971fc9c292d18499cc7cdf6a00",
    "Hypothesiscbf75db3d2b0c36069d4bfa8d6b24e0f",
    "Hypothesis1b54800f85eea4d0bfa633af6b4f6320",
    "Hypothesise892848c2e9249ddc0b28d8b2c989391",
    "Hypothesis32b540c6041c634ae8de0e75bb4801e8",
    "Hypothesiseec5522f1467dcf72ed1f083e5f143fb",
    "Hypothesis418e872f80810f12634f87bcaf323c41",
    "Hypothesis3e2b034fcf175c2c5f46186581f2578f",
    "Hypothesis77c9e42c15b4252014748c6452037640",
    "Hypothesis5bf0ff6068593c827b4201e8add91a20",
    "Hypothesis3ff6000baabc7bb9479d9c9b6e02b43e",
    "Hypothesiscc23b581785ce25a7e55a4940dfef526",
    "Hypothesis39010175992dae380356915fe1fbe88b",
    "Hypothesise92ce8dbdc75658e14cc8fb3b9042e8a",
    "Hypothesisdb374c6ea57feeb70c5d0fd2182fddf4",
    "Hypothesisd067d04e052f26f370d46a6441455eef",
    "Hypothesis42df4fae3adba46ae23c2c13caa00d47",
    "Hypothesis17b636ff1a0cc295479338121bf3d27e",
    "Hypothesis8b7d7833e5abffa2b2dea012cad68041",
    "Hypothesisb2ff74c06daa74c515dc77be836dedb9",
    "Hypothesis98d1b7f0faac8bb8a706e6c8db1052b2",
]
