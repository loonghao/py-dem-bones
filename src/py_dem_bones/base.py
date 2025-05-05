"""
Python wrapper classes for DemBones and DemBonesExt.

This module provides Python-friendly wrapper classes that enhance the functionality
of the C++ bindings with additional features such as named bones, error handling,
and convenience methods.
"""

# Import standard library modules
from typing import Callable, Optional, Union

# Import third-party modules
import numpy as np

# Import local modules
from py_dem_bones._py_dem_bones import DemBones as _DemBones, DemBonesExt as _DemBonesExt
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
        self._weights_computed = False  # Flag to track if weights have been computed

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
            # If the name already exists, use its index
            if name in self._targets:
                index = self._targets[name]
            else:
                # Otherwise, use the next available index (max of existing indices + 1)
                # This ensures we don't reuse indices that are already in use
                index = self._dem_bones.nS if self._dem_bones.nS > 0 else 0

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

        # We need to maintain a separate bind matrix for each bone
        # Since the C++ binding doesn't support this, we maintain these matrices in Python
        if not hasattr(self, "_bind_matrices"):
            self._bind_matrices = [np.eye(4) for _ in range(self.num_bones)]

        # Ensure we have enough bind matrices
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

        # We need to maintain a separate bind matrix for each bone
        # Since the C++ binding doesn't support this, we maintain these matrices in Python
        if not hasattr(self, "_bind_matrices"):
            self._bind_matrices = [np.eye(4) for _ in range(self.num_bones)]

        # Ensure we have enough bind matrices
        while len(self._bind_matrices) <= bone:
            self._bind_matrices.append(np.eye(4))

        # Update bind matrix
        self._bind_matrices[bone] = matrix.copy()

        # Get current transformation matrix
        transformations = self._dem_bones.get_transformations()

        # If there's no transformation matrix, create a new array
        if transformations.shape[0] == 0:
            self._dem_bones.nF = 1  # Only one frame (bind pose)

            # Create a new transformation matrix array
            # In the C++ binding, we expect a 2D matrix
            # where each 3 rows represent the first 3 rows of a bone's transformation matrix
            flat_transforms = np.zeros((3 * self.num_bones, 4))

            # For each bone, set its transformation matrix
            for b in range(self.num_bones):
                if b < len(self._bind_matrices):
                    # Only copy the first 3 rows, the last row [0,0,0,1] is implicit
                    flat_transforms[b * 3 : (b + 1) * 3, :] = self._bind_matrices[b][
                        :3, :
                    ]
                else:
                    # For bones without a bind matrix, use identity matrix
                    flat_transforms[b * 3 : (b + 1) * 3, :] = np.eye(4)[:3, :]

            # Update transformation matrix in DemBones
            self._dem_bones.set_transformations(flat_transforms)

    def get_weights(self):
        """
        Get the weight matrix.

        Returns:
            numpy.ndarray: The weights matrix with shape [num_bones, num_vertices]
        """
        # If we have cached weights, return them
        if hasattr(self, "_cached_weights") and self._cached_weights is not None:
            return self._cached_weights

        # Check if dimensions are valid
        if self.num_bones <= 0 or self.num_vertices <= 0:
            # Return empty array for invalid dimensions
            return np.zeros((0, 0), dtype=np.float64)

        # Check if compute has been run
        # If not, return zeros with the correct shape
        # This avoids calling C++ code that might access uninitialized memory
        if not hasattr(self, "_weights_computed") or not self._weights_computed:
            # Return zeros with the correct shape
            return np.zeros((self.num_bones, self.num_vertices), dtype=np.float64)

        try:
            # Otherwise get weights from C++ binding
            weights = self._dem_bones.get_weights()

            # Validate the returned weights
            if weights.size == 0:
                # If empty, return properly shaped zero array
                return np.zeros((self.num_bones, self.num_vertices), dtype=np.float64)

            return weights
        except Exception as e:
            # If any error occurs, return zero weights
            print(f"Warning: Error getting weights: {e}")
            return np.zeros((self.num_bones, self.num_vertices), dtype=np.float64)

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

        # Cache weights so get_weights can return the same value
        self._cached_weights = weights.copy()

        # Set flag indicating weights have been set
        self._weights_computed = True

        # Update weights in C++ binding
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
            # Ensure the number of targets is updated when using index directly
            if target_idx >= self._dem_bones.nS:
                self._dem_bones.nS = target_idx + 1

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

        # Check if poses has the expected shape (3D array)
        if len(poses.shape) < 3:
            # If poses is not a 3D array, create a new one
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

        # Convert 3D array to the format expected by C++ binding
        # In C++, we expect a 2D matrix where rows are vertex coordinates and columns are vertex indices
        # We need to reshape [3, num_vertices, num_targets] to [3, num_vertices * num_targets]
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
        # Get transformation matrices from C++ binding
        transforms = self._dem_bones.get_transformations()

        # If there are no transformation matrices, return empty array
        if transforms.shape[0] == 0:
            return np.zeros((0, 4, 4))

        # C++ binding already returns array in [num_frames, 4, 4] format, return directly
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

        # Convert 3D array to C++ binding expected format
        num_frames = transformations.shape[0]
        flat_transforms = np.zeros((num_frames * 3, 4))

        for f in range(num_frames):
            # Only copy the first 3 rows, the last row [0,0,0,1] is implicit
            flat_transforms[f * 3 : f * 3 + 3, :] = transformations[f, :3, :]

        self._dem_bones.set_transformations(flat_transforms)

    def compute(self, callback: Optional[Callable[[float], None]] = None):
        """
        Compute the skinning weights and transformations.

        Args:
            callback (callable, optional): A function to call with progress updates (0.0 to 1.0)

        Returns:
            bool: True if computation succeeded

        Raises:
            ComputationError: If the computation fails
        """
        try:
            # Validate input data before computing
            try:
                self._validate_computation_inputs()
            except ParameterError as e:
                # Wrap ParameterError in ComputationError with 'compute' in the message
                raise ComputationError(f"Cannot compute: {str(e)}")

            # If a callback is provided, we need to monitor progress
            if callback is not None:
                # Get the total number of iterations
                total_iters = self.num_iterations
                if total_iters <= 0:
                    total_iters = 100  # Default if not set

                # Initial progress
                callback(0.0)

                # Start computation
                result = self._dem_bones.compute()

                # Final progress
                callback(1.0)
            else:
                # No callback, just compute
                result = self._dem_bones.compute()

            if not result:
                raise ComputationError("DemBones.compute() returned failure")

            # Clear any cached weights since we've computed new ones
            if hasattr(self, "_cached_weights"):
                delattr(self, "_cached_weights")

            # Set flag indicating weights have been computed
            self._weights_computed = True

            return result
        except ComputationError:
            # Re-raise ComputationError as is
            raise
        except Exception as e:
            # Wrap any other exception in ComputationError
            raise ComputationError(f"Computation failed: {str(e)}")

    def _validate_computation_inputs(self):
        """
        Validate that all required inputs are set before computation.

        Raises:
            ParameterError: If any required inputs are missing or invalid
        """
        # Check number of vertices
        if self.num_vertices <= 0:
            raise ParameterError("Number of vertices must be set and positive")

        # Check rest pose
        rest_pose = self._dem_bones.get_rest_pose()
        if rest_pose.size == 0:
            raise ParameterError("Rest pose must be set before computation")

        # Check animated poses
        animated_poses = self._dem_bones.get_animated_poses()
        if animated_poses.size == 0:
            raise ParameterError(
                "At least one target pose must be set before computation. "
                "Use set_target_vertices() to add target poses."
            )

        # Check number of bones
        if self.num_bones <= 0:
            raise ParameterError("Number of bones must be set and positive")

    def clear(self):
        """Clear all data and reset the computation."""
        self._dem_bones.clear()
        self._bones = {}
        self._targets = {}

        # Clear any cached data
        if hasattr(self, "_cached_weights"):
            delattr(self, "_cached_weights")
        if hasattr(self, "_bind_matrices"):
            delattr(self, "_bind_matrices")

        # Reset computation flags
        self._weights_computed = False

    def export_to_dict(self):
        """
        Export the current state to a dictionary for serialization.

        Returns:
            dict: Dictionary containing all data needed to reconstruct the state
        """
        data = {
            "num_bones": self.num_bones,
            "num_vertices": self.num_vertices,
            "num_iterations": self.num_iterations,
            "max_influences": self.max_influences,
            "weight_smoothness": self.weight_smoothness,
            "bone_names": self.bone_names,
            "target_names": self.target_names,
        }

        # Export weights if available
        try:
            weights = self.get_weights()
            if weights.size > 0:
                data["weights"] = weights.tolist()
        except Exception:  # Catch specific exceptions when possible
            pass

        # Export transformations if available
        try:
            transforms = self.get_transformations()
            if transforms.size > 0:
                data["transformations"] = transforms.tolist()
        except Exception:  # Catch specific exceptions when possible
            pass

        # Export bind matrices if available
        if hasattr(self, "_bind_matrices"):
            data["bind_matrices"] = [m.tolist() for m in self._bind_matrices]

        return data

    def import_from_dict(self, data):
        """
        Import state from a dictionary.

        Args:
            data (dict): Dictionary containing state data

        Returns:
            bool: True if import was successful
        """
        # Clear current state
        self.clear()

        # Set basic parameters
        if "num_bones" in data:
            self.num_bones = data["num_bones"]
        if "num_vertices" in data:
            self.num_vertices = data["num_vertices"]
        if "num_iterations" in data:
            self.num_iterations = data["num_iterations"]
        if "max_influences" in data:
            self.max_influences = data["max_influences"]
        if "weight_smoothness" in data:
            self.weight_smoothness = data["weight_smoothness"]

        # Set bone names
        if "bone_names" in data:
            for i, name in enumerate(data["bone_names"]):
                if name:  # Only set non-empty names
                    self.set_bone_name(name, i)

        # Set target names
        if "target_names" in data:
            for i, name in enumerate(data["target_names"]):
                if name:  # Only set non-empty names
                    self.set_target_name(name, i)

        # Set weights if available
        if "weights" in data:
            weights = np.array(data["weights"])
            self.set_weights(weights)

        # Set transformations if available
        if "transformations" in data:
            transforms = np.array(data["transformations"])
            self.set_transformations(transforms)

        # Set bind matrices if available
        if "bind_matrices" in data:
            self._bind_matrices = [np.array(m) for m in data["bind_matrices"]]

        return True


class DemBonesExtWrapper(DemBonesWrapper):
    """
    Python wrapper for the DemBonesExt C++ class.

    This class extends DemBonesWrapper with additional functionality provided by
    the DemBonesExt C++ class, such as advanced skinning algorithms and hierarchical
    skeleton support.
    """

    def __init__(self):
        """Initialize a new DemBonesExtWrapper instance."""
        super().__init__()
        # Replace the base C++ object with the extended version
        self._dem_bones = _DemBonesExt()
        # Initialize parent-child relationships
        self._parent_map = {}  # Maps bone index to parent bone index

    # Additional properties and methods specific to DemBonesExt

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

    @property
    def parent_bones(self):
        """
        Get the parent bone indices for all bones.

        Returns:
            dict: Dictionary mapping bone indices to their parent bone indices
        """
        return self._parent_map.copy()

    def set_parent_bone(self, bone: Union[str, int], parent: Union[str, int, None]):
        """
        Set the parent bone for a bone.

        Args:
            bone (str or int): The bone name or index
            parent (str, int, or None): The parent bone name or index, or None for root bones

        Returns:
            tuple: (bone_index, parent_index) of the updated relationship
        """
        # Convert bone names to indices if needed
        if isinstance(bone, str):
            bone_idx = self.get_bone_index(bone)
        else:
            bone_idx = bone

        # Validate bone index
        if bone_idx >= self.num_bones:
            raise IndexError(
                f"Bone index {bone_idx} out of range (0-{self.num_bones-1})"
            )

        # Handle parent bone
        if parent is None:
            # Root bone (no parent)
            parent_idx = -1
        elif isinstance(parent, str):
            parent_idx = self.get_bone_index(parent)
        else:
            parent_idx = parent

        # Validate parent index if not a root
        if parent_idx >= self.num_bones:
            raise IndexError(
                f"Parent bone index {parent_idx} out of range (0-{self.num_bones-1})"
            )

        # Check for circular references
        if parent_idx != -1:
            # Temporary map to check for cycles
            temp_map = self._parent_map.copy()
            temp_map[bone_idx] = parent_idx

            # Check for cycles
            current = parent_idx
            visited = set([bone_idx])

            while current != -1:
                if current in visited:
                    raise ValueError(
                        f"Circular parent-child relationship detected for bone {bone_idx}"
                    )
                visited.add(current)
                current = temp_map.get(current, -1)

        # Update parent map
        self._parent_map[bone_idx] = parent_idx

        # Update C++ parent array
        parent_array = np.ones(self.num_bones, dtype=np.int32) * -1
        for b, p in self._parent_map.items():
            if 0 <= b < self.num_bones:
                parent_array[b] = p

        self._dem_bones.parent = parent_array

        return (bone_idx, parent_idx)

    def get_bone_hierarchy(self):
        """
        Get the complete bone hierarchy as a tree structure.

        Returns:
            dict: Nested dictionary representing the bone hierarchy
        """
        # Build a map of parent to children
        children_map = {}
        for bone, parent in self._parent_map.items():
            if parent not in children_map:
                children_map[parent] = []
            children_map[parent].append(bone)

        # Build the tree starting from root bones
        root_bones = children_map.get(-1, [])

        # If no explicit root bones are defined but we have bones,
        # use the first bone as the root
        if not root_bones and self.num_bones > 0:
            root_bones = [0]  # Use bone 0 as the default root

        def build_tree(bone_idx):
            bone_name = (
                self.bone_names[bone_idx]
                if bone_idx < len(self.bone_names)
                else f"Bone_{bone_idx}"
            )
            children = children_map.get(bone_idx, [])
            return {
                "name": bone_name,
                "index": bone_idx,
                "children": [build_tree(child) for child in children],
            }

        return [build_tree(root) for root in root_bones]

    def set_bone_names_with_hierarchy(self, hierarchy):
        """
        Set bone names and hierarchy from a nested structure.

        Args:
            hierarchy (list): List of dictionaries representing the bone hierarchy

        Returns:
            int: Number of bones set
        """
        # Clear existing bones and hierarchy
        self._bones = {}
        self._parent_map = {}

        # Process the hierarchy
        def process_node(node, parent_idx=-1):
            name = node.get("name", f"Bone_{len(self._bones)}")
            bone_idx = self.set_bone_name(name)

            # Set parent relationship
            if parent_idx != -1:
                self.set_parent_bone(bone_idx, parent_idx)

            # Process children
            for child in node.get("children", []):
                process_node(child, bone_idx)

        # Process all root nodes
        for root in hierarchy:
            process_node(root)

        return len(self._bones)

    def export_to_dict(self):
        """
        Export the current state to a dictionary for serialization.

        Returns:
            dict: Dictionary containing all data needed to reconstruct the state
        """
        # Get base class data
        data = super().export_to_dict()

        # Add DemBonesExt specific data
        data["bind_update"] = self.bind_update
        data["parent_map"] = self._parent_map

        # Add bone hierarchy
        data["bone_hierarchy"] = self.get_bone_hierarchy()

        return data

    def import_from_dict(self, data):
        """
        Import state from a dictionary.

        Args:
            data (dict): Dictionary containing state data

        Returns:
            bool: True if import was successful
        """
        # Import base class data
        super().import_from_dict(data)

        # Import DemBonesExt specific data
        if "bind_update" in data:
            self.bind_update = data["bind_update"]

        # Import parent map
        if "parent_map" in data:
            self._parent_map = {}
            for bone, parent in data["parent_map"].items():
                self._parent_map[int(bone)] = int(parent)

            # Update C++ parent array
            parent_array = np.ones(self.num_bones, dtype=np.int32) * -1
            for b, p in self._parent_map.items():
                if 0 <= b < self.num_bones:
                    parent_array[b] = p

            self._dem_bones.parent = parent_array

        # Import bone hierarchy (overrides parent_map if both are present)
        if "bone_hierarchy" in data:
            self.set_bone_names_with_hierarchy(data["bone_hierarchy"])

        return True
