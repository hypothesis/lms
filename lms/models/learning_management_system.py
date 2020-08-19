from sqlalchemy import Column, String, UnicodeText

from lms.db import BASE


class LearningManagementSystem(BASE):
    """
    A Learning Management System (LMS) instance.

    For example a particular Canvas site, or Blackboard, site, etc.

    """

    __tablename__ = "learning_management_systems"

    consumer_key = Column(String, primary_key=True)

    # The consumer_key column above has to use SQLAlchemy's String type
    # (which corresponds to Postgres's CHARACTER VARYING) because it's a
    # foreign key to the ApplicationInstance.consumer_key column which uses the
    # String type. But generally speaking you should use UnicodeText
    # (Postgres's TEXT) not String, for SQLAlchemy columns. See this note from
    # SQLAlchemy's docs:
    #
    # > In the vast majority of cases, the Unicode or UnicodeText datatypes
    # > should be used for a Column that expects to store non-ascii data. These
    # > datatypes will ensure that the correct types are used on the database
    # > side as well as set up the correct Unicode behaviors under Python 2.
    # > https://docs.sqlalchemy.org/en/13/core/type_basics.html#sqlalchemy.types.String
    #
    # The consumer_key column can get away with being String because we
    # generate the values for that column and they're always ASCII.
    # The columns below receive values from the outside world (from LTI launch
    # params) so they can't make the ASCII assumption.
    #
    # The difference between the Unicode and UnicodeText types is that
    # UnicodeText is unbounded-length. UnicodeText corresponds to Postgres's
    # TEXT whereas Unicode corresponds to CHARACTER VARYING).
    #
    # For docs on the Postgres types see
    # https://www.postgresql.org/docs/11/datatype-character.html
    tool_consumer_instance_guid = Column(UnicodeText, primary_key=True)
    ext_lms = Column(UnicodeText))
    tool_consumer_info_product_family_code = Column(UnicodeText))
    tool_consumer_info_version = Column(UnicodeText))
    tool_consumer_instance_name = Column(UnicodeText))
    tool_consumer_instance_description = Column(UnicodeText))
    tool_consumer_instance_contact_email = Column(UnicodeText))
