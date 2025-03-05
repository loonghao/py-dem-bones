#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RBF与DemBones在Maya中的集成演示

这个例子展示了如何在Maya中结合DemBones和SciPy的RBF功能，实现类似于Chad Vernon的RBF节点功能。
我们将使用DemBones计算骨骼权重和变换，然后使用RBF插值器驱动辅助关节。

要运行此示例，您需要：
1. 在Maya的Python环境中安装以下依赖项：
    pip install py-dem-bones numpy scipy

2. 确保maya_example.py文件在同一目录下或者在Python路径中

3. 将此脚本复制到Maya的脚本编辑器中运行，或通过Maya的Python命令行执行：
    import maya_rbf_demo
    maya_rbf_demo.main()
"""

import numpy as np
from scipy.interpolate import RBFInterpolator
import maya.cmds as cmds
import maya.OpenMaya as om
import py_dem_bones as pdb
from py_dem_bones.interfaces import DCCInterface

# 导入MayaDCCInterface类
from maya_example import MayaDCCInterface


def create_cube_mesh(name="demBonesCube", size=2.0):
    """
    在Maya中创建一个用于测试的立方体网格
    """
    # 创建立方体
    cube = cmds.polyCube(
        name=name,
        width=size,
        height=size,
        depth=size,
        subdivisionsX=2,
        subdivisionsY=2,
        subdivisionsZ=2
    )[0]
    
    return cube


def create_joints(root_name="demBonesRoot", joint_positions=None):
    """
    在Maya中创建测试用的骨骼链
    """
    if joint_positions is None:
        joint_positions = [
            (-1, 0, 0),  # 根关节
            (1, 0, 0),   # 末端关节
        ]
    
    cmds.select(clear=True)
    joints = []
    
    for i, pos in enumerate(joint_positions):
        name = f"{root_name}_{i+1}"
        if i == 0:
            joint = cmds.joint(name=name, position=pos)
        else:
            joint = cmds.joint(name=name, position=pos)
        joints.append(joint)
    
    return joints


def create_rbf_joints(name_prefix="rbfJoint", positions=None):
    """
    创建RBF控制用的辅助关节
    """
    if positions is None:
        positions = [
            (0.5, 0.5, 0.0),  # 第一个辅助关节
            (0.5, 0.5, 1.0),  # 第二个辅助关节
        ]
    
    joints = []
    for i, pos in enumerate(positions):
        cmds.select(clear=True)
        joint = cmds.joint(name=f"{name_prefix}_{i+1}", position=pos)
        # 添加控制器
        ctrl = create_control(f"{name_prefix}Ctrl_{i+1}", joint)
        joints.append(joint)
    
    return joints


def create_control(name, target):
    """
    为关节创建NURBS控制器
    """
    # 创建NURBS圆环
    ctrl = cmds.circle(name=name, normal=(0, 1, 0), radius=0.3)[0]
    # 获取目标世界位置
    pos = cmds.xform(target, query=True, worldSpace=True, translation=True)
    # 移动控制器到目标位置
    cmds.xform(ctrl, worldSpace=True, translation=pos)
    # 父子关系
    cmds.parentConstraint(ctrl, target, maintainOffset=True)
    
    return ctrl


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
    """
    return RBFInterpolator(
        key_poses, 
        key_values,
        kernel=rbf_function,
        smoothing=0.0  # 无平滑，精确插值
    )


def setup_rbf_driven_keys(source_ctrl, target_joint, rbf):
    """
    设置RBF驱动的关键帧动画
    """
    # 创建节点来存储RBF权重
    weight_node = cmds.createNode('multiplyDivide', name=f"{target_joint}_rbfWeight")
    
    # 连接控制器属性到权重节点
    cmds.connectAttr(f"{source_ctrl}.translateX", f"{weight_node}.input1X")
    cmds.connectAttr(f"{source_ctrl}.translateY", f"{weight_node}.input1Y")
    
    # 设置驱动关键帧
    cmds.setDrivenKeyframe(
        f"{target_joint}.translateX",
        currentDriver=f"{weight_node}.outputX",
        driverValue=0.0,
        value=0.0
    )
    cmds.setDrivenKeyframe(
        f"{target_joint}.translateY",
        currentDriver=f"{weight_node}.outputY",
        driverValue=0.0,
        value=0.0
    )


def main():
    """Maya中的RBF演示主函数"""
    try:
        # 清理已存在的对象
        for obj in ['demBonesCube', 'demBonesRoot_1', 'rbfJoint_1', 'rbfJointCtrl_1']:
            if cmds.objExists(obj):
                cmds.delete(obj)
        
        # 1. 创建测试场景
        print("\n1. 创建测试场景...")
        # 创建立方体网格
        cube = create_cube_mesh()
        # 创建骨骼链
        joints = create_joints()
        # 创建RBF辅助关节和控制器
        rbf_joints = create_rbf_joints()
        
        # 2. 设置DemBones和Maya接口
        print("\n2. 设置DemBones...")
        dem_bones = pdb.DemBones()
        
        # 创建MayaDCCInterface实例
        try:
            maya_interface = MayaDCCInterface(dem_bones)
        except NameError:
            print("错误：无法找到MayaDCCInterface类。请确保maya_example.py文件在同一目录下或者在Python路径中。")
            return
        
        # 3. 从Maya导入数据
        print("\n3. 从Maya导入数据...")
        success = maya_interface.from_dcc_data(
            mesh_name=cube,
            joint_names=joints,
            use_world_space=True,
            max_influences=4
        )
        
        if not success:
            print("从Maya导入数据失败！")
            return
        
        # 4. 计算蒙皮权重
        print("\n4. 计算蒙皮权重...")
        dem_bones.compute()
        
        # 5. 导出权重到Maya
        print("\n5. 导出权重到Maya...")
        maya_interface.to_dcc_data(
            apply_weights=True,
            create_skin_cluster=True,
            skin_cluster_name='demBonesSkinCluster'
        )
        
        # 6. 设置RBF插值
        print("\n6. 设置RBF插值...")
        # 定义关键姿势
        key_poses = np.array([
            [0.0, 0.0],  # 默认姿势
            [1.0, 0.0],  # X方向极值
            [0.0, 1.0],  # Y方向极值
        ])
        
        # 定义对应的辅助关节位置
        key_values = np.array([
            # 默认姿势的辅助关节位置
            [[0.5, 0.5, 0.0], [0.5, 0.5, 1.0]],
            # X方向极值的辅助关节位置
            [[0.7, 0.5, 0.0], [0.7, 0.5, 1.2]],
            # Y方向极值的辅助关节位置
            [[0.5, 0.7, 0.0], [0.5, 0.7, 1.2]],
        ])
        
        # 创建RBF插值器
        try:
            rbf = create_rbf_interpolator(
                key_poses,
                key_values.reshape(3, -1),
                rbf_function='thin_plate_spline'
            )
        except Exception as e:
            print(f"创建RBF插值器失败：{e}")
            return
        
        # 7. 设置Maya驱动关键帧
        print("\n7. 设置驱动关键帧...")
        for i, joint in enumerate(rbf_joints):
            ctrl_name = f"rbfJointCtrl_{i+1}"
            setup_rbf_driven_keys(ctrl_name, joint, rbf)
        
        print("\n演示设置完成！")
        print("1. 选择rbfJointCtrl_1来控制辅助关节")
        print("2. 移动控制器查看效果")
        print("3. 尝试不同的极限位置来测试RBF插值效果")
    except Exception as e:
        print(f"错误：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
