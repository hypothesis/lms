from lms.models import Assignment
from lms.product.plugin.misc import AssignmentConfig, MiscPlugin


class MoodleMiscPlugin(MiscPlugin):
    def get_assignment_configuration(
        self,
        request,
        assignment: Assignment | None,
        _historical_assignment: Assignment | None,
    ) -> AssignmentConfig:
        deep_linked_config = self.get_deep_linked_assignment_configuration(request)

        if (
            # We found an assignment that corresponds to this launch on the DB
            assignment
            # that assignment was originally deep linked
            and assignment.deep_linking_uuid
            # the UUID we generated on the deep link doesn't match our record in the DB
            and assignment.deep_linking_uuid
            != deep_linked_config.get("deep_linking_uuid")
        ):
            # The assignment must have been re-deep-linked in Moodle and our DB record is outdated
            # Update our uuid so we can trust our DB again
            assignment.deep_linking_uuid = deep_linked_config.get("deep_linking_uuid")
            # Get the config from the DL
            return self._assignment_config_from_deep_linked_config(deep_linked_config)

        if (
            # We found an assignment that corresponds to this launch on the DB
            assignment
            # That assignment was not originally DL, is was created before DL was enabled in the school
            and not assignment.deep_linking_uuid
            # And now has been deep linked, ie edited using the LMS re-deep-link option.
            and deep_linked_config.get("deep_linking_uuid")
        ):
            # Let's store the UUID so next time we recognize correctly
            assignment.deep_linking_uuid = deep_linked_config.get("deep_linking_uuid")

            # Use the DL config instead of the one in our DB
            return self._assignment_config_from_deep_linked_config(deep_linked_config)

        if assignment:
            # In other cases, if we have a record of the assignment in our DB, trust that info.
            return self._assignment_config_from_assignment(assignment)

        # In other LMSes we'd look at historical_assignment here.
        # Moodle doesn't support resource_link_id so we will never have a historical_assignment

        # If we don't have an assignment in the DB this means
        # - This is the first launch of a deep linked assignment, get the info from the DL.
        # - This install doesn't use deep linking, rely on `.get`'s default to return None.
        #     That will make this an "un_configured assignment" and we'll show the file picker.
        return self._assignment_config_from_deep_linked_config(deep_linked_config)

    @classmethod
    def factory(cls, _context, request):  # pragma: no cover  # noqa: ARG003
        return cls()
