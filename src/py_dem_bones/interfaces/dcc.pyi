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
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from py_dem_bones.base import DemBonesWrapper, DemBonesExtWrapper

__all__ = ["ABC", "DCCInterface", "BaseDCCInterface", "abstractmethod"]

class DCCInterface(abc.ABC):
    """
    Abstract base class for DCC software integration.

    This class defines methods that must be implemented by any class
    that wants to provide integration between py-dem-bones and a specific
    DCC software application.
    """

    # ABC implementation details
    __abstractmethods__: typing.ClassVar[frozenset]

    def __init__(
        self, dem_bones: Optional[Union[DemBonesWrapper, DemBonesExtWrapper]] = None
    ) -> None:
        """
        Initialize the DCC interface.

        Args:
            dem_bones (DemBonesWrapper or DemBonesExtWrapper, optional):
                The DemBones instance to use. If None, a new instance will be created.
        """
    @property
    def dem_bones(self) -> Union[DemBonesWrapper, DemBonesExtWrapper]:
        """
        Get the DemBones instance.

        Returns:
            DemBonesWrapper or DemBonesExtWrapper: The DemBones instance
        """
    @dem_bones.setter
    def dem_bones(self, value: Union[DemBonesWrapper, DemBonesExtWrapper]) -> None:
        """
        Set the DemBones instance.

        Args:
            value (DemBonesWrapper or DemBonesExtWrapper): The DemBones instance
        """
    def apply_coordinate_system_transform(
        self, data: np.ndarray, from_dcc: bool = True
    ) -> np.ndarray:
        """
        Apply coordinate system transformations.

        This is a utility method to handle coordinate system differences
        between DCC software and DemBones. The base implementation is a
        no-op that returns the data unchanged. Subclasses should override
        this method if the DCC software uses a different coordinate system.

        Args:
            data (numpy.ndarray): The data to transform
            from_dcc (bool): If True, transform from DCC to DemBones coordinate system,
                            otherwise transform from DemBones to DCC coordinate system

        Returns:
            numpy.ndarray: The transformed data
        """
    @abstractmethod
    def convert_matrices(
        self, matrices: np.ndarray, from_dcc: bool = True
    ) -> np.ndarray:
        """
        Convert between DCC-specific and DemBones matrix formats.

        Many DCC software applications use different coordinate systems,
        matrix layouts, or conventions than those used by DemBones.
        This method handles the conversion between these formats.

        Args:
            matrices (numpy.ndarray): The matrices to convert
            from_dcc (bool): If True, convert from DCC format to DemBones format,
                            otherwise convert from DemBones format to DCC format

        Returns:
            numpy.ndarray: The converted matrices
        """
    @abstractmethod
    def from_dcc_data(self, **kwargs) -> bool:
        """
        Import data from DCC software into DemBones.

        This method should convert data structures specific to the DCC software
        into the format required by the DemBones library.

        Args:
            **kwargs: DCC-specific parameters

        Returns:
            bool: True if import was successful
        """
    @abstractmethod
    def to_dcc_data(self, **kwargs) -> Dict[str, Any]:
        """
        Export DemBones data to DCC software.

        This method should convert DemBones data structures into the format
        required by the DCC software.

        Args:
            **kwargs: DCC-specific parameters

        Returns:
            dict: Dictionary containing exported data
        """
    def get_dcc_info(self) -> Dict[str, Any]:
        """
        Get information about the DCC software.

        Returns:
            dict: Dictionary containing information about the DCC software
        """
    def validate_dcc_data(self, **kwargs) -> Tuple[bool, str]:
        """
        Validate DCC data before import.

        Args:
            **kwargs: DCC-specific parameters

        Returns:
            tuple: (is_valid, error_message)
        """

class BaseDCCInterface(DCCInterface):
    """
    Base implementation of the DCC interface.

    This class provides a simple implementation that can be used as a starting point
    for custom DCC integrations. It assumes a right-handed coordinate system with
    Y-up orientation, which is common in many 3D applications.
    """

    def __init__(
        self, dem_bones: Optional[Union[DemBonesWrapper, DemBonesExtWrapper]] = None
    ) -> None:
        """
        Initialize the base DCC interface.

        Args:
            dem_bones (DemBonesWrapper or DemBonesExtWrapper, optional):
                The DemBones instance to use. If None, a new instance will be created.
        """
    def get_dcc_info(self) -> Dict[str, Any]:
        """
        Get information about the DCC software.

        Returns:
            dict: Dictionary containing information about the DCC software
        """
    def from_dcc_data(
        self,
        rest_pose: np.ndarray,
        target_poses: List[np.ndarray],
        bone_names: Optional[List[str]] = None,
        **kwargs,
    ) -> bool:
        """
        Import data from DCC software into DemBones.

        Args:
            rest_pose (numpy.ndarray): Rest pose vertices with shape [num_vertices, 3]
            target_poses (list): List of target pose vertices, each with shape [num_vertices, 3]
            bone_names (list, optional): List of bone names
            **kwargs: Additional parameters

        Returns:
            bool: True if import was successful
        """
    def to_dcc_data(self, **kwargs) -> Dict[str, Any]:
        """
        Export DemBones data to DCC software.

        Args:
            **kwargs: Additional parameters

        Returns:
            dict: Dictionary containing exported data
        """
    def convert_matrices(
        self, matrices: np.ndarray, from_dcc: bool = True
    ) -> np.ndarray:
        """
        Convert between DCC-specific and DemBones matrix formats.

        Args:
            matrices (numpy.ndarray): The matrices to convert
            from_dcc (bool): If True, convert from DCC format to DemBones format,
                            otherwise convert from DemBones format to DCC format

        Returns:
            numpy.ndarray: The converted matrices
        """
    def set_coordinate_system(self, transform_matrix: np.ndarray) -> None:
        """
        Set the coordinate system transformation matrix.

        Args:
            transform_matrix (numpy.ndarray): 4x4 transformation matrix
        """
