"""
Example of using py-dem-bones with SideFX Houdini.

This example demonstrates how to implement the DCCInterface for Houdini
and use it to compute skinning weights for a Houdini mesh.

Note: This example requires Houdini to be installed and the script to be run from within Houdini.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union

import py_dem_bones as pdb
from py_dem_bones.interfaces import DCCInterface


class HoudiniDCCInterface(DCCInterface):
    """
    Implementation of DCCInterface for SideFX Houdini.
    
    This class provides methods to convert between Houdini's data structures
    and the format required by py-dem-bones.
    """
    
    def __init__(self, dem_bones_instance=None):
        """
        Initialize the Houdini DCC interface.
        
        Args:
            dem_bones_instance: Optional DemBones or DemBonesExt instance.
                               If not provided, a new instance will be created.
        """
        self.dem_bones = dem_bones_instance or pdb.DemBones()
        self._houdini_data = {}
        
    def from_dcc_data(self, 
                     geo_path: str, 
                     bone_paths: List[str], 
                     capture_paths: Optional[List[str]] = None,
                     **kwargs) -> bool:
        """
        Import data from Houdini into DemBones.
        
        Args:
            geo_path: Path to the base geometry node in Houdini
            bone_paths: List of paths to bone nodes
            capture_paths: List of paths to capture/pose geometry nodes
            **kwargs: Additional Houdini-specific parameters
                     - use_world_space: Whether to use world space (default: True)
                     - max_influences: Maximum number of influences per vertex (default: 4)
                     - smooth_iterations: Number of smoothing iterations (default: 3)
                     - capture_attr: Name of the capture attribute (default: None)
        
        Returns:
            bool: True if import was successful
        """
        try:
            # Import Houdini modules (only available in Houdini)
            import hou
            
            # Store Houdini data for later use
            self._houdini_data = {
                'geo_path': geo_path,
                'bone_paths': bone_paths,
                'capture_paths': capture_paths,
                'kwargs': kwargs
            }
            
            # Get parameters from kwargs
            use_world_space = kwargs.get('use_world_space', True)
            max_influences = kwargs.get('max_influences', 4)
            smooth_iterations = kwargs.get('smooth_iterations', 3)
            capture_attr = kwargs.get('capture_attr', None)
            
            # Get geometry and bones
            geo_node = hou.node(geo_path)
            bone_nodes = [hou.node(path) for path in bone_paths]
            
            if not geo_node or None in bone_nodes:
                print(f"Error: Nodes not found: {geo_path} or one of the bones")
                return False
            
            # Get geometry
            geo = geo_node.geometry()
            if not geo:
                print(f"Error: No geometry found at {geo_path}")
                return False
            
            # Setup DemBones parameters
            self.dem_bones.nV = len(geo.points())
            self.dem_bones.nB = len(bone_nodes)
            self.dem_bones.nnz = max_influences
            self.dem_bones.weightsSmooth = 0.0001 * smooth_iterations
            
            # Get rest pose vertices
            rest_verts = self._get_vertices(geo, use_world_space)
            self.dem_bones.u = np.array(rest_verts, dtype=np.float64)
            
            # Get capture poses if provided
            if capture_paths:
                capture_nodes = [hou.node(path) for path in capture_paths]
                if None in capture_nodes:
                    print(f"Warning: Some capture nodes not found")
                    # Filter out None values
                    capture_nodes = [node for node in capture_nodes if node is not None]
                    capture_paths = [path for i, path in enumerate(capture_paths) if capture_nodes[i] is not None]
                
                if capture_nodes:
                    self.dem_bones.nF = len(capture_nodes)
                    self.dem_bones.nS = 1
                    self.dem_bones.fStart = np.array([0], dtype=np.int32)
                    self.dem_bones.subjectID = np.zeros(len(capture_nodes), dtype=np.int32)
                    
                    # Collect all capture vertices
                    all_capture_verts = []
                    for capture_node in capture_nodes:
                        capture_geo = capture_node.geometry()
                        if not capture_geo:
                            print(f"Warning: No geometry found at {capture_node.path()}")
                            continue
                        
                        capture_verts = self._get_vertices(capture_geo, use_world_space, capture_attr)
                        all_capture_verts.extend(capture_verts)
                    
                    self.dem_bones.v = np.array(all_capture_verts, dtype=np.float64)
            
            # If we're using DemBonesExt, set up the skeleton hierarchy
            if isinstance(self.dem_bones, pdb.DemBonesExt):
                # Get bone hierarchy from Houdini
                parent_indices = self._get_bone_hierarchy(bone_nodes)
                self.dem_bones.parent = np.array(parent_indices, dtype=np.int32)
                self.dem_bones.boneName = [node.name() for node in bone_nodes]
                self.dem_bones.bindUpdate = 1
            
            return True
            
        except ImportError:
            print("Error: This script must be run from within Houdini.")
            return False
        except Exception as e:
            print(f"Error importing data from Houdini: {e}")
            return False
    
    def to_dcc_data(self, apply_weights: bool = True, **kwargs) -> bool:
        """
        Export DemBones data to Houdini.
        
        Args:
            apply_weights: Whether to apply the computed weights to the Houdini geometry
            **kwargs: Additional Houdini-specific parameters
                     - weight_attr_prefix: Prefix for weight attributes (default: 'weight_')
                     - create_capture_attr: Whether to create a capture attribute (default: False)
                     - capture_attr_name: Name of the capture attribute (default: 'capture')
        
        Returns:
            bool: True if export was successful
        """
        try:
            # Import Houdini modules
            import hou
            
            # Check if we have computed weights
            if not hasattr(self.dem_bones, 'get_weights'):
                print("Error: No weights computed. Call compute() first.")
                return False
            
            # Get parameters from kwargs
            weight_attr_prefix = kwargs.get('weight_attr_prefix', 'weight_')
            create_capture_attr = kwargs.get('create_capture_attr', False)
            capture_attr_name = kwargs.get('capture_attr_name', 'capture')
            
            # Get data from stored Houdini data
            geo_path = self._houdini_data.get('geo_path')
            bone_paths = self._houdini_data.get('bone_paths')
            
            if not geo_path or not bone_paths:
                print("Error: Missing Houdini data. Call from_dcc_data() first.")
                return False
            
            # Get geometry
            geo_node = hou.node(geo_path)
            if not geo_node:
                print(f"Error: Node not found: {geo_path}")
                return False
            
            geo = geo_node.geometry()
            if not geo:
                print(f"Error: No geometry found at {geo_path}")
                return False
            
            # Get computed weights
            weights = self.dem_bones.get_weights()
            
            if apply_weights:
                # Apply weights to geometry
                self._apply_weights_to_geometry(geo, weights, bone_paths, weight_attr_prefix, create_capture_attr, capture_attr_name)
                
                print(f"Successfully applied weights to {geo_path}")
            
            return True
            
        except ImportError:
            print("Error: This script must be run from within Houdini.")
            return False
        except Exception as e:
            print(f"Error exporting data to Houdini: {e}")
            return False
    
    def _get_vertices(self, geo, use_world_space=True, capture_attr=None):
        """
        Get vertices from a Houdini geometry.
        
        Args:
            geo: Houdini geometry
            use_world_space: Whether to get vertices in world space
            capture_attr: Name of the capture attribute
            
        Returns:
            List of vertex positions as [x1, y1, z1, x2, y2, z2, ...]
        """
        verts = []
        
        if capture_attr and capture_attr in geo.pointAttribs():
            # Use capture attribute if provided
            attr = geo.findPointAttrib(capture_attr)
            for point in geo.points():
                pos = point.attribValue(attr)
                verts.extend([pos[0], pos[1], pos[2]])
        else:
            # Use point positions
            for point in geo.points():
                if use_world_space:
                    # Get point in world space
                    pos = point.position()
                    # Convert to world space if needed
                    # This is simplified - in a real implementation you would need to 
                    # apply the proper transformation from the node
                else:
                    # Get point in local space
                    pos = point.position()
                
                verts.extend([pos[0], pos[1], pos[2]])
        
        return verts
    
    def _get_bone_hierarchy(self, bone_nodes):
        """
        Get bone hierarchy from Houdini bone nodes.
        
        Args:
            bone_nodes: List of Houdini bone nodes
            
        Returns:
            List of parent indices for each bone (-1 for root bones)
        """
        parent_indices = []
        
        for bone in bone_nodes:
            # Get parent node
            parent = bone.parent()
            
            # Check if parent is in the bone list
            if parent in bone_nodes:
                parent_indices.append(bone_nodes.index(parent))
            else:
                parent_indices.append(-1)  # Root bone
        
        return parent_indices
    
    def _apply_weights_to_geometry(self, geo, weights, bone_paths, weight_attr_prefix, create_capture_attr, capture_attr_name):
        """
        Apply weights to Houdini geometry.
        
        Args:
            geo: Houdini geometry
            weights: Weights matrix from DemBones
            bone_paths: List of bone paths
            weight_attr_prefix: Prefix for weight attributes
            create_capture_attr: Whether to create a capture attribute
            capture_attr_name: Name of the capture attribute
        """
        import hou
        
        # Create weight attributes
        for i, bone_path in enumerate(bone_paths):
            bone_name = hou.node(bone_path).name()
            attr_name = f"{weight_attr_prefix}{bone_name}"
            
            # Create or get attribute
            if attr_name not in geo.pointAttribs():
                attr = geo.addAttrib(hou.attribType.Point, attr_name, 0.0)
            else:
                attr = geo.findPointAttrib(attr_name)
            
            # Set weights for each point
            for j, point in enumerate(geo.points()):
                weight = weights[j * len(bone_paths) + i]
                point.setAttribValue(attr, weight)
        
        # Create capture attribute if requested
        if create_capture_attr:
            if capture_attr_name not in geo.pointAttribs():
                geo.addAttrib(hou.attribType.Point, capture_attr_name, (0.0, 0.0, 0.0))


def example_usage():
    """
    Example of how to use the HoudiniDCCInterface in Houdini.
    
    This function demonstrates the typical workflow:
    1. Create a DemBonesExt instance
    2. Create a HoudiniDCCInterface with the DemBonesExt instance
    3. Import data from Houdini
    4. Compute weights
    5. Export weights back to Houdini
    
    To run this example in Houdini:
    1. Create a geometry and a skeleton
    2. Run this script from the Python Shell
    3. Call example_usage() with the appropriate parameters
    """
    try:
        import hou
        
        # Create a DemBonesExt instance
        dem_bones = pdb.DemBonesExt()
        
        # Create a HoudiniDCCInterface with the DemBonesExt instance
        interface = HoudiniDCCInterface(dem_bones)
        
        # Get the current node
        current_node = hou.pwd()
        if not current_node:
            print("Error: No current node. Please run this script from a node context.")
            return
        
        # Get the geometry node - assuming we're in a geometry context
        geo_node = current_node
        if geo_node.type().name() != 'geo':
            # Try to find a parent geo node
            parent = current_node.parent()
            while parent and parent.type().name() != 'geo':
                parent = parent.parent()
            
            if parent and parent.type().name() == 'geo':
                geo_node = parent
            else:
                print("Error: No geometry node found in the hierarchy.")
                return
        
        geo_path = geo_node.path()
        
        # Find bone nodes - this is a simple example
        # In a real scenario, you might want to select bones manually
        bone_nodes = []
        
        # Look for bone nodes in the /obj context
        obj = hou.node('/obj')
        for child in obj.children():
            if child.type().name() == 'bone':
                bone_nodes.append(child.path())
        
        if not bone_nodes:
            print("Error: No bone nodes found in /obj.")
            return
        
        print(f"Using geometry: {geo_path}")
        print(f"Found {len(bone_nodes)} bones: {', '.join(bone_nodes)}")
        
        # Import data from Houdini
        success = interface.from_dcc_data(
            geo_path=geo_path,
            bone_paths=bone_nodes,
            capture_paths=None,  # No capture poses in this example
            use_world_space=True,
            max_influences=4,
            smooth_iterations=3
        )
        
        if not success:
            print("Error: Failed to import data from Houdini.")
            return
        
        # Compute weights
        print("Computing weights...")
        interface.dem_bones.compute()
        
        # Export weights back to Houdini
        success = interface.to_dcc_data(
            apply_weights=True,
            weight_attr_prefix='weight_',
            create_capture_attr=False
        )
        
        if not success:
            print("Error: Failed to export weights to Houdini.")
            return
        
        print("Successfully computed and applied weights!")
        
    except ImportError:
        print("Error: This script must be run from within Houdini.")
    except Exception as e:
        print(f"Error in example_usage: {e}")


if __name__ == "__main__":
    # This script should be run from within Houdini
    try:
        import hou
        print("Houdini detected. Run example_usage() to compute weights.")
    except ImportError:
        print("Error: This script must be run from within Houdini.")
