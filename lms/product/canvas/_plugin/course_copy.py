class CanvasCourseCopyPlugin:
    """Handle course copy in Canvas."""

    def find_matching_group_set_in_course(self, _course, _group_set_id):
        # We are not yet handling course copy for groups in Canvas.
        # Canvas doesn't copy group sets during course copy so the approach taken
        # in other LMS won't make sense here.
        # We implement this method so we can call `find_mapped_group_set_id` in all LMS's
        return None

    @classmethod
    def factory(cls, _context, _request):
        return cls()
