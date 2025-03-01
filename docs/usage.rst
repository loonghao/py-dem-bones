Usage
=====

Basic Usage
----------

Here's a simple example of how to use py-dem-bones:

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

Using DemBonesExt
----------------

For more advanced usage with hierarchical skeletons:

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

Converting Between NumPy and Eigen
--------------------------------

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
