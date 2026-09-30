"""Unreal integration through an explicit, version-owned mesh data bridge.

Unreal's Python mesh/morph sampling APIs vary by release and plugin. This module
does not claim a built-in sampler. Supply a ``sampler(**request)`` callable and,
for writes, ``writer(request=request, result=result)``. A writer must return a
dict with ``success is True`` only after its host operation has completed.
"""

# Import standard library modules
from copy import deepcopy

# Import third-party modules
import numpy as np

# Import local modules
from py_dem_bones.adapters.base import HostAdapter


class UnrealDCCInterface(HostAdapter):
    """Bridge host mesh data into the same validated solver used by other DCCs.

    The sampler returns ``rest_vertices``, ``poses``, ``faces``, ``pose_faces``,
    ``bone_names``, ``vertex_ids``, and ``pose_vertex_ids``. Each pose has matching
    vertex IDs and topology. IDs are stable mesh-description IDs, not render
    section offsets. ``identity`` is an opaque stable asset/LOD/revision token.
    All vertices must be in the same asset-local coordinate space.
    """

    def __init__(self, dem_bones_instance=None, *, sampler=None, writer=None):
        super().__init__(dem_bones_instance)
        self._sampler = sampler
        self._writer = writer
        self._unreal_data = None

    def get_dcc_info(self):
        return {"name": "Unreal Engine", "coordinate_system": "Asset local space",
                "capabilities": ["caller_supplied_sampler", "caller_supplied_writer"],
                "unsupported": ["builtin_mesh_sampling", "asset_duplication", "bone_animation"]}

    @staticmethod
    def _validate_sample(data):
        rest = np.asarray(data["rest_vertices"], dtype=float)
        poses = np.asarray(data["poses"], dtype=float)
        faces = tuple(tuple(face) for face in data["faces"])
        vertex_ids = tuple(data["vertex_ids"])
        bones = tuple(data["bone_names"])
        if len(set(vertex_ids)) != len(vertex_ids) or len(vertex_ids) != len(rest):
            raise ValueError("Stable unique vertex IDs must match the rest vertices")
        if len(poses) != len(data["pose_faces"]) or len(poses) != len(data["pose_vertex_ids"]):
            raise ValueError("Every pose must include topology and stable vertex IDs")
        for pose_faces, pose_ids in zip(data["pose_faces"], data["pose_vertex_ids"]):
            if tuple(tuple(face) for face in pose_faces) != faces or tuple(pose_ids) != vertex_ids:
                raise ValueError("Pose topology or vertex mapping differs from the rest mesh")
        identity = data["identity"]
        if identity is None:
            raise ValueError("A stable asset/LOD/revision identity is required")
        return rest, poses, faces, bones, (deepcopy(identity), vertex_ids, faces, bones)

    def from_dcc_data(self, skeletal_mesh_path, skeleton_path, morph_target_names=None, **kwargs):
        """Sample through the supplied bridge; missing integration fails explicitly."""
        self._begin_import()
        self._unreal_data = None
        try:
            if not callable(self._sampler):
                raise NotImplementedError("Unreal mesh sampling requires a version-specific sampler callable")
            if kwargs.get("use_world_space", False):
                raise NotImplementedError("Unreal assets use local space; world-space actor sampling is unsupported")
            request = {
                "skeletal_mesh_path": skeletal_mesh_path,
                "skeleton_path": skeleton_path,
                "morph_target_names": tuple(morph_target_names or ()),
                "lod_index": kwargs.get("lod_index", 0),
            }
            lod = request["lod_index"]
            if isinstance(lod, bool) or not isinstance(lod, int) or lod < 0:
                raise ValueError("lod_index must be a nonnegative integer")
            rest, poses, faces, bones, fingerprint = self._validate_sample(self._sampler(**request))
            if not self._import_sequence(
                rest, poses, list(bones), faces,
                max_influences=kwargs.get("max_influences", 4),
                smooth_iterations=kwargs.get("smooth_iterations", 3),
            ):
                return False
            self._unreal_data = (request, fingerprint)
            return True
        except Exception as exc:
            self._failure(exc)
            return False

    def to_dcc_data(self, apply_weights=True, **kwargs):
        """Export complete arrays or call the supplied writer after resampling identity."""
        try:
            result = self._export_result()
            if not result["success"]:
                return result
            if self._unreal_data is None:
                raise RuntimeError("Import an Unreal sequence before exporting weights")
            request, fingerprint = self._unreal_data
            result["vertex_ids"] = fingerprint[1]
            result["asset_identity"] = deepcopy(fingerprint[0])
            if not apply_weights:
                return result
            if not callable(self._writer):
                raise NotImplementedError("Unreal weight application requires a version-specific writer callable")
            if kwargs.get("create_new_asset", False) or kwargs.get("new_asset_path"):
                raise NotImplementedError("Asset duplication must be handled explicitly by the host workflow")
            if kwargs.get("lod_index", request["lod_index"]) != request["lod_index"]:
                raise ValueError("Export LOD must match the imported LOD")
            current = self._validate_sample(self._sampler(**request))[-1]
            if current != fingerprint:
                raise ValueError("Asset identity, topology, vertex IDs, or bone mapping changed after import")
            response = self._writer(request=dict(request), result=result)
            if not isinstance(response, dict) or response.get("success") is not True:
                detail = response.get("error", "unknown error") if isinstance(response, dict) else "invalid response"
                raise RuntimeError("Unreal writer failed: " + str(detail))
            result["applied"] = True
            result["host_result"] = response
            return result
        except Exception as exc:
            return self._failure(exc)
