from lms.services.grouping.service import GroupingService
from lms.services.segment import SegmentService


def service_factory(_context, request):
    return GroupingService(
        db=request.db,
        application_instance=(
            request.lti_user.application_instance if request.lti_user else None
        ),
        plugin=request.product.plugin.grouping,
        segment_service=request.find_service(SegmentService),
    )
