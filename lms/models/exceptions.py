class ReusedConsumerKey(Exception):
    """Application Instance launched in a different LMS install."""

    def __init__(self, existing_guid, new_guid):
        super().__init__(None)
        self.existing_guid = existing_guid
        self.new_guid = new_guid
