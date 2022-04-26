from dataclasses import dataclass


@dataclass
class LTIGradingClient:
    grading_url: str

    def read_result(self, grading_id):
        raise NotImplementedError()

    def record_result(self, grading_id, score=None, pre_record_hook=None):
        raise NotImplementedError()
