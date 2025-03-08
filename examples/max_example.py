"""
Example of using py-dem-bones with Autodesk 3ds Max.

This example demonstrates how to implement the DCCInterface for 3ds Max
and use it to compute skinning weights for a 3ds Max mesh.

Note: This example requires 3ds Max 2024+ to be installed and the script to be run from within 3ds Max.
"""

import numpy as np
from typing import List, Optional

import py_dem_bones as pdb
from py_dem_bones.interfaces import DCCInterface


class MaxDCCInterface(DCCInterface):
    """
    Implementation of DCCInterface for Autodesk 3ds Max.
    
    This class provides methods to convert between 3ds Max's data structures
    and the format required by py-dem-bones.
    """
    
    def __init__(self, dem_bones_instance=None):
        """
        Initialize the 3ds Max DCC interface.
        
        Args:
            dem_bones_instance: Optional DemBones or DemBonesExt instance.
                               If not provided, a new instance will be created.
        """
        self.dem_bones = dem_bones_instance or pdb.DemBones()
        self._max_data = {}
        
    def from_dcc_data(self, 
                     mesh_node: str, 
                     bone_nodes: List[str], 
                     morph_targets: Optional[List[str]] = None,
                     **kwargs) -> bool:
        """
        Import data from 3ds Max into DemBones.
        
        Args:
            mesh_node: Name of the base mesh in 3ds Max
            bone_nodes: List of bone node names to use for skinning
            morph_targets: List of morph target mesh names
            **kwargs: Additional 3ds Max-specific parameters
                     - use_world_space: Whether to use world space (default: True)
                     - max_influences: Maximum number of influences per vertex (default: 4)
                     - smooth_iterations: Number of smoothing iterations (default: 3)
        
        Returns:
            bool: True if import was successful
        """
        try:
            # Import 3ds Max Python API (only available in 3ds Max)
            import pymxs
            rt = pymxs.runtime
            
            # Store 3ds Max data for later use
            self._max_data = {
                'mesh_node': mesh_node,
                'bone_nodes': bone_nodes,
                'morph_targets': morph_targets,
                'kwargs': kwargs
            }
            
            # Get parameters from kwargs
            use_world_space = kwargs.get('use_world_space', True)
            max_influences = kwargs.get('max_influences', 4)
            smooth_iterations = kwargs.get('smooth_iterations', 3)
            
            # Get mesh and bones from scene
            mesh = rt.getNodeByName(mesh_node)
            bones = [rt.getNodeByName(bone) for bone in bone_nodes]
            
            if not mesh or None in bones:
                print(f"Error: Objects not found: {mesh_node} or one of the bones")
                return False
            
            # Setup DemBones parameters
            self.dem_bones.nV = rt.getNumVerts(mesh)
            self.dem_bones.nB = len(bones)
            self.dem_bones.nnz = max_influences
            self.dem_bones.weightsSmooth = 0.0001 * smooth_iterations
            
            # Get rest pose vertices
            rest_verts = self._get_vertices(mesh, use_world_space)
            self.dem_bones.u = np.array(rest_verts, dtype=np.float64)
            
            # Get morph targets if provided
            if morph_targets:
                morph_target_meshes = [rt.getNodeByName(mt) for mt in morph_targets]
                if None in morph_target_meshes:
                    print(f"Warning: Some morph targets not found")
                    # Filter out None values
                    morph_target_meshes = [mt for mt in morph_target_meshes if mt is not None]
                    morph_targets = [mt for i, mt in enumerate(morph_targets) if morph_target_meshes[i] is not None]
                
                if morph_target_meshes:
                    self.dem_bones.nF = len(morph_target_meshes)
                    self.dem_bones.nS = 1
                    self.dem_bones.fStart = np.array([0], dtype=np.int32)
                    self.dem_bones.subjectID = np.zeros(len(morph_target_meshes), dtype=np.int32)
                    
                    # Collect all morph target vertices
                    all_morph_verts = []
                    for morph_mesh in morph_target_meshes:
                        morph_verts = self._get_vertices(morph_mesh, use_world_space)
                        all_morph_verts.extend(morph_verts)
                    
                    self.dem_bones.v = np.array(all_morph_verts, dtype=np.float64)
            
            # If we're using DemBonesExt, set up the skeleton hierarchy
            if isinstance(self.dem_bones, pdb.DemBonesExt):
                # Get bone hierarchy from 3ds Max
                parent_indices = self._get_bone_hierarchy(bones)
                self.dem_bones.parent = np.array(parent_indices, dtype=np.int32)
                self.dem_bones.boneName = bone_nodes
                self.dem_bones.bindUpdate = 1
            
            return True
            
        except ImportError:
            print("Error: This script must be run from within 3ds Max.")
            return False
        except Exception as e:
            print(f"Error importing data from 3ds Max: {e}")
            return False
    
    def to_dcc_data(self, apply_weights: bool = True, **kwargs) -> bool:
        """
        Export DemBones data to 3ds Max.
        
        Args:
            apply_weights: Whether to apply the computed weights to the 3ds Max mesh
            **kwargs: Additional 3ds Max-specific parameters
                     - create_skin_modifier: Whether to create a new Skin modifier (default: True)
                     - normalize_weights: Whether to normalize weights (default: True)
        
        Returns:
            bool: True if export was successful
        """
        try:
            # Import 3ds Max Python API
            import pymxs
            rt = pymxs.runtime
            
            # Check if we have computed weights
            if not hasattr(self.dem_bones, 'get_weights'):
                print("Error: No weights computed. Call compute() first.")
                return False
            
            # Get parameters from kwargs
            create_skin_modifier = kwargs.get('create_skin_modifier', True)
            normalize_weights = kwargs.get('normalize_weights', True)
            
            # Get data from stored 3ds Max data
            mesh_node = self._max_data.get('mesh_node')
            bone_nodes = self._max_data.get('bone_nodes')
            
            if not mesh_node or not bone_nodes:
                print("Error: Missing 3ds Max data. Call from_dcc_data() first.")
                return False
            
            # Get mesh and bones from scene
            mesh = rt.getNodeByName(mesh_node)
            bones = [rt.getNodeByName(bone) for bone in bone_nodes]
            
            if not mesh or None in bones:
                print(f"Error: Objects not found: {mesh_node} or one of the bones")
                return False
            
            # Get computed weights
            weights = self.dem_bones.get_weights()
            
            if apply_weights:
                # Create or get Skin modifier
                skin_mod = None
                
                if create_skin_modifier:
                    # Remove existing Skin modifiers
                    for i in range(rt.modPanel.getModifierCount(mesh)):
                        mod = rt.modPanel.getModifier(mesh, i)
                        if rt.classOf(mod) == rt.Skin:
                            rt.deleteModifier(mesh, mod)
                    
                    # Create new Skin modifier
                    skin_mod = rt.Skin()
                    rt.addModifier(mesh, skin_mod)
                else:
                    # Find existing Skin modifier
                    for i in range(rt.modPanel.getModifierCount(mesh)):
                        mod = rt.modPanel.getModifier(mesh, i)
                        if rt.classOf(mod) == rt.Skin:
                            skin_mod = mod
                            break
                
                if not skin_mod:
                    print("Error: No Skin modifier found and create_skin_modifier is False.")
                    return False
                
                # Add bones to Skin modifier
                for bone in bones:
                    rt.skinOps.addBone(skin_mod, bone, 0)
                
                # Apply weights to Skin modifier
                self._apply_weights_to_skin_modifier(skin_mod, mesh, bones, weights)
                
                print(f"Successfully applied weights to {mesh_node}")
            
            return True
            
        except ImportError:
            print("Error: This script must be run from within 3ds Max.")
            return False
        except Exception as e:
            print(f"Error exporting data to 3ds Max: {e}")
            return False
    
    def _get_vertices(self, mesh, use_world_space=True):
        """
        Get vertices from a 3ds Max mesh.
        
        Args:
            mesh: 3ds Max mesh node
            use_world_space: Whether to get vertices in world space
            
        Returns:
            List of vertex positions as [x1, y1, z1, x2, y2, z2, ...]
        """
        import pymxs
        rt = pymxs.runtime
        
        verts = []
        num_verts = rt.getNumVerts(mesh)
        
        for i in range(1, num_verts + 1):  # 3ds Max indices are 1-based
            if use_world_space:
                # Get vertex in world space
                pos = rt.getVert(mesh, i)
                pos = rt.point3(pos.x, pos.y, pos.z)
                pos = rt.execute(f"in coordsys world {mesh}.verts[{i}].pos")
            else:
                # Get vertex in local space
                pos = rt.getVert(mesh, i)
            
            verts.extend([pos.x, pos.y, pos.z])
        
        return verts
    
    def _get_bone_hierarchy(self, bones):
        """
        Get bone hierarchy from 3ds Max bones.
        
        Args:
            bones: List of 3ds Max bone nodes
            
        Returns:
            List of parent indices for each bone (-1 for root bones)
        """
        import pymxs
        rt = pymxs.runtime
        
        parent_indices = []
        
        for bone in bones:
            parent = bone.parent
            if parent is None or parent not in bones:
                parent_indices.append(-1)  # Root bone
            else:
                parent_indices.append(bones.index(parent))
        
        return parent_indices
    
    def _apply_weights_to_skin_modifier(self, skin_mod, mesh, bones, weights):
        """
        Apply weights to a 3ds Max Skin modifier.
        
        Args:
            skin_mod: 3ds Max Skin modifier
            mesh: 3ds Max mesh node
            bones: List of 3ds Max bone nodes
            weights: Weights matrix from DemBones
        """
        import pymxs
        rt = pymxs.runtime
        
        num_verts = rt.getNumVerts(mesh)
        
        # For each vertex
        for v_idx in range(num_verts):
            # Get non-zero weights for this vertex
            v_weights = []
            for b_idx in range(len(bones)):
                weight = weights[v_idx * len(bones) + b_idx]
                if weight > 0.0001:  # Threshold to avoid very small weights
                    v_weights.append((b_idx, weight))
            
            # Sort by weight (descending)
            v_weights.sort(key=lambda x: x[1], reverse=True)
            
            # Apply weights to vertex
            rt.skinOps.ReplaceVertexWeights(skin_mod, v_idx + 1, 
                                           rt.point3Array([bone_idx + 1 for bone_idx, _ in v_weights]), 
                                           rt.point3Array([weight for _, weight in v_weights]))


def example_usage():
    """
    Example of how to use the MaxDCCInterface in 3ds Max.
    
    This function demonstrates the typical workflow:
    1. Create a DemBonesExt instance
    2. Create a MaxDCCInterface with the DemBonesExt instance
    3. Import data from 3ds Max
    4. Compute weights
    5. Export weights back to 3ds Max
    
    To run this example in 3ds Max:
    1. Create a mesh and a skeleton
    2. Run this script from the MAXScript Listener
    3. Call example_usage() with the appropriate parameters
    """
    try:
        import pymxs
        rt = pymxs.runtime
        
        # Create a DemBonesExt instance
        dem_bones = pdb.DemBonesExt()
        
        # Create a MaxDCCInterface with the DemBonesExt instance
        interface = MaxDCCInterface(dem_bones)
        
        # Get the selected mesh
        selected = rt.selection
        if len(selected) == 0:
            print("Error: No objects selected. Please select a mesh.")
            return
        
        mesh = selected[0]
        mesh_name = mesh.name
        
        # Find bones in the scene
        # This is a simple example - in a real scenario, you might want to select bones manually
        all_nodes = rt.objects
        bone_nodes = []
        for node in all_nodes:
            if rt.isKindOf(node, rt.BoneSys.Bone) or rt.isKindOf(node, rt.Biped_Object):
                bone_nodes.append(node.name)
        
        if not bone_nodes:
            print("Error: No bones found in the scene.")
            return
        
        print(f"Using mesh: {mesh_name}")
        print(f"Found {len(bone_nodes)} bones: {', '.join(bone_nodes)}")
        
        # Import data from 3ds Max
        success = interface.from_dcc_data(
            mesh_node=mesh_name,
            bone_nodes=bone_nodes,
            morph_targets=None,  # No morph targets in this example
            use_world_space=True,
            max_influences=4,
            smooth_iterations=3
        )
        
        if not success:
            print("Error: Failed to import data from 3ds Max.")
            return
        
        # Compute weights
        print("Computing weights...")
        interface.dem_bones.compute()
        
        # Export weights back to 3ds Max
        success = interface.to_dcc_data(
            apply_weights=True,
            create_skin_modifier=True,
            normalize_weights=True
        )
        
        if not success:
            print("Error: Failed to export weights to 3ds Max.")
            return
        
        print("Successfully computed and applied weights!")
        
    except ImportError:
        print("Error: This script must be run from within 3ds Max.")
    except Exception as e:
        print(f"Error in example_usage: {e}")


if __name__ == "__main__":
    # This script should be run from within 3ds Max
    try:
        import pymxs
        print("3ds Max detected. Run example_usage() to compute weights.")
    except ImportError:
        print("Error: This script must be run from within 3ds Max.")
