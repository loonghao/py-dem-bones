#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RBF Integration with DemBones Demo

This example demonstrates how to combine DemBones with SciPy's RBF functionality, similar to Chad Vernon's implementation.
We will use DemBones to calculate bone weights and transformations, then use RBF interpolators to drive auxiliary joints.

To run this example, you need to install the following dependencies:
    pip install py-dem-bones numpy matplotlib scipy
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import RBFInterpolator
import py_dem_bones as pdb


def create_simple_mesh():
    """
    Create a simple test mesh (cube)
    """
    # Create cube vertices
    vertices = np.array([
        [0, 0, 0],  # 0
        [1, 0, 0],  # 1
        [1, 1, 0],  # 2
        [0, 1, 0],  # 3
        [0, 0, 1],  # 4
        [1, 0, 1],  # 5
        [1, 1, 1],  # 6
        [0, 1, 1],  # 7
    ], dtype=np.float64)
    
    return vertices


def create_deformed_mesh(vertices, deformation_amount=0.3):
    """
    Create a deformed mesh
    """
    # Deform the upper part of the cube
    deformed = vertices.copy()
    # Deform the upper part (vertices 4-7)
    deformed[4:, 0] += deformation_amount  # Offset along X axis
    deformed[4:, 2] += deformation_amount  # Offset along Z axis
    
    return deformed


def compute_dem_bones(rest_pose, deformed_pose, num_bones=2):
    """
    Use DemBones to calculate skinning weights and bone transformations
    """
    # Create DemBones instance
    dem_bones = pdb.DemBones()
    
    # Set parameters
    dem_bones.nIters = 30
    dem_bones.nInitIters = 10
    dem_bones.nTransIters = 5
    dem_bones.nWeightsIters = 3
    dem_bones.nnz = 4  # Number of non-zero weights per vertex
    dem_bones.weightsSmooth = 1e-4
    
    # Set data
    dem_bones.nV = len(rest_pose)  # Number of vertices
    dem_bones.nB = num_bones  # Number of bones
    dem_bones.nF = 1  # Number of frames
    dem_bones.nS = 1  # Number of subjects
    dem_bones.fStart = np.array([0], dtype=np.int32)  # Starting frame index for each subject
    dem_bones.subjectID = np.zeros(1, dtype=np.int32)  # Subject ID for each frame
    dem_bones.u = rest_pose  # Rest pose
    dem_bones.v = deformed_pose  # Deformed pose
    
    # Compute skinning decomposition
    dem_bones.compute()
    
    # Get results
    weights = dem_bones.get_weights()
    transformations = dem_bones.get_transformations()
    
    return weights, transformations


def create_rbf_interpolator(key_poses, key_values, rbf_function='thin_plate_spline'):
    """
    Create RBF interpolator, similar to Chad Vernon's RBF nodes
    
    Parameters:
        key_poses: Input values for key poses (n_samples, n_features)
        key_values: Output values for each key pose (n_samples, m)
        rbf_function: RBF function type, options include:
            - 'thin_plate_spline': Thin plate spline (default)
            - 'multiquadric': Multiquadric
            - 'inverse_multiquadric': Inverse multiquadric
            - 'gaussian': Gaussian function
            - 'linear': Linear function
            - 'cubic': Cubic function
            - 'quintic': Quintic function
    
    Returns:
        RBF interpolator
    """
    # Use SciPy's RBFInterpolator, which is a more modern alternative to the Rbf class
    return RBFInterpolator(
        key_poses, 
        key_values,
        kernel=rbf_function,
        smoothing=0.0  # No smoothing, exact interpolation
    )


def visualize_results(rest_pose, deformed_pose, dem_bones_weights, helper_joint_positions):
    """
    Visualize results
    
    Parameters:
        rest_pose: Vertex positions in rest pose
        deformed_pose: Vertex positions in deformed pose
        dem_bones_weights: Bone weights calculated by DemBones
        helper_joint_positions: Auxiliary joint positions calculated by RBF interpolator
    """
    fig = plt.figure(figsize=(18, 6))
    
    # First subplot: Original mesh
    ax1 = fig.add_subplot(131, projection='3d')
    ax1.scatter(rest_pose[:, 0], rest_pose[:, 1], rest_pose[:, 2], c='blue', s=100)
    ax1.set_title('Original Mesh')
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    ax1.set_zlabel('Z')
    
    # Second subplot: Deformed mesh
    ax2 = fig.add_subplot(132, projection='3d')
    ax2.scatter(deformed_pose[:, 0], deformed_pose[:, 1], deformed_pose[:, 2], c='red', s=100)
    ax2.set_title('Deformed Mesh')
    ax2.set_xlabel('X')
    ax2.set_ylabel('Y')
    ax2.set_zlabel('Z')
    
    # Third subplot: Weights and auxiliary joints
    ax3 = fig.add_subplot(133, projection='3d')
    # Use weight values as colors
    colors = dem_bones_weights[:, 0]  # Use weights of the first bone as colors
    scatter = ax3.scatter(
        deformed_pose[:, 0], 
        deformed_pose[:, 1], 
        deformed_pose[:, 2], 
        c=colors, 
        cmap='viridis', 
        s=100
    )
    # Add auxiliary joint positions
    ax3.scatter(
        helper_joint_positions[:, 0],
        helper_joint_positions[:, 1],
        helper_joint_positions[:, 2],
        c='red',
        marker='x',
        s=200
    )
    ax3.set_title('Bone Weights and Auxiliary Joints')
    ax3.set_xlabel('X')
    ax3.set_ylabel('Y')
    ax3.set_zlabel('Z')
    plt.colorbar(scatter, ax=ax3, label='Bone Weights')
    
    plt.tight_layout()
    plt.show()


def main():
    # Create test data
    rest_pose = create_simple_mesh()
    deformed_pose = create_deformed_mesh(rest_pose)
    
    print("1. Computing DemBones weights and transformations...")
    weights, transformations = compute_dem_bones(rest_pose, deformed_pose)
    
    print("Bone weights:")
    print(weights)
    print("\nBone transformations:")
    print(transformations)
    
    # Create RBF interpolation data
    print("\n2. Creating RBF interpolator...")
    
    # Define input key poses
    # In a real scenario, these might be controller positions or other control values
    key_poses = np.array([
        [0.0, 0.0],  # Default pose
        [1.0, 0.0],  # X-direction extreme
        [0.0, 1.0],  # Y-direction extreme
    ])
    
    # Define output values - auxiliary joint positions
    # These are the positions of auxiliary joints corresponding to each key pose
    key_values = np.array([
        # Auxiliary joint positions for default pose
        [[0.5, 0.5, 0.0], [0.5, 0.5, 1.0]],
        # Auxiliary joint positions for X-direction extreme
        [[0.7, 0.5, 0.0], [0.7, 0.5, 1.2]],
        # Auxiliary joint positions for Y-direction extreme
        [[0.5, 0.7, 0.0], [0.5, 0.7, 1.2]],
    ])
    
    # Create RBF interpolator
    rbf = create_rbf_interpolator(key_poses, key_values.reshape(3, -1), rbf_function='thin_plate_spline')
    
    # Test RBF interpolation
    test_pose = np.array([[0.5, 0.5]])  # Test pose
    interpolated = rbf(test_pose).reshape(-1, 3)  # Get interpolation result
    
    print("Input test pose:", test_pose)
    print("Interpolated auxiliary joint positions:")
    print(interpolated)
    
    # Visualize results
    visualize_results(rest_pose, deformed_pose, weights, interpolated)
    
    print("\n3. Testing RBF interpolation for different poses:")
    # Test RBF interpolation for different poses
    test_poses = [
        [0.0, 0.0],  # Default pose
        [1.0, 0.0],  # X-direction extreme
        [0.0, 1.0],  # Y-direction extreme
        [0.5, 0.5],  # Middle pose
        [0.25, 0.75],  # Other pose
    ]
    
    for i, pose in enumerate(test_poses):
        test_pose = np.array([pose])
        result = rbf(test_pose).reshape(-1, 3)
        print(f"\nTest pose {i+1}: {pose}")
        print(f"Interpolated auxiliary joint positions:")
        print(result)


if __name__ == "__main__":
    main()