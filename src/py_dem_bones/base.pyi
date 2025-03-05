"""

Python wrapper classes for DemBones and DemBonesExt.

This module provides Python-friendly wrapper classes that enhance the functionality
of the C++ bindings with additional features such as named bones, error handling,
and convenience methods.
"""
from __future__ import annotations
import numpy as np
from py_dem_bones._py_dem_bones import DemBones as _DemBones
from py_dem_bones._py_dem_bones import DemBonesExt as _DemBonesExt
from py_dem_bones.exceptions import ComputationError
from py_dem_bones.exceptions import IndexError
from py_dem_bones.exceptions import NameError
from py_dem_bones.exceptions import ParameterError

__all__ = [
    "ComputationError",
    "DemBonesExtWrapper",
    "DemBonesWrapper",
    "IndexError",
    "NameError",
    "ParameterError",
    "np",
]

class DemBonesExtWrapper(DemBonesWrapper):
    """

    Python wrapper for the DemBonesExt C++ class.

    This class extends DemBonesWrapper with additional functionality provided by
    the DemBonesExt C++ class, such as advanced skinning algorithms.

    """

    def __init__(self):
        """
        Initialize a new DemBonesExtWrapper instance.
        """
    @property
    def bind_update(self):
        """
        Get the bind update parameter.
        """
    @bind_update.setter
    def bind_update(self, value):
        """
        Set the bind update parameter.
        """

class DemBonesWrapper:
    """

    Python wrapper for the DemBones C++ class.

    This class provides a more Pythonic interface to the C++ DemBones class,
    adding support for named bones, error handling, and convenience methods.

    """

    def __init__(self):
        """
        Initialize a new DemBonesWrapper instance.
        """
    def clear(self):
        """
        Clear all data and reset the computation.
        """
    def compute(self):
        """

        Compute the skinning weights and transformations.

        Returns:
            bool: True if computation succeeded

        Raises:
            ComputationError: If the computation fails

        """
    def get_bind_matrix(self, bone):
        """

        Get the bind matrix for a bone.

        Args:
            bone (str or int): The bone name or index

        Returns:
            numpy.ndarray: The 4x4 bind matrix

        """
    def get_bone_index(self, name):
        """

        Get the index for a bone name.

        Args:
            name (str): The bone name

        Returns:
            int: The bone index

        Raises:
            NameError: If the bone name is not found

        """
    def get_bone_names(self):
        """

        Get all bone names as a list.

        Returns:
            list: List of bone names

        """
    def get_target_index(self, name):
        """

        Get the index for a target name.

        Args:
            name (str): The target name

        Returns:
            int: The target index

        Raises:
            NameError: If the target name is not found

        """
    def get_target_names(self):
        """

        Get all target names as a list.

        Returns:
            list: List of target names

        """
    def get_transformations(self):
        """

        Get the transformation matrices for all bones.

        Returns:
            numpy.ndarray: Array of 4x4 transformation matrices with shape [num_frames, 4, 4]

        """
    def get_weights(self):
        """

        Get the weight matrix.

        Returns:
            numpy.ndarray: The weights matrix with shape [num_bones, num_vertices]

        """
    def set_bind_matrix(self, bone, matrix):
        """

        Set the bind matrix for a bone.

        Args:
            bone (str or int): The bone name or index
            matrix (numpy.ndarray): The 4x4 transform matrix

        """
    def set_bone_name(self, name, index=None):
        """

        Set a bone name to index mapping.

        Args:
            name (str): The bone name
            index (int, optional): The bone index. If None, uses the next available index.

        Returns:
            int: The assigned bone index

        """
    def set_bone_names(self, *names):
        """

        Set multiple bone names at once.

        Args:
            *names: Variable number of bone names

        Returns:
            list: The assigned bone indices

        """
    def set_rest_pose(self, vertices):
        """

        Set the rest pose vertices.

        Args:
            vertices (numpy.ndarray): The rest pose vertices with shape [3, num_vertices]

        """
    def set_target_name(self, name, index=None):
        """

        Set a target name to index mapping.

        Args:
            name (str): The target name
            index (int, optional): The target index. If None, uses the next available index.

        Returns:
            int: The assigned target index

        """
    def set_target_vertices(self, target, vertices):
        """

        Set the vertices for a target pose.

        Args:
            target (str or int): The target name or index
            vertices (numpy.ndarray): The target vertices with shape [3, num_vertices]

        """
    def set_transformations(self, transformations):
        """

        Set the transformation matrices for all bones.

        Args:
            transformations (numpy.ndarray): Array of 4x4 transformation matrices with shape [num_frames, 4, 4]

        """
    def set_weights(self, weights):
        """

        Set the weight matrix.

        Args:
            weights (numpy.ndarray): The weights matrix with shape [num_bones, num_vertices]

        """
    @property
    def bone_names(self):
        """
        Get all bone names as a list, ordered by bone index.
        """
    @property
    def max_influences(self):
        """
        Get the maximum number of non-zero weights per vertex.
        """
    @max_influences.setter
    def max_influences(self, value):
        """
        Set the maximum number of non-zero weights per vertex.
        """
    @property
    def num_bones(self):
        """
        Get the number of bones.
        """
    @num_bones.setter
    def num_bones(self, value):
        """
        Set the number of bones.
        """
    @property
    def num_frames(self):
        """
        Get the number of animation frames.
        """
    @property
    def num_iterations(self):
        """
        Get the total number of iterations.
        """
    @num_iterations.setter
    def num_iterations(self, value):
        """
        Set the total number of iterations.
        """
    @property
    def num_targets(self):
        """
        Get the number of target poses.
        """
    @property
    def num_vertices(self):
        """
        Get the number of vertices.
        """
    @num_vertices.setter
    def num_vertices(self, value):
        """
        Set the number of vertices.
        """
    @property
    def target_names(self):
        """
        Get all target names as a list, ordered by target index.
        """
    @property
    def weight_smoothness(self):
        """
        Get the weight smoothness parameter.
        """
    @weight_smoothness.setter
    def weight_smoothness(self, value):
        """
        Set the weight smoothness parameter.
        """
