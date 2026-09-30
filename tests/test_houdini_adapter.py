"""Houdini SDK boundary tests; host calls are mocked, solving is native."""

# Import standard library modules
import sys
from types import SimpleNamespace

# Import third-party modules
import numpy as np
import pytest

# Import local modules
from py_dem_bones.adapters.houdini import HoudiniDCCInterface

REST = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float)
FACES = ((0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3))


class Geometry:
    def __init__(self, vertices=REST, faces=FACES, readonly=False):
        self.vertices = vertices.copy()
        self.faces = faces
        self.readonly = readonly
        self.attributes = {}
        self.values = {}

    def points(self):
        return [SimpleNamespace(number=lambda i=i: i, position=lambda i=i: self.vertices[i])
                for i in range(len(self.vertices))]

    def prims(self):
        points = self.points()
        return [SimpleNamespace(
            type=lambda: 'Polygon', isClosed=lambda: True,
            vertices=lambda face=face: [SimpleNamespace(point=lambda i=i: points[i]) for i in face],
        ) for face in self.faces]

    def isReadOnly(self):
        return self.readonly

    def findPointAttrib(self, name):
        return self.attributes.get(name)

    def addAttrib(self, kind, name, default):
        assert kind == 'Point' and default == 0.0
        self.attributes[name] = SimpleNamespace(size=lambda: 1, dataType=lambda: 'Float')

    def setPointFloatAttribValues(self, name, values):
        self.values[name] = values

    def pointFloatAttribValues(self, name):
        return self.values[name]


@pytest.fixture
def host(monkeypatch):
    source = Geometry(readonly=True)
    pose = Geometry(REST + [1, 2, 3], readonly=True)
    nodes = {
        '/rest': SimpleNamespace(geometry=lambda: source),
        '/pose': SimpleNamespace(geometry=lambda: pose),
        '/bone': SimpleNamespace(name=lambda: 'joint'),
    }
    monkeypatch.setitem(sys.modules, 'hou', SimpleNamespace(
        node=nodes.get, primType=SimpleNamespace(Polygon='Polygon'),
        attribType=SimpleNamespace(Point='Point'), attribData=SimpleNamespace(Float='Float'),
    ))
    return source, pose, nodes


def solved(host):
    adapter = HoudiniDCCInterface()
    assert adapter.from_dcc_data('/rest', ['/bone'], ['/rest', '/pose']), adapter.last_error
    adapter.compute()
    return adapter


def test_native_solve_and_explicit_writable_attributes(host):
    adapter = solved(host)
    result = adapter.to_dcc_data(apply_weights=False)
    assert result['success']
    assert result['weights'].shape == (1, 4)
    assert result['transformations'].shape == (2, 1, 4, 4)
    np.testing.assert_allclose(result['transformations'][1, 0, :3, 3], [1, 2, 3])
    output = Geometry()
    result = adapter.to_dcc_data(geometry=output)
    assert result['success'] and result['applied']
    assert result['weight_attributes'] == {'joint': 'weight_0'}
    np.testing.assert_allclose(output.values['weight_0'], np.ones(4))
    assert not host[0].values


@pytest.mark.parametrize('case', ['missing_pose', 'topology', 'no_poses'])
def test_bad_import_invalidates_previous_result(host, case):
    adapter = solved(host)
    poses = ['/pose']
    if case == 'missing_pose':
        poses = ['/missing']
    elif case == 'topology':
        host[1].faces = tuple(reversed(FACES))
    else:
        poses = []
    assert not adapter.from_dcc_data('/rest', ['/bone'], poses)
    assert adapter.last_error
    assert not adapter.to_dcc_data(apply_weights=False)['success']


@pytest.mark.parametrize('case', ['readonly', 'topology', 'source_topology', 'bone', 'capture', 'type'])
def test_write_preconditions_do_not_mutate_output(host, case):
    adapter = solved(host)
    output = Geometry()
    kwargs = {}
    if case == 'readonly':
        output.readonly = True
    elif case == 'topology':
        output.faces = tuple(reversed(FACES))
    elif case == 'source_topology':
        host[0].faces = tuple(reversed(FACES))
    elif case == 'bone':
        host[2]['/bone'] = SimpleNamespace(name=lambda: 'joint')
    elif case == 'capture':
        kwargs['create_capture_attr'] = True
    else:
        output.attributes['weight_0'] = SimpleNamespace(size=lambda: 3, dataType=lambda: 'Float')
    result = adapter.to_dcc_data(geometry=output, **kwargs)
    assert not result['success']
    assert result['error']
    assert not output.values


def test_write_keeps_small_bone_weights(host, monkeypatch):
    adapter = solved(host)
    second = SimpleNamespace(name=lambda: 'other')
    host[2]['/other'] = second
    original = adapter._houdini_data
    adapter._houdini_data = (original[0], original[1], ('/bone', '/other'),
                             (host[2]['/bone'], second), original[-1])
    weights = np.array([[0.999999] * 4, [0.000001] * 4])
    monkeypatch.setattr(adapter, '_export_result', lambda: {
        'success': True, 'weights': weights, 'bone_names': ['joint', 'other']
    })
    output = Geometry()
    assert adapter.to_dcc_data(geometry=output)['success']
    np.testing.assert_equal(output.values['weight_1'], weights[1])


def test_two_bone_native_solve_exports_all_bone_slots(host):
    rest = np.vstack([REST, REST + [3, 0, 0]])
    pose = rest.copy()
    pose[:4] += [1, 0, 0]
    pose[4:] += [0, 2, 0]
    faces = FACES + tuple(tuple(index + 4 for index in face) for face in FACES)
    host[0].vertices, host[0].faces = rest, faces
    host[1].vertices, host[1].faces = pose, faces
    host[2]['/other'] = SimpleNamespace(name=lambda: 'other')
    adapter = HoudiniDCCInterface()
    assert adapter.from_dcc_data('/rest', ['/bone', '/other'], ['/rest', '/pose'])
    adapter.compute()
    result = adapter.to_dcc_data(geometry=Geometry(rest, faces))
    assert result['success'], result
    assert result['weights'].shape == (2, 8)
    assert result['transformations'].shape == (2, 2, 4, 4)
    homogeneous = np.column_stack([rest, np.ones(8)])
    rebuilt = np.einsum('bv,fbij,vj->fvi', result['weights'], result['transformations'], homogeneous)[..., :3]
    np.testing.assert_allclose(rebuilt, [rest, pose], atol=1e-6)
