Examples
========

Here are some examples of how to use py-dem-bones in various scenarios.

Basic Skinning Decomposition
---------------------------

This example demonstrates how to perform basic skinning decomposition on a simple mesh:

.. code-block:: python

    import numpy as np
    import py_dem_bones as pdb

    # Create a simple cube mesh
    def create_cube():
        vertices = np.array([
            [-1, -1, -1],  # 0
            [ 1, -1, -1],  # 1
            [ 1,  1, -1],  # 2
            [-1,  1, -1],  # 3
            [-1, -1,  1],  # 4
            [ 1, -1,  1],  # 5
            [ 1,  1,  1],  # 6
            [-1,  1,  1]   # 7
        ], dtype=np.float64)
        
        return vertices

    # Create a deformed cube by stretching it along the y-axis
    def create_deformed_cube(scale_y):
        vertices = create_cube()
        deformed = vertices.copy()
        deformed[:, 1] *= scale_y
        return deformed

    # Create rest pose and animated poses
    rest_pose = create_cube()
    animated_poses = np.vstack([
        create_deformed_cube(1.2),  # Frame 1
        create_deformed_cube(1.5),  # Frame 2
        create_deformed_cube(1.8)   # Frame 3
    ])

    # Create DemBones instance
    dem_bones = pdb.DemBones()

    # Set parameters
    dem_bones.nIters = 20
    dem_bones.nInitIters = 10
    dem_bones.nTransIters = 5
    dem_bones.nWeightsIters = 3
    dem_bones.nnz = 4
    dem_bones.weightsSmooth = 1e-4

    # Set data
    dem_bones.nV = 8  # 8 vertices in a cube
    dem_bones.nB = 2  # 2 bones
    dem_bones.nF = 3  # 3 frames
    dem_bones.nS = 1  # 1 subject
    dem_bones.fStart = np.array([0], dtype=np.int32)
    dem_bones.subjectID = np.zeros(3, dtype=np.int32)
    dem_bones.u = rest_pose
    dem_bones.v = animated_poses

    # Compute skinning decomposition
    dem_bones.compute()

    # Get results
    weights = dem_bones.get_weights()
    transformations = dem_bones.get_transformations()

    print("Skinning weights:")
    print(weights)
    print("\nBone transformations:")
    print(transformations)

Working with Hierarchical Skeletons
----------------------------------

This example shows how to use DemBonesExt for hierarchical skeletons:

.. code-block:: python

    import numpy as np
    import py_dem_bones as pdb

    # Create a simple articulated mesh (two connected boxes)
    def create_articulated_mesh():
        # First box: vertices 0-7
        box1 = np.array([
            [-2, -1, -1],
            [-1, -1, -1],
            [-1,  1, -1],
            [-2,  1, -1],
            [-2, -1,  1],
            [-1, -1,  1],
            [-1,  1,  1],
            [-2,  1,  1]
        ], dtype=np.float64)
        
        # Second box: vertices 8-15
        box2 = np.array([
            [ 1, -1, -1],
            [ 2, -1, -1],
            [ 2,  1, -1],
            [ 1,  1, -1],
            [ 1, -1,  1],
            [ 2, -1,  1],
            [ 2,  1,  1],
            [ 1,  1,  1]
        ], dtype=np.float64)
        
        return np.vstack([box1, box2])

    # Create a deformed articulated mesh by rotating the second box
    def create_deformed_articulated_mesh(angle_deg):
        vertices = create_articulated_mesh()
        angle_rad = np.radians(angle_deg)
        
        # Keep the first box fixed
        deformed = vertices.copy()
        
        # Rotate the second box around the y-axis
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)
        
        for i in range(8, 16):
            x, z = vertices[i, 0], vertices[i, 2]
            deformed[i, 0] = x * cos_a - z * sin_a
            deformed[i, 2] = x * sin_a + z * cos_a
        
        return deformed

    # Create rest pose and animated poses
    rest_pose = create_articulated_mesh()
    animated_poses = np.vstack([
        create_deformed_articulated_mesh(15),  # Frame 1
        create_deformed_articulated_mesh(30),  # Frame 2
        create_deformed_articulated_mesh(45)   # Frame 3
    ])

    # Create DemBonesExt instance
    dem_bones_ext = pdb.DemBonesExt()

    # Set parameters
    dem_bones_ext.nIters = 20
    dem_bones_ext.nInitIters = 10
    dem_bones_ext.nTransIters = 5
    dem_bones_ext.nWeightsIters = 3
    dem_bones_ext.nnz = 4
    dem_bones_ext.weightsSmooth = 1e-4

    # Set data
    dem_bones_ext.nV = 16  # 16 vertices in the articulated mesh
    dem_bones_ext.nB = 2   # 2 bones
    dem_bones_ext.nF = 3   # 3 frames
    dem_bones_ext.nS = 1   # 1 subject
    dem_bones_ext.fStart = np.array([0], dtype=np.int32)
    dem_bones_ext.subjectID = np.zeros(3, dtype=np.int32)
    dem_bones_ext.u = rest_pose
    dem_bones_ext.v = animated_poses

    # Set hierarchical skeleton data
    dem_bones_ext.parent = np.array([-1, 0], dtype=np.int32)  # Bone 1 is the child of Bone 0
    dem_bones_ext.boneName = ["Box1", "Box2"]
    dem_bones_ext.bindUpdate = 1

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

Converting Blendshapes to LBS
----------------------------

This example demonstrates how to convert blendshapes to linear blend skinning:

.. code-block:: python

    import numpy as np
    import py_dem_bones as pdb

    # Create a simple face mesh with blendshapes
    def create_face_mesh():
        # Simplified face mesh with 9 vertices
        vertices = np.array([
            [0, 0, 0],    # Center
            [-1, 1, 0],   # Top left
            [0, 1, 0],    # Top center
            [1, 1, 0],    # Top right
            [-1, 0, 0],   # Middle left
            [1, 0, 0],    # Middle right
            [-1, -1, 0],  # Bottom left
            [0, -1, 0],   # Bottom center
            [1, -1, 0]    # Bottom right
        ], dtype=np.float64)
        return vertices

    # Create blendshapes
    def create_smile_blendshape():
        base = create_face_mesh()
        smile = base.copy()
        # Move corners of mouth up for smile
        smile[6, 1] += 0.2  # Bottom left
        smile[8, 1] += 0.2  # Bottom right
        return smile

    def create_frown_blendshape():
        base = create_face_mesh()
        frown = base.copy()
        # Move corners of mouth down for frown
        frown[6, 1] -= 0.2  # Bottom left
        frown[8, 1] -= 0.2  # Bottom right
        return frown

    # Create rest pose and blendshapes
    rest_pose = create_face_mesh()
    smile = create_smile_blendshape()
    frown = create_frown_blendshape()

    # Stack all poses
    animated_poses = np.vstack([smile, frown])

    # Create DemBonesWrapper for easier use
    dem_bones = pdb.DemBonesWrapper()

    # Set parameters
    dem_bones.num_iterations = 20
    dem_bones.num_init_iterations = 10
    dem_bones.num_transform_iterations = 5
    dem_bones.num_weights_iterations = 3
    dem_bones.max_nonzeros_per_vertex = 4
    dem_bones.weights_smoothness = 1e-4

    # Set data
    dem_bones.set_rest_pose(rest_pose)
    dem_bones.set_animated_poses(animated_poses)
    dem_bones.set_num_bones(2)  # One bone for smile, one for frown
    dem_bones.set_bone_names(["Smile", "Frown"])

    # Compute skinning decomposition
    dem_bones.compute()

    # Get results
    weights = dem_bones.get_weights()
    transformations = dem_bones.get_transformations()

    print("Skinning weights:")
    print(weights)
    print("\nBone transformations:")
    print(transformations)

    # Now we can use the weights and transformations for animation
    # For example, to create a 50% smile:
    smile_factor = 0.5
    frown_factor = 0.0

    # Apply the transformations with the given factors
    # (This is a simplified example, in practice you would use a proper skinning function)
    deformed_vertices = rest_pose.copy()
    for i in range(len(rest_pose)):
        for b in range(2):  # 2 bones
            if b == 0:  # Smile bone
                factor = smile_factor
            else:  # Frown bone
                factor = frown_factor
                
            # Apply weighted transformation
            if weights[i, b] > 0:
                # In a real application, you would apply the full transformation matrix
                # This is a simplified version
                if b == 0:  # Smile
                    deformed_vertices[i, 1] += weights[i, b] * factor * 0.2
                else:  # Frown
                    deformed_vertices[i, 1] -= weights[i, b] * factor * 0.2

    print("\nDeformed vertices with 50% smile:")
    print(deformed_vertices)
