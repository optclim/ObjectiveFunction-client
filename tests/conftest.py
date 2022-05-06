import pytest

from ObjectiveFunction_client import ParameterFloat, ParameterInt


@pytest.fixture
def paramsA():
    return {'a': ParameterFloat(0, -1, 1),
            'b': ParameterFloat(1, 0, 2, 1e-7),
            'c': ParameterFloat(-2.5, -5, 0)}


@pytest.fixture
def paramsB():
    return {'a': ParameterFloat(0, -1, 1),
            'b': ParameterFloat(0, 0, 2, 1e-7)}


@pytest.fixture
def paramsC():
    return {'a': ParameterFloat(0, -1, 1),
            'b': ParameterFloat(1, 0, 2, 1e-7, constant=True),
            'c': ParameterFloat(-2.5, -5, 0)}


@pytest.fixture
def valuesA():
    return {'a': 0., 'b': 1., 'c': -2}


@pytest.fixture
def valuesB():
    return {'a': 0.5, 'b': 1., 'c': -2}


@pytest.fixture
def paramSet():
    return {'af': ParameterFloat(1, 0, 2, 1e-7),
            'bf': ParameterFloat(1.5, 1, 2, 1e-7),
            'cf': ParameterFloat(1.5, 0, 3, 1e-7),
            'df': ParameterFloat(1, 0, 2, 1e-6),
            'ai': ParameterInt(1, 0, 2),
            'bi': ParameterInt(1, 1, 2),
            'ci': ParameterInt(2, 0, 3)}


@pytest.fixture
def baseurl():
    return 'http://testlocation.org/api/'


@pytest.fixture
def request_token(requests_mock, baseurl):
    requests_mock.register_uri(
        'GET', baseurl + 'token', json={'token': 'some_token'})


@pytest.fixture
def study():
    return "study"


@pytest.fixture
def params(paramsA):
    params = {}
    for p in paramsA:
        params[p] = paramsA[p].to_dict
    return params


@pytest.fixture
def requests_objfun_new(requests_mock, baseurl, study):
    requests_mock.register_uri(
        'GET', baseurl + f'studies/{study}/parameters',
        status_code=404)
    requests_mock.register_uri(
        'POST', baseurl + 'create_study', status_code=201)
    requests_mock.register_uri(
        'POST', baseurl + f'studies/{study}/create_scenario',
        status_code=201)


@pytest.fixture
def requests_objfun_existing(requests_mock, baseurl, study, params):
    requests_mock.register_uri(
        'GET', baseurl + f'studies/{study}/parameters',
        status_code=200, json=params)
    requests_mock.register_uri(
        'POST', baseurl + 'create_study', status_code=201)
    requests_mock.register_uri(
        'POST', baseurl + f'studies/{study}/create_scenario',
        status_code=201)
