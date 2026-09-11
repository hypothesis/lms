import logging

from lms.models import Assignment, Grouping
from lms.services import HAPI
from lms.services.document_uri import pdf_fingerprint
from lms.tasks.celery import app

LOG = logging.getLogger(__name__)


@app.task(
    max_retries=3,
    retry_backoff=10,
    autoretry_for=(Exception,),
)
def fingerprint_checkpoint_document(*, assignment_id: int, public_url: str):
    """Identify a Hide & Reveal assignment's file, and create its checkpoint.

    Queued from the viewer, where a working credential has just been proven by
    the file resolving at all. The launch can't rely on one: it runs before the
    browser has had a chance to refresh or obtain the token, and a launch that
    can't read the file leaves the assignment with nothing hidden.
    """
    with app.request_context() as request:  # noqa: SIM117
        with request.tm:
            assignment = request.db.get(Assignment, assignment_id)
            if not assignment or assignment.document_uri:
                # Every viewer queues this until it lands, so most runs are a
                # later one finding the work already done.
                return

            pdf = request.find_service(name="http").get(public_url).content
            assignment.document_uri = f"urn:x-pdf:{pdf_fingerprint(pdf)}"

            # A course's checkpoint is shared with every assignment on the same
            # document, so it is only the fallback. Same rule as the reveal API.
            groupings = assignment.groupings.all()
            scoped = [g for g in groupings if g.type != Grouping.Type.COURSE]

            request.find_service(HAPI).sync_checkpoints(
                checkpoints=[
                    {
                        "group_authority_provided_id": grouping.authority_provided_id,
                        "document_uri": assignment.document_uri,
                    }
                    for grouping in (scoped or groupings)
                ]
            )
