"""Max SDK boundary tests using mocked runtime operations and native solving."""

# Import standard library modules
import sys
from types import SimpleNamespace

# Import third-party modules
import numpy as np
import pytest

# Import local modules
from py_dem_bones.adapters.max import MaxDCCInterface

REST = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float)
FACES = ((0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3))


class Node:
    def __init__(self, name, vertices=REST, faces=FACES):
        self.name = name
        self.vertices = vertices.copy()
        self.faces = faces
        self.modifiers = []


class Skin:
    def __init__(self, bone):
        # Skin system IDs need not equal their UI list positions.
        self.bones = {7: bone}
        self.weights = {}


@pytest.fixture
def host(monkeypatch):
    mesh = Node('rest')
    pose = Node('pose', REST + [1, 2, 3])
    bone = Node('joint')
    skin = Skin(bone)
    mesh.modifiers.append(skin)
    nodes = [mesh, pose, bone]
    deleted = []

    def get_node_by_name(name, *, exact, ignoreCase, all):
        assert exact is True and ignoreCase is False and all is True
        return [node for node in nodes if node.name == name]

    skin_ops = SimpleNamespace(
        GetNumberBones=lambda modifier: len(modifier.bones),
        GetBoneIDByListID=lambda modifier, index: sorted(modifier.bones)[index - 1],
        GetBoneNode=lambda modifier, index: modifier.bones[index],
        GetNumberVertices=lambda modifier: len(mesh.vertices),
        ReplaceVertexWeights=lambda modifier, vertex, ids, values: modifier.weights.update(
            {vertex: dict(zip(ids, values))}
        ),
        GetVertexWeightCount=lambda modifier, vertex: len(modifier.weights[vertex]),
        GetVertexWeightBoneID=lambda modifier, vertex, index: list(modifier.weights[vertex])[index - 1],
        GetVertexWeight=lambda modifier, vertex, index: list(modifier.weights[vertex].values())[index - 1],
    )
    rt = SimpleNamespace(
        getNodeByName=get_node_by_name,
        snapshotAsMesh=lambda node: Node(node.name, node.vertices, node.faces),
        getNumVerts=lambda mesh: len(mesh.vertices),
        getNumFaces=lambda mesh: len(mesh.faces),
        getVert=lambda mesh, index: SimpleNamespace(**dict(zip(('x', 'y', 'z'), mesh.vertices[index - 1]))),
        getFace=lambda mesh, index: SimpleNamespace(**dict(zip(('x', 'y', 'z'), np.array(mesh.faces[index - 1]) + 1))),
        delete=deleted.append, isValidNode=lambda node: node in nodes,
        classOf=type, Skin=Skin, skinOps=skin_ops, Array=lambda *values: values,
        modPanel=SimpleNamespace(getCurrentObject=lambda: skin),
        scene_nodes=nodes,
    )
    monkeypatch.setitem(sys.modules, 'pymxs', SimpleNamespace(runtime=rt))
    return mesh, pose, bone, skin, rt, deleted


def solved(host):
    adapter = MaxDCCInterface()
    assert adapter.from_dcc_data('rest', ['joint'], ['rest', 'pose']), adapter.last_error
    adapter.compute()
    return adapter


def test_native_solve_releases_snapshots_and_updates_existing_skin(host):
    adapter = solved(host)
    assert len(host[-1]) == 3
    result = adapter.to_dcc_data(skin_modifier=host[3])
    assert result['success'] and result['applied']
    assert result['weights'].shape == (1, 4)
    assert result['transformations'].shape == (2, 1, 4, 4)
    np.testing.assert_allclose(result['transformations'][1, 0, :3, 3], [1, 2, 3])
    assert host[3].weights == {index: {7: 1.0} for index in range(1, 5)}
    assert host[0].modifiers == [host[3]]


@pytest.mark.parametrize('case', ['missing_pose', 'topology', 'no_poses'])
def test_bad_import_clears_previous_result(host, case):
    adapter = solved(host)
    poses = ['pose']
    if case == 'missing_pose':
        poses = ['missing']
    elif case == 'topology':
        host[1].faces = tuple(reversed(FACES))
    else:
        poses = []
    assert not adapter.from_dcc_data('rest', ['joint'], poses)
    assert adapter.last_error
    assert not adapter.to_dcc_data(apply_weights=False)['success']


@pytest.mark.parametrize('case', ['missing_skin', 'create', 'topology', 'bone', 'above_skin', 'inactive_skin'])
def test_write_preconditions_do_not_alter_skin(host, case):
    adapter = solved(host)
    kwargs = {'skin_modifier': host[3]}
    if case == 'missing_skin':
        kwargs = {}
    elif case == 'create':
        kwargs['create_skin_modifier'] = True
    elif case == 'topology':
        host[0].faces = tuple(reversed(FACES))
    elif case == 'bone':
        host[2].name = 'renamed'
    elif case == 'above_skin':
        host[0].modifiers.insert(0, object())
    else:
        host[4].modPanel.getCurrentObject = lambda: None
    assert not adapter.to_dcc_data(**kwargs)['success']
    assert not host[3].weights


def test_readback_detects_host_dropping_weights(host):
    adapter = solved(host)
    host[4].skinOps.ReplaceVertexWeights = lambda *args: host[3].weights.update({args[1]: {7: 0.5}})
    result = adapter.to_dcc_data(skin_modifier=host[3])
    assert not result['success']
    assert 'readback' in result['error']


def test_write_uses_system_bone_ids_and_preserves_tiny_weights(host, monkeypatch):
    adapter = solved(host)
    other = host[1]
    other.name = 'other'
    mesh, bones, topology, world_space = adapter._max_data
    adapter._max_data = (mesh, (bones[0], other), topology, world_space)
    host[3].bones[2] = other
    weights = np.array([[0.999999] * 4, [0.000001] * 4])
    monkeypatch.setattr(adapter, '_export_result', lambda: {
        'success': True, 'weights': weights, 'bone_names': ['joint', 'other']
    })
    result = adapter.to_dcc_data(skin_modifier=host[3])
    assert result['success'], result
    assert host[3].weights[1] == {7: 0.999999, 2: 0.000001}


def test_two_bone_native_solve_maps_and_writes_all_vertices(host):
    rest = np.vstack([REST, REST + [3, 0, 0]])
    pose = rest.copy()
    pose[:4] += [1, 0, 0]
    pose[4:] += [0, 2, 0]
    faces = FACES + tuple(tuple(index + 4 for index in face) for face in FACES)
    host[0].vertices, host[0].faces = rest, faces
    host[1].vertices, host[1].faces = pose, faces
    host[3].bones[2] = host[1]
    adapter = MaxDCCInterface()
    assert adapter.from_dcc_data('rest', ['joint', 'pose'], ['rest', 'pose'])
    adapter.compute()
    result = adapter.to_dcc_data(skin_modifier=host[3])
    assert result['success'], result
    assert result['weights'].shape == (2, 8)
    assert result['transformations'].shape == (2, 2, 4, 4)
    assert len(host[3].weights) == 8
    homogeneous = np.column_stack([rest, np.ones(8)])
    rebuilt = np.einsum('bv,fbij,vj->fvi', result['weights'], result['transformations'], homogeneous)[..., :3]
    np.testing.assert_allclose(rebuilt, [rest, pose], atol=1e-6)


@pytest.mark.parametrize('role', ['mesh', 'bone', 'pose'])
@pytest.mark.parametrize('problem', ['duplicate', 'case_mismatch'])
def test_ambiguous_or_inexact_names_invalidate_import_without_writes(host, role, problem):
    adapter = solved(host)
    original_names = {'mesh': 'rest', 'bone': 'joint', 'pose': 'pose'}
    name = original_names[role]
    extra_node = Node(name if problem == 'duplicate' else name.title())
    extra_skin = Skin(extra_node)
    extra_node.modifiers.append(extra_skin)
    host[4].scene_nodes.append(extra_node)
    names = dict(original_names)
    if problem == 'case_mismatch':
        # Two case-insensitive matches exist, but neither is an exact match.
        names[role] = name.upper()
    snapshots_before = len(host[-1])
    assert not adapter.from_dcc_data(names['mesh'], [names['bone']], [names['pose']])
    assert 'case-sensitive match' in adapter.last_error
    assert len(host[-1]) == snapshots_before
    assert not adapter.to_dcc_data(skin_modifier=host[3])['success']
    assert not host[3].weights and not extra_skin.weights


def test_export_keeps_imported_node_identity_when_duplicate_names_appear(host):
    adapter = solved(host)
    duplicate = Node('rest')
    duplicate_skin = Skin(host[2])
    duplicate.modifiers.append(duplicate_skin)
    host[4].scene_nodes.append(duplicate)
    result = adapter.to_dcc_data(skin_modifier=host[3])
    assert result['success'], result
    assert host[3].weights
    assert not duplicate_skin.weights
