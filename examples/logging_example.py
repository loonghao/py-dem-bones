#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Logging Example

This script demonstrates how to use py_dem_bones logging functionality.
"""

import numpy as np
import py_dem_bones as pdb


def main():
    # Configure logging system
    pdb.configure_logging(
        level=pdb.LogLevel.DEBUG,  # Set log level to DEBUG
        to_console=True,           # Output to console
        to_python=True,            # Forward to Python logging system
        log_file="dem_bones.log"   # Output to file
    )
    
    # Get logger, can be used directly
    logger = pdb.get_logger()
    logger.info("Using Python logger")
    
    # Can also use convenience functions
    pdb.info("This message will be logged to both C++ and Python logging systems")
    pdb.debug("This is a debug message")
    
    # Create DemBones instance
    dem_bones = pdb.DemBonesWrapper()
    
    # Set basic parameters
    dem_bones.num_bones = 2
    dem_bones.num_vertices = 10
    dem_bones.num_iterations = 10
    dem_bones.weight_smoothness = 0.1
    dem_bones.max_influences = 4
    
    # Set bone names
    dem_bones.set_bone_names("bone1", "bone2")
    
    # Set vertex data (randomly generated)
    vertices = np.random.rand(3, dem_bones.num_vertices)
    dem_bones.set_rest_pose(vertices)
    
    # Set target pose (slightly modified vertex positions)
    target_vertices = vertices + np.random.normal(0, 0.1, vertices.shape)
    dem_bones.set_target_vertices(0, target_vertices)
    
    # Perform computation
    pdb.info("Starting weight and transform computation")
    success, error_msg = dem_bones.compute()
    
    if success:
        pdb.info("Computation completed successfully")
        # Get computation results
        weights = dem_bones.get_weights()
        transforms = dem_bones.get_transformations()
        
        # Output summary
        pdb.info(f"Weight matrix shape: {weights.shape}")
        pdb.info(f"Transform matrix shape: {transforms.shape}")
    else:
        pdb.error(f"Computation failed: {error_msg}")
    
    # Use extended version
    pdb.info("\nUsing DemBonesExt for computation")
    dem_bones_ext = pdb.DemBonesExtWrapper()
    
    # Set same parameters
    dem_bones_ext.num_bones = 2
    dem_bones_ext.num_vertices = 10
    dem_bones_ext.num_iterations = 10
    dem_bones_ext.weight_smoothness = 0.1
    dem_bones_ext.max_influences = 4
    dem_bones_ext.bind_update = True  # Extended version-specific parameter
    
    # Set same data
    dem_bones_ext.set_bone_names("bone1", "bone2")
    dem_bones_ext.set_rest_pose(vertices)
    dem_bones_ext.set_target_vertices(0, target_vertices)
    
    # Perform computation
    pdb.info("Starting DemBonesExt computation")
    success, error_msg = dem_bones_ext.compute()
    
    if success:
        pdb.info("DemBonesExt computation completed successfully")
        # Get computation results
        weights = dem_bones_ext.get_weights()
        transforms = dem_bones_ext.get_transformations()
        
        # Output summary
        pdb.info(f"DemBonesExt weight matrix shape: {weights.shape}")
        pdb.info(f"DemBonesExt transform matrix shape: {transforms.shape}")
    else:
        pdb.error(f"DemBonesExt computation failed: {error_msg}")


if __name__ == "__main__":
    main()
