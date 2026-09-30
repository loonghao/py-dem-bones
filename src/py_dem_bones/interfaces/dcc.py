"""
DCC software integration interface for py-dem-bones.

This module defines an abstract interface that can be implemented by third-party
developers to integrate py-dem-bones with various digital content creation (DCC)
software such as Maya, Blender, or custom 3D applications.
"""

# Import standard library modules
# Import built-in modules
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

# Import third-party modules
import numpy as np

# Import local modules
from py_dem_bones.base import DemBonesExtWrapper, DemBonesWrapper
from py_dem_bones.portable import CoordinateSystem


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
    def to_dcc_data(self, **kwargs) -> Dict[str, Any]:
        """
        Export DemBones data to DCC software.

        This method should convert DemBones data structures into the format
        required by the DCC software.

        Args:
            **kwargs: DCC-specific parameters

        Returns:
            dict: Exported data, including a success flag
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
        self._coordinates = CoordinateSystem(self._coord_transform)
        self._import_succeeded = False

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
        *,
        faces: Optional[Sequence[Sequence[int]]] = None,
        bone_count: Optional[int] = None,
        **kwargs,
    ) -> bool:
        """
        Import data from DCC software into DemBones.

        Args:
            rest_pose (numpy.ndarray): Rest pose vertices with shape [num_vertices, 3]
            target_poses (list): List of target pose vertices, each with shape [num_vertices, 3]
            bone_names (list, optional): List of bone names
            faces (sequence, optional): Polygon vertex indices; required for multiple bones.
            bone_count (int, optional): Requested bones. Defaults to the names count or
                the existing wrapper's bone count.
            **kwargs: Additional parameters

        Returns:
            bool: True if import was successful
        """
        self._import_succeeded = False
        if self._dem_bones is None:
            return False

        try:
            rest_pose = self.apply_coordinate_system_transform(rest_pose, from_dcc=True)
            target_poses = self.apply_coordinate_system_transform(np.asarray(target_poses), from_dcc=True)
            self._dem_bones.set_mesh_sequence(
                rest_pose,
                target_poses,
                bone_count=bone_count,
                bone_names=bone_names,
                faces=faces,
            )
            self._import_succeeded = True
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
            if not self._import_succeeded:
                raise RuntimeError("Import a mesh sequence using the current coordinate system before exporting")
            result = self._dem_bones.get_skinning_result()
            transforms = self.convert_matrices(result.transforms, from_dcc=False)

            # Return the data
            return {
                "weights": result.weights,
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
        if from_dcc:
            return self._coordinates.transforms_to_solver(matrices)
        return self._coordinates.transforms_to_host(matrices)

    def apply_coordinate_system_transform(
        self, data: np.ndarray, from_dcc: bool = True
    ) -> np.ndarray:
        """Convert points ``(V, 3)`` or a complete sequence ``(F, V, 3)``."""
        if from_dcc:
            return self._coordinates.points_to_solver(data)
        return self._coordinates.points_to_host(data)

    def set_coordinate_system(self, transform_matrix: np.ndarray):
        """
        Set the coordinate system transformation matrix.

        Changing the basis invalidates the import; reimport the mesh sequence
        and compute again before exporting.

        Args:
            transform_matrix (numpy.ndarray): 4x4 transformation matrix
        """
        if not isinstance(transform_matrix, np.ndarray) or transform_matrix.shape != (
            4,
            4,
        ):
            raise ValueError("Transform matrix must be a 4x4 numpy array")

        coordinates = CoordinateSystem(transform_matrix)
        if not np.array_equal(self._coord_transform, transform_matrix):
            self._import_succeeded = False
        self._coord_transform = transform_matrix.copy()
        self._coordinates = coordinates
