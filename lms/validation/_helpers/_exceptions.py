"""Exceptions raised by code in :mod:`lms.validation._helpers`."""


__all__ = ["HelpersError", "JWTError", "ExpiredJWTError", "InvalidJWTError"]


class HelpersError(Exception):
    """Base class for all :mod:`lms.validation._helpers` exceptions."""


class JWTError(HelpersError):
    """A problem with a JWT."""


class ExpiredJWTError(JWTError):
    """Decoding a JWT failed because the JWT was expired."""


class InvalidJWTError(JWTError):
    """Decoding a JWT failed because the JWT was invalid."""
