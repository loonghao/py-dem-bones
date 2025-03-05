#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RBF与DemBones结合的演示

这个例子展示了如何结合DemBones和SciPy的RBF功能，类似于Chad Vernon的实现。
我们将使用DemBones计算骨骼权重和变换，然后使用RBF插值器驱动辅助关节。

要运行此示例，您需要安装以下依赖项：
    pip install py-dem-bones numpy matplotlib scipy
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import RBFInterpolator
import py_dem_bones as pdb


def create_simple_mesh():
    """
    创建一个简单的测试网格（立方体）
    """
    # 创建一个立方体的顶点
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
    创建变形后的网格
    """
    # 对立方体上半部分顶点进行变形
    deformed = vertices.copy()
    # 变形上半部分(顶点4-7)
    deformed[4:, 0] += deformation_amount  # 沿X轴偏移
    deformed[4:, 2] += deformation_amount  # 沿Z轴偏移
    
    return deformed


def compute_dem_bones(rest_pose, deformed_pose, num_bones=2):
    """
    使用DemBones计算蒙皮权重和骨骼变换
    """
    # 创建DemBones实例
    dem_bones = pdb.DemBones()
    
    # 设置参数
    dem_bones.nIters = 30
    dem_bones.nInitIters = 10
    dem_bones.nTransIters = 5
    dem_bones.nWeightsIters = 3
    dem_bones.nnz = 4  # 每个顶点的非零权重数
    dem_bones.weightsSmooth = 1e-4
    
    # 设置数据
    dem_bones.nV = len(rest_pose)  # 顶点数
    dem_bones.nB = num_bones  # 骨骼数
    dem_bones.nF = 1  # 帧数
    dem_bones.nS = 1  # 主体数
    dem_bones.fStart = np.array([0], dtype=np.int32)  # 每个主体的帧起始索引
    dem_bones.subjectID = np.zeros(1, dtype=np.int32)  # 每帧的主体ID
    dem_bones.u = rest_pose  # 静止姿态
    dem_bones.v = deformed_pose  # 变形姿态
    
    # 计算蒙皮分解
    dem_bones.compute()
    
    # 获取结果
    weights = dem_bones.get_weights()
    transformations = dem_bones.get_transformations()
    
    return weights, transformations


def create_rbf_interpolator(key_poses, key_values, rbf_function='thin_plate_spline'):
    """
    创建RBF插值器，类似于Chad Vernon的RBF节点
    
    参数：
        key_poses: 关键姿势的输入值 (n_samples, n_features)
        key_values: 每个关键姿势对应的输出值 (n_samples, m)
        rbf_function: RBF函数类型，可选值包括：
            - 'thin_plate_spline': 薄板样条(默认)
            - 'multiquadric': 多二次曲面
            - 'inverse_multiquadric': 反多二次曲面
            - 'gaussian': 高斯函数
            - 'linear': 线性函数
            - 'cubic': 三次函数
            - 'quintic': 五次函数
    
    返回：
        RBF插值器
    """
    # 使用SciPy的RBFInterpolator，它是更现代的替代Rbf类
    return RBFInterpolator(
        key_poses, 
        key_values,
        kernel=rbf_function,
        smoothing=0.0  # 无平滑，精确插值
    )


def visualize_results(rest_pose, deformed_pose, dem_bones_weights, helper_joint_positions):
    """
    可视化结果
    
    参数：
        rest_pose: 静止姿态的顶点位置
        deformed_pose: 变形姿态的顶点位置
        dem_bones_weights: DemBones计算的骨骼权重
        helper_joint_positions: RBF插值器计算的辅助关节位置
    """
    fig = plt.figure(figsize=(18, 6))
    
    # 第一个子图：原始网格
    ax1 = fig.add_subplot(131, projection='3d')
    ax1.scatter(rest_pose[:, 0], rest_pose[:, 1], rest_pose[:, 2], c='blue', s=100)
    ax1.set_title('原始网格')
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    ax1.set_zlabel('Z')
    
    # 第二个子图：变形网格
    ax2 = fig.add_subplot(132, projection='3d')
    ax2.scatter(deformed_pose[:, 0], deformed_pose[:, 1], deformed_pose[:, 2], c='red', s=100)
    ax2.set_title('变形网格')
    ax2.set_xlabel('X')
    ax2.set_ylabel('Y')
    ax2.set_zlabel('Z')
    
    # 第三个子图：权重和辅助关节
    ax3 = fig.add_subplot(133, projection='3d')
    # 使用权重值作为颜色
    colors = dem_bones_weights[:, 0]  # 使用第一根骨骼的权重作为颜色
    scatter = ax3.scatter(
        deformed_pose[:, 0], 
        deformed_pose[:, 1], 
        deformed_pose[:, 2], 
        c=colors, 
        cmap='viridis', 
        s=100
    )
    # 添加辅助关节位置
    ax3.scatter(
        helper_joint_positions[:, 0],
        helper_joint_positions[:, 1],
        helper_joint_positions[:, 2],
        c='red',
        marker='x',
        s=200
    )
    ax3.set_title('骨骼权重和辅助关节')
    ax3.set_xlabel('X')
    ax3.set_ylabel('Y')
    ax3.set_zlabel('Z')
    plt.colorbar(scatter, ax=ax3, label='骨骼权重')
    
    plt.tight_layout()
    plt.show()


def main():
    # 创建测试数据
    rest_pose = create_simple_mesh()
    deformed_pose = create_deformed_mesh(rest_pose)
    
    print("1. 计算DemBones权重和变换...")
    weights, transformations = compute_dem_bones(rest_pose, deformed_pose)
    
    print("骨骼权重:")
    print(weights)
    print("\n骨骼变换:")
    print(transformations)
    
    # 创建RBF插值数据
    print("\n2. 创建RBF插值器...")
    
    # 定义输入关键姿势
    # 在实际情况下，这些可能是控制器的位置或其他控制值
    key_poses = np.array([
        [0.0, 0.0],  # 默认姿势
        [1.0, 0.0],  # X方向极值
        [0.0, 1.0],  # Y方向极值
    ])
    
    # 定义输出值 - 辅助关节位置
    # 这些是对应每个关键姿势的辅助关节的位置
    key_values = np.array([
        # 默认姿势的辅助关节位置
        [[0.5, 0.5, 0.0], [0.5, 0.5, 1.0]],
        # X方向极值的辅助关节位置
        [[0.7, 0.5, 0.0], [0.7, 0.5, 1.2]],
        # Y方向极值的辅助关节位置
        [[0.5, 0.7, 0.0], [0.5, 0.7, 1.2]],
    ])
    
    # 创建RBF插值器
    rbf = create_rbf_interpolator(key_poses, key_values.reshape(3, -1), rbf_function='thin_plate_spline')
    
    # 测试RBF插值
    test_pose = np.array([[0.5, 0.5]])  # 测试姿势
    interpolated = rbf(test_pose).reshape(-1, 3)  # 获取插值结果
    
    print("输入测试姿势:", test_pose)
    print("插值辅助关节位置:")
    print(interpolated)
    
    # 可视化结果
    visualize_results(rest_pose, deformed_pose, weights, interpolated)
    
    print("\n3. 测试不同姿势的RBF插值:")
    # 测试不同姿势的RBF插值
    test_poses = [
        [0.0, 0.0],  # 默认姿势
        [1.0, 0.0],  # X方向极值
        [0.0, 1.0],  # Y方向极值
        [0.5, 0.5],  # 中间姿势
        [0.25, 0.75],  # 其他姿势
    ]
    
    for i, pose in enumerate(test_poses):
        test_pose = np.array([pose])
        result = rbf(test_pose).reshape(-1, 3)
        print(f"\n测试姿势 {i+1}: {pose}")
        print(f"插值辅助关节位置:")  
        print(result)


if __name__ == "__main__":
    main()