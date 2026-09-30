"""Houdini polygon sampling and writable geometry weight attributes.

This adapter writes independent point attributes, not ``boneCapture``. A Python
SOP can pass its writable output geometry to :meth:`to_dcc_data`.
"""

# Import standard library modules
import re

# Import third-party modules
import numpy as np

# Import local modules
from py_dem_bones.adapters.base import HostAdapter


class HoudiniDCCInterface(HostAdapter):
    """Sample matching SOP meshes without changing the Houdini coordinate basis."""

    def __init__(self, dem_bones_instance=None):
        super().__init__(dem_bones_instance)
        self._houdini_data = None

    def get_dcc_info(self):
        return {"name": "Houdini", "coordinate_system": "Host geometry space",
                "capabilities": ["polygon_sampling", "writable_point_weight_attributes"],
                "unsupported": ["boneCapture", "bone_animation"]}

    @staticmethod
    def _topology(geometry):
        # Import third-party modules
        import hou

        points = geometry.points()
        if [point.number() for point in points] != list(range(len(points))):
            raise ValueError("Geometry point numbers must be contiguous")
        faces = []
        for primitive in geometry.prims():
            if primitive.type() != hou.primType.Polygon or not primitive.isClosed():
                raise ValueError("Only closed polygon primitives are supported")
            faces.append(tuple(vertex.point().number() for vertex in primitive.vertices()))
        return len(points), tuple(faces)

    @classmethod
    def _sample(cls, node, world_space):
        geometry = node.geometry()
        topology = cls._topology(geometry)
        positions = [point.position() for point in geometry.points()]
        if world_space:
            container = node.creator()
            if not hasattr(container, "worldTransform"):
                raise ValueError("World-space sampling requires an object geometry container")
            transform = container.worldTransform()
            positions = [position * transform for position in positions]
        return np.asarray([tuple(position) for position in positions], dtype=float), topology

    def from_dcc_data(self, geo_path, bone_paths, capture_paths=None, **kwargs):
        """Sample rest/pose SOPs. All meshes must have identical point and polygon order."""
        self._begin_import()
        self._houdini_data = None
        try:
            # Import third-party modules
            import hou

            if kwargs.get("capture_attr") is not None:
                raise NotImplementedError("Alternate capture attributes are unsupported; supply pose SOPs")
            node = hou.node(geo_path)
            bones = [hou.node(path) for path in bone_paths]
            poses = [hou.node(path) for path in (capture_paths or [])]
            if node is None or not bones or any(item is None for item in bones + poses):
                raise ValueError("Rest, bone, and pose nodes must all exist")
            if len(set(bone_paths)) != len(bones):
                raise ValueError("Bone paths must be unique")
            world_space = kwargs.get("use_world_space", False)
            rest, topology = self._sample(node, world_space)
            samples = []
            for pose in poses:
                vertices, pose_topology = self._sample(pose, world_space)
                if pose_topology != topology:
                    raise ValueError("Pose topology differs from the rest mesh")
                samples.append(vertices)
            if not samples:
                raise ValueError("At least one capture pose SOP is required")
            if not self._import_sequence(
                rest, samples, [bone.name() for bone in bones], topology[1],
                max_influences=kwargs.get("max_influences", 4),
                smooth_iterations=kwargs.get("smooth_iterations", 3),
            ):
                return False
            self._houdini_data = (geo_path, node, tuple(bone_paths), tuple(bones), topology)
            return True
        except Exception as exc:
            self._failure(exc)
            return False

    def to_dcc_data(self, apply_weights=True, *, geometry=None, **kwargs):
        """Return all frames/bones; optionally write scalar point attributes.

        ``geometry`` must be an explicit writable ``hou.Geometry`` matching the
        imported mesh. No SOP is unlocked or edited implicitly. The returned
        ``weight_attributes`` maps each bone name to its point attribute.
        """
        try:
            result = self._export_result()
            if not result["success"] or not apply_weights:
                return result
            # Import third-party modules
            import hou

            if kwargs.get("create_capture_attr", False):
                raise NotImplementedError("boneCapture output is unsupported; use independent weight attributes")
            if self._houdini_data is None:
                raise RuntimeError("Import a Houdini sequence before writing weights")
            path, original_node, bone_paths, original_bones, topology = self._houdini_data
            if hou.node(path) != original_node or tuple(hou.node(item) for item in bone_paths) != original_bones:
                raise ValueError("The imported geometry or bone mapping has changed")
            if [bone.name() for bone in original_bones] != list(result["bone_names"]):
                raise ValueError("The imported bone names have changed")
            if self._topology(original_node.geometry()) != topology:
                raise ValueError("Source topology changed after import")
            if geometry is None or geometry.isReadOnly():
                raise ValueError("Pass an explicit writable hou.Geometry, such as the Python SOP output")
            if self._topology(geometry) != topology:
                raise ValueError("Output topology differs from the imported mesh")
            prefix = kwargs.get("weight_attr_prefix", "weight_")
            if not isinstance(prefix, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", prefix):
                raise ValueError("weight_attr_prefix must be a valid Houdini attribute prefix")
            names = [prefix + str(index) for index in range(len(result["bone_names"]))]
            for name in names:
                attribute = geometry.findPointAttrib(name)
                if attribute is not None and (attribute.size() != 1 or attribute.dataType() != hou.attribData.Float):
                    raise ValueError("Existing weight attributes must be scalar floats")
            for index, name in enumerate(names):
                if geometry.findPointAttrib(name) is None:
                    geometry.addAttrib(hou.attribType.Point, name, 0.0)
                geometry.setPointFloatAttribValues(name, result["weights"][index].tolist())
                if not np.allclose(geometry.pointFloatAttribValues(name), result["weights"][index],
                                   rtol=1e-6, atol=1e-8):
                    raise RuntimeError("Houdini weight readback differs from the solver output")
            result["weight_attributes"] = dict(zip(result["bone_names"], names))
            result["applied"] = True
            return result
        except Exception as exc:
            return self._failure(exc)
