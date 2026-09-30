"""Host-independent adapter lifecycle tests using the native solver."""

# Import standard library modules
import gc

# Import third-party modules
import numpy as np
import pytest

# Import local modules
from py_dem_bones import DemBones, DemBonesExt, DemBonesExtWrapper, DemBonesWrapper
from py_dem_bones.adapters.base import HostAdapter

REST = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float)
FACES = [[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]]


@pytest.mark.parametrize("factory", [DemBones, DemBonesExt, DemBonesWrapper, DemBonesExtWrapper])
def test_native_and_wrapped_solvers_follow_adapter_lifecycle(factory):
    solver = factory()
    adapter = HostAdapter(solver)
    assert not adapter._export_result()["success"]
    with pytest.raises(RuntimeError, match="Import"):
        adapter.compute()
    poses = np.stack([REST, REST + [1, 2, 3]])
    assert adapter._import_sequence(REST, poses, ["joint"], FACES)
    assert not adapter._export_result()["success"]
    assert adapter.compute()
    result = adapter._export_result()
    assert result["success"]
    np.testing.assert_allclose(result["weights"], np.ones((1, 4)))
    np.testing.assert_allclose(result["transformations"][1, 0, :3, 3], [1, 2, 3])
    if isinstance(solver, (DemBones, DemBonesExt)):
        # The supplied native solver was configured, not silently replaced.
        assert solver.nV == 4 and solver.nF == 2
    adapter._begin_import()
    assert not adapter._export_result()["success"]


def test_failed_import_and_coordinate_change_invalidate_export():
    adapter = HostAdapter()
    assert adapter._import_sequence(REST, [REST], ["joint"], FACES)
    adapter.compute()
    assert not adapter._import_sequence(REST, [REST], [], FACES)
    assert not adapter._export_result()["success"]
    assert adapter._import_sequence(REST, [REST], ["joint"], FACES)
    adapter.compute()
    adapter.set_coordinate_system(np.diag([100, 100, 100, 1]))
    with pytest.raises(RuntimeError, match="Import"):
        adapter.compute()
    assert not adapter._export_result()["success"]


@pytest.mark.parametrize("kwargs", [{"max_influences": True}, {"smooth_iterations": -1}])
def test_invalid_options_do_not_reuse_old_result(kwargs):
    adapter = HostAdapter()
    assert not adapter._import_sequence(REST, [REST], ["joint"], FACES, **kwargs)
    assert adapter.last_error
    assert not adapter._export_result()["success"]


def test_wrapper_rejects_incompatible_native_objects():
    with pytest.raises(TypeError):
        DemBonesWrapper(object())
    with pytest.raises(TypeError):
        DemBonesExtWrapper(DemBones())
    with pytest.raises(TypeError):
        HostAdapter(object())


@pytest.mark.parametrize("factory", [DemBones, DemBonesExt, DemBonesWrapper, DemBonesExtWrapper])
def test_two_adapters_cannot_own_the_same_solver(factory):
    solver = factory()
    first = HostAdapter(solver)
    with pytest.raises(ValueError, match="one live host adapter"):
        HostAdapter(solver)
    # A second Python wrapper cannot hide the same native instance.
    with pytest.raises(ValueError, match="one live host adapter"):
        HostAdapter(DemBonesWrapper(first.dem_bones.native_solver))
    del first
    gc.collect()
    assert HostAdapter(solver) is not None


def test_export_owns_a_snapshot_and_does_not_follow_external_native_changes():
    adapter = HostAdapter()
    assert adapter._import_sequence(REST, [REST + [1, 0, 0]], ["joint"], FACES)
    adapter.compute()
    first = adapter._export_result()
    first["transformations"][:] = 0
    first["weights"][:] = 0
    # Advanced native changes are outside the adapter contract, but must not
    # replace a completed result that is about to be written into a host.
    adapter.dem_bones.set_mesh_sequence(REST, [REST + [9, 0, 0]], bone_names=["joint"], faces=FACES)
    adapter.dem_bones.compute()
    result = adapter._export_result()
    np.testing.assert_allclose(result["transformations"][0, 0, :3, 3], [1, 0, 0], atol=1e-12)
    np.testing.assert_allclose(result["weights"], 1)
    with pytest.raises(AttributeError):
        adapter.dem_bones = DemBonesWrapper()
