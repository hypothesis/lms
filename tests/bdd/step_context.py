class StepContext:
    """Step and tear down for an object powering step specific tasks."""

    # Does this class always exist, or does it come and go?
    ephemeral = False

    # The key to use when attaching to the context
    context_key = None

    def __init__(self, **kwargs):
        pass

    def do_setup(self):
        """Set up the class for work before the scenario."""

    def do_teardown(self):
        """Clean up the class for work after the scenario."""

    @classmethod
    def register(cls, context, **kwargs):
        instance = cls(**kwargs)
        setattr(context, cls.context_key, instance)

        return instance

    @classmethod
    def setup(cls, context):
        instance = cls.get_instance(context)
        if instance:
            instance.do_setup()

    @classmethod
    def teardown(cls, context):
        if cls.ephemeral:
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


class StepContextManager:
    """Manage all sub-classes of StepContext at once."""

    @classmethod
    def before_all(cls, context, **kwargs):
        for step_context in StepContext.__subclasses__():
            if not step_context.ephemeral:
                step_context.register(context, **kwargs)

    @classmethod
    def before_scenario(cls, context):
        for step_context in StepContext.__subclasses__():
            step_context.setup(context)

    @classmethod
    def after_scenario(cls, context):
        for step_context in StepContext.__subclasses__():
            step_context.teardown(context)
