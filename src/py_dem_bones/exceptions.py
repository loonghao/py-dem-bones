"""
Custom exceptions for py-dem-bones.

This module defines custom exceptions used throughout the py-dem-bones library
to provide more specific error information and improve error handling.
"""


class DemBonesError(Exception):
    """Base class for all py-dem-bones exceptions."""


class ParameterError(DemBonesError):
    """
    Exception raised for invalid parameter values.

    This exception is raised when a function or method receives a parameter
    with an invalid value, such as incorrect array shapes, types, or ranges.
    """


class ComputationError(DemBonesError):
    """
    Exception raised when computation fails.

    This exception is raised when the core computation algorithm fails,
    for example due to numerical instability or invalid input data.
    """


class IndexError(DemBonesError):
    """
    Exception raised for invalid indices.

    This exception is raised when an index is out of range, for example
    when trying to access a bone index that exceeds the number of bones.
    """


class NameError(DemBonesError):
    """
    Exception raised for name-related errors.

    This exception is raised when a name-to-index mapping fails, for example
    when trying to retrieve a bone index for a non-existent bone name.
    """


class ConfigurationError(DemBonesError):
    """
    Exception raised for configuration errors.

    This exception is raised when there are problems with the configuration
    of the algorithm or incompatible settings.
    """


class NotImplementedError(DemBonesError):
    """
    Exception raised for unimplemented features.

    This exception is raised when a feature described in the API is not
    yet implemented.
    """


class IOError(DemBonesError):
    """
    Exception raised for input/output errors.

    This exception is raised when operations involving file I/O or
    data exchange with external software fail.
    """
