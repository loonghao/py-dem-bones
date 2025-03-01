"""
Example of using py-dem-bones with hierarchical skeletons.
"""

import numpy as np

import py_dem_bones as pdb


def create_articulated_mesh():
    """Create a simple articulated mesh (two connected boxes)."""
    # First box: vertices 0-7
    box1 = np.array([
        [-2, -1, -1],
        [-1, -1, -1],
        [-1, 1, -1],
        [-2, 1, -1],
        [-2, -1, 1],
        [-1, -1, 1],
        [-1, 1, 1],
        [-2, 1, 1]
    ], dtype=np.float64)

    # Second box: vertices 8-15
    box2 = np.array([
        [1, -1, -1],
        [2, -1, -1],
        [2, 1, -1],
        [1, 1, -1],
        [1, -1, 1],
        [2, -1, 1],
        [2, 1, 1],
        [1, 1, 1]
    ], dtype=np.float64)

    return np.vstack([box1, box2])


def create_deformed_articulated_mesh(angle_deg):
    """Create a deformed articulated mesh by rotating the second box."""
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


def main():
    """Run the example."""
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


if __name__ == "__main__":
    main()
