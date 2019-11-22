class StepContext:
    singleton = True
    context_key = None

    def __init__(self, **kwargs):
        pass

    @classmethod
    def register(cls, context, **kwargs):
        instance = cls(**kwargs)
        setattr(context, cls.context_key, instance)

        return instance

    def do_setup(self):
        pass

    def do_teardown(self):
        pass

    @classmethod
    def setup(cls, context):
        instance = cls.get_instance(context)
        if instance:
            instance.do_setup()

    @classmethod
    def teardown(cls, context):
        if not cls.singleton:
            setattr(context, cls.context_key, None)
            return

        instance = cls.get_instance(context)
        if instance:
            instance.do_teardown()

    @classmethod
    def get_instance(cls, context):
        try:
            return getattr(context, cls.context_key)
        except AttributeError:
            return None
