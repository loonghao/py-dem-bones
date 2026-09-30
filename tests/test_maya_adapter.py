"""Maya adapter boundary tests with host doubles and the actual native solver."""

# Import standard library modules
import sys
from types import ModuleType, SimpleNamespace

# Import third-party modules
import numpy as np
import pytest

# Import local modules
from py_dem_bones.adapters.maya import MayaDCCInterface

REST = np.asarray([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float)
FACES = ((0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3))


@pytest.fixture
def maya_host(monkeypatch):
    state = SimpleNamespace(
        meshes={"|mesh|shape": (REST.copy(), FACES), "|pose|shape": (REST + [1, 2, 3], FACES)},
        nodes={"|mesh|shape": "mesh", "|pose|shape": "mesh", "|joint": "joint", "|other": "joint"},
        uuids={}, skins=["skin"], influences=["|joint"], writes=[], creates=[], samples=[],
        weights=[0.5] * 4, reject_write=False, deleted=[],
    )

    class Path:
        def __init__(self, name):
            self.name = name

        def fullPathName(self):
            return self.name

    class Selection:
        def add(self, name):
            self.name = name

        def getDagPath(self, _):
            return Path(self.name)

        def getDependNode(self, _):
            return self.name

    class Mesh:
        def __init__(self, path):
            self.name = path.name

        def getPoints(self, space):
            state.samples.append((self.name, space))
            return [SimpleNamespace(x=p[0], y=p[1], z=p[2]) for p in state.meshes[self.name][0]]

        def getVertices(self):
            faces = state.meshes[self.name][1]
            return [len(face) for face in faces], [index for face in faces for index in face]

    class Component:
        def create(self, _):
            return self

        def addElements(self, indices):
            self.indices = list(indices)

    class Skin:
        def __init__(self, _):
            pass

        def influenceObjects(self):
            return [Path(name) for name in state.influences]

        def setWeights(self, path, component, indices, weights, normalize):
            state.writes.append((path.name, component.indices, list(indices), list(weights), normalize))
            if not state.reject_write:
                state.weights = list(weights)

        def getWeights(self, path, component):
            return list(state.weights), len(state.influences)

    def ls(names, **kwargs):
        if kwargs.get("type") == "skinCluster":
            return list(state.skins)
        if kwargs.get("uuid"):
            return [state.uuids.get(names, names)]
        return [names] if names in state.nodes else []

    def create_skin(joints, mesh, **kwargs):
        state.creates.append((joints, mesh, kwargs))
        state.influences = list(joints)
        state.skins = ["newSkin"]
        state.weights = [1.0 / len(joints)] * (len(joints) * 4)
        return state.skins

    maya, api, om, oma, cmds = [ModuleType(name) for name in (
        "maya", "maya.api", "maya.api.OpenMaya", "maya.api.OpenMayaAnim", "maya.cmds"
    )]
    om.MSelectionList, om.MFnMesh, om.MFnSingleIndexedComponent = Selection, Mesh, Component
    om.MSpace = SimpleNamespace(kWorld="world", kObject="object")
    om.MFn = SimpleNamespace(kMeshVertComponent=1)
    om.MIntArray, om.MDoubleArray = list, list
    oma.MFnSkinCluster = Skin
    cmds.ls, cmds.nodeType = ls, state.nodes.__getitem__
    cmds.listHistory = lambda _: list(state.skins)
    cmds.skinCluster = create_skin
    cmds.delete = state.deleted.append
    maya.api, maya.cmds, api.OpenMaya, api.OpenMayaAnim = api, cmds, om, oma
    for module in (maya, api, om, oma, cmds):
        monkeypatch.setitem(sys.modules, module.__name__, module)
    return state


def import_mesh(adapter):
    assert adapter.from_dcc_data("|mesh|shape", ["|joint"], ["|pose|shape"]), adapter.last_error


def test_maya_native_sequence_and_bulk_weight_write(maya_host):
    adapter = MayaDCCInterface()
    import_mesh(adapter)
    adapter.compute()
    result = adapter.to_dcc_data(create_skin_cluster=False)
    assert result["success"], result
    assert result["weights"].shape == (1, 4)
    assert result["transformations"].shape == (1, 1, 4, 4)
    homogeneous = np.column_stack([REST, np.ones(len(REST))])
    np.testing.assert_allclose((homogeneous @ result["transformations"][0, 0])[:, :3], REST + [1, 2, 3])
    assert maya_host.writes == [("|mesh|shape", [0, 1, 2, 3], [0], [1.0] * 4, False)]
    assert not maya_host.creates
    assert maya_host.samples[0][1] == "world"


def test_maya_matrix_conversion_preserves_batch_axes():
    adapter = MayaDCCInterface()
    matrices = np.broadcast_to(np.eye(4), (3, 2, 4, 4)).copy()
    matrices[:, :, :3, 3] = [1, 2, 3]
    host = adapter.convert_matrices(matrices, False)
    assert host.shape == (3, 2, 4, 4)
    np.testing.assert_array_equal(host[..., 3, :3], np.broadcast_to([1, 2, 3], (3, 2, 3)))
    np.testing.assert_array_equal(adapter.convert_matrices(host), matrices)


def test_maya_complete_multiframe_native_sequence(maya_host):
    maya_host.meshes["|pose2|shape"] = (REST + [-2, 3, 1], FACES)
    maya_host.nodes["|pose2|shape"] = "mesh"
    adapter = MayaDCCInterface()
    assert adapter.from_dcc_data("|mesh|shape", ["|joint"], ["|pose|shape", "|pose2|shape"])
    adapter.compute()
    result = adapter.to_dcc_data(apply_weights=False)
    assert result["success"]
    assert result["transformations"].shape == (2, 1, 4, 4)
    np.testing.assert_allclose(result["transformations"][:, 0, 3, :3], [[1, 2, 3], [-2, 3, 1]])


def test_maya_optional_poses_import_a_static_frame(maya_host):
    adapter = MayaDCCInterface()
    assert adapter.from_dcc_data("|mesh|shape", ["|joint"])
    adapter.compute()
    result = adapter.to_dcc_data(apply_weights=False)
    assert result["success"]
    np.testing.assert_allclose(result["transformations"][0, 0], np.eye(4), atol=1e-12)


def test_maya_pose_connectivity_failure_invalidates_old_result(maya_host):
    adapter = MayaDCCInterface()
    import_mesh(adapter)
    adapter.compute()
    maya_host.meshes["|pose|shape"] = (REST, tuple(reversed(FACES)))
    assert not adapter.from_dcc_data("|mesh|shape", ["|joint"], ["|pose|shape"])
    assert "topology" in adapter.last_error
    assert not adapter.to_dcc_data()["success"]
    assert not maya_host.writes


@pytest.mark.parametrize("change", ["topology", "identity", "joint", "influences", "multiple_skins"])
def test_maya_rejects_changed_target_before_writing(maya_host, change):
    adapter = MayaDCCInterface()
    import_mesh(adapter)
    adapter.compute()
    if change == "topology":
        maya_host.meshes["|mesh|shape"] = (REST, tuple(reversed(FACES)))
    elif change == "identity":
        maya_host.uuids["|mesh|shape"] = "replacement"
    elif change == "joint":
        maya_host.uuids["|joint"] = "replacement"
    elif change == "influences":
        maya_host.influences = ["|other"]
    else:
        maya_host.skins.append("secondSkin")
    assert not adapter.to_dcc_data()["success"]
    assert not maya_host.writes and not maya_host.creates


def test_maya_create_skin_opt_in_and_full_weight_layout(maya_host, monkeypatch):
    adapter = MayaDCCInterface()
    assert adapter.from_dcc_data("|mesh|shape", ["|joint", "|other"], ["|pose|shape"])
    weights = np.asarray([[1.0, 1e-8, 0.0, 0.2], [0.0, 1 - 1e-8, 1.0, 0.8]])
    monkeypatch.setattr(adapter, "_export_result", lambda: {
        "success": True, "weights": weights, "bone_names": ["|joint", "|other"]
    })
    maya_host.skins = []
    assert not adapter.to_dcc_data(create_skin_cluster=False)["success"]
    assert not maya_host.creates
    assert adapter.to_dcc_data()["success"]
    assert len(maya_host.creates) == 1
    assert maya_host.writes[0][2] == [0, 1]
    np.testing.assert_array_equal(maya_host.writes[0][3], weights.T.reshape(-1))


def test_maya_unsolved_result_never_touches_host(maya_host):
    adapter = MayaDCCInterface()
    import_mesh(adapter)
    maya_host.samples.clear()
    assert not adapter.to_dcc_data()["success"]
    assert not maya_host.samples and not maya_host.writes and not maya_host.creates


@pytest.mark.parametrize("create_new", [False, True])
def test_maya_rejected_weight_write_never_reports_success(maya_host, monkeypatch, create_new):
    adapter = MayaDCCInterface()
    import_mesh(adapter)
    adapter.compute()
    maya_host.reject_write = True
    if create_new:
        # Force a requested result distinct from newly bound weights.
        maya_host.skins = []
        original_create = sys.modules["maya.cmds"].skinCluster

        def create(*args, **kwargs):
            result = original_create(*args, **kwargs)
            maya_host.weights = [0.5] * 4
            return result

        monkeypatch.setattr(sys.modules["maya.cmds"], "skinCluster", create)
    result = adapter.to_dcc_data()
    assert not result["success"]
    assert "readback" in result["error"]
    if create_new:
        assert maya_host.deleted == ["newSkin"]
    else:
        assert not maya_host.deleted
        assert maya_host.writes[-1][3] == [0.5] * 4
