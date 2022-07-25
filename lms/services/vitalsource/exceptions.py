class VitalSourceError(Exception):
    """Indicate a failure in the VitalSource service or client."""

    def __init__(self, error_code, message=None):
        """
        Instantiate the error.

        :param error_code: A string code used to present specific dialogs in
            the front end. For details of the codes see:
            lms/static/scripts/frontend_apps/components/LaunchErrorDialog.js
        :param message: A normal error message, mostly for debugging
        """
        self.error_code = error_code
        super().__init__(message)
