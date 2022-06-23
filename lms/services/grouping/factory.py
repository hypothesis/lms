from lms.services.grouping.service import GroupingService


def service_factory(_context, request):
    return GroupingService(
        db=request.db,
        application_instance=request.find_service(
            name="application_instance"
        ).get_current(),
        plugin=request.product.plugin.grouping_service,
    )
