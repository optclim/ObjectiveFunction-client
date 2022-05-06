import pytest

from ObjectiveFunction_client.cache import ObjFunCache
from ObjectiveFunction_client import LookupState


@pytest.fixture
def rundir(tmpdir_factory):
    res = tmpdir_factory.mktemp("of-cache")
    return res


@pytest.fixture
def params():
    return ['b', 'a']


def test_wrong_result_type(params):
    with pytest.raises(ValueError):
        ObjFunCache(":memory:", params, 'wrong')


def test_no_params():
    with pytest.raises(ValueError):
        ObjFunCache(":memory:", [], 'real')


@pytest.mark.parametrize("result_type",
                         ["real", "text"])
def test_create_cache(params, result_type):
    cache = ObjFunCache(":memory:", params, result_type)
    assert cache.parameters == tuple(sorted(params))
    assert len(cache) == 0


@pytest.fixture
def cache(rundir, params):
    return ObjFunCache(rundir / 'cache.sqlite', params, 'real')


def test_wrong_number_of_params(rundir, cache):
    with pytest.raises(RuntimeError):
        ObjFunCache(rundir / 'cache.sqlite', ['a', 'b', 'c'], 'real')


def test_wrong_param_name(rundir, cache):
    with pytest.raises(RuntimeError):
        ObjFunCache(rundir / 'cache.sqlite', ['a', 'wrong'], 'real')


def test_wrong_key(cache):
    with pytest.raises(KeyError):
        cache._check_key({'a': 1})


def test_lookup_failure(cache):
    with pytest.raises(LookupError):
        cache[{'a': 1, 'b': 2}]


@pytest.fixture
def entry(params):
    value = {}
    for v, p in enumerate(params):
        value[p] = v
    result = {'id': 1, 'value': 10.}
    return (value, result)


@pytest.fixture
def cache_with_entry(cache, entry):
    value, result = entry
    cache[value] = result
    return cache


def test_len(cache_with_entry):
    assert len(cache_with_entry) == 1


def test_lookup(cache_with_entry, entry):
    value, result = entry
    lookup = cache_with_entry[value]
    for p in result:
        assert lookup[p] == result[p]
    assert lookup['state'] == LookupState.COMPLETED


def test_lookup_fail_same_id(cache_with_entry, entry):
    value, result = entry
    value['a'] = 10
    with pytest.raises(RuntimeError):
        cache_with_entry[value] = result


def test_lookup_fail_same_value(cache_with_entry, entry):
    value, result = entry
    result['id'] = 10
    with pytest.raises(RuntimeError):
        cache_with_entry[value] = result
