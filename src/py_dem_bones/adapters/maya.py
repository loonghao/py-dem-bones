"""Maya mesh sampling and weight writes; host modules are imported on demand."""

# Import third-party modules
import numpy as np

# Import local modules
from py_dem_bones.adapters.base import HostAdapter


class MayaDCCInterface(HostAdapter):
    """Solve in Maya's current space and return Maya row-vector matrices.

    ``to_dcc_data`` returns a result dictionary, not the legacy boolean. Only
    weights are written. The caller owns bind matrices, hierarchy, and animation
    authoring for the returned ``(frames, bones, 4, 4)`` transformations.
    """

    def __init__(self, dem_bones_instance=None):
        super().__init__(dem_bones_instance)
        self._maya_data = {}

    def get_dcc_info(self):
        return {"name": "Maya", "version": "Host provided", "coordinate_system": "Host space; row-vector matrices"}

    @staticmethod
    def _unique_name(cmds, name, node_type=None):
        matches = cmds.ls(name, long=True) or []
        if len(matches) != 1:
            raise ValueError("Expected one unambiguous Maya object: {}".format(name))
        if node_type and cmds.nodeType(matches[0]) != node_type:
            raise ValueError("Expected a {}: {}".format(node_type, name))
        return matches[0]

    @classmethod
    def _sample_mesh(cls, cmds, om, name, world_space):
        name = cls._unique_name(cmds, name)
        if cmds.nodeType(name) == "transform":
            shapes = cmds.listRelatives(name, shapes=True, noIntermediate=True, fullPath=True) or []
            shapes = [shape for shape in shapes if cmds.nodeType(shape) == "mesh"]
            if len(shapes) != 1:
                raise ValueError("Expected exactly one mesh shape: {}".format(name))
            name = shapes[0]
        if cmds.nodeType(name) != "mesh":
            raise ValueError("Expected a polygon mesh: {}".format(name))
        selection = om.MSelectionList()
        selection.add(name)
        path = selection.getDagPath(0)
        mesh = om.MFnMesh(path)
        space = om.MSpace.kWorld if world_space else om.MSpace.kObject
        points = np.asarray([(point.x, point.y, point.z) for point in mesh.getPoints(space)], dtype=float)
        counts, indices = mesh.getVertices()
        faces = []
        offset = 0
        for count in counts:
            faces.append(tuple(int(index) for index in indices[offset:offset + count]))
            offset += count
        return points, tuple(faces), path

    def from_dcc_data(self, mesh_name, joint_names, anim_mesh_names=None, **kwargs):
        """Import matching indexed meshes; omitted poses mean one static frame.

        ``use_world_space`` defaults to True. All poses must share vertex order
        and ordered polygon connectivity. Identical connectivity cannot prove
        semantic correspondence between independently created meshes.
        """
        self._begin_import()
        self._maya_data = {}
        try:
            # Import third-party modules
            import maya.api.OpenMaya as om
            import maya.cmds as cmds

            joints = [self._unique_name(cmds, name, "joint") for name in joint_names]
            world_space = kwargs.get("use_world_space", True)
            rest, faces, path = self._sample_mesh(cmds, om, mesh_name, world_space)
            poses = []
            for name in list(anim_mesh_names or []):
                points, pose_faces, _ = self._sample_mesh(cmds, om, name, world_space)
                if points.shape != rest.shape or pose_faces != faces:
                    raise ValueError("Pose topology or indexed vertex order differs: {}".format(name))
                poses.append(points)
            imported = self._import_sequence(
                rest, poses or [rest.copy()], joints, faces,
                max_influences=kwargs.get("max_influences", 4),
                smooth_iterations=kwargs.get("smooth_iterations", 3),
            )
            if not imported:
                return False
            self._maya_data = {
                "mesh": path.fullPathName(), "joints": joints,
                "mesh_id": tuple(cmds.ls(path.fullPathName(), uuid=True)),
                "joint_ids": [tuple(cmds.ls(name, uuid=True)) for name in joints],
                "topology": (len(rest), faces), "world_space": world_space,
            }
            return True
        except Exception as exc:
            self._begin_import()
            self._maya_data = {}
            self._failure(exc)
            return False

    def convert_matrices(self, matrices, from_dcc=True):
        """Transpose only matrix axes, including complete frame/bone batches."""
        matrices = np.asarray(matrices, dtype=float)
        if matrices.shape[-2:] != (4, 4):
            raise ValueError("Maya matrices must end in (4, 4)")
        if from_dcc:
            return super().convert_matrices(matrices.swapaxes(-1, -2), from_dcc=True)
        return super().convert_matrices(matrices, from_dcc=False).swapaxes(-1, -2)

    def to_dcc_data(self, apply_weights=True, **kwargs):
        """Return the result and optionally write all skin weights without pruning.

        Existing skins are reused only when their influence order matches; none
        are deleted. ``create_skin_cluster`` (default True) permits creating a
        skin only when none exists. ``normalize_weights`` controls new skin
        settings; validated, normalized solver weights are written unchanged.
        """
        result = self._export_result()
        if not result.get("success") or not apply_weights:
            return result
        created_skin = None
        try:
            # Import third-party modules
            import maya.api.OpenMaya as om
            import maya.api.OpenMayaAnim as oma
            import maya.cmds as cmds

            data = self._maya_data
            points, faces, path = self._sample_mesh(cmds, om, data["mesh"], data["world_space"])
            if (len(points), faces) != data["topology"]:
                raise ValueError("Mesh topology changed; reimport before writing weights")
            if tuple(cmds.ls(data["mesh"], uuid=True)) != data["mesh_id"]:
                raise ValueError("Mesh identity changed; reimport before writing weights")
            joints = [self._unique_name(cmds, name, "joint") for name in data["joints"]]
            identities = [tuple(cmds.ls(name, uuid=True)) for name in joints]
            if joints != result["bone_names"] or identities != data["joint_ids"]:
                raise ValueError("Joint identity or order changed; reimport before writing weights")
            skins = list(dict.fromkeys(cmds.ls(cmds.listHistory(data["mesh"]) or [], type="skinCluster") or []))
            if len(skins) > 1:
                raise ValueError("Multiple skin clusters found; choose an unambiguous target mesh")
            if skins:
                skin = skins[0]
            elif kwargs.get("create_skin_cluster", True):
                skin = cmds.skinCluster(
                    joints, data["mesh"], name=kwargs.get("skin_cluster_name", "demBonesSkinCluster"),
                    toSelectedBones=True, bindMethod=0,
                    normalizeWeights=2 if kwargs.get("normalize_weights", True) else 0,
                    maximumInfluences=self.dem_bones.max_influences,
                )[0]
                created_skin = skin
            else:
                raise ValueError("No skin cluster exists and creation is disabled")
            selection = om.MSelectionList()
            selection.add(skin)
            skin_fn = oma.MFnSkinCluster(selection.getDependNode(0))
            influences = [influence.fullPathName() for influence in skin_fn.influenceObjects()]
            if influences != joints:
                raise ValueError("Skin influence order differs from the imported joint order")
            component_fn = om.MFnSingleIndexedComponent()
            component = component_fn.create(om.MFn.kMeshVertComponent)
            component_fn.addElements(range(len(points)))
            # MFnSkinCluster uses physical influence indices, in vertex-major order.
            indices = om.MIntArray(range(len(joints)))
            requested = result["weights"].T.reshape(-1)
            previous, previous_count = skin_fn.getWeights(path, component)
            if previous_count != len(joints) or len(previous) != len(requested):
                raise ValueError("Existing skin weight layout differs from the imported mesh")
            try:
                skin_fn.setWeights(path, component, indices, om.MDoubleArray(requested.tolist()), False)
                written, count = skin_fn.getWeights(path, component)
                if count != len(joints) or not np.allclose(written, requested, rtol=1e-7, atol=1e-12):
                    raise RuntimeError("Maya weight readback differs from the requested solver weights")
            except Exception:
                # Preserve a pre-existing skin if the SDK rejects or alters a write.
                if created_skin is None:
                    skin_fn.setWeights(path, component, indices, previous, False)
                raise
            result["skin_cluster"] = skin
            return result
        except Exception as exc:
            if created_skin is not None:
                try:
                    cmds.delete(created_skin)
                except Exception as cleanup_error:
                    return self._failure("{}; new skin cleanup failed: {}".format(exc, cleanup_error))
            return self._failure(exc)
