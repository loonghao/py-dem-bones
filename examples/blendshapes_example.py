"""
Example of using py-dem-bones to convert blendshapes to linear blend skinning.
"""

import numpy as np

import py_dem_bones as pdb


def create_face_mesh():
    """Create a simple face mesh with 9 vertices."""
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


def create_blendshapes():
    """Create blendshapes for the face mesh."""
    base = create_face_mesh()

    # Smile blendshape
    smile = base.copy()
    smile[6:9, 1] += 0.5  # Move bottom vertices up

    # Frown blendshape
    frown = base.copy()
    frown[1:4, 1] -= 0.5  # Move top vertices down

    # Surprise blendshape
    surprise = base.copy()
    surprise[1:4, 1] += 0.3  # Move top vertices up
    surprise[6:9, 1] -= 0.3  # Move bottom vertices down

    return np.vstack([base, smile, frown, surprise])


def main():
    """Run the example."""
    # Create DemBones instance
    dem_bones = pdb.DemBones()

    # Set parameters
    dem_bones.nIters = 30
    dem_bones.nInitIters = 10
    dem_bones.nTransIters = 5
    dem_bones.nWeightsIters = 3
    dem_bones.nnz = 4
    dem_bones.weightsSmooth = 1e-4

    # Set data
    rest_pose = create_face_mesh()
    blendshapes = create_blendshapes()

    dem_bones.nV = 9    # 9 vertices in the face mesh
    dem_bones.nB = 3    # 3 bones (one for each expression)
    dem_bones.nF = 4    # 4 frames (base + 3 expressions)
    dem_bones.nS = 1    # 1 subject
    dem_bones.fStart = np.array([0], dtype=np.int32)
    dem_bones.subjectID = np.zeros(4, dtype=np.int32)
    dem_bones.u = rest_pose
    dem_bones.v = blendshapes

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
