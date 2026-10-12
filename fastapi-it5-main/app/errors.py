"""Custom errors raised by the repositories and services.

main.py converts these into proper HTTP responses.
"""


class NotFoundError(Exception):
    """A record the request refers to does not exist (HTTP 404)."""


class ConflictError(Exception):
    """The request breaks a business rule or a database constraint (HTTP 409)."""
