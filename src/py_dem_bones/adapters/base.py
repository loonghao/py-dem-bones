"""Shared lifecycle and output checks for host adapters."""

# Import standard library modules
from numbers import Integral
from threading import Lock
from weakref import WeakKeyDictionary, ref

# Import third-party modules
import numpy as np

# Import local modules
from py_dem_bones._py_dem_bones import DemBones, DemBonesExt
from py_dem_bones.base import DemBonesExtWrapper, DemBonesWrapper
from py_dem_bones.interfaces.dcc import BaseDCCInterface

_SOLVER_OWNERS = WeakKeyDictionary()
_OWNER_LOCK = Lock()


class HostAdapter(BaseDCCInterface):
    """Keep host sampling and writing outside the solver's array contract.

    Call ``from_dcc_data``, then ``compute``, then ``to_dcc_data``. Native
    instances supplied by older callers are retained, but compute must go
    through the adapter so its result lifecycle is tracked. Solved bone slots
    are labels, not a fit constrained to an existing skeleton's bind pose.
    """

    def __init__(self, dem_bones_instance=None):
        if dem_bones_instance is None:
            wrapper = DemBonesWrapper()
        elif isinstance(dem_bones_instance, DemBonesWrapper):
            wrapper = dem_bones_instance
        elif isinstance(dem_bones_instance, DemBonesExt):
            wrapper = DemBonesExtWrapper(dem_bones_instance)
        elif isinstance(dem_bones_instance, DemBones):
            wrapper = DemBonesWrapper(dem_bones_instance)
        else:
            raise TypeError("dem_bones_instance must be a native solver or DemBonesWrapper")
        with _OWNER_LOCK:
            owner = _SOLVER_OWNERS.get(wrapper.native_solver)
            if owner is not None and owner() is not None:
                raise ValueError("A native solver can be owned by only one live host adapter")
            _SOLVER_OWNERS[wrapper.native_solver] = ref(self)
        super().__init__(wrapper)
        self._begin_import()

    @property
    def dem_bones(self):
        """The borrowed wrapper; replacing it would invalidate solver ownership."""
        return self._dem_bones

    def _begin_import(self):
        self._import_succeeded = False
        self._result = None
        self._requested_bone_names = ()
        self._vertex_count = 0
        self._host_data = {}
        self.last_error = None

    def _import_sequence(self, rest, poses, bone_names, faces, *, max_influences=4, smooth_iterations=3):
        self._import_succeeded = False
        self._result = None
        try:
            if not isinstance(max_influences, Integral) or isinstance(max_influences, bool) or max_influences < 1:
                raise ValueError("max_influences must be a positive integer")
            if (
                not isinstance(smooth_iterations, Integral)
                or isinstance(smooth_iterations, bool)
                or smooth_iterations < 0
            ):
                raise ValueError("smooth_iterations must be a nonnegative integer")
            names = tuple(bone_names)
            if not names:
                raise ValueError("At least one named bone is required")
            self.dem_bones.max_influences = int(max_influences)
            self.dem_bones.weight_smoothness = 0.0001 * int(smooth_iterations)
            self.dem_bones.set_mesh_sequence(
                self.apply_coordinate_system_transform(rest),
                self.apply_coordinate_system_transform(np.asarray(poses)),
                bone_count=len(names), bone_names=names, faces=faces,
            )
            self._requested_bone_names = names
            self._vertex_count = self.dem_bones.num_vertices
            self._import_succeeded = True
            self.last_error = None
            return True
        except Exception as exc:
            self.last_error = str(exc)
            return False

    def compute(self):
        """Solve the last successfully imported sequence."""
        if not self._import_succeeded:
            raise RuntimeError("Import a valid mesh sequence before computing")
        self._result = None
        self.dem_bones.compute()
        self._result = self.dem_bones.get_skinning_result()
        self._result_bone_names = tuple(self.dem_bones.bone_names)
        return True

    def _export_result(self):
        if not self._import_succeeded or self._result is None:
            return self._failure("Import and compute a mesh sequence before exporting")
        # The adapter owns a snapshot. Later native operations or a caller
        # mutating an exported array cannot replace this adapter's solution.
        result = {
            "success": True,
            "weights": self._result.weights.copy(),
            "transformations": self.convert_matrices(self._result.transforms, from_dcc=False).copy(),
            "bone_names": list(self._result_bone_names),
        }
        weights = result["weights"]
        if tuple(result["bone_names"]) != self._requested_bone_names:
            return self._failure("Solved bone slots differ from the imported bone mapping")
        if weights.shape != (len(self._requested_bone_names), self._vertex_count):
            return self._failure("Solved weights do not match the imported mesh and bones")
        if not np.isfinite(weights).all() or np.any(weights < 0):
            return self._failure("Solved weights must be finite and nonnegative")
        if not np.allclose(weights.sum(axis=0), 1, rtol=1e-6, atol=1e-8):
            return self._failure("Solved weights must sum to one for every vertex")
        return result

    def _failure(self, error):
        self.last_error = str(error)
        return {"success": False, "error": self.last_error}

    def to_dcc_data(self, **kwargs):
        """Export this adapter's computed snapshot without host mutation."""
        return self._export_result()
