from sqlalchemy.exc import NoResultFound

from lms.models import Grouping, GroupingMembership, User, LTIRole


class EmailDigestsService:
    def __init__(self, db, h_api):
        self.db = db
        self.h_api = h_api

    def get(self, user_id, since, until):
        """Get course activity for the given instructor and time period.

        Returns the total number of student annotations in the given
        instructor's courses in the given timeframe, plus a list of the courses
        that had new annotations in the timeframe with their course titles and
        the numbers of annotations per course:

        {
            "num_annotations": 34,
            "courses": [
                {
                    "title": "Making sociology fun",
                    "num_annotations": 30,
                },
                {
                    "title": "History of jazz music",
                    "num_annotations": 4,
                },
            ],
        }
        """
        try:
            user = self.db.query(User).filter_by(id=user_id).one()
        except NoResultFound:
            return {"num_annotations": 0, "courses": []}

        group_activity = self.h_api._api_request(
            "GET",
            path="email_digests",
            params={
                "user": user.h_userid,
                "since": since.isoformat(),
                "until": until.isoformat(),
            },
        ).json()

        print(group_activity)

        courses = {}

        for group in group_activity["groups"]:
            # Find all the groupings for this group.
            groupings = (
                self.db.query(Grouping).filter_by(
                    authority_provided_id=group["authority_provided_id"]
                )
            ).all()

            if not groupings:
                continue

            # Find all the course groupings that all the groupings belong to.
            course_groupings = []
            for grouping in groupings:
                if grouping.type == Grouping.Type.COURSE:
                    course_groupings.append(grouping)
                else:
                    assert grouping.parent.type == Grouping.Type.COURSE
                    course_groupings.append(grouping.parent)

            # All the course groupings for an h group should have the same authority_provided_id.
            for grouping in course_groupings:
                assert (
                    grouping.authority_provided_id
                    == course_groupings[0].authority_provided_id
                )

            # Don't count courses the user isn't an instructor in.
            is_instructor = bool(
                self.db.query(GroupingMembership)
                .join(User)
                .filter(User.id == user_id)
                .join(LTIRole)
                .filter(LTIRole.type == "instructor", LTIRole.scope == "course")
                .join(Grouping)
                .filter(
                    Grouping.authority_provided_id
                    == course_groupings[0].authority_provided_id
                )
                .count()
            )
            if not is_instructor:
                continue

            num_annotations = sum(
                (
                    user_["num_annotations"]
                    for user_ in group["users"]
                    if user_["userid"] != user.h_userid
                )
            )

            if course_groupings[0].authority_provided_id in courses:
                courses[course_groupings[0].authority_provided_id][
                    "num_annotations"
                ] += num_annotations
            else:
                courses[course_groupings[0].authority_provided_id] = {
                    "title": course_groupings[0].lms_name,
                    "num_annotations": num_annotations,
                }

        return {
            "num_annotations": sum(
                (course["num_annotations"] for course in courses.values())
            ),
            "courses": list(courses.values()),
        }


def factory(_context, request):
    return EmailDigestsService(request.db, request.find_service(name="h_api"))
