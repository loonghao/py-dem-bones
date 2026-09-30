"""Unreal data bridge contracts, with a real native solve and no Unreal dependency."""

# Import standard library modules
from copy import deepcopy

# Import third-party modules
import numpy as np
import pytest

# Import local modules
from py_dem_bones.adapters.unreal import UnrealDCCInterface

REST = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float)
FACES = ((0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3))


@pytest.fixture
def sample():
    return {
        'rest_vertices': REST.copy(), 'poses': np.stack([REST, REST + [1, 2, 3]]),
        'faces': FACES, 'pose_faces': [FACES, FACES], 'bone_names': ['joint'],
        'vertex_ids': [1, 5, 9, 20], 'pose_vertex_ids': [[1, 5, 9, 20]] * 2,
        'identity': ('/Game/Mesh', 0, 'revision1'),
    }


def solved(sample, writer=None):
    adapter = UnrealDCCInterface(sampler=lambda **request: deepcopy(sample), writer=writer)
    assert adapter.from_dcc_data('/Game/Mesh', '/Game/Skeleton', ['pose']), adapter.last_error
    adapter.compute()
    return adapter


def test_native_solve_and_writer_receives_complete_contract(sample):
    received = []
    adapter = solved(sample, lambda **payload: received.append(payload) or {'success': True})
    result = adapter.to_dcc_data()
    assert result['success'] and result['applied']
    assert result['weights'].shape == (1, 4)
    assert result['transformations'].shape == (2, 1, 4, 4)
    np.testing.assert_allclose(result['transformations'][1, 0, :3, 3], [1, 2, 3])
    assert received[0]['request']['lod_index'] == 0
    assert received[0]['result']['weights'].shape == (1, 4)
    assert received[0]['result']['vertex_ids'] == (1, 5, 9, 20)


def test_missing_engine_bridge_is_explicitly_unsupported(sample):
    adapter = UnrealDCCInterface()
    assert not adapter.from_dcc_data('/Game/Mesh', '/Game/Skeleton')
    assert 'sampler' in adapter.last_error
    adapter = solved(sample)
    assert adapter.to_dcc_data(apply_weights=False)['success']
    result = adapter.to_dcc_data()
    assert not result['success'] and 'writer' in result['error']


@pytest.mark.parametrize('case', ['topology', 'vertex_order', 'bone_order', 'identity'])
def test_mutated_asset_blocks_writer(sample, case):
    received = []
    adapter = solved(sample, lambda **payload: received.append(payload) or {'success': True})
    if case == 'topology':
        sample['faces'] = tuple(reversed(FACES))
        sample['pose_faces'] = [sample['faces']] * 2
    elif case == 'vertex_order':
        sample['vertex_ids'] = [5, 1, 9, 20]
        sample['pose_vertex_ids'] = [sample['vertex_ids']] * 2
    elif case == 'bone_order':
        sample['bone_names'] = ['different']
    else:
        sample['identity'] = ('/Game/Mesh', 0, 'revision2')
    assert not adapter.to_dcc_data()['success']
    assert not received


@pytest.mark.parametrize('case', ['pose_topology', 'pose_ids', 'missing_ids', 'invalid_lod', 'world_space'])
def test_invalid_sample_clears_previous_result(sample, case):
    adapter = solved(sample)
    kwargs = {}
    if case == 'pose_topology':
        sample['pose_faces'][1] = tuple(reversed(FACES))
    elif case == 'pose_ids':
        sample['pose_vertex_ids'][1] = [5, 1, 9, 20]
    elif case == 'missing_ids':
        del sample['vertex_ids']
    elif case == 'invalid_lod':
        kwargs['lod_index'] = -1
    else:
        kwargs['use_world_space'] = True
    assert not adapter.from_dcc_data('/Game/Mesh', '/Game/Skeleton', **kwargs)
    assert adapter.last_error
    assert not adapter.to_dcc_data(apply_weights=False)['success']


@pytest.mark.parametrize('response', [None, True, {}, {'success': False, 'error': 'commit failed'}])
def test_writer_failure_is_not_reported_as_success(sample, response):
    adapter = solved(sample, lambda **payload: response)
    result = adapter.to_dcc_data()
    assert not result['success']
    assert 'writer failed' in result['error']


def test_export_cannot_silently_switch_lod_or_replace_assets(sample):
    adapter = solved(sample, lambda **payload: pytest.fail('Writer must not run'))
    assert not adapter.to_dcc_data(lod_index=1)['success']
    assert not adapter.to_dcc_data(create_new_asset=True, new_asset_path='/Game/Existing')['success']


def test_two_bone_native_bridge_reconstructs_both_poses(sample):
    rest = np.vstack([REST, REST + [3, 0, 0]])
    pose = rest.copy()
    pose[:4] += [1, 0, 0]
    pose[4:] += [0, 2, 0]
    faces = FACES + tuple(tuple(index + 4 for index in face) for face in FACES)
    sample.update(rest_vertices=rest, poses=[rest, pose], faces=faces,
                  pose_faces=[faces, faces], bone_names=['joint', 'other'],
                  vertex_ids=list(range(8)), pose_vertex_ids=[list(range(8))] * 2)
    adapter = solved(sample)
    result = adapter.to_dcc_data(apply_weights=False)
    assert result['success'], result
    assert result['weights'].shape == (2, 8)
    assert result['transformations'].shape == (2, 2, 4, 4)
    homogeneous = np.column_stack([rest, np.ones(8)])
    rebuilt = np.einsum('bv,fbij,vj->fvi', result['weights'], result['transformations'], homogeneous)[..., :3]
    np.testing.assert_allclose(rebuilt, [rest, pose], atol=1e-6)


def test_mutable_identity_token_is_snapshotted(sample):
    sample['identity'] = {'path': '/Game/Mesh', 'revision': 1}
    adapter = UnrealDCCInterface(sampler=lambda **request: sample,
                                writer=lambda **payload: pytest.fail('Writer must not run'))
    assert adapter.from_dcc_data('/Game/Mesh', '/Game/Skeleton')
    adapter.compute()
    sample['identity']['revision'] = 2
    assert not adapter.to_dcc_data()['success']
