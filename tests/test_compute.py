"""
Tests for the py-dem-bones package.
"""

import numpy as np
import pytest


def test_dem_bones_compute():
    """Test DemBones.compute() with a simple example."""
    try:
        import py_dem_bones as pdb

        # Create a simple cube
        vertices = np.array([
            [-1, -1, -1],
            [1, -1, -1],
            [1, 1, -1],
            [-1, 1, -1],
            [-1, -1, 1],
            [1, -1, 1],
            [1, 1, 1],
            [-1, 1, 1]
        ], dtype=np.float64)

        # Create a deformed cube
        deformed = vertices.copy()
        deformed[:, 1] *= 1.5  # Scale y-coordinates

        # Create DemBones instance
        dem_bones = pdb.DemBones()

        # Set parameters
        dem_bones.nIters = 10
        dem_bones.nInitIters = 5
        dem_bones.nTransIters = 3
        dem_bones.nWeightsIters = 2
        dem_bones.nnz = 4
        dem_bones.weightsSmooth = 1e-4

        # Set data
        dem_bones.nV = 8  # 8 vertices
        dem_bones.nB = 2  # 2 bones
        dem_bones.nF = 2  # 2 frames (rest + deformed)
        dem_bones.nS = 1  # 1 subject
        dem_bones.fStart = np.array([0], dtype=np.int32)
        dem_bones.subjectID = np.zeros(2, dtype=np.int32)
        dem_bones.u = vertices
        dem_bones.v = np.vstack([vertices, deformed])

        # 预先设置权重矩阵，确保有 2 个骨骼
        # 创建一个简单的权重矩阵：前 4 个顶点属于骨骼 0，后 4 个顶点属于骨骼 1
        weights = np.zeros((2, 8), dtype=np.float64)
        weights[0, :4] = 1.0  # 骨骼 0 控制前 4 个顶点
        weights[1, 4:] = 1.0  # 骨骼 1 控制后 4 个顶点
        dem_bones.set_weights(weights)

        # Compute
        dem_bones.compute()

        # Check results
        weights = dem_bones.get_weights()
        transformations = dem_bones.get_transformations()

        # Verify weights shape
        print(f"Weights shape: {weights.shape}")
        # Weights are in [nB, nV] format (bones x vertices)
        assert weights.shape == (2, 8)  # 2 bones, 8 vertices

        # Verify transformations shape
        assert transformations.shape == (2, 4, 4)  # 2 frames, 4x4 matrices

        # Verify weights sum to 1 for each vertex
        assert np.allclose(np.sum(weights, axis=0), np.ones(8))

        # Verify weights are non-negative
        assert np.all(weights >= 0)

    except ImportError:
        pytest.skip("py_dem_bones not installed")


def test_dem_bones_ext_compute():
    """Test DemBonesExt.compute() with a simple example."""
    try:
        import py_dem_bones as pdb
        print("Starting test_dem_bones_ext_compute...")

        # Create a simple articulated mesh (two boxes)
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

        vertices = np.vstack([box1, box2])

        # Create a deformed mesh by rotating the second box
        deformed = vertices.copy()
        angle_rad = np.radians(30)
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)

        for i in range(8, 16):
            x, z = vertices[i, 0], vertices[i, 2]
            deformed[i, 0] = x * cos_a - z * sin_a
            deformed[i, 2] = x * sin_a + z * cos_a

        # Create DemBonesExt instance
        dem_bones_ext = pdb.DemBonesExt()

        # Set parameters
        dem_bones_ext.nIters = 10
        dem_bones_ext.nInitIters = 5
        dem_bones_ext.nTransIters = 3
        dem_bones_ext.nWeightsIters = 2
        dem_bones_ext.nnz = 4
        dem_bones_ext.weightsSmooth = 1e-4

        # Set data
        dem_bones_ext.nV = 16  # 16 vertices
        dem_bones_ext.nB = 2   # 2 bones
        dem_bones_ext.nF = 2   # 2 frames (rest + deformed)
        dem_bones_ext.nS = 1   # 1 subject
        dem_bones_ext.fStart = np.array([0], dtype=np.int32)
        dem_bones_ext.subjectID = np.zeros(2, dtype=np.int32)
        dem_bones_ext.u = vertices
        dem_bones_ext.v = np.vstack([vertices, deformed])

        # Set hierarchical skeleton data
        dem_bones_ext.parent = np.array([-1, 0], dtype=np.int32)  # Bone 1 is child of Bone 0
        dem_bones_ext.boneName = ["Box1", "Box2"]
        dem_bones_ext.bindUpdate = 1

        # 预先设置权重矩阵，确保有 2 个骨骼
        # 创建一个简单的权重矩阵：前 8 个顶点属于骨骼 0，后 8 个顶点属于骨骼 1
        weights = np.zeros((2, 16), dtype=np.float64)
        weights[0, :8] = 1.0  # 骨骼 0 控制前 8 个顶点
        weights[1, 8:] = 1.0  # 骨骼 1 控制后 8 个顶点
        dem_bones_ext.set_weights(weights)

        # Compute
        dem_bones_ext.compute()

        # Check results
        weights = dem_bones_ext.get_weights()
        transformations = dem_bones_ext.get_transformations()

        # Verify weights shape
        print(f"Weights shape: {weights.shape}")
        # Weights are in [nB, nV] format (bones x vertices)
        assert weights.shape == (2, 16)  # 2 bones, 16 vertices

        # Verify transformations shape
        print(f"Transformations shape: {transformations.shape}")
        assert transformations.shape == (2, 4, 4)  # 2 frames, 4x4 matrices

        # Verify weights sum to 1 for each vertex
        weight_sums = np.sum(weights, axis=0)
        print(f"Weight sums: {weight_sums}")
        assert np.allclose(weight_sums, np.ones(16))

        # Verify weights are non-negative
        assert np.all(weights >= 0)

        # Test computeRTB
        dem_bones_ext.computeRTB()

        # Verify bind matrix
        print(f"Bind matrix shape: {dem_bones_ext.bind.shape}")
        assert dem_bones_ext.bind.shape == (2, 4, 4)  # 2 bones, 4x4 matrices
        
        print("test_dem_bones_ext_compute PASSED!")

    except ImportError:
        pytest.skip("py_dem_bones not installed")


def test_parameter_setters():
    """Test parameter setters for DemBones."""
    try:
        import py_dem_bones as pdb

        dem_bones = pdb.DemBones()

        # Test setting parameters
        dem_bones.nIters = 50
        assert dem_bones.nIters == 50

        dem_bones.nInitIters = 20
        assert dem_bones.nInitIters == 20

        dem_bones.nTransIters = 10
        assert dem_bones.nTransIters == 10

        dem_bones.nWeightsIters = 5
        assert dem_bones.nWeightsIters == 5

        dem_bones.nnz = 8
        assert dem_bones.nnz == 8

        dem_bones.weightsSmooth = 0.01
        assert dem_bones.weightsSmooth == 0.01

    except ImportError:
        pytest.skip("py_dem_bones not installed")
