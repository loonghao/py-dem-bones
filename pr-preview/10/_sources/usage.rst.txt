Usage
=====

Basic Usage
----------

Here's a simple example of how to use py-dem-bones with the direct C++ bindings:

.. code-block:: python

    import numpy as np
    import py_dem_bones as pdb

    # Create a DemBones instance
    dem_bones = pdb.DemBones()

    # Set parameters
    dem_bones.nIters = 30
    dem_bones.nInitIters = 10
    dem_bones.nTransIters = 5
    dem_bones.nWeightsIters = 3
    dem_bones.nnz = 4
    dem_bones.weightsSmooth = 1e-4

    # Set up data
    # Rest pose vertices (nV x 3)
    rest_pose = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0]
    ], dtype=np.float64)

    # Animated pose vertices (nF * nV x 3)
    animated_poses = np.array([
        # Frame 1
        [0.0, 0.0, 0.0],
        [1.0, 0.1, 0.0],
        [0.0, 1.1, 0.0],
        [0.0, 0.0, 1.0],
        # Frame 2
        [0.0, 0.0, 0.0],
        [1.0, 0.2, 0.0],
        [0.0, 1.2, 0.0],
        [0.0, 0.0, 1.0]
    ], dtype=np.float64)

    # Set data
    dem_bones.nV = 4  # Number of vertices
    dem_bones.nB = 2  # Number of bones
    dem_bones.nF = 2  # Number of frames
    dem_bones.nS = 1  # Number of subjects
    dem_bones.fStart = np.array([0], dtype=np.int32)  # Frame start indices for each subject
    dem_bones.subjectID = np.zeros(2, dtype=np.int32)  # Subject ID for each frame
    dem_bones.u = rest_pose  # Rest pose
    dem_bones.v = animated_poses  # Animated poses

    # Compute skinning decomposition
    dem_bones.compute()

    # Get results
    weights = dem_bones.get_weights()
    transformations = dem_bones.get_transformations()

    print("Skinning weights:")
    print(weights)
    print("\nBone transformations:")
    print(transformations)

Using the Python Wrapper Classes
--------------------------------

For a more Pythonic experience, you can use the wrapper classes that provide enhanced functionality:

.. code-block:: python

    import numpy as np
    import py_dem_bones as pdb

    # Create a DemBonesWrapper instance
    dem_bones = pdb.DemBonesWrapper()

    # Set parameters using Pythonic property names
    dem_bones.num_iterations = 30
    dem_bones.num_init_iterations = 10
    dem_bones.num_transform_iterations = 5
    dem_bones.num_weights_iterations = 3
    dem_bones.max_nonzeros_per_vertex = 4
    dem_bones.weights_smoothness = 1e-4

    # Set up data
    # Rest pose vertices
    rest_pose = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0]
    ], dtype=np.float64)

    # Animated pose vertices
    animated_poses = np.array([
        # Frame 1
        [0.0, 0.0, 0.0],
        [1.0, 0.1, 0.0],
        [0.0, 1.1, 0.0],
        [0.0, 0.0, 1.0],
        # Frame 2
        [0.0, 0.0, 0.0],
        [1.0, 0.2, 0.0],
        [0.0, 1.2, 0.0],
        [0.0, 0.0, 1.0]
    ], dtype=np.float64)

    # Set data with error handling
    try:
        dem_bones.set_rest_pose(rest_pose)
        dem_bones.set_animated_poses(animated_poses)
        dem_bones.set_num_bones(2)
        
        # Optionally, you can name your bones
        dem_bones.set_bone_names(["Root", "Arm"])
        
        # Compute skinning decomposition
        dem_bones.compute()
        
        # Get results with error handling
        weights = dem_bones.get_weights()
        transformations = dem_bones.get_transformations()
        
        print("Skinning weights:")
        print(weights)
        print("\nBone transformations:")
        print(transformations)
        
    except pdb.DemBonesError as e:
        print(f"Error: {e}")

Using DemBonesExt for Hierarchical Skeletons
--------------------------------------------

For more advanced usage with hierarchical skeletons, use the DemBonesExt class:

.. code-block:: python

    import numpy as np
    import py_dem_bones as pdb

    # Create a DemBonesExt instance
    dem_bones_ext = pdb.DemBonesExt()

    # Set parameters (same as DemBones)
    dem_bones_ext.nIters = 30
    dem_bones_ext.nInitIters = 10
    dem_bones_ext.nTransIters = 5
    dem_bones_ext.nWeightsIters = 3
    dem_bones_ext.nnz = 4
    dem_bones_ext.weightsSmooth = 1e-4

    # Set up data (same as DemBones)
    # ...

    # Set additional DemBonesExt data
    dem_bones_ext.parent = np.array([-1, 0], dtype=np.int32)  # Parent bone indices (-1 for root)
    dem_bones_ext.boneName = ["Root", "Child"]  # Bone names
    dem_bones_ext.bindUpdate = 1  # Bind transformation update mode

    # Compute skinning decomposition
    dem_bones_ext.compute()

    # Get results
    weights = dem_bones_ext.get_weights()
    transformations = dem_bones_ext.get_transformations()

    # Compute local rotations and translations
    dem_bones_ext.computeRTB()

    print("Skinning weights:")
    print(weights)
    print("\nBone transformations:")
    print(transformations)

Or use the Python wrapper for DemBonesExt:

.. code-block:: python

    import numpy as np
    import py_dem_bones as pdb

    # Create a DemBonesExtWrapper instance
    dem_bones_ext = pdb.DemBonesExtWrapper()

    # Set parameters
    dem_bones_ext.num_iterations = 30
    dem_bones_ext.num_init_iterations = 10
    dem_bones_ext.num_transform_iterations = 5
    dem_bones_ext.num_weights_iterations = 3
    dem_bones_ext.max_nonzeros_per_vertex = 4
    dem_bones_ext.weights_smoothness = 1e-4

    # Set up data
    # ...

    # Set parent-child relationships
    dem_bones_ext.set_parent_indices([-1, 0])  # -1 means root bone
    dem_bones_ext.set_bone_names(["Root", "Child"])
    dem_bones_ext.bind_update = 1  # Enable bind transformation updates

    # Compute skinning decomposition
    dem_bones_ext.compute()

    # Get results
    weights = dem_bones_ext.get_weights()
    transformations = dem_bones_ext.get_transformations()

    # Compute local rotations and translations
    dem_bones_ext.compute_local_transforms()

    print("Skinning weights:")
    print(weights)
    print("\nBone transformations:")
    print(transformations)

Converting Between NumPy and Eigen
----------------------------------

py-dem-bones provides utility functions to convert between NumPy arrays and Eigen matrices:

.. code-block:: python

    import numpy as np
    import py_dem_bones as pdb

    # Create a NumPy array
    arr = np.array([[1.0, 2.0], [3.0, 4.0]])

    # Convert to Eigen-compatible format
    eigen_arr = pdb.numpy_to_eigen(arr)

    # Convert back to NumPy with reshaping
    reshaped = pdb.eigen_to_numpy(eigen_arr, shape=(4,))
    print(reshaped)  # [1.0, 2.0, 3.0, 4.0]

Error Handling
--------------

The library provides comprehensive error handling through custom exception classes:

.. code-block:: python

    import py_dem_bones as pdb

    try:
        # Create an instance
        dem_bones = pdb.DemBonesWrapper()
        
        # Set invalid parameters
        dem_bones.num_bones = -1  # This will raise an error
        
    except pdb.ParameterError as e:
        print(f"Parameter error: {e}")
    except pdb.ComputationError as e:
        print(f"Computation error: {e}")
    except pdb.IndexError as e:
        print(f"Index error: {e}")
    except pdb.DemBonesError as e:
        print(f"General error: {e}")

Advanced Configuration
----------------------

Fine-tuning the skinning decomposition parameters:

.. code-block:: python

    import py_dem_bones as pdb

    dem_bones = pdb.DemBonesWrapper()
    
    # Basic parameters
    dem_bones.num_iterations = 30
    dem_bones.num_init_iterations = 10
    dem_bones.num_transform_iterations = 5
    dem_bones.num_weights_iterations = 3
    
    # Advanced parameters
    dem_bones.max_nonzeros_per_vertex = 4  # Maximum number of non-zero weights per vertex
    dem_bones.weights_smoothness = 1e-4  # Smoothness regularization term
    dem_bones.enable_bind_update = True  # Enable bind pose transformation updates
    dem_bones.enable_joint_constraints = True  # Enable joint constraints
    
    # Set weight constraints
    dem_bones.set_weight_constraints(np.zeros((4, 2)), np.ones((4, 2)))
    
    # Set transformation constraints
    dem_bones.set_transformation_constraints(np.eye(4), np.eye(4))
