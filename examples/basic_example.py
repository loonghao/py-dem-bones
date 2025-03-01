"""
Example of using py-dem-bones for basic skinning decomposition.
"""

import numpy as np

import py_dem_bones as pdb


def create_cube():
    """Create a simple cube mesh."""
    vertices = np.array([
        [-1, -1, -1],  # 0
        [1, -1, -1],   # 1
        [1, 1, -1],    # 2
        [-1, 1, -1],   # 3
        [-1, -1, 1],   # 4
        [1, -1, 1],    # 5
        [1, 1, 1],     # 6
        [-1, 1, 1]     # 7
    ], dtype=np.float64)

    return vertices


def create_deformed_cube(scale_y):
    """Create a deformed cube by stretching it along the y-axis."""
    vertices = create_cube()
    deformed = vertices.copy()
    deformed[:, 1] *= scale_y
    return deformed


def main():
    """Run the example."""
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


if __name__ == "__main__":
    main()
