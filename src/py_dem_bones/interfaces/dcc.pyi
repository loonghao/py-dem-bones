"""

DCC software integration interface for py-dem-bones.

This module defines an abstract interface that can be implemented by third-party
developers to integrate py-dem-bones with various digital content creation (DCC)
software such as Maya, Blender, or custom 3D applications.
"""
from __future__ import annotations
import abc
from abc import ABC
from abc import abstractmethod
import typing

__all__ = ["ABC", "DCCInterface", "abstractmethod"]

class DCCInterface(abc.ABC):
    """

    Abstract base class for DCC software integration.

    This class defines methods that must be implemented by any class
    that wants to provide integration between py-dem-bones and a specific
    DCC software application.

    """

    __abstractmethods__: typing.ClassVar[
        frozenset
    ]  # value = frozenset({'convert_matrices', 'to_dcc_data', 'from_dcc_data'})
    _abc_impl: typing.ClassVar[_abc._abc_data]  # value = <_abc._abc_data object>
    def apply_coordinate_system_transform(self, data, from_dcc=True):
        """

        Apply coordinate system transformations.

        This is a utility method to handle coordinate system differences
        between DCC software and DemBones. The base implementation is a
        no-op that returns the data unchanged. Subclasses should override
        this method if the DCC software uses a different coordinate system.

        Args:
            data: The data to transform
            from_dcc (bool): If True, transform from DCC to DemBones coordinate system,
                            otherwise transform from DemBones to DCC coordinate system

        Returns:
            The transformed data

        """
    def convert_matrices(self, matrices, from_dcc=True):
        """

        Convert between DCC-specific and DemBones matrix formats.

        Many DCC software applications use different coordinate systems,
        matrix layouts, or conventions than those used by DemBones.
        This method handles the conversion between these formats.

        Args:
            matrices: The matrices to convert
            from_dcc (bool): If True, convert from DCC format to DemBones format,
                            otherwise convert from DemBones format to DCC format

        Returns:
            The converted matrices

        """
    def from_dcc_data(self, **kwargs):
        """

        Import data from DCC software into DemBones.

        This method should convert data structures specific to the DCC software
        into the format required by the DemBones library.

        Args:
            **kwargs: DCC-specific parameters

        Returns:
            bool: True if import was successful

        """
    def to_dcc_data(self, **kwargs):
        """

        Export DemBones data to DCC software.

        This method should convert DemBones data structures into the format
        required by the DCC software.

        Args:
            **kwargs: DCC-specific parameters

        Returns:
            bool: True if export was successful

        """
