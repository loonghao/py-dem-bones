#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Integration Demo of RBF with DemBones in Maya

This example demonstrates how to combine DemBones with SciPy's RBF functionality in Maya,
implementing functionality similar to Chad Vernon's RBF nodes.
We will use DemBones to calculate bone weights and transformations, then use RBF interpolators
to drive auxiliary joints.

To run this example, you need:
1. Install the following dependencies in Maya's Python environment:
    pip install py-dem-bones numpy scipy

2. Ensure that the maya_example.py file is in the same directory or in the Python path

3. Copy this script to Maya's script editor to run, or execute via Maya's Python command line:
    import maya_rbf_demo
    maya_rbf_demo.main()
"""

import numpy as np
from scipy.interpolate import RBFInterpolator
import maya.cmds as cmds
import maya.OpenMaya as om
import py_dem_bones as pdb
from py_dem_bones.interfaces import DCCInterface

# Import MayaDCCInterface class
from maya_example import MayaDCCInterface


def create_cube_mesh(name="demBonesCube", size=2.0):
    """
    Create a test cube mesh in Maya
    """
    # Create cube
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
    Create test joint chain in Maya
    """
    if joint_positions is None:
        joint_positions = [
            (-1, 0, 0),  # Root joint
            (1, 0, 0),   # End joint
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
    Create auxiliary joints for RBF control
    """
    if positions is None:
        positions = [
            (0.5, 0.5, 0.0),  # First auxiliary joint
            (0.5, 0.5, 1.0),  # Second auxiliary joint
        ]
    
    joints = []
    for i, pos in enumerate(positions):
        cmds.select(clear=True)
        joint = cmds.joint(name=f"{name_prefix}_{i+1}", position=pos)
        # Add controller
        ctrl = create_control(f"{name_prefix}Ctrl_{i+1}", joint)
        joints.append(joint)
    
    return joints


def create_control(name, target):
    """
    Create NURBS controller for joint
    """
    # Create NURBS circle
    ctrl = cmds.circle(name=name, normal=(0, 1, 0), radius=0.3)[0]
    # Get target world position
    pos = cmds.xform(target, query=True, worldSpace=True, translation=True)
    # Move controller to target position
    cmds.xform(ctrl, worldSpace=True, translation=pos)
    # Parent relationship
    cmds.parentConstraint(ctrl, target, maintainOffset=True)
    
    return ctrl


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
    """
    return RBFInterpolator(
        key_poses, 
        key_values,
        kernel=rbf_function,
        smoothing=0.0  # No smoothing, exact interpolation
    )


def setup_rbf_driven_keys(source_ctrl, target_joint, rbf):
    """
    Set up RBF-driven keyframe animation
    """
    # Create node to store RBF weights
    weight_node = cmds.createNode('multiplyDivide', name=f"{target_joint}_rbfWeight")
    
    # Connect controller attributes to weight node
    cmds.connectAttr(f"{source_ctrl}.translateX", f"{weight_node}.input1X")
    cmds.connectAttr(f"{source_ctrl}.translateY", f"{weight_node}.input1Y")
    
    # Set driven keyframes
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
    """Main function for RBF demo in Maya"""
    try:
        # Clean up existing objects
        for obj in ['demBonesCube', 'demBonesRoot_1', 'rbfJoint_1', 'rbfJointCtrl_1']:
            if cmds.objExists(obj):
                cmds.delete(obj)
        
        # 1. Create test scene
        print("\n1. Creating test scene...")
        # Create cube mesh
        cube = create_cube_mesh()
        # Create joint chain
        joints = create_joints()
        # Create RBF auxiliary joints and controllers
        rbf_joints = create_rbf_joints()
        
        # 2. Set up DemBones and Maya interface
        print("\n2. Setting up DemBones...")
        dem_bones = pdb.DemBones()
        
        # Create MayaDCCInterface instance
        try:
            maya_interface = MayaDCCInterface(dem_bones)
        except NameError:
            print("Error: Cannot find MayaDCCInterface class. Please ensure maya_example.py file is in the same directory or in the Python path.")
            return
        
        # 3. Import data from Maya
        print("\n3. Importing data from Maya...")
        success = maya_interface.from_dcc_data(
            mesh_name=cube,
            joint_names=joints,
            use_world_space=True,
            max_influences=4
        )
        
        if not success:
            print("Failed to import data from Maya!")
            return
        
        # 4. Calculate skinning weights
        print("\n4. Calculating skinning weights...")
        dem_bones.compute()
        
        # 5. Export weights to Maya
        print("\n5. Exporting weights to Maya...")
        maya_interface.to_dcc_data(
            apply_weights=True,
            create_skin_cluster=True,
            skin_cluster_name='demBonesSkinCluster'
        )
        
        # 6. Set up RBF interpolation
        print("\n6. Setting up RBF interpolation...")
        # Define key poses
        key_poses = np.array([
            [0.0, 0.0],  # Default pose
            [1.0, 0.0],  # X-direction extreme
            [0.0, 1.0],  # Y-direction extreme
        ])
        
        # Define corresponding auxiliary joint positions
        key_values = np.array([
            # Auxiliary joint positions for default pose
            [[0.5, 0.5, 0.0], [0.5, 0.5, 1.0]],
            # Auxiliary joint positions for X-direction extreme
            [[0.7, 0.5, 0.0], [0.7, 0.5, 1.2]],
            # Auxiliary joint positions for Y-direction extreme
            [[0.5, 0.7, 0.0], [0.5, 0.7, 1.2]],
        ])
        
        # Create RBF interpolator
        try:
            rbf = create_rbf_interpolator(
                key_poses,
                key_values.reshape(3, -1),
                rbf_function='thin_plate_spline'
            )
        except Exception as e:
            print(f"Failed to create RBF interpolator: {e}")
            return
        
        # 7. Set up Maya driven keyframes
        print("\n7. Setting up driven keyframes...")
        for i, joint in enumerate(rbf_joints):
            ctrl_name = f"rbfJointCtrl_{i+1}"
            setup_rbf_driven_keys(ctrl_name, joint, rbf)
        
        print("\nDemo setup complete!")
        print("1. Select rbfJointCtrl_1 to control auxiliary joints")
        print("2. Move the controller to see the effect")
        print("3. Try different extreme positions to test RBF interpolation effect")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
