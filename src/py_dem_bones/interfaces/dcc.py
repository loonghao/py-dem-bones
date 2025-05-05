"""
DCC software integration interface for py-dem-bones.

This module defines an abstract interface that can be implemented by third-party
developers to integrate py-dem-bones with various digital content creation (DCC)
software such as Maya, Blender, or custom 3D applications.
"""

# Import standard library modules
# Import built-in modules
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union

# Import third-party modules
import numpy as np

# Import local modules
from py_dem_bones.base import DemBonesExtWrapper, DemBonesWrapper


class DCCInterface(ABC):
    """
    Abstract base class for DCC software integration.

    This class defines methods that must be implemented by any class
    that wants to provide integration between py-dem-bones and a specific
    DCC software application.
    """

    def __init__(
        self, dem_bones: Optional[Union[DemBonesWrapper, DemBonesExtWrapper]] = None
    ):
        """
        Initialize the DCC interface.

        Args:
            dem_bones (DemBonesWrapper or DemBonesExtWrapper, optional):
                The DemBones instance to use. If None, a new instance will be created.
        """
        self._dem_bones = dem_bones

    @property
    def dem_bones(self) -> Union[DemBonesWrapper, DemBonesExtWrapper]:
        """
        Get the DemBones instance.

        Returns:
            DemBonesWrapper or DemBonesExtWrapper: The DemBones instance
        """
        return self._dem_bones

    @dem_bones.setter
    def dem_bones(self, value: Union[DemBonesWrapper, DemBonesExtWrapper]):
        """
        Set the DemBones instance.

        Args:
            value (DemBonesWrapper or DemBonesExtWrapper): The DemBones instance
        """
        self._dem_bones = value

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
    def to_dcc_data(self, **kwargs) -> bool:
        """
        Export DemBones data to DCC software.

        This method should convert DemBones data structures into the format
        required by the DCC software.

        Args:
            **kwargs: DCC-specific parameters

        Returns:
            bool: True if export was successful
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
        return data

    def get_dcc_info(self) -> Dict[str, Any]:
        """
        Get information about the DCC software.

        Returns:
            dict: Dictionary containing information about the DCC software
        """
        return {
            "name": "Unknown DCC",
            "version": "Unknown",
            "coordinate_system": "Unknown",
        }

    def validate_dcc_data(self, **kwargs) -> Tuple[bool, str]:
        """
        Validate DCC data before import.

        Args:
            **kwargs: DCC-specific parameters

        Returns:
            tuple: (is_valid, error_message)
        """
        return True, ""


class BaseDCCInterface(DCCInterface):
    """
    Base implementation of the DCC interface.

    This class provides a simple implementation that can be used as a starting point
    for custom DCC integrations. It assumes a right-handed coordinate system with
    Y-up orientation, which is common in many 3D applications.
    """

    def __init__(
        self, dem_bones: Optional[Union[DemBonesWrapper, DemBonesExtWrapper]] = None
    ):
        """
        Initialize the base DCC interface.

        Args:
            dem_bones (DemBonesWrapper or DemBonesExtWrapper, optional):
                The DemBones instance to use. If None, a new instance will be created.
        """
        super().__init__(dem_bones)

        # Create a new DemBonesExtWrapper if none was provided
        if self._dem_bones is None:
            self._dem_bones = DemBonesExtWrapper()

        # Default coordinate system transformation matrix
        # Identity matrix (no transformation)
        self._coord_transform = np.eye(4)

    def get_dcc_info(self) -> Dict[str, Any]:
        """
        Get information about the DCC software.

        Returns:
            dict: Dictionary containing information about the DCC software
        """
        return {
            "name": "Generic DCC",
            "version": "1.0",
            "coordinate_system": "Right-handed, Y-up",
        }

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
        if self._dem_bones is None:
            return False

        try:
            # Convert coordinate system if needed
            rest_pose = self.apply_coordinate_system_transform(rest_pose, from_dcc=True)
            target_poses = [
                self.apply_coordinate_system_transform(pose, from_dcc=True)
                for pose in target_poses
            ]

            # Set bone names if provided
            if bone_names:
                self._dem_bones.set_bone_names(*bone_names)

            # Set rest pose (transpose to match DemBones format [3, num_vertices])
            self._dem_bones.set_rest_pose(rest_pose.T)

            # Set target poses
            for i, pose in enumerate(target_poses):
                self._dem_bones.set_target_vertices(i, pose.T)

            return True
        except Exception as e:
            print(f"Error importing DCC data: {str(e)}")
            return False

    def to_dcc_data(self, **kwargs) -> Dict[str, Any]:
        """
        Export DemBones data to DCC software.

        Args:
            **kwargs: Additional parameters

        Returns:
            dict: Dictionary containing exported data
        """
        if self._dem_bones is None:
            return {}

        try:
            # Get weights and transformations
            weights = self._dem_bones.get_weights()
            transforms = self._dem_bones.get_transformations()

            # Convert transformations to DCC format
            transforms = self.convert_matrices(transforms, from_dcc=False)

            # Return the data
            return {
                "weights": weights,
                "transformations": transforms,
                "bone_names": self._dem_bones.bone_names,
                "success": True,
            }
        except Exception as e:
            print(f"Error exporting DCC data: {str(e)}")
            return {"success": False, "error": str(e)}

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
        # Apply coordinate system transformation
        if from_dcc:
            # DCC to DemBones
            if len(matrices.shape) == 2 and matrices.shape == (4, 4):
                # Single matrix
                return (
                    self._coord_transform
                    @ matrices
                    @ np.linalg.inv(self._coord_transform)
                )
            elif len(matrices.shape) == 3 and matrices.shape[1:] == (4, 4):
                # Array of matrices
                result = np.zeros_like(matrices)
                for i in range(matrices.shape[0]):
                    result[i] = (
                        self._coord_transform
                        @ matrices[i]
                        @ np.linalg.inv(self._coord_transform)
                    )
                return result
        else:
            # DemBones to DCC
            if len(matrices.shape) == 2 and matrices.shape == (4, 4):
                # Single matrix
                return (
                    np.linalg.inv(self._coord_transform)
                    @ matrices
                    @ self._coord_transform
                )
            elif len(matrices.shape) == 3 and matrices.shape[1:] == (4, 4):
                # Array of matrices
                result = np.zeros_like(matrices)
                for i in range(matrices.shape[0]):
                    result[i] = (
                        np.linalg.inv(self._coord_transform)
                        @ matrices[i]
                        @ self._coord_transform
                    )
                return result

        # If we get here, the input format wasn't recognized
        return matrices

    def set_coordinate_system(self, transform_matrix: np.ndarray):
        """
        Set the coordinate system transformation matrix.

        Args:
            transform_matrix (numpy.ndarray): 4x4 transformation matrix
        """
        if not isinstance(transform_matrix, np.ndarray) or transform_matrix.shape != (
            4,
            4,
        ):
            raise ValueError("Transform matrix must be a 4x4 numpy array")

        self._coord_transform = transform_matrix.copy()
