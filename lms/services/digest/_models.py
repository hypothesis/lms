from dataclasses import dataclass
from functools import cached_property
from typing import List

from lms.services.mailchimp import EmailRecipient


@dataclass
class HUser(EmailRecipient):
    """A class representing H users."""

    h_userid: str
    """The H userid like 'acct:name@lms.example.com'."""


@dataclass
class HCourse:
    """A class representing courses as groups in H."""

    title: str
    """Title for the course."""

    authority_provided_id: str
    """The course's authority provided id."""

    aka: List[str]
    """All authority provided ids which map to the course from groups etc."""

    instructors: List[str]
    """A list of H userids for users who are instructors for the course."""

    annotations: List[dict] = None
    """A list of annotations in the course."""

    @cached_property
    def learner_annotations(self):
        """Get the annotations, but filtered to users who are learners."""

        return [
            annotation
            for annotation in self.annotations
            if annotation["author"]["userid"] not in self.instructors
        ]


@dataclass
class Digest:
    """A digest of activity for a given user."""

    audience_user: HUser
    """The user who is the intended recipient of the information."""

    courses: List[HCourse]
    """Courses which the digest is summarising."""

    def serialize(self) -> dict:
        """Get a plain dict representation of this digest."""

        digest = {"total_annotations": 0, "courses": []}

        for course in self.courses:
            # We only count learner activity at the moment, not teachers
            if course.learner_annotations:
                digest["total_annotations"] += len(course.learner_annotations)
                digest["courses"].append(
                    {
                        "title": course.title,
                        "num_annotations": len(course.learner_annotations),
                    }
                )

        return digest
