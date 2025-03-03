"""
Example of using py-dem-bones with Unreal Engine.

This example demonstrates how to implement the DCCInterface for Unreal Engine
and use it to compute skinning weights for an Unreal skeletal mesh.

Note: This example requires Unreal Engine Python API to be enabled and the script 
to be run from within Unreal Engine's Python environment.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union

import py_dem_bones as pdb
from py_dem_bones.interfaces import DCCInterface


class UnrealDCCInterface(DCCInterface):
    """
    Implementation of DCCInterface for Unreal Engine.
    
    This class provides methods to convert between Unreal Engine's data structures
    and the format required by py-dem-bones.
    """
    
    def __init__(self, dem_bones_instance=None):
        """
        Initialize the Unreal Engine DCC interface.
        
        Args:
            dem_bones_instance: Optional DemBones or DemBonesExt instance.
                               If not provided, a new instance will be created.
        """
        self.dem_bones = dem_bones_instance or pdb.DemBones()
        self._unreal_data = {}
        
    def from_dcc_data(self, 
                     skeletal_mesh_path: str, 
                     skeleton_path: str, 
                     morph_target_names: Optional[List[str]] = None,
                     **kwargs) -> bool:
        """
        Import data from Unreal Engine into DemBones.
        
        Args:
            skeletal_mesh_path: Path to the skeletal mesh asset in Unreal
            skeleton_path: Path to the skeleton asset in Unreal
            morph_target_names: List of morph target names to use as poses
            **kwargs: Additional Unreal-specific parameters
                     - use_world_space: Whether to use world space (default: True)
                     - max_influences: Maximum number of influences per vertex (default: 4)
                     - smooth_iterations: Number of smoothing iterations (default: 3)
                     - lod_index: LOD index to use (default: 0)
        
        Returns:
            bool: True if import was successful
        """
        try:
            # Import Unreal modules (only available in Unreal Engine)
            import unreal
            
            # Store Unreal data for later use
            self._unreal_data = {
                'skeletal_mesh_path': skeletal_mesh_path,
                'skeleton_path': skeleton_path,
                'morph_target_names': morph_target_names,
                'kwargs': kwargs
            }
            
            # Get parameters from kwargs
            use_world_space = kwargs.get('use_world_space', True)
            max_influences = kwargs.get('max_influences', 4)
            smooth_iterations = kwargs.get('smooth_iterations', 3)
            lod_index = kwargs.get('lod_index', 0)
            
            # Load assets
            skeletal_mesh = unreal.EditorAssetLibrary.load_asset(skeletal_mesh_path)
            skeleton = unreal.EditorAssetLibrary.load_asset(skeleton_path)
            
            if not skeletal_mesh or not skeleton:
                print(f"Error: Assets not found: {skeletal_mesh_path}, {skeleton_path}")
                return False
            
            # Get skeleton bones
            skeleton_data = unreal.SkeletonEditorLibrary.get_skeleton_bones_names(skeleton)
            bones = [bone.to_string() for bone in skeleton_data]
            
            # Get mesh data
            mesh_import_data = unreal.SkeletalMeshEditorLibrary.get_skeletal_mesh_lod_build_settings(skeletal_mesh, lod_index)
            
            # Get vertices from the skeletal mesh
            mesh_data = unreal.SkeletalMeshEditorLibrary.get_skeletal_mesh_lod_model(skeletal_mesh, lod_index)
            vertices = self._get_vertices_from_mesh_data(mesh_data, use_world_space)
            
            # Setup DemBones parameters
            self.dem_bones.nV = len(vertices)
            self.dem_bones.nB = len(bones)
            self.dem_bones.nnz = max_influences
            self.dem_bones.weightsSmooth = 0.0001 * smooth_iterations
            
            # Set rest pose
            self.dem_bones.u = np.array(vertices, dtype=np.float64)
            
            # Get morph targets if provided
            if morph_target_names:
                # Check if all morph targets exist
                valid_morph_targets = []
                for mt_name in morph_target_names:
                    if unreal.SkeletalMeshEditorLibrary.has_morph_target(skeletal_mesh, mt_name):
                        valid_morph_targets.append(mt_name)
                    else:
                        print(f"Warning: Morph target {mt_name} not found in {skeletal_mesh_path}")
                
                if valid_morph_targets:
                    self.dem_bones.nF = len(valid_morph_targets)
                    self.dem_bones.nS = 1
                    self.dem_bones.fStart = np.array([0], dtype=np.int32)
                    self.dem_bones.subjectID = np.zeros(len(valid_morph_targets), dtype=np.int32)
                    
                    # Collect all morph target vertices
                    all_morph_vertices = []
                    for mt_name in valid_morph_targets:
                        morph_data = unreal.SkeletalMeshEditorLibrary.get_morph_target_delta_vertices(
                            skeletal_mesh, mt_name, lod_index
                        )
                        
                        # Apply morph deltas to base vertices
                        morph_vertices = vertices.copy()
                        for i, delta in enumerate(morph_data):
                            vertex_id = delta.source_vertex_id
                            if vertex_id < len(morph_vertices):
                                morph_vertices[vertex_id][0] += delta.position_delta.x
                                morph_vertices[vertex_id][1] += delta.position_delta.y
                                morph_vertices[vertex_id][2] += delta.position_delta.z
                        
                        all_morph_vertices.extend(morph_vertices)
                    
                    self.dem_bones.v = np.array(all_morph_vertices, dtype=np.float64)
            
            # If we're using DemBonesExt, set up the skeleton hierarchy
            if isinstance(self.dem_bones, pdb.DemBonesExt):
                # Get bone hierarchy from Unreal
                parent_indices = self._get_bone_hierarchy(skeleton, bones)
                self.dem_bones.parent = np.array(parent_indices, dtype=np.int32)
                self.dem_bones.boneName = bones
                self.dem_bones.bindUpdate = 1
            
            return True
            
        except ImportError:
            print("Error: This script must be run from within Unreal Engine with Python API enabled.")
            return False
        except Exception as e:
            print(f"Error importing data from Unreal Engine: {e}")
            return False
    
    def to_dcc_data(self, apply_weights: bool = True, **kwargs) -> bool:
        """
        Export DemBones data to Unreal Engine.
        
        Args:
            apply_weights: Whether to apply the computed weights to the Unreal skeletal mesh
            **kwargs: Additional Unreal-specific parameters
                     - create_new_asset: Whether to create a new skeletal mesh asset (default: False)
                     - new_asset_path: Path for the new asset if create_new_asset is True
                     - lod_index: LOD index to modify (default: 0)
        
        Returns:
            bool: True if export was successful
        """
        try:
            # Import Unreal modules
            import unreal
            
            # Check if we have computed weights
            if not hasattr(self.dem_bones, 'get_weights'):
                print("Error: No weights computed. Call compute() first.")
                return False
            
            # Get parameters from kwargs
            create_new_asset = kwargs.get('create_new_asset', False)
            new_asset_path = kwargs.get('new_asset_path', '')
            lod_index = kwargs.get('lod_index', 0)
            
            # Get data from stored Unreal data
            skeletal_mesh_path = self._unreal_data.get('skeletal_mesh_path')
            skeleton_path = self._unreal_data.get('skeleton_path')
            
            if not skeletal_mesh_path or not skeleton_path:
                print("Error: Missing Unreal data. Call from_dcc_data() first.")
                return False
            
            # Load assets
            skeletal_mesh = unreal.EditorAssetLibrary.load_asset(skeletal_mesh_path)
            skeleton = unreal.EditorAssetLibrary.load_asset(skeleton_path)
            
            if not skeletal_mesh or not skeleton:
                print(f"Error: Assets not found: {skeletal_mesh_path}, {skeleton_path}")
                return False
            
            # Get skeleton bones
            skeleton_data = unreal.SkeletonEditorLibrary.get_skeleton_bones_names(skeleton)
            bones = [bone.to_string() for bone in skeleton_data]
            
            # Get computed weights
            weights = self.dem_bones.get_weights()
            
            if apply_weights:
                # Create a new asset if requested
                target_mesh = skeletal_mesh
                if create_new_asset and new_asset_path:
                    # Duplicate the asset
                    if unreal.EditorAssetLibrary.does_asset_exist(new_asset_path):
                        unreal.EditorAssetLibrary.delete_asset(new_asset_path)
                    
                    unreal.EditorAssetLibrary.duplicate_asset(skeletal_mesh_path, new_asset_path)
                    target_mesh = unreal.EditorAssetLibrary.load_asset(new_asset_path)
                    
                    if not target_mesh:
                        print(f"Error: Failed to create new asset at {new_asset_path}")
                        return False
                
                # Apply weights to the skeletal mesh
                self._apply_weights_to_skeletal_mesh(target_mesh, bones, weights, lod_index)
                
                # Save the modified asset
                unreal.EditorAssetLibrary.save_asset(target_mesh.get_path_name())
                
                print(f"Successfully applied weights to {target_mesh.get_path_name()}")
            
            return True
            
        except ImportError:
            print("Error: This script must be run from within Unreal Engine with Python API enabled.")
            return False
        except Exception as e:
            print(f"Error exporting data to Unreal Engine: {e}")
            return False
    
    def _get_vertices_from_mesh_data(self, mesh_data, use_world_space=True):
        """
        Extract vertex positions from Unreal mesh data.
        
        Args:
            mesh_data: Unreal mesh data object
            use_world_space: Whether to return vertices in world space
        
        Returns:
            List of vertex positions as [x, y, z] coordinates
        """
        import unreal
        
        vertices = []
        
        # Get vertex positions from mesh sections
        for section_idx in range(mesh_data.get_editor_property('sections').num()):
            section = mesh_data.get_editor_property('sections').get(section_idx)
            section_vertices = section.get_editor_property('soft_vertices')
            
            for vertex in section_vertices:
                position = vertex.get_editor_property('position')
                
                # Convert to world space if requested
                if use_world_space:
                    # In a real implementation, we would apply the mesh's transform here
                    # For simplicity, we're just using the local space coordinates
                    pass
                
                vertices.append([position.x, position.y, position.z])
        
        return vertices
    
    def _get_bone_hierarchy(self, skeleton, bone_names):
        """
        Get parent indices for each bone in the skeleton.
        
        Args:
            skeleton: Unreal skeleton asset
            bone_names: List of bone names
        
        Returns:
            List of parent indices for each bone
        """
        import unreal
        
        parent_indices = []
        
        # Get the bone hierarchy from the skeleton
        for bone_name in bone_names:
            bone_index = bone_names.index(bone_name)
            bone_info = unreal.SkeletonEditorLibrary.get_bone_info(skeleton, unreal.Name(bone_name))
            parent_name = bone_info.get_editor_property('parent_name').to_string()
            
            if parent_name and parent_name in bone_names:
                parent_index = bone_names.index(parent_name)
            else:
                parent_index = -1  # Root bone
            
            parent_indices.append(parent_index)
        
        return parent_indices
    
    def _apply_weights_to_skeletal_mesh(self, skeletal_mesh, bone_names, weights, lod_index=0):
        """
        Apply computed weights to an Unreal skeletal mesh.
        
        Args:
            skeletal_mesh: Unreal skeletal mesh asset
            bone_names: List of bone names
            weights: Computed skinning weights
            lod_index: LOD index to modify
        """
        import unreal
        
        # Get mesh data
        mesh_data = unreal.SkeletalMeshEditorLibrary.get_skeletal_mesh_lod_model(skeletal_mesh, lod_index)
        
        # Prepare new skin weights
        new_skin_weights = []
        
        # Process each section
        vertex_offset = 0
        for section_idx in range(mesh_data.get_editor_property('sections').num()):
            section = mesh_data.get_editor_property('sections').get(section_idx)
            section_vertices = section.get_editor_property('soft_vertices')
            
            # Process each vertex in this section
            for i in range(len(section_vertices)):
                vertex_id = vertex_offset + i
                
                if vertex_id < len(weights):
                    # Get weights for this vertex
                    vertex_weights = weights[vertex_id]
                    
                    # Create influence entries
                    influences = []
                    for bone_idx, weight in enumerate(vertex_weights):
                        if weight > 0.01:  # Only include significant weights
                            influence = unreal.SkeletalMeshVertexInfluence()
                            influence.set_editor_property('bone_index', bone_idx)
                            influence.set_editor_property('weight', float(weight))
                            influences.append(influence)
                    
                    # Sort influences by weight (descending)
                    influences.sort(key=lambda infl: infl.get_editor_property('weight'), reverse=True)
                    
                    # Limit to max influences
                    influences = influences[:self.dem_bones.nnz]
                    
                    # Normalize weights
                    total_weight = sum(infl.get_editor_property('weight') for infl in influences)
                    if total_weight > 0:
                        for infl in influences:
                            infl.set_editor_property('weight', infl.get_editor_property('weight') / total_weight)
                    
                    # Add to new skin weights
                    skin_weight = unreal.SkeletalMeshVertexSkinWeight()
                    skin_weight.set_editor_property('influences', influences)
                    new_skin_weights.append(skin_weight)
            
            vertex_offset += len(section_vertices)
        
        # Apply new skin weights
        unreal.SkeletalMeshEditorLibrary.set_skeletal_mesh_lod_skin_weights(
            skeletal_mesh, lod_index, new_skin_weights
        )


def example_usage():
    """
    Example of how to use the UnrealDCCInterface in Unreal Engine.
    
    This function demonstrates the typical workflow for computing skinning weights
    for an Unreal Engine skeletal mesh using py-dem-bones.
    """
    try:
        import unreal
        
        # Create a DemBonesExt instance for hierarchical skinning
        dem_bones = pdb.DemBonesExt()
        
        # Configure DemBones parameters
        dem_bones.nIters = 10
        dem_bones.nInitIters = 5
        dem_bones.nTransIters = 3
        dem_bones.nWeightsIters = 3
        
        # Create the Unreal DCC interface
        unreal_interface = UnrealDCCInterface(dem_bones)
        
        # Define assets to use
        skeletal_mesh_path = "/Game/Characters/Mannequin/Meshes/SK_Mannequin"
        skeleton_path = "/Game/Characters/Mannequin/Meshes/UE4_Mannequin_Skeleton"
        morph_targets = ["Smile", "Frown", "EyesBlink"]
        
        # Import data from Unreal Engine
        print("Importing data from Unreal Engine...")
        success = unreal_interface.from_dcc_data(
            skeletal_mesh_path=skeletal_mesh_path,
            skeleton_path=skeleton_path,
            morph_target_names=morph_targets,
            max_influences=4,
            smooth_iterations=3,
            lod_index=0
        )
        
        if not success:
            print("Failed to import data from Unreal Engine.")
            return
        
        # Compute skinning weights
        print("Computing skinning weights...")
        dem_bones.compute()
        
        # Export data back to Unreal Engine
        print("Exporting data to Unreal Engine...")
        success = unreal_interface.to_dcc_data(
            apply_weights=True,
            create_new_asset=True,
            new_asset_path="/Game/Characters/Mannequin/Meshes/SK_Mannequin_DemBones",
            lod_index=0
        )
        
        if success:
            print("Successfully computed and applied skinning weights!")
        else:
            print("Failed to export data to Unreal Engine.")
        
    except ImportError:
        print("This example must be run from within Unreal Engine with Python API enabled.")
    except Exception as e:
        print(f"Error in example: {e}")


if __name__ == "__main__":
    # This script should be run from within Unreal Engine
    try:
        example_usage()
    except Exception as e:
        print(f"Error: {e}")
