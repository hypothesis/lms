class SessionExtension:
    """
    A self returning descriptor to adding functionality to a session.

    To use this, sub-class it and then add your object to the session:

    class CustomSession(Session):
        my_extension = MyExtension()

    The `name` and `session` attributes will be available to your instance.
    """

    session = None
    name = None

    def __set_name__(self, owner, name):
        # Store the name for more informative errors
        self.name = name

    def __get__(self, instance, owner):
        if not instance:
            raise TypeError(
                f"You can only call '{self.name}' on instances not the bare "
                f"class: '{owner.__name__}'"
            )

        # Store the session and return ourselves
        self.session = instance
        return self
