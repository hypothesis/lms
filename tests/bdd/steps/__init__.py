# As HAPIContext currently defines no steps it isn't automatically loaded
# into context by behave, so we have to make sure it gets seen at least once
# for the StepContextManager to know it exists.
from tests.bdd.steps.h_api import HAPIContext
