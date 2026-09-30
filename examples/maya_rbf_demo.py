#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DemBones skinning and an offline RBF interpolation preview in Maya.

This example uses the packaged Maya adapter to calculate skinning data from
sampled mesh poses, then evaluates a SciPy RBF interpolator in Python. It does
not install a live Maya RBF node or connect the interpolator to joint updates.

To run this example, you need:
1. Install the following dependencies in Maya's Python environment:
    pip install py-dem-bones numpy scipy

2. Provide animated mesh samples with the same vertex order and polygon topology
   as a size-2 cube with two subdivisions on each axis, created by this demo.

3. Copy this script to Maya's script editor to run, or execute via Maya's Python command line:
    import maya_rbf_demo
    maya_rbf_demo.main(anim_mesh_names=["cubePose1", "cubePose2"])
"""

import numpy as np
from scipy.interpolate import RBFInterpolator
import maya.cmds as cmds
from py_dem_bones.adapters.maya import MayaDCCInterface


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
        create_control(f"{name_prefix}Ctrl_{i+1}", joint)
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
    """Reserved for a Maya node or callback that evaluates the interpolator."""
    raise NotImplementedError(
        "Live RBF-driven joints require a Maya evaluation node or callback; "
        "this example only evaluates the interpolator in Python."
    )


def main(anim_mesh_names=None):
    """Solve sampled cube poses and preview RBF outputs, without a live RBF rig."""
    if not anim_mesh_names:
        print("Provide anim_mesh_names with sampled cube poses; a static mesh and joint positions are insufficient.")
        return False
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
        create_rbf_joints()
        
        # 2. Set up DemBones and Maya interface
        print("\n2. Setting up DemBones...")
        maya_interface = MayaDCCInterface()
        
        # 3. Import data from Maya
        print("\n3. Importing data from Maya...")
        success = maya_interface.from_dcc_data(
            mesh_name=cube,
            joint_names=joints,
            anim_mesh_names=anim_mesh_names,
            use_world_space=True,
            max_influences=4
        )
        
        if not success:
            print(f"Failed to import data from Maya: {maya_interface.last_error}")
            return False
        
        # 4. Calculate skinning weights
        print("\n4. Calculating skinning weights...")
        maya_interface.compute()
        
        # 5. Export weights to Maya
        print("\n5. Exporting weights to Maya...")
        export_result = maya_interface.to_dcc_data(
            apply_weights=True,
            create_skin_cluster=True,
            skin_cluster_name='demBonesSkinCluster'
        )
        if not export_result.get("success", False):
            print(f"Failed to export skinning data to Maya: {export_result.get('error', 'unknown error')}")
            return False
        
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
            return False
        
        print("\n7. Previewing RBF interpolation at controller input [0.5, 0.5]...")
        print(rbf(np.array([[0.5, 0.5]])).reshape(-1, 3))
        print("Skinning export and Python RBF preview complete.")
        print("Live RBF-driven joints are not implemented; moving the controllers does not evaluate this interpolator.")
        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    main()
