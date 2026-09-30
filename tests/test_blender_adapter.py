"""Blender evaluated sampling, restoration, and write-boundary contracts."""

# Import standard library modules
import sys
from types import SimpleNamespace

# Import third-party modules
import numpy as np
import pytest

# Import local modules
from py_dem_bones.adapters.blender import BlenderDCCInterface

REST = np.asarray([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float)
FACES = ((0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3))


class Data(SimpleNamespace):
    def as_pointer(self):
        return id(self)


class Group:
    def __init__(self, name):
        self.name, self.lock_weight = name, False
        self.weights = {}
        self.calls = []

    def add(self, indices, weight, mode):
        assert mode == "REPLACE"
        self.calls.append((list(indices), weight))
        for index in indices:
            self.weights[index] = weight


class Groups(dict):
    def new(self, name):
        self[name] = Group(name)
        return self[name]


def mesh_data(points=REST, faces=FACES):
    return Data(vertices=[Data(co=point) for point in points], polygons=[Data(vertices=face) for face in faces])


@pytest.fixture
def blender_host(monkeypatch):
    basis, pose = Data(name="Basis", value=0.0, mute=False), Data(name="Pose", value=0.3, mute=False)
    keys = Data(use_relative=True, key_blocks=[basis, pose])
    mesh = mesh_data()
    mesh.shape_keys = keys
    groups = Groups()
    groups.new("Bone").weights = {index: 0.5 for index in range(4)}
    groups.new("Unrelated").weights = {0: 0.8}
    obj = Data(name="Mesh", type="MESH", mode="OBJECT", data=mesh, vertex_groups=groups, show_only_shape_key=True)
    armature = Data(name="Rig", type="ARMATURE", data=Data(bones=[Data(name="Bone", use_deform=True)]))
    state = Data(obj=obj, armature=armature, keys=keys, samples=[], clears=0, updates=0,
                 break_pose=False, fail_pose=False, topology_changed=False, driver_override=False)

    class Matrix:
        def __matmul__(self, vector):
            return vector + [5, 0, 0]

    class Evaluated:
        matrix_world = Matrix()

        def to_mesh(self):
            value = pose.value
            state.samples.append(value)
            if state.fail_pose and value == 1.0:
                # A failure while reading points must still free the temporary mesh.
                return Data(vertices=[Data(co=None)], polygons=[])
            faces = tuple(reversed(FACES)) if state.topology_changed or (state.break_pose and value == 1) else FACES
            return mesh_data(REST + value * np.array([1, 2, 3]), faces)

        def to_mesh_clear(self):
            state.clears += 1

    obj.evaluated_get = lambda _: Evaluated()

    def update():
        state.updates += 1
        if state.driver_override:
            pose.value = 0.6

    bpy = Data(
        data=Data(objects={"Mesh": obj, "Rig": armature}),
        context=Data(view_layer=Data(update=update), evaluated_depsgraph_get=lambda: object()),
    )
    monkeypatch.setitem(sys.modules, "bpy", bpy)
    state.bpy = bpy
    return state


def import_mesh(adapter):
    assert adapter.from_dcc_data("Mesh", "Rig", ["Pose"]), adapter.last_error


def test_blender_samples_evaluated_mesh_restores_keys_and_native_solve(blender_host):
    adapter = BlenderDCCInterface()
    import_mesh(adapter)
    assert blender_host.samples == [0.0, 1.0]
    assert blender_host.clears == 2
    assert blender_host.keys.key_blocks[1].value == 0.3
    assert blender_host.obj.show_only_shape_key is True
    adapter.compute()
    result = adapter.to_dcc_data()
    assert result["success"], result
    assert result["transformations"].shape == (1, 1, 4, 4)
    np.testing.assert_allclose(result["transformations"][0, 0, :3, 3], [1, 2, 3])
    assert blender_host.obj.vertex_groups["Bone"].weights == {index: 1.0 for index in range(4)}
    assert blender_host.obj.vertex_groups["Unrelated"].weights == {0: 0.8}


@pytest.mark.parametrize("failure", ["topology", "read"])
def test_blender_restores_shape_state_and_temporary_mesh_on_failure(blender_host, failure):
    adapter = BlenderDCCInterface()
    import_mesh(adapter)
    adapter.compute()
    blender_host.break_pose = failure == "topology"
    blender_host.fail_pose = failure == "read"
    assert not adapter.from_dcc_data("Mesh", "Rig", ["Pose"])
    assert blender_host.keys.key_blocks[1].value == 0.3
    assert blender_host.obj.show_only_shape_key is True
    assert blender_host.clears == 4
    assert not adapter.to_dcc_data()["success"]
    assert not blender_host.obj.vertex_groups["Bone"].calls


def test_blender_missing_key_fails_without_mutating_caller_names(blender_host):
    names = ["Pose", "Missing"]
    adapter = BlenderDCCInterface()
    assert not adapter.from_dcc_data("Mesh", "Rig", names)
    assert names == ["Pose", "Missing"]
    assert blender_host.keys.key_blocks[1].value == 0.3
    assert not blender_host.samples


def test_blender_optional_keys_import_a_static_frame(blender_host):
    adapter = BlenderDCCInterface()
    assert adapter.from_dcc_data("Mesh", "Rig")
    adapter.compute()
    result = adapter.to_dcc_data(apply_weights=False)
    assert result["success"]
    np.testing.assert_allclose(result["transformations"][0, 0], np.eye(4), atol=1e-12)
    assert blender_host.keys.key_blocks[1].value == 0.3


def test_blender_rejects_modifier_topology_and_driver_overrides(blender_host):
    adapter = BlenderDCCInterface()
    blender_host.topology_changed = True
    assert not adapter.from_dcc_data("Mesh", "Rig", ["Pose"])
    assert "topology" in adapter.last_error
    blender_host.topology_changed = False
    blender_host.driver_override = True
    assert not adapter.from_dcc_data("Mesh", "Rig", ["Pose"])
    assert "drivers" in adapter.last_error


@pytest.mark.parametrize("change", ["topology", "evaluated", "identity", "bone_order", "locked", "edit_mode"])
def test_blender_preflight_rejects_changed_targets_before_writing(blender_host, change):
    adapter = BlenderDCCInterface()
    import_mesh(adapter)
    adapter.compute()
    if change == "topology":
        blender_host.obj.data.polygons.reverse()
    elif change == "evaluated":
        blender_host.topology_changed = True
    elif change == "identity":
        blender_host.obj.data = Data(**vars(blender_host.obj.data))
    elif change == "bone_order":
        blender_host.armature.data.bones[0].name = "NewBone"
    elif change == "locked":
        blender_host.obj.vertex_groups["Bone"].lock_weight = True
    else:
        blender_host.obj.mode = "EDIT"
    result = adapter.to_dcc_data()
    assert not result["success"]
    assert not blender_host.obj.vertex_groups["Bone"].calls
    assert list(blender_host.obj.vertex_groups) == ["Bone", "Unrelated"]


def test_blender_full_weight_replacement_preserves_tiny_values_and_unrelated_groups(blender_host, monkeypatch):
    blender_host.armature.data.bones.append(Data(name="Second", use_deform=True))
    adapter = BlenderDCCInterface()
    import_mesh(adapter)
    weights = np.asarray([[1.0, 1e-8, 0.0, 0.2], [0.0, 1 - 1e-8, 1.0, 0.8]])
    monkeypatch.setattr(adapter, "_export_result", lambda: {
        "success": True, "weights": weights, "bone_names": ["Bone", "Second"]
    })
    assert not adapter.to_dcc_data(create_vertex_groups=False)["success"]
    assert not blender_host.obj.vertex_groups["Bone"].calls
    assert adapter.to_dcc_data(clear_existing_weights=True)["success"]
    for index, name in enumerate(["Bone", "Second"]):
        np.testing.assert_array_equal(list(blender_host.obj.vertex_groups[name].weights.values()), weights[index])
    assert blender_host.obj.vertex_groups["Unrelated"].weights == {0: 0.8}


def test_blender_unsolved_result_never_samples_or_writes(blender_host):
    adapter = BlenderDCCInterface()
    import_mesh(adapter)
    blender_host.samples.clear()
    assert not adapter.to_dcc_data()["success"]
    assert not blender_host.samples
    assert not blender_host.obj.vertex_groups["Bone"].calls
