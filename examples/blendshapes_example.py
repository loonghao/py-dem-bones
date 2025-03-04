"""
Blendshapes to Linear Blend Skinning Conversion
==============================================

This example demonstrates how to convert facial blendshapes to a linear blend skinning
representation using py-dem-bones. This is useful for facial animation systems that
need to be compatible with skeletal animation pipelines.

The example:
1. Creates a simple face mesh
2. Defines several blendshapes (smile, frown, surprise)
3. Uses py-dem-bones to extract a skinning decomposition
4. Demonstrates how to use the resulting bones and weights to recreate the blendshapes
"""

import numpy as np

import py_dem_bones as pdb


def create_face_mesh():
    """Create a simple face mesh with 9 vertices.
    
    Returns:
        np.ndarray: A 9x3 array of vertex positions representing a simple face.
    """
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
    """Create blendshapes for the face mesh.
    
    This function creates three blendshapes (smile, frown, surprise) based on
    the base face mesh.
    
    Returns:
        np.ndarray: A stacked array containing the base mesh and three blendshapes.
    """
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
    """Run the blendshapes to skinning conversion example.
    
    This function demonstrates the complete workflow:
    1. Create blendshapes
    2. Configure the DemBones algorithm
    3. Compute the skinning decomposition
    4. Retrieve and use the resulting bones and weights
    """
    # Create DemBones instance
    dem_bones = pdb.DemBones()

    # Set parameters
    dem_bones.nIters = 20
    dem_bones.nInitIters = 10
    dem_bones.nTransformIters = 5
    dem_bones.nWeightsIters = 3
    dem_bones.maxNonZerosPerVertex = 4
    dem_bones.weightsSmoothness = 1e-4

    # Create blendshapes
    blendshapes = create_blendshapes()
    num_vertices = 9
    num_frames = 4  # Base + 3 blendshapes

    # Set rest pose (first frame)
    dem_bones.setRestPose(blendshapes[:num_vertices])

    # Set animated poses (all frames including rest pose)
    dem_bones.setAnimatedPoses(blendshapes.reshape(num_frames, num_vertices, 3))

    # Set number of bones
    dem_bones.nBones = 3

    # Compute skinning decomposition
    dem_bones.compute()

    # Get results
    weights = dem_bones.getWeights()
    transforms = dem_bones.getTransforms()

    print("Skinning weights:")
    print(weights)
    print("\nBone transforms (first frame):")
    print(transforms[0])

    # Example: Deform the mesh using the extracted skinning weights and transforms
    # Here we use 50% of the smile transform (index 1)
    blend_factor = 0.5
    interpolated_transforms = transforms[0].copy()  # Start with rest pose transforms
    
    # Blend with smile transforms (index 1)
    for i in range(len(interpolated_transforms)):
        interpolated_transforms[i] = (1 - blend_factor) * transforms[0][i] + blend_factor * transforms[1][i]
    
    # Apply skinning
    deformed_vertices = np.zeros((num_vertices, 3))
    for v in range(num_vertices):
        for b in range(dem_bones.nBones):
            if weights[v, b] > 0:
                # Apply bone transformation weighted by skinning weight
                bone_transform = interpolated_transforms[b]
                vertex = blendshapes[v].copy()  # Rest pose vertex
                
                # Apply transformation (simplified for this example)
                transformed = vertex + bone_transform[:3]  # Just apply translation part
                deformed_vertices[v] += weights[v, b] * transformed

    print("\nDeformed vertices with 50% smile:")
    print(deformed_vertices)


if __name__ == "__main__":
    main()
