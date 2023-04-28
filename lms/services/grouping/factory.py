from lms.services.grouping.service import GroupingService


def service_factory(_context, request):
    return GroupingService(
        db=request.db,
        application_instance=request.lti_user.application_instance,
        plugin=request.product.plugin.grouping,
    )
