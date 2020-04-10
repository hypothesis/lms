def includeme(config):  # pragma: no cover
    config.scan(__name__)
    config.include("lms.views.predicates")
