"""
Python wrapper classes for DemBones and DemBonesExt.

This module provides Python-friendly wrapper classes that enhance the functionality
of the C++ bindings with additional features such as named bones, error handling,
and convenience methods.
"""

# Import third-party modules
import numpy as np

# Import local modules
from py_dem_bones._py_dem_bones import DemBones as _DemBones
from py_dem_bones._py_dem_bones import DemBonesExt as _DemBonesExt
from py_dem_bones.exceptions import ComputationError, IndexError, NameError, ParameterError


class DemBonesWrapper:
    """
    Python wrapper for the DemBones C++ class.

    This class provides a more Pythonic interface to the C++ DemBones class,
    adding support for named bones, error handling, and convenience methods.
    """

    def __init__(self):
        """Initialize a new DemBonesWrapper instance."""
        self._dem_bones = _DemBones()
        self._bones = {}  # Mapping of bone names to indices
        self._targets = {}  # Mapping of target names to indices

    # Basic properties (delegated to C++ object)

    @property
    def num_bones(self):
        """Get the number of bones."""
        return self._dem_bones.nB

    @num_bones.setter
    def num_bones(self, value):
        """Set the number of bones."""
        if not isinstance(value, int) or value <= 0:
            raise ParameterError("Number of bones must be a positive integer")
        self._dem_bones.nB = value

    @property
    def num_vertices(self):
        """Get the number of vertices."""
        return self._dem_bones.nV

    @num_vertices.setter
    def num_vertices(self, value):
        """Set the number of vertices."""
        if not isinstance(value, int) or value <= 0:
            raise ParameterError("Number of vertices must be a positive integer")
        self._dem_bones.nV = value

    @property
    def num_frames(self):
        """Get the number of animation frames."""
        return self._dem_bones.nF

    @property
    def num_targets(self):
        """Get the number of target poses."""
        return self._dem_bones.nS

    # Algorithm parameters

    @property
    def num_iterations(self):
        """Get the total number of iterations."""
        return self._dem_bones.nIters

    @num_iterations.setter
    def num_iterations(self, value):
        """Set the total number of iterations."""
        if not isinstance(value, int) or value < 0:
            raise ParameterError("Number of iterations must be a non-negative integer")
        self._dem_bones.nIters = value

    @property
    def weight_smoothness(self):
        """Get the weight smoothness parameter."""
        return self._dem_bones.weightsSmooth

    @weight_smoothness.setter
    def weight_smoothness(self, value):
        """Set the weight smoothness parameter."""
        if value < 0:
            raise ParameterError("Weight smoothness must be non-negative")
        self._dem_bones.weightsSmooth = value

    @property
    def max_influences(self):
        """Get the maximum number of non-zero weights per vertex."""
        return self._dem_bones.nnz

    @max_influences.setter
    def max_influences(self, value):
        """Set the maximum number of non-zero weights per vertex."""
        if not isinstance(value, int) or value <= 0:
            raise ParameterError("Maximum influences must be a positive integer")
        self._dem_bones.nnz = value

    # Bone name management

    @property
    def bone_names(self):
        """Get all bone names as a list, ordered by bone index."""
        result = [""] * self.num_bones
        for name, idx in self._bones.items():
            if 0 <= idx < len(result):
                result[idx] = name
        return result

    def get_bone_names(self):
        """
        Get all bone names as a list.

        Returns:
            list: List of bone names
        """
        return list(self._bones.keys())

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
        if name not in self._bones:
            raise NameError(f"Bone name '{name}' not found")
        return self._bones[name]

    def set_bone_name(self, name, index=None):
        """
        Set a bone name to index mapping.

        Args:
            name (str): The bone name
            index (int, optional): The bone index. If None, uses the next available index.

        Returns:
            int: The assigned bone index
        """
        if index is None:
            index = self._bones.get(name, self.num_bones)

        if index >= self.num_bones:
            self.num_bones = index + 1

        # Remove any existing associations for this index
        for key in list(self._bones):
            if self._bones[key] == index:
                self._bones.pop(key)

        self._bones[name] = index
        return index

    def set_bone_names(self, *names):
        """
        Set multiple bone names at once.

        Args:
            *names: Variable number of bone names

        Returns:
            list: The assigned bone indices
        """
        indices = []
        for i, name in enumerate(names):
            indices.append(self.set_bone_name(name, i))
        return indices

    # Target name management

    @property
    def target_names(self):
        """Get all target names as a list, ordered by target index."""
        result = [""] * self.num_targets
        for name, idx in self._targets.items():
            if 0 <= idx < len(result):
                result[idx] = name
        return result

    def get_target_names(self):
        """
        Get all target names as a list.

        Returns:
            list: List of target names
        """
        return list(self._targets.keys())

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
        if name not in self._targets:
            raise NameError(f"Target name '{name}' not found")
        return self._targets[name]

    def set_target_name(self, name, index=None):
        """
        Set a target name to index mapping.

        Args:
            name (str): The target name
            index (int, optional): The target index. If None, uses the next available index.

        Returns:
            int: The assigned target index
        """
        if index is None:
            index = self._targets.get(name, len(self._targets))

        # Update the number of shapes if needed
        if index >= self._dem_bones.nS:
            self._dem_bones.nS = index + 1

        # Remove any existing associations for this index
        for key in list(self._targets):
            if self._targets[key] == index:
                self._targets.pop(key)

        self._targets[name] = index
        return index

    # Matrix operations

    def get_bind_matrix(self, bone):
        """
        Get the bind matrix for a bone.

        Args:
            bone (str or int): The bone name or index

        Returns:
            numpy.ndarray: The 4x4 bind matrix
        """
        if isinstance(bone, str):
            try:
                bone = self.get_bone_index(bone)
            except NameError as e:
                raise NameError(str(e))

        if bone >= self.num_bones:
            raise IndexError(f"Bone index {bone} out of range (0-{self.num_bones-1})")

        # 我们需要为每个骨骼维护一个单独的绑定矩阵
        # 由于 C++ 绑定不支持这一点，我们在 Python 端维护这些矩阵
        if not hasattr(self, "_bind_matrices"):
            self._bind_matrices = [np.eye(4) for _ in range(self.num_bones)]

        # 确保我们有足够的绑定矩阵
        while len(self._bind_matrices) <= bone:
            self._bind_matrices.append(np.eye(4))

        return self._bind_matrices[bone]

    def set_bind_matrix(self, bone, matrix):
        """
        Set the bind matrix for a bone.

        Args:
            bone (str or int): The bone name or index
            matrix (numpy.ndarray): The 4x4 transform matrix
        """
        if isinstance(bone, str):
            try:
                bone = self.get_bone_index(bone)
            except NameError as e:
                raise NameError(str(e))

        if bone >= self.num_bones:
            raise IndexError(f"Bone index {bone} out of range (0-{self.num_bones-1})")

        # Ensure the matrix is 4x4
        if not isinstance(matrix, np.ndarray) or matrix.shape != (4, 4):
            raise ParameterError("Matrix must be a 4x4 numpy array")

        # 我们需要为每个骨骼维护一个单独的绑定矩阵
        # 由于 C++ 绑定不支持这一点，我们在 Python 端维护这些矩阵
        if not hasattr(self, "_bind_matrices"):
            self._bind_matrices = [np.eye(4) for _ in range(self.num_bones)]

        # 确保我们有足够的绑定矩阵
        while len(self._bind_matrices) <= bone:
            self._bind_matrices.append(np.eye(4))

        # 更新绑定矩阵
        self._bind_matrices[bone] = matrix.copy()

        # 获取当前变换矩阵
        transformations = self._dem_bones.get_transformations()

        # 如果没有变换矩阵，创建一个新的数组
        if transformations.shape[0] == 0:
            self._dem_bones.nF = 1  # 只有一帧（绑定姿势）

            # 创建一个新的变换矩阵数组
            # 在 C++ 绑定中，我们期望一个 2D 矩阵
            # 其中每 3 行表示一个骨骼的前 3 行变换矩阵
            flat_transforms = np.zeros((3 * self.num_bones, 4))

            # 对于每个骨骼，设置其变换矩阵
            for b in range(self.num_bones):
                if b < len(self._bind_matrices):
                    # 只复制前 3 行，最后一行 [0,0,0,1] 是隐含的
                    flat_transforms[b * 3 : (b + 1) * 3, :] = self._bind_matrices[b][
                        :3, :
                    ]
                else:
                    # 对于没有绑定矩阵的骨骼，使用单位矩阵
                    flat_transforms[b * 3 : (b + 1) * 3, :] = np.eye(4)[:3, :]

            # 更新 DemBones 中的变换矩阵
            self._dem_bones.set_transformations(flat_transforms)

    def get_weights(self):
        """
        Get the weight matrix.

        Returns:
            numpy.ndarray: The weights matrix with shape [num_bones, num_vertices]
        """
        # 如果我们有缓存的权重，返回它
        if hasattr(self, "_cached_weights") and self._cached_weights is not None:
            return self._cached_weights

        # 否则从 C++ 绑定获取权重
        weights = self._dem_bones.get_weights()
        return weights

    def set_weights(self, weights):
        """
        Set the weight matrix.

        Args:
            weights (numpy.ndarray): The weights matrix with shape [num_bones, num_vertices]
        """
        if not isinstance(weights, np.ndarray):
            try:
                weights = np.asarray(weights)
            except ValueError as e:
                raise ParameterError(
                    f"Failed to convert weights to numpy array: {str(e)}"
                )

        # Check dimensions
        if len(weights.shape) != 2:
            raise ParameterError(
                f"Weights must be a 2D array, got shape {weights.shape}"
            )

        # Update the number of bones if needed
        if weights.shape[0] > self.num_bones:
            self.num_bones = weights.shape[0]

        # Process weights to ensure they are valid
        weights = np.clip(weights, 0.0, 1.0)

        # Normalize weights
        sums = np.sum(weights, axis=0)
        mask = sums > 0
        if np.any(mask):
            weights[:, mask] = weights[:, mask] / sums[mask]

        # 缓存权重，以便 get_weights 可以返回相同的值
        self._cached_weights = weights.copy()

        # 更新 C++ 绑定中的权重
        self._dem_bones.set_weights(weights)

    def set_rest_pose(self, vertices):
        """
        Set the rest pose vertices.

        Args:
            vertices (numpy.ndarray): The rest pose vertices with shape [3, num_vertices]
        """
        if not isinstance(vertices, np.ndarray):
            try:
                vertices = np.asarray(vertices)
            except ValueError as e:
                raise ParameterError(
                    f"Failed to convert vertices to numpy array: {str(e)}"
                )

        # Check dimensions
        if len(vertices.shape) != 2 or vertices.shape[0] != 3:
            raise ParameterError(
                f"Rest pose must be a 2D array with shape [3, num_vertices], "
                f"got {vertices.shape}"
            )

        # Update the number of vertices if needed
        if vertices.shape[1] != self.num_vertices:
            self.num_vertices = vertices.shape[1]

        self._dem_bones.set_rest_pose(vertices)

    def set_target_vertices(self, target, vertices):
        """
        Set the vertices for a target pose.

        Args:
            target (str or int): The target name or index
            vertices (numpy.ndarray): The target vertices with shape [3, num_vertices]
        """
        if isinstance(target, str):
            target_idx = self.set_target_name(target)
        else:
            target_idx = target

        if not isinstance(vertices, np.ndarray):
            try:
                vertices = np.asarray(vertices)
            except ValueError as e:
                raise ParameterError(
                    f"Failed to convert vertices to numpy array: {str(e)}"
                )

        # Check dimensions
        if len(vertices.shape) != 2 or vertices.shape[0] != 3:
            raise ParameterError(
                f"Target vertices must be a 2D array with shape [3, num_vertices], "
                f"got {vertices.shape}"
            )

        # Update the number of vertices if needed
        if vertices.shape[1] > self.num_vertices:
            self.num_vertices = vertices.shape[1]

        # Get current animated poses
        poses = self._dem_bones.get_animated_poses()

        # If no poses yet, create a new array
        if poses.size == 0:
            num_targets = max(self._dem_bones.nS, target_idx + 1)
            num_vertices = vertices.shape[1]
            poses = np.zeros((3, num_vertices, num_targets))

        # Ensure poses array is large enough
        if target_idx >= poses.shape[2]:
            new_poses = np.zeros((3, poses.shape[1], target_idx + 1))
            new_poses[:, :, : poses.shape[2]] = poses
            poses = new_poses

        # Update the target pose
        poses[:, :, target_idx] = vertices

        # 将 3D 数组转换为 C++ 绑定期望的格式
        # 在 C++ 中，我们期望一个 2D 矩阵，其中行是顶点坐标，列是顶点索引
        # 我们需要将 [3, num_vertices, num_targets] 重塑为 [3, num_vertices * num_targets]
        num_vertices = poses.shape[1]
        num_targets = poses.shape[2]
        flat_poses = np.zeros((3, num_vertices * num_targets))

        for t in range(num_targets):
            flat_poses[:, t * num_vertices : (t + 1) * num_vertices] = poses[:, :, t]

        # Update animated poses in DemBones
        self._dem_bones.set_animated_poses(flat_poses)

    def get_transformations(self):
        """
        Get the transformation matrices for all bones.

        Returns:
            numpy.ndarray: Array of 4x4 transformation matrices with shape [num_frames, 4, 4]
        """
        # 获取 C++ 绑定中的变换矩阵
        transforms = self._dem_bones.get_transformations()

        # 如果没有变换矩阵，返回空数组
        if transforms.shape[0] == 0:
            return np.zeros((0, 4, 4))

        # C++ 绑定已经返回了 [num_frames, 4, 4] 格式的数组，直接返回
        return transforms

    def set_transformations(self, transformations):
        """
        Set the transformation matrices for all bones.

        Args:
            transformations (numpy.ndarray): Array of 4x4 transformation matrices with shape [num_frames, 4, 4]
        """
        if not isinstance(transformations, np.ndarray):
            try:
                transformations = np.asarray(transformations)
            except ValueError as e:
                raise ParameterError(
                    f"Failed to convert transformations to numpy array: {str(e)}"
                )

        # Check dimensions
        if len(transformations.shape) != 3 or transformations.shape[1:] != (4, 4):
            raise ParameterError(
                f"Transformations must have shape [num_frames, 4, 4], got {transformations.shape}"
            )

        # Update the number of frames if needed
        if transformations.shape[0] > self.num_frames:
            self._dem_bones.nF = transformations.shape[0]

        # 将 3D 数组转换为 C++ 绑定期望的格式
        num_frames = transformations.shape[0]
        flat_transforms = np.zeros((num_frames * 3, 4))

        for f in range(num_frames):
            # 只复制前 3 行，最后一行 [0,0,0,1] 是隐含的
            flat_transforms[f * 3 : f * 3 + 3, :] = transformations[f, :3, :]

        self._dem_bones.set_transformations(flat_transforms)

    def compute(self):
        """
        Compute the skinning weights and transformations.

        Returns:
            bool: True if computation succeeded

        Raises:
            ComputationError: If the computation fails
        """
        try:
            result = self._dem_bones.compute()
            if not result:
                raise ComputationError("DemBones.compute() returned failure")
            return result
        except Exception as e:
            raise ComputationError(f"Computation failed: {str(e)}")

    def clear(self):
        """Clear all data and reset the computation."""
        self._dem_bones.clear()
        self._bones = {}
        self._targets = {}


class DemBonesExtWrapper(DemBonesWrapper):
    """
    Python wrapper for the DemBonesExt C++ class.

    This class extends DemBonesWrapper with additional functionality provided by
    the DemBonesExt C++ class, such as advanced skinning algorithms.
    """

    def __init__(self):
        """Initialize a new DemBonesExtWrapper instance."""
        super().__init__()
        # Replace the base C++ object with the extended version
        self._dem_bones = _DemBonesExt()

    # Additional properties and methods specific to DemBonesExt
    # can be added here as the C++ bindings evolve

    @property
    def bind_update(self):
        """Get the bind update parameter."""
        return self._dem_bones.bindUpdate

    @bind_update.setter
    def bind_update(self, value):
        """Set the bind update parameter."""
        if not isinstance(value, int) or value < 0:
            raise ParameterError("Bind update must be a non-negative integer")
        self._dem_bones.bindUpdate = value
