def includeme(config):
    config.scan(__name__)
    config.include("lms.views.predicates")
