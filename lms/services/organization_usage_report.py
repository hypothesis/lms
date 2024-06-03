from dataclasses import asdict, dataclass
from datetime import datetime
from logging import getLogger

from sqlalchemy import Date, func, select
from sqlalchemy.orm import Session, aliased

from lms.models import (
    ApplicationInstance,
    Grouping,
    GroupingMembership,
    Organization,
    OrganizationUsageReport,
    User,
)
from lms.services.h_api import HAPI
from lms.services.organization import OrganizationService

LOG = getLogger(__name__)


@dataclass
class UsageReportRow:
    name: str | None
    email: str | None
    h_userid: str

    course_name: str
    course_created: datetime
    authority_provided_id: str


class OrganizationUsageReportService:
    def __init__(
        self,
        db_session: Session,
        h_api: HAPI,
        organization_service: OrganizationService,
    ):
        self._db_session = db_session
        self._organization_service = organization_service
        self._h_api = h_api

    def generate_usage_report(
        self, organization_id: int, tag: str, since: datetime, until: datetime
    ):
        """Generate and store an usage report for one organization."""
        organization = self._organization_service.get_by_id(organization_id)
        assert organization
        report_key = OrganizationUsageReport.generate_key(
            organization, tag, since, until
        )

        if (
            report := self._db_session.query(OrganizationUsageReport)
            .filter_by(key=report_key)
            .one_or_none()
        ):
            LOG.debug("Report already exists, skipping generation. %s", report_key)
            return report

        report = OrganizationUsageReport(
            organization=organization,
            key=report_key,
            since=since,
            until=until,
            tag=tag,
        )
        self._db_session.add(report)

        report_rows = self.usage_report(organization, since, until)

        report.unique_users = len({r.h_userid for r in report_rows})
        report.report = [asdict(r) for r in report_rows]

        return report

    def usage_report(
        self,
        organization: Organization,
        since: datetime,
        until: datetime,
    ):
        # Organizations that are children of the current one.
        # It includes the current org ID.
        organization_children = self._organization_service.get_hierarchy_ids(
            organization.id, include_parents=False
        )
        # All the groups that can hold annotations (courses and segments) from this org
        groups_from_org = self._db_session.scalars(
            select(Grouping.authority_provided_id)
            .join(ApplicationInstance)
            .where(
                ApplicationInstance.organization_id.in_(organization_children),
                # If a group was created after the date we are interested, exclude it
                Grouping.created <= until,
            )
        ).all()

        if not groups_from_org:
            raise ValueError(f"No courses found for {organization.public_id}")

        # Of those groups, get the ones that do have annotations in the time period
        groups_with_annos = [
            group.authority_provided_id
            for group in self._h_api.get_groups(groups_from_org, since, until)
        ]
        if not groups_with_annos:
            raise ValueError(
                f"No courses with activity found for {organization.public_id}"
            )

        # Based on those groups generate the usage report based on the definition of unique user:
        # Users that belong to a course in which there are annotations in the time period
        parent = aliased(Grouping)
        query = (
            select(
                User.display_name.label("name"),
                User.email.label("email"),
                User.h_userid.label("h_userid"),
                Grouping.lms_name.label("course_name"),
                func.date_trunc("day", Grouping.created)
                .cast(Date)
                .label("course_created"),
                Grouping.authority_provided_id,
            )
            .select_from(User)
            .join(GroupingMembership)
            .join(Grouping)
            .distinct()
            .where(
                Grouping.authority_provided_id.in_(
                    # The report is based in courses so we query either
                    # groupings with no parent (courses) or the parents of segments (courses)
                    select(
                        func.coalesce(
                            parent.authority_provided_id, Grouping.authority_provided_id
                        )
                    )
                    .select_from(Grouping)
                    .outerjoin(parent, Grouping.parent_id == parent.id)
                    .where(Grouping.authority_provided_id.in_(groups_with_annos))
                ),
                # We can't exactly know the state of membership in the past but we can
                # know if someone was added to the group after the date we are interested
                GroupingMembership.created <= until,
            )
        )
        return [
            UsageReportRow(
                # Students might have name but they never have email
                name=row.name if row.email else "<STUDENT>",
                email=row.email if row.email else "<STUDENT>",
                h_userid=row.h_userid,
                course_name=row.course_name,
                course_created=row.course_created.isoformat(),
                authority_provided_id=row.authority_provided_id,
            )
            for row in self._db_session.execute(query).all()
        ]


def service_factory(_context, request) -> OrganizationUsageReportService:
    return OrganizationUsageReportService(
        db_session=request.db,
        h_api=request.find_service(HAPI),
        organization_service=request.find_service(OrganizationService),
    )
