"""All of this app's custom Pyramid tweens."""
from pyramid.tweens import EXCVIEW

__all__ = []


def rollback_db_session_tween_factory(handler, _registry):
    """Return the rollback_db_session_on_exception_tween."""

    def rollback_db_session_tween(request):
        """
        Rollback the DB session before exception views are called.

        Catches any exception raised by view processing and rollback the
        sqlalchemy database session before exception view processing begins.

        This means that code can access the DB session during exception view
        processing without getting an InvalidRequestError from sqlalchemy
        ("This Session's transaction has been rolled back due to a previous
        exception during flush. To begin a new transaction with this Session,
        first issue Session.rollback()"), even if exception view processing was
        trigged by a sqlalchemy IntegrityError during view processing.
        """
        try:
            return handler(request)
        except Exception:
            request.db.rollback()
            raise

    return rollback_db_session_tween


def includeme(config):
    config.add_tween(rollback_db_session_tween_factory, under=EXCVIEW)
