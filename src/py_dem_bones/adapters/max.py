"""3ds Max mesh sampling and explicit Skin weight updates via pymxs."""

# Import third-party modules
import numpy as np

# Import local modules
from py_dem_bones.adapters.base import HostAdapter


class MaxDCCInterface(HostAdapter):
    """Sample TriMesh snapshots and update an existing, configured Skin modifier.

    Skin creation and modifier-panel activation belong to the host workflow.
    The adapter does not delete modifiers or change the user's selection.
    """

    def __init__(self, dem_bones_instance=None):
        super().__init__(dem_bones_instance)
        self._max_data = None

    def get_dcc_info(self):
        return {"name": "3ds Max", "coordinate_system": "Host mesh space",
                "capabilities": ["trimesh_sampling", "existing_skin_weights"],
                "unsupported": ["skin_creation", "modifier_panel_activation", "bone_animation"]}

    @staticmethod
    def _resolve_node(rt, name):
        if not isinstance(name, str) or not name:
            raise ValueError("Node names must be nonempty strings")
        matches = list(rt.getNodeByName(name, all=True, ignoreCase=False, exact=True))
        if len(matches) != 1 or str(matches[0].name) != name:
            raise ValueError("Node name must resolve to exactly one case-sensitive match: " + name)
        return matches[0]

    @staticmethod
    def _sample(rt, node, world_space):
        mesh = rt.snapshotAsMesh(node)
        try:
            positions = []
            for index in range(1, rt.getNumVerts(mesh) + 1):
                point = rt.getVert(mesh, index)
                if world_space:
                    point = point * node.objectTransform
                positions.append([point.x, point.y, point.z])
            faces = []
            for index in range(1, rt.getNumFaces(mesh) + 1):
                face = rt.getFace(mesh, index)
                faces.append((int(face.x) - 1, int(face.y) - 1, int(face.z) - 1))
            return np.asarray(positions, dtype=float), (len(positions), tuple(faces))
        finally:
            rt.delete(mesh)

    def from_dcc_data(self, mesh_node, bone_nodes, morph_targets=None, **kwargs):
        """Read matching pose meshes using unique, case-sensitive scene node names."""
        self._begin_import()
        self._max_data = None
        try:
            # Import third-party modules
            import pymxs

            rt = pymxs.runtime
            mesh = self._resolve_node(rt, mesh_node)
            bones = [self._resolve_node(rt, name) for name in bone_nodes]
            poses = [self._resolve_node(rt, name) for name in (morph_targets or [])]
            if not bones:
                raise ValueError("At least one bone is required")
            if len(set(bone_nodes)) != len(bones):
                raise ValueError("Bone names must be unique")
            world_space = kwargs.get("use_world_space", False)
            rest, topology = self._sample(rt, mesh, world_space)
            samples = []
            for pose in poses:
                vertices, pose_topology = self._sample(rt, pose, world_space)
                if pose_topology != topology:
                    raise ValueError("Pose topology differs from the rest mesh")
                samples.append(vertices)
            if not samples:
                raise ValueError("At least one morph target mesh is required")
            if not self._import_sequence(
                rest, samples, list(bone_nodes), topology[1],
                max_influences=kwargs.get("max_influences", 4),
                smooth_iterations=kwargs.get("smooth_iterations", 3),
            ):
                return False
            self._max_data = (mesh, tuple(bones), topology, world_space)
            return True
        except Exception as exc:
            self._failure(exc)
            return False

    def to_dcc_data(self, apply_weights=True, *, skin_modifier=None, **kwargs):
        """Write full weights to a caller-selected Skin already containing the bones.

        Some Max versions require the modifier to be active in the Modify panel.
        Set that up in the host before calling. Existing influences are replaced
        for each vertex; all positive solver weights, including tiny ones, survive.
        """
        try:
            result = self._export_result()
            if not result["success"] or not apply_weights:
                return result
            # Import third-party modules
            import pymxs

            rt = pymxs.runtime
            if kwargs.get("create_skin_modifier", False):
                raise NotImplementedError("Create and configure Skin in the host, then pass skin_modifier explicitly")
            if kwargs.get("normalize_weights", True) is not True:
                raise ValueError("Normalized skinning weights are required")
            if self._max_data is None:
                raise RuntimeError("Import a Max sequence before writing weights")
            mesh, bones, topology, world_space = self._max_data
            if not rt.isValidNode(mesh) or any(not rt.isValidNode(bone) for bone in bones):
                raise ValueError("Imported nodes no longer exist")
            if [str(bone.name) for bone in bones] != list(result["bone_names"]):
                raise ValueError("Bone names changed after import")
            if self._sample(rt, mesh, world_space)[1] != topology:
                raise ValueError("Mesh topology changed after import")
            if skin_modifier is None or skin_modifier not in list(mesh.modifiers):
                raise ValueError("Pass an existing Skin modifier attached to the imported mesh")
            if rt.classOf(skin_modifier) != rt.Skin:
                raise ValueError("skin_modifier must be a Skin modifier")
            if rt.modPanel.getCurrentObject() != skin_modifier:
                raise ValueError("Activate the supplied Skin in the Modify panel before applying weights")
            if list(mesh.modifiers)[0] != skin_modifier:
                raise ValueError("Skin must be the top modifier to preserve vertex mapping")
            skin_ids = [rt.skinOps.GetBoneIDByListID(skin_modifier, index)
                        for index in range(1, rt.skinOps.GetNumberBones(skin_modifier) + 1)]
            skin_bones = [rt.skinOps.GetBoneNode(skin_modifier, index) for index in skin_ids]
            if len(skin_bones) != len(bones) or any(bone not in skin_bones for bone in bones):
                raise ValueError("Skin must contain exactly the imported bones")
            if rt.skinOps.GetNumberVertices(skin_modifier) != topology[0]:
                raise ValueError("Skin vertex count differs from the imported mesh")
            bone_ids = [skin_ids[skin_bones.index(bone)] for bone in bones]
            for vertex in range(topology[0]):
                weights = result["weights"][:, vertex]
                active = [index for index, weight in enumerate(weights) if weight > 0]
                rt.skinOps.ReplaceVertexWeights(
                    skin_modifier, vertex + 1,
                    rt.Array(*(bone_ids[index] for index in active)),
                    rt.Array(*(float(weights[index]) for index in active)),
                )
                observed = {}
                for influence in range(1, rt.skinOps.GetVertexWeightCount(skin_modifier, vertex + 1) + 1):
                    bone_id = rt.skinOps.GetVertexWeightBoneID(skin_modifier, vertex + 1, influence)
                    observed[bone_id] = rt.skinOps.GetVertexWeight(skin_modifier, vertex + 1, influence)
                if any(index not in bone_ids for index in observed) or not np.allclose(
                    [observed.get(index, 0.0) for index in bone_ids], weights, rtol=1e-6, atol=1e-8
                ):
                    raise RuntimeError("Skin weight readback differs from the solver output")
            result["applied"] = True
            return result
        except Exception as exc:
            return self._failure(exc)
