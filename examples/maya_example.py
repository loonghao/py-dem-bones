"""
Example of using py-dem-bones with Autodesk Maya.

This example demonstrates how to implement the DCCInterface for Maya
and use it to compute skinning weights for a Maya mesh.

Note: This example requires Maya to be installed and the script to be run from within Maya.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union

import py_dem_bones as pdb
from py_dem_bones.interfaces import DCCInterface


class MayaDCCInterface(DCCInterface):
    """
    Implementation of DCCInterface for Autodesk Maya.
    
    This class provides methods to convert between Maya's data structures
    and the format required by py-dem-bones.
    """
    
    def __init__(self, dem_bones_instance=None):
        """
        Initialize the Maya DCC interface.
        
        Args:
            dem_bones_instance: Optional DemBones or DemBonesExt instance.
                               If not provided, a new instance will be created.
        """
        self.dem_bones = dem_bones_instance or pdb.DemBones()
        self._maya_data = {}
        
    def from_dcc_data(self, 
                     mesh_name: str, 
                     joint_names: List[str], 
                     anim_mesh_names: Optional[List[str]] = None,
                     **kwargs) -> bool:
        """
        Import data from Maya into DemBones.
        
        Args:
            mesh_name: Name of the base mesh in Maya
            joint_names: List of joint names to use for skinning
            anim_mesh_names: List of animated mesh names (blendshapes or poses)
            **kwargs: Additional Maya-specific parameters
                     - use_world_space: Whether to use world space (default: True)
                     - max_influences: Maximum number of influences per vertex (default: 4)
                     - smooth_iterations: Number of smoothing iterations (default: 3)
        
        Returns:
            bool: True if import was successful
        """
        try:
            # Import Maya commands (only available in Maya)
            import maya.cmds as cmds
            
            # Store Maya data for later use
            self._maya_data = {
                'mesh_name': mesh_name,
                'joint_names': joint_names,
                'anim_mesh_names': anim_mesh_names,
                'kwargs': kwargs
            }
            
            # Get parameters from kwargs
            use_world_space = kwargs.get('use_world_space', True)
            max_influences = kwargs.get('max_influences', 4)
            smooth_iterations = kwargs.get('smooth_iterations', 3)
            
            # Get rest pose vertices
            if use_world_space:
                rest_verts = self._get_world_space_vertices(mesh_name)
            else:
                rest_verts = self._get_local_space_vertices(mesh_name)
            
            # Setup DemBones parameters
            self.dem_bones.nV = len(rest_verts)
            self.dem_bones.nB = len(joint_names)
            self.dem_bones.nnz = max_influences
            self.dem_bones.weightsSmooth = 0.0001 * smooth_iterations
            
            # Set rest pose
            self.dem_bones.u = np.array(rest_verts, dtype=np.float64)
            
            # Get animated poses if provided
            if anim_mesh_names:
                self.dem_bones.nF = len(anim_mesh_names)
                self.dem_bones.nS = 1
                self.dem_bones.fStart = np.array([0], dtype=np.int32)
                self.dem_bones.subjectID = np.zeros(len(anim_mesh_names), dtype=np.int32)
                
                # Collect all animated vertices
                all_anim_verts = []
                for anim_mesh in anim_mesh_names:
                    if use_world_space:
                        anim_verts = self._get_world_space_vertices(anim_mesh)
                    else:
                        anim_verts = self._get_local_space_vertices(anim_mesh)
                    all_anim_verts.extend(anim_verts)
                
                self.dem_bones.v = np.array(all_anim_verts, dtype=np.float64)
            
            # If we're using DemBonesExt, set up the skeleton hierarchy
            if isinstance(self.dem_bones, pdb.DemBonesExt):
                # Get joint hierarchy from Maya
                parent_indices = self._get_joint_hierarchy(joint_names)
                self.dem_bones.parent = np.array(parent_indices, dtype=np.int32)
                self.dem_bones.boneName = joint_names
                self.dem_bones.bindUpdate = 1
            
            return True
            
        except ImportError:
            print("Error: This script must be run from within Maya.")
            return False
        except Exception as e:
            print(f"Error importing data from Maya: {e}")
            return False
    
    def to_dcc_data(self, apply_weights: bool = True, **kwargs) -> bool:
        """
        Export DemBones data to Maya.
        
        Args:
            apply_weights: Whether to apply the computed weights to the Maya mesh
            **kwargs: Additional Maya-specific parameters
                     - create_skin_cluster: Whether to create a new skin cluster (default: True)
                     - skin_cluster_name: Name of the skin cluster to create/use
                     - normalize_weights: Whether to normalize weights (default: True)
        
        Returns:
            bool: True if export was successful
        """
        try:
            # Import Maya commands
            import maya.cmds as cmds
            
            # Check if we have computed weights
            if not hasattr(self.dem_bones, 'get_weights'):
                print("Error: No weights computed. Call compute() first.")
                return False
            
            # Get parameters from kwargs
            create_skin_cluster = kwargs.get('create_skin_cluster', True)
            skin_cluster_name = kwargs.get('skin_cluster_name', 'demBonesSkinCluster')
            normalize_weights = kwargs.get('normalize_weights', True)
            
            # Get data from stored Maya data
            mesh_name = self._maya_data.get('mesh_name')
            joint_names = self._maya_data.get('joint_names')
            
            if not mesh_name or not joint_names:
                print("Error: Missing Maya data. Call from_dcc_data() first.")
                return False
            
            # Get computed weights
            weights = self.dem_bones.get_weights()
            
            if apply_weights:
                # Create or get skin cluster
                skin_cluster = None
                if create_skin_cluster:
                    # Remove existing skin clusters
                    existing_skin_clusters = cmds.listConnections(mesh_name, type='skinCluster')
                    if existing_skin_clusters:
                        for sc in existing_skin_clusters:
                            cmds.skinCluster(sc, e=True, unbind=True)
                    
                    # Create new skin cluster
                    skin_cluster = cmds.skinCluster(
                        joint_names, 
                        mesh_name, 
                        name=skin_cluster_name,
                        toSelectedBones=True,
                        bindMethod=0,  # Closest distance
                        normalizeWeights=2 if normalize_weights else 0,
                        maximumInfluences=self.dem_bones.nnz
                    )[0]
                else:
                    # Use existing skin cluster
                    existing_skin_clusters = cmds.listConnections(mesh_name, type='skinCluster')
                    if existing_skin_clusters:
                        skin_cluster = existing_skin_clusters[0]
                    else:
                        print("Error: No existing skin cluster found and create_skin_cluster is False.")
                        return False
                
                # Apply weights to skin cluster
                self._apply_weights_to_skin_cluster(skin_cluster, mesh_name, joint_names, weights)
                
                print(f"Successfully applied weights to {mesh_name}")
            
            return True
            
        except ImportError:
            print("Error: This script must be run from within Maya.")
            return False
        except Exception as e:
            print(f"Error exporting data to Maya: {e}")
            return False
    
    def convert_matrices(self, matrices, from_dcc=True):
        """
        Convert between Maya and DemBones matrix formats.
        
        Args:
            matrices: The matrices to convert
            from_dcc: If True, convert from Maya to DemBones format,
                     otherwise convert from DemBones to Maya format
        
        Returns:
            The converted matrices
        """
        # Maya uses row-major matrices, DemBones uses column-major
        # This is a simplified example - in practice, more conversion might be needed
        if from_dcc:
            # Convert from Maya to DemBones
            return np.array([m.transpose() for m in matrices])
        else:
            # Convert from DemBones to Maya
            return np.array([m.transpose() for m in matrices])
    
    def apply_coordinate_system_transform(self, data, from_dcc=True):
        """
        Apply coordinate system transformations between Maya and DemBones.
        
        Maya uses a right-handed Y-up coordinate system, while DemBones
        typically uses a right-handed Z-up system. This method handles
        the conversion between these coordinate systems.
        
        Args:
            data: The data to transform (vertices or matrices)
            from_dcc: If True, transform from Maya to DemBones coordinate system,
                     otherwise transform from DemBones to Maya coordinate system
        
        Returns:
            The transformed data
        """
        # This is a simplified example - in practice, a proper transformation matrix would be used
        # For this example, we'll just swap Y and Z coordinates
        if isinstance(data, np.ndarray) and data.shape[-1] >= 3:
            result = data.copy()
            if from_dcc:
                # Maya to DemBones (Y-up to Z-up)
                result[..., [1, 2]] = result[..., [2, 1]]
                result[..., 2] *= -1  # Flip Z
            else:
                # DemBones to Maya (Z-up to Y-up)
                result[..., 2] *= -1  # Flip Z
                result[..., [1, 2]] = result[..., [2, 1]]
            return result
        return data
    
    # Helper methods
    def _get_world_space_vertices(self, mesh_name):
        """Get world space vertices from a Maya mesh."""
        import maya.cmds as cmds
        
        # Get vertex positions in world space
        vertices = []
        num_vertices = cmds.polyEvaluate(mesh_name, vertex=True)
        
        for i in range(num_vertices):
            pos = cmds.xform(f"{mesh_name}.vtx[{i}]", query=True, translation=True, worldSpace=True)
            vertices.append(pos)
            
        return vertices
    
    def _get_local_space_vertices(self, mesh_name):
        """Get local space vertices from a Maya mesh."""
        import maya.cmds as cmds
        
        # Get vertex positions in object space
        vertices = []
        num_vertices = cmds.polyEvaluate(mesh_name, vertex=True)
        
        for i in range(num_vertices):
            pos = cmds.xform(f"{mesh_name}.vtx[{i}]", query=True, translation=True, objectSpace=True)
            vertices.append(pos)
            
        return vertices
    
    def _get_joint_hierarchy(self, joint_names):
        """Get the parent indices for each joint in the list."""
        import maya.cmds as cmds
        
        parent_indices = []
        for joint in joint_names:
            parent = cmds.listRelatives(joint, parent=True, type='joint')
            if parent and parent[0] in joint_names:
                parent_index = joint_names.index(parent[0])
            else:
                parent_index = -1  # No parent or parent not in our joint list
            parent_indices.append(parent_index)
            
        return parent_indices
    
    def _apply_weights_to_skin_cluster(self, skin_cluster, mesh_name, joint_names, weights):
        """Apply computed weights to a Maya skin cluster."""
        import maya.cmds as cmds
        
        # Get number of vertices
        num_vertices = cmds.polyEvaluate(mesh_name, vertex=True)
        
        # For each vertex
        for vertex_idx in range(num_vertices):
            # Get weights for this vertex
            vertex_weights = {}
            
            # For each joint
            for joint_idx, joint_name in enumerate(joint_names):
                weight = weights[joint_idx, vertex_idx]
                if weight > 0.0001:  # Skip very small weights
                    vertex_weights[joint_name] = weight
            
            # Set weights for this vertex
            if vertex_weights:
                # Convert to format expected by Maya: [(joint1, weight1), (joint2, weight2), ...]
                weight_list = [(joint, weight) for joint, weight in vertex_weights.items()]
                
                # Apply weights
                cmds.skinPercent(
                    skin_cluster,
                    f"{mesh_name}.vtx[{vertex_idx}]",
                    transformValue=weight_list,
                    normalize=False
                )


def example_usage():
    """Example of how to use the MayaDCCInterface in Maya."""
    # This function would be called from within Maya
    
    # Import Maya commands
    import maya.cmds as cmds
    
    # Create a simple scene for testing
    if not cmds.objExists('testCube'):
        cmds.polyCube(name='testCube', width=2, height=2, depth=2, subdivisionsX=2, subdivisionsY=2, subdivisionsZ=2)
    
    if not cmds.objExists('joint1'):
        cmds.select(clear=True)
        cmds.joint(name='joint1', position=(-1, 0, 0))
        cmds.joint(name='joint2', position=(1, 0, 0))
    
    # Create a deformed version of the cube
    if not cmds.objExists('deformedCube'):
        cmds.duplicate('testCube', name='deformedCube')
        cmds.move(0, 1, 0, 'deformedCube.vtx[0:3]', relative=True)
    
    # Create DemBones instance
    dem_bones = pdb.DemBones()
    
    # Create Maya interface
    maya_interface = MayaDCCInterface(dem_bones)
    
    # Import data from Maya
    success = maya_interface.from_dcc_data(
        mesh_name='testCube',
        joint_names=['joint1', 'joint2'],
        anim_mesh_names=['deformedCube'],
        use_world_space=True,
        max_influences=4
    )
    
    if success:
        # Compute skinning weights
        dem_bones.compute()
        
        # Export data back to Maya
        maya_interface.to_dcc_data(
            apply_weights=True,
            create_skin_cluster=True,
            skin_cluster_name='demBonesSkin'
        )
        
        print("Successfully computed and applied skinning weights!")
    else:
        print("Failed to import data from Maya.")


if __name__ == "__main__":
    # This script should be run from within Maya
    try:
        import maya.cmds
        example_usage()
    except ImportError:
        print("This script must be run from within Maya.")
