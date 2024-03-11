from lms.product.plugin.misc import MiscPlugin


class MoodleMiscPlugin(MiscPlugin):
    def get_document_url(
        self, request, assignment, _historical_assignment
    ) -> str | None:
        """Get a document URL from an assignment launch."""

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
            # The assignment must have been re-deep-linked in Moodle our our DB record is outdated
            # Update our uuid so we can trust our DB again
            assignment.deep_linking_uuid = deep_linked_config.get("deep_linking_uuid")
            # Get the URL from the DL
            return deep_linked_config.get("url")

        if assignment:
            # In other cases, if we have a record of the assignment in our DB, trust that info.
            return assignment.document_url

        # In other LMSes we'd look at historical_assignment here.
        # Moodle doesn't support resource_link_id so we will never have an historical_assignment

        # If we don't have an assignment in the DB this means
        # - This is the first launch of a deep linked assignment, get the info from the DL.
        # - This install doesn't use deep linking, rely on `.get`'s default to return None.
        #     That will make this an "un_configured assignment" and we'll show the file picker.
        return deep_linked_config.get("url")

    @classmethod
    def factory(cls, _context, request):  # pragma: no cover
        return cls()
