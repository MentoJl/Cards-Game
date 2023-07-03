"""
Exception definitions.
"""

class AuthorizationFailure(Exception):
    """
    Return when credentials passed are rejected
    with a 401 response code
    """
    pass

class ResourceNotFound(Exception):
    """
    Return when an object is not found
    """
    pass

class NodeNotInPool(Exception):
    """
    Return when an action for a given node in a pool
    is not in the pool. IE: Drain node X in pool Y
    """
    pass

class DrainError(Exception):
    """
    Return when a set contains duplicates
    """
    pass