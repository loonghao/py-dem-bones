"""
Example of using py-dem-bones with Blender.

This example demonstrates how to implement the DCCInterface for Blender
and use it to compute skinning weights for a Blender mesh.

Note: This example requires Blender to be installed and the script to be run from within Blender.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union

import py_dem_bones as pdb
from py_dem_bones.interfaces import DCCInterface


class BlenderDCCInterface(DCCInterface):
    """
    Implementation of DCCInterface for Blender.
    
    This class provides methods to convert between Blender's data structures
    and the format required by py-dem-bones.
    """
    
    def __init__(self, dem_bones_instance=None):
        """
        Initialize the Blender DCC interface.
        
        Args:
            dem_bones_instance: Optional DemBones or DemBonesExt instance.
                               If not provided, a new instance will be created.
        """
        self.dem_bones = dem_bones_instance or pdb.DemBones()
        self._blender_data = {}
        
    def from_dcc_data(self, 
                     obj_name: str, 
                     armature_name: str, 
                     shape_key_names: Optional[List[str]] = None,
                     **kwargs) -> bool:
        """
        Import data from Blender into DemBones.
        
        Args:
            obj_name: Name of the base mesh object in Blender
            armature_name: Name of the armature object
            shape_key_names: List of shape key names to use as poses
            **kwargs: Additional Blender-specific parameters
                     - use_world_space: Whether to use world space (default: True)
                     - max_influences: Maximum number of influences per vertex (default: 4)
                     - smooth_iterations: Number of smoothing iterations (default: 3)
        
        Returns:
            bool: True if import was successful
        """
        try:
            # Import Blender modules (only available in Blender)
            import bpy
            import mathutils
            
            # Store Blender data for later use
            self._blender_data = {
                'obj_name': obj_name,
                'armature_name': armature_name,
                'shape_key_names': shape_key_names,
                'kwargs': kwargs
            }
            
            # Get parameters from kwargs
            use_world_space = kwargs.get('use_world_space', True)
            max_influences = kwargs.get('max_influences', 4)
            smooth_iterations = kwargs.get('smooth_iterations', 3)
            
            # Get objects
            obj = bpy.data.objects.get(obj_name)
            armature = bpy.data.objects.get(armature_name)
            
            if not obj or not armature:
                print(f"Error: Objects not found: {obj_name}, {armature_name}")
                return False
            
            # Get bones from armature
            bones = [bone.name for bone in armature.data.bones]
            
            # Setup DemBones parameters
            self.dem_bones.nV = len(obj.data.vertices)
            self.dem_bones.nB = len(bones)
            self.dem_bones.nnz = max_influences
            self.dem_bones.weightsSmooth = 0.0001 * smooth_iterations
            
            # Get rest pose vertices
            rest_verts = self._get_vertices(obj, use_world_space)
            self.dem_bones.u = np.array(rest_verts, dtype=np.float64)
            
            # Get shape keys if provided
            if shape_key_names and obj.data.shape_keys:
                # Check if all shape keys exist
                for sk_name in shape_key_names:
                    if sk_name not in obj.data.shape_keys.key_blocks:
                        print(f"Warning: Shape key {sk_name} not found in {obj_name}")
                        shape_key_names.remove(sk_name)
                
                if shape_key_names:
                    self.dem_bones.nF = len(shape_key_names)
                    self.dem_bones.nS = 1
                    self.dem_bones.fStart = np.array([0], dtype=np.int32)
                    self.dem_bones.subjectID = np.zeros(len(shape_key_names), dtype=np.int32)
                    
                    # Collect all shape key vertices
                    all_shape_key_verts = []
                    for sk_name in shape_key_names:
                        # Save current state
                        original_values = {}
                        for kb in obj.data.shape_keys.key_blocks:
                            original_values[kb.name] = kb.value
                            kb.value = 0.0
                        
                        # Set only this shape key to 1.0
                        obj.data.shape_keys.key_blocks[sk_name].value = 1.0
                        
                        # Get vertices with this shape key applied
                        sk_verts = self._get_vertices(obj, use_world_space)
                        all_shape_key_verts.extend(sk_verts)
                        
                        # Restore original state
                        for kb_name, value in original_values.items():
                            obj.data.shape_keys.key_blocks[kb_name].value = value
                    
                    self.dem_bones.v = np.array(all_shape_key_verts, dtype=np.float64)
            
            # If we're using DemBonesExt, set up the skeleton hierarchy
            if isinstance(self.dem_bones, pdb.DemBonesExt):
                # Get bone hierarchy from Blender
                parent_indices = self._get_bone_hierarchy(armature, bones)
                self.dem_bones.parent = np.array(parent_indices, dtype=np.int32)
                self.dem_bones.boneName = bones
                self.dem_bones.bindUpdate = 1
            
            return True
            
        except ImportError:
            print("Error: This script must be run from within Blender.")
            return False
        except Exception as e:
            print(f"Error importing data from Blender: {e}")
            return False
    
    def to_dcc_data(self, apply_weights: bool = True, **kwargs) -> bool:
        """
        Export DemBones data to Blender.
        
        Args:
            apply_weights: Whether to apply the computed weights to the Blender mesh
            **kwargs: Additional Blender-specific parameters
                     - create_vertex_groups: Whether to create new vertex groups (default: True)
                     - clear_existing_weights: Whether to clear existing weights (default: True)
        
        Returns:
            bool: True if export was successful
        """
        try:
            # Import Blender modules
            import bpy
            
            # Check if we have computed weights
            if not hasattr(self.dem_bones, 'get_weights'):
                print("Error: No weights computed. Call compute() first.")
                return False
            
            # Get parameters from kwargs
            create_vertex_groups = kwargs.get('create_vertex_groups', True)
            clear_existing_weights = kwargs.get('clear_existing_weights', True)
            
            # Get data from stored Blender data
            obj_name = self._blender_data.get('obj_name')
            armature_name = self._blender_data.get('armature_name')
            
            if not obj_name or not armature_name:
                print("Error: Missing Blender data. Call from_dcc_data() first.")
                return False
            
            # Get objects
            obj = bpy.data.objects.get(obj_name)
            armature = bpy.data.objects.get(armature_name)
            
            if not obj or not armature:
                print(f"Error: Objects not found: {obj_name}, {armature_name}")
                return False
            
            # Get bones from armature
            bones = [bone.name for bone in armature.data.bones]
            
            # Get computed weights
            weights = self.dem_bones.get_weights()
            
            if apply_weights:
                # Clear existing vertex groups if requested
                if clear_existing_weights:
                    for vg in obj.vertex_groups:
                        obj.vertex_groups.remove(vg)
                
                # Create vertex groups for each bone
                vertex_groups = {}
                for bone_name in bones:
                    if bone_name not in obj.vertex_groups:
                        vg = obj.vertex_groups.new(name=bone_name)
                    else:
                        vg = obj.vertex_groups[bone_name]
                    vertex_groups[bone_name] = vg
                
                # Apply weights to vertex groups
                for vertex_idx in range(len(obj.data.vertices)):
                    for bone_idx, bone_name in enumerate(bones):
                        weight = weights[bone_idx, vertex_idx]
                        if weight > 0.0001:  # Skip very small weights
                            vertex_groups[bone_name].add([vertex_idx], weight, 'REPLACE')
                
                # Make sure the armature modifier exists and is set up correctly
                self._setup_armature_modifier(obj, armature)
                
                print(f"Successfully applied weights to {obj_name}")
            
            return True
            
        except ImportError:
            print("Error: This script must be run from within Blender.")
            return False
        except Exception as e:
            print(f"Error exporting data to Blender: {e}")
            return False
    
    def convert_matrices(self, matrices, from_dcc=True):
        """
        Convert between Blender and DemBones matrix formats.
        
        Args:
            matrices: The matrices to convert
            from_dcc: If True, convert from Blender to DemBones format,
                     otherwise convert from DemBones to Blender format
        
        Returns:
            The converted matrices
        """
        # This is a simplified conversion - in practice, more conversion might be needed
        # Blender uses column-major matrices, same as DemBones, but coordinate system differs
        import mathutils
        
        result = []
        for m in matrices:
            if from_dcc:
                # Convert from Blender to DemBones
                # Apply coordinate system transformation
                m_copy = m.copy()
                # Swap Y and Z axes
                m_copy = self._swap_yz_matrix(m_copy)
                result.append(m_copy)
            else:
                # Convert from DemBones to Blender
                m_copy = m.copy()
                # Swap Y and Z axes back
                m_copy = self._swap_yz_matrix(m_copy)
                result.append(m_copy)
        
        return np.array(result)
    
    def apply_coordinate_system_transform(self, data, from_dcc=True):
        """
        Apply coordinate system transformations between Blender and DemBones.
        
        Blender uses a right-handed Z-up coordinate system, while DemBones
        typically uses a right-handed Y-up system. This method handles
        the conversion between these coordinate systems.
        
        Args:
            data: The data to transform (vertices or matrices)
            from_dcc: If True, transform from Blender to DemBones coordinate system,
                     otherwise transform from DemBones to Blender coordinate system
        
        Returns:
            The transformed data
        """
        # Blender and DemBones both use right-handed coordinate systems,
        # but Blender is Z-up while DemBones is typically Y-up
        if isinstance(data, np.ndarray) and data.shape[-1] >= 3:
            result = data.copy()
            if from_dcc:
                # Blender to DemBones (Z-up to Y-up)
                result[..., [1, 2]] = result[..., [2, 1]]
                result[..., 1] *= -1  # Flip Y
            else:
                # DemBones to Blender (Y-up to Z-up)
                result[..., 1] *= -1  # Flip Y
                result[..., [1, 2]] = result[..., [2, 1]]
            return result
        return data
    
    # Helper methods
    def _get_vertices(self, obj, world_space=True):
        """Get vertices from a Blender mesh."""
        import bpy
        
        # Get vertex positions
        vertices = []
        
        if world_space:
            # Get world space coordinates
            world_matrix = obj.matrix_world
            for v in obj.data.vertices:
                # Transform vertex to world space
                world_pos = world_matrix @ v.co
                vertices.append([world_pos.x, world_pos.y, world_pos.z])
        else:
            # Get local space coordinates
            for v in obj.data.vertices:
                vertices.append([v.co.x, v.co.y, v.co.z])
                
        return vertices
    
    def _get_bone_hierarchy(self, armature, bone_names):
        """Get the parent indices for each bone in the list."""
        parent_indices = []
        
        for bone_name in bone_names:
            bone = armature.data.bones.get(bone_name)
            if bone and bone.parent and bone.parent.name in bone_names:
                parent_index = bone_names.index(bone.parent.name)
            else:
                parent_index = -1  # No parent or parent not in our bone list
            parent_indices.append(parent_index)
            
        return parent_indices
    
    def _setup_armature_modifier(self, obj, armature):
        """Set up the armature modifier for the object."""
        import bpy
        
        # Check if an armature modifier already exists
        armature_modifier = None
        for mod in obj.modifiers:
            if mod.type == 'ARMATURE' and mod.object == armature:
                armature_modifier = mod
                break
        
        # Create a new armature modifier if needed
        if not armature_modifier:
            armature_modifier = obj.modifiers.new(name="Armature", type='ARMATURE')
            armature_modifier.object = armature
            armature_modifier.use_vertex_groups = True
            armature_modifier.use_bone_envelopes = False
    
    def _swap_yz_matrix(self, matrix):
        """Swap Y and Z axes in a matrix."""
        # Create a copy of the matrix
        result = matrix.copy()
        
        # Swap Y and Z rows and columns
        result[[1, 2], :] = result[[2, 1], :]
        result[:, [1, 2]] = result[:, [2, 1]]
        
        # Negate Y components (or Z after swapping)
        result[1, :] *= -1
        result[:, 1] *= -1
        
        return result


def example_usage():
    """Example of how to use the BlenderDCCInterface in Blender."""
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
        cube.name = 'TestCube'
        
        # Subdivide the cube
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.subdivide(number_cuts=1)
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Create an armature
        bpy.ops.object.armature_add(location=(0, 0, 0))
        armature = bpy.context.active_object
        armature.name = 'TestArmature'
        
        # Edit the armature
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Get the first bone
        bone1 = armature.data.edit_bones[0]
        bone1.name = 'Bone1'
        bone1.head = (-1, 0, 0)
        bone1.tail = (0, 0, 0)
        
        # Create a second bone
        bone2 = armature.data.edit_bones.new('Bone2')
        bone2.head = (0, 0, 0)
        bone2.tail = (1, 0, 0)
        bone2.parent = bone1
        
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Create a shape key for the cube
        bpy.context.view_layer.objects.active = cube
        cube.shape_key_add(name='Basis')
        key1 = cube.shape_key_add(name='Key1')
        
        # Modify the shape key
        for i in range(4):  # Move top vertices up
            key1.data[i + 4].co.z += 1.0
        
        return cube.name, armature.name
    
    # Create the test scene
    cube_name, armature_name = create_test_scene()
    
    # Create DemBones instance
    dem_bones = pdb.DemBones()
    
    # Create Blender interface
    blender_interface = BlenderDCCInterface(dem_bones)
    
    # Import data from Blender
    success = blender_interface.from_dcc_data(
        obj_name=cube_name,
        armature_name=armature_name,
        shape_key_names=['Key1'],
        use_world_space=True,
        max_influences=4
    )
    
    if success:
        # Compute skinning weights
        dem_bones.compute()
        
        # Export data back to Blender
        blender_interface.to_dcc_data(
            apply_weights=True,
            create_vertex_groups=True,
            clear_existing_weights=True
        )
        
        print("Successfully computed and applied skinning weights!")
    else:
        print("Failed to import data from Blender.")


if __name__ == "__main__":
    # This script should be run from within Blender
    try:
        import bpy
        example_usage()
    except ImportError:
        print("This script must be run from within Blender.")
