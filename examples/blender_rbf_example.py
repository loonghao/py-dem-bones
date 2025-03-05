#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RBF Drivers for Blender using py-dem-bones

This example demonstrates how to implement RBF drivers in Blender using
py-dem-bones and SciPy's RBF interpolation, similar to James Snowden's RBF Drivers.

Features:
- Multiple inputs and outputs in a single RBF driver
- Support for various RBF kernel functions
- Pose-based workflow (define poses, get interpolation)
- Drive bone transforms, shape keys, and custom properties

Requirements:
    pip install py-dem-bones numpy scipy

Usage:
    Run this script from within Blender
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union

import py_dem_bones as pdb
from scipy.interpolate import RBFInterpolator

# Import the BlenderDCCInterface from blender_example.py
from blender_example import BlenderDCCInterface


class BlenderRBFDriver:
    """
    RBF Driver implementation for Blender, similar to James Snowden's RBF Drivers.
    
    This class provides a pose-based workflow for creating RBF drivers in Blender,
    allowing users to define poses and corresponding outputs, and then interpolate
    between them.
    """
    
    def __init__(self, name="RBFDriver", kernel="thin_plate_spline", smoothing=0.0):
        """
        Initialize a new RBF Driver.
        
        Args:
            name: Name of the RBF driver
            kernel: RBF kernel function to use. Options include:
                - 'thin_plate_spline': Thin plate spline (default)
                - 'multiquadric': Multiquadric
                - 'inverse_multiquadric': Inverse multiquadric
                - 'gaussian': Gaussian
                - 'linear': Linear
                - 'cubic': Cubic
                - 'quintic': Quintic
            smoothing: Smoothing parameter for the RBF interpolation
        """
        self.name = name
        self.kernel = kernel
        self.smoothing = smoothing
        
        # Input and output definitions
        self.input_objects = []  # Objects whose properties will be used as inputs
        self.input_properties = []  # Properties to use as inputs (location, rotation, etc.)
        self.output_objects = []  # Objects whose properties will be driven
        self.output_properties = []  # Properties to drive
        
        # Pose data
        self.poses = []  # List of input poses
        self.outputs = []  # List of corresponding output values
        
        # RBF interpolator
        self.rbf = None
        self.is_initialized = False
    
    def add_input(self, obj, property_path):
        """
        Add an input to the RBF driver.
        
        Args:
            obj: Blender object to use as input
            property_path: Property path to use as input (e.g., 'location', 'rotation_euler')
        """
        self.input_objects.append(obj)
        self.input_properties.append(property_path)
        self.is_initialized = False  # Reset initialization flag
    
    def add_output(self, obj, property_path):
        """
        Add an output to the RBF driver.
        
        Args:
            obj: Blender object to drive
            property_path: Property path to drive (e.g., 'location', 'rotation_euler')
        """
        self.output_objects.append(obj)
        self.output_properties.append(property_path)
        self.is_initialized = False  # Reset initialization flag
    
    def capture_pose(self):
        """
        Capture the current pose of input objects and corresponding output values.
        
        Returns:
            Tuple of (input_values, output_values)
        """
        try:
            import bpy
            
            # Capture input values
            input_values = []
            for obj, prop in zip(self.input_objects, self.input_properties):
                # Get property value
                value = self._get_property_value(obj, prop)
                # Flatten the value to a list
                if hasattr(value, "__iter__"):
                    input_values.extend(list(value))
                else:
                    input_values.append(value)
            
            # Capture output values
            output_values = []
            for obj, prop in zip(self.output_objects, self.output_properties):
                # Get property value
                value = self._get_property_value(obj, prop)
                # Flatten the value to a list
                if hasattr(value, "__iter__"):
                    output_values.extend(list(value))
                else:
                    output_values.append(value)
            
            return np.array(input_values), np.array(output_values)
        
        except ImportError:
            print("Error: This script must be run from within Blender.")
            return None, None
    
    def add_pose(self):
        """
        Add the current pose to the list of poses.
        
        Returns:
            Index of the added pose
        """
        input_values, output_values = self.capture_pose()
        if input_values is not None and output_values is not None:
            self.poses.append(input_values)
            self.outputs.append(output_values)
            self.is_initialized = False  # Reset initialization flag
            return len(self.poses) - 1
        return -1
    
    def remove_pose(self, index):
        """
        Remove a pose from the list of poses.
        
        Args:
            index: Index of the pose to remove
        """
        if 0 <= index < len(self.poses):
            self.poses.pop(index)
            self.outputs.pop(index)
            self.is_initialized = False  # Reset initialization flag
    
    def initialize(self):
        """
        Initialize the RBF interpolator with the current poses.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        if len(self.poses) < 2:
            print("Error: At least two poses are required for RBF interpolation.")
            return False
        
        # Convert poses and outputs to numpy arrays
        poses_array = np.array(self.poses)
        outputs_array = np.array(self.outputs)
        
        # Create RBF interpolator
        self.rbf = RBFInterpolator(
            poses_array,
            outputs_array,
            kernel=self.kernel,
            smoothing=self.smoothing
        )
        
        self.is_initialized = True
        return True
    
    def update(self):
        """
        Update the driven properties based on the current input values.
        
        Returns:
            True if update was successful, False otherwise
        """
        try:
            import bpy
            
            # Initialize if not already initialized
            if not self.is_initialized:
                if not self.initialize():
                    return False
            
            # Get current input values
            input_values, _ = self.capture_pose()
            if input_values is None:
                return False
            
            # Predict output values using RBF interpolator
            output_values = self.rbf(input_values.reshape(1, -1))[0]
            
            # Apply output values to driven properties
            output_index = 0
            for obj, prop in zip(self.output_objects, self.output_properties):
                # Get the property value to determine its size
                current_value = self._get_property_value(obj, prop)
                
                # Determine how many values to extract from output_values
                if hasattr(current_value, "__iter__"):
                    value_size = len(current_value)
                    new_value = output_values[output_index:output_index + value_size]
                    output_index += value_size
                else:
                    new_value = output_values[output_index]
                    output_index += 1
                
                # Set the property value
                self._set_property_value(obj, prop, new_value)
            
            return True
        
        except ImportError:
            print("Error: This script must be run from within Blender.")
            return False
    
    def _get_property_value(self, obj, property_path):
        """
        Get the value of a property from a Blender object.
        
        Args:
            obj: Blender object
            property_path: Property path (e.g., 'location', 'rotation_euler')
        
        Returns:
            Property value
        """
        # Handle special cases
        if property_path == 'location':
            return obj.location
        elif property_path == 'rotation_euler':
            return obj.rotation_euler
        elif property_path == 'scale':
            return obj.scale
        elif property_path.startswith('pose.bones'):
            # Handle pose bone properties
            bone_name = property_path.split('[')[1].split(']')[0].strip('"\'')
            sub_prop = property_path.split('.')[-1]
            if sub_prop == 'location':
                return obj.pose.bones[bone_name].location
            elif sub_prop == 'rotation_euler':
                return obj.pose.bones[bone_name].rotation_euler
            elif sub_prop == 'scale':
                return obj.pose.bones[bone_name].scale
        elif property_path.startswith('key_blocks'):
            # Handle shape keys
            key_name = property_path.split('[')[1].split(']')[0].strip('"\'')
            return obj.data.shape_keys.key_blocks[key_name].value
        
        # Handle custom properties and other properties using eval
        try:
            return eval(f"obj.{property_path}")
        except:
            print(f"Error: Could not get property {property_path} from {obj.name}")
            return 0.0
    
    def _set_property_value(self, obj, property_path, value):
        """
        Set the value of a property on a Blender object.
        
        Args:
            obj: Blender object
            property_path: Property path (e.g., 'location', 'rotation_euler')
            value: Value to set
        """
        # Handle special cases
        if property_path == 'location':
            obj.location = value
        elif property_path == 'rotation_euler':
            obj.rotation_euler = value
        elif property_path == 'scale':
            obj.scale = value
        elif property_path.startswith('pose.bones'):
            # Handle pose bone properties
            bone_name = property_path.split('[')[1].split(']')[0].strip('"\'')
            sub_prop = property_path.split('.')[-1]
            if sub_prop == 'location':
                obj.pose.bones[bone_name].location = value
            elif sub_prop == 'rotation_euler':
                obj.pose.bones[bone_name].rotation_euler = value
            elif sub_prop == 'scale':
                obj.pose.bones[bone_name].scale = value
        elif property_path.startswith('key_blocks'):
            # Handle shape keys
            key_name = property_path.split('[')[1].split(']')[0].strip('"\'')
            obj.data.shape_keys.key_blocks[key_name].value = value
        else:
            # Handle custom properties and other properties using exec
            try:
                exec(f"obj.{property_path} = {value}")
            except:
                print(f"Error: Could not set property {property_path} on {obj.name}")


def create_rbf_driver_example():
    """
    Example of how to use the BlenderRBFDriver in Blender.
    """
    # This function would be called from within Blender
    
    # Import Blender modules
    import bpy
    
    # Create a simple scene for testing
    def create_test_scene():
        # Clear existing objects
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.select_by_type(type='MESH')
        bpy.ops.object.select_by_type(type='ARMATURE')
        bpy.ops.object.delete()
        
        # Create a cube
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        cube = bpy.context.active_object
        cube.name = 'ControlCube'
        
        # Create a sphere as a target object
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(3, 0, 0))
        sphere = bpy.context.active_object
        sphere.name = 'TargetSphere'
        
        # Create a shape key for the sphere
        sphere.shape_key_add(name='Basis')
        key1 = sphere.shape_key_add(name='Deform')
        
        # Modify the shape key
        for v in key1.data:
            v.co.z *= 1.5  # Stretch in Z direction
        
        # Create an empty as a helper object
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(3, 3, 0))
        helper = bpy.context.active_object
        helper.name = 'HelperEmpty'
        
        return cube, sphere, helper
    
    # Create the test scene
    control_cube, target_sphere, helper_empty = create_test_scene()
    
    # Create an RBF driver
    rbf_driver = BlenderRBFDriver(name="TestRBFDriver", kernel="thin_plate_spline")
    
    # Add inputs (control cube location)
    rbf_driver.add_input(control_cube, "location")
    
    # Add outputs (target sphere location and shape key value)
    rbf_driver.add_output(target_sphere, "location")
    rbf_driver.add_output(helper_empty, "location")
    rbf_driver.add_output(target_sphere, "key_blocks['Deform']")
    
    # Capture poses
    
    # Pose 1: Default pose
    control_cube.location = (0, 0, 0)
    target_sphere.location = (3, 0, 0)
    helper_empty.location = (3, 3, 0)
    target_sphere.data.shape_keys.key_blocks['Deform'].value = 0.0
    rbf_driver.add_pose()
    
    # Pose 2: Control cube moved in X direction
    control_cube.location = (1, 0, 0)
    target_sphere.location = (4, 0, 1)
    helper_empty.location = (4, 4, 1)
    target_sphere.data.shape_keys.key_blocks['Deform'].value = 0.5
    rbf_driver.add_pose()
    
    # Pose 3: Control cube moved in Y direction
    control_cube.location = (0, 1, 0)
    target_sphere.location = (3, 1, 1)
    helper_empty.location = (3, 4, 1)
    target_sphere.data.shape_keys.key_blocks['Deform'].value = 0.3
    rbf_driver.add_pose()
    
    # Pose 4: Control cube moved in Z direction
    control_cube.location = (0, 0, 1)
    target_sphere.location = (3, 0, 2)
    helper_empty.location = (3, 3, 2)
    target_sphere.data.shape_keys.key_blocks['Deform'].value = 1.0
    rbf_driver.add_pose()
    
    # Initialize the RBF driver
    rbf_driver.initialize()
    
    # Create a handler to update the RBF driver on each frame change
    def frame_change_handler(scene):
        rbf_driver.update()
    
    # Register the handler
    bpy.app.handlers.frame_change_post.append(frame_change_handler)
    
    # Test the RBF driver by moving the control cube
    control_cube.location = (0.5, 0.5, 0.5)
    rbf_driver.update()
    
    print("RBF Driver example created successfully!")
    print("Move the control cube to see the RBF driver in action.")
    print("The target sphere and helper empty will move and deform based on the control cube's position.")
    
    return rbf_driver


def main():
    # This script should be run from within Blender
    try:
        import bpy
        print("Creating RBF Driver example in Blender...")
        rbf_driver = create_rbf_driver_example()
        print("Done!")
    except ImportError:
        print("This script must be run from within Blender.")


if __name__ == "__main__":
    main()
