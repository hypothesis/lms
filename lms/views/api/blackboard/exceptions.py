class BlackboardFileNotFoundInCourse(Exception):
    """A Blackboard file ID wasn't found in the current course."""

    explanation = (
        "Hypothesis couldn't find the assignment's PDF file in the Blackboard course."
    )

    def __init__(self, document_url):
        self.details = {"document_url": document_url}
        super().__init__(self.details)
