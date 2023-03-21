from copy import deepcopy

import pytest

from lms.services.digest._models import Digest, HCourse, HUser


class TestHCourse:
    def test_learner_annotations(self, course):
        assert course.learner_annotations == [{"author": {"userid": "acct:learner"}}]


class TestDigest:
    def test_serialize(self, course):
        course_2 = deepcopy(course)
        course_2.annotations = []

        digest = Digest(
            audience_user=HUser("acct:audience", "display_name", "email@1"),
            courses=[course, course, course_2],
        )

        # Note that we've ignored the teachers annotations in this count, and
        # that course 2 is missing, as it has no annotations
        assert digest.serialize() == {
            "total_annotations": 2,
            "courses": [
                {"title": "Title", "num_annotations": 1},
                {"title": "Title", "num_annotations": 1},
            ],
        }


@pytest.fixture
def course():
    return HCourse(
        title="Title",
        authority_provided_id="aid",
        aka=["aid", "aid_2"],
        instructors=["acct:instructor"],
        annotations=[
            {"author": {"userid": "acct:learner"}},
            {"author": {"userid": "acct:instructor"}},
        ],
    )
