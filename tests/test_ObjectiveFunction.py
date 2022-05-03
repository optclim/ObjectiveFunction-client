import pytest
import numpy

from ObjectiveFunction_client import LookupState
from ObjectiveFunction_client import ParameterFloat, ParameterInt
from ObjectiveFunction_client import NoNewRun
from ObjectiveFunction_client.objective_function import ObjectiveFunction


@pytest.fixture
def rundir(tmpdir_factory):
    res = tmpdir_factory.mktemp("objective_function")
    return res


@pytest.fixture
def objfun():
    return ObjectiveFunction


def test_create_fail_create_study(
        objfun, requests_mock, rundir, baseurl, paramsA):
    requests_mock.register_uri(
        'GET', baseurl + 'token', json={'token': 'some_token'})
    requests_mock.register_uri(
        'GET', baseurl + f'studies/study/parameters',
        status_code=404)
    requests_mock.register_uri(
        'POST', baseurl + 'create_study', status_code=400)
    with pytest.raises(RuntimeError):
        objfun('test', 'test_secret', "study", rundir, paramsA,
               url_base=baseurl)


def test_create_fail_study(
        objfun, requests_mock, rundir, baseurl, paramsA):
    requests_mock.register_uri(
        'GET', baseurl + 'token', json={'token': 'some_token'})
    requests_mock.register_uri(
        'GET', baseurl + f'studies/study/parameters',
        status_code=400)
    with pytest.raises(RuntimeError):
        objfun('test', 'test_secret', "study", rundir, paramsA,
               url_base=baseurl)


class TestObjectiveFunctionExisting:
    study = "study"
    scenario = None

    @pytest.fixture
    def params(self, paramsA):
        params = {}
        for p in paramsA:
            params[p] = paramsA[p].to_dict
        return params

    @pytest.fixture
    def requests(self, requests_mock, baseurl, params):
        requests_mock.register_uri(
            'GET', baseurl + 'token', json={'token': 'some_token'})
        requests_mock.register_uri(
            'GET', baseurl + f'studies/{self.study}/parameters',
            status_code=200, json=params)
        requests_mock.register_uri(
            'POST', baseurl + 'create_study', status_code=201)
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/create_scenario',
            status_code=201)

    def test_no_params(self, objfun, requests, baseurl):
        with pytest.raises(RuntimeError):
            objfun('test', 'test_secret', self.study, rundir, {},
                   scenario=self.scenario, url_base=baseurl)

    def test_existing_success(self, objfun, requests, baseurl, paramsA):
        p = objfun('test', 'test_secret',
                   self.study, rundir, paramsA, scenario=self.scenario,
                   url_base=baseurl)
        assert p.study == self.study
        assert p._scenario == self.scenario

    def test_existing_fail_config(self, objfun, requests, baseurl, paramsB):
        # wrong number of parameters in config
        with pytest.raises(RuntimeError):
            objfun('test', 'test_secret', self.study, rundir, paramsB,
                   scenario=self.scenario, url_base=baseurl)

    def test_existing_fail_config2(self, objfun, requests, baseurl, paramsB):
        # wrong parameter name in config
        paramsB['d'] = ParameterFloat(15, 10, 20)
        with pytest.raises(RuntimeError):
            objfun('test', 'test_secret', self.study, rundir, paramsB,
                   scenario=self.scenario, url_base=baseurl)

    def test_existing_fail_wrong_type(
            self, objfun, requests, baseurl, paramsB):
        # wrong parameter type in config
        paramsB['c'] = ParameterInt(15, 10, 20)
        with pytest.raises(RuntimeError):
            objfun('test', 'test_secret', self.study, rundir, paramsB,
                   scenario=self.scenario, url_base=baseurl)

    def test_existing_fail_db(self, objfun, requests, baseurl, paramsA):
        paramsA['d'] = ParameterFloat(15, 10, 20)
        # wrong number of parameters in db
        with pytest.raises(RuntimeError):
            objfun('test', 'test_secret', self.study, rundir, paramsA,
                   scenario=self.scenario, url_base=baseurl)

    @pytest.mark.parametrize("minv,maxv,resolution",
                             [
                                 (-6, 0, 1e-6),
                                 (-5, 1, 1e-6),
                                 (-5, 0, 1e-7)])
    def test_existing_fail_wrong_values(
            self, objfun, requests, baseurl, paramsB, minv, maxv, resolution):
        paramsB['c'] = ParameterFloat(minv, minv, maxv, resolution=resolution)
        with pytest.raises(RuntimeError):
            objfun('test', 'test_secret', self.study, rundir, paramsB,
                   scenario=self.scenario, url_base=baseurl)


class TestObjectiveFunctionBase:
    study = "study"
    scenario = None

    @pytest.fixture
    def requests(self, requests_mock, baseurl):
        requests_mock.register_uri(
            'GET', baseurl + 'token', json={'token': 'some_token'})
        requests_mock.register_uri(
            'GET', baseurl + f'studies/{self.study}/parameters',
            status_code=404)
        requests_mock.register_uri(
            'POST', baseurl + 'create_study', status_code=201)
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/create_scenario',
            status_code=201)

    @pytest.fixture
    def objectiveA(self, objfun, requests, rundir, baseurl, paramsA):
        return objfun('test', 'test_secret',
                      self.study, rundir, paramsA, scenario=self.scenario,
                      url_base=baseurl)

    def test_study_name(self, objectiveA):
        assert objectiveA.study == self.study

    def test_scenario_name(self, objectiveA):
        assert objectiveA._scenario == self.scenario

    def test_basedir(self, objectiveA, rundir):
        assert objectiveA.basedir == rundir

    def test_num_params(self, objectiveA):
        assert objectiveA.num_params == 3

    def test_num_active_params(self, objectiveA):
        assert objectiveA.num_active_params == 3

    def test_lower_bounds(self, objectiveA):
        assert numpy.all(
            objectiveA.lower_bounds == numpy.array((-1, 0, -5)))

    def test_upper_bounds(self, objectiveA):
        assert numpy.all(
            objectiveA.upper_bounds == numpy.array((1, 2, 0)))

    def test_values2params_fail(self, objectiveA):
        with pytest.raises(RuntimeError):
            objectiveA.values2params((0, 1))
        with pytest.raises(RuntimeError):
            objectiveA.values2params((0, 1, 3, 4))

    def test_values2params(self, objectiveA):
        assert objectiveA.values2params((0, 1, 2)) == {
            'a': 0, 'b': 1, 'c': 2}

    def test_params2values(self, objectiveA):
        assert numpy.all(
            objectiveA.params2values({'a': 0, 'b': 1, 'c': 2}) == (0, 1, 2))

    def test_parameters(self, objectiveA):
        assert list(objectiveA.parameters.keys()) == ['a', 'b', 'c']

    def test_active_parameters(self, objectiveA):
        assert list(objectiveA.active_parameters.keys()) == ['a', 'b', 'c']

    def test_constant_parameters(self, objectiveA):
        assert len(objectiveA.constant_parameters.keys()) == 0


class TestObjectiveFunctionConstParam(TestObjectiveFunctionBase):
    @pytest.fixture
    def objectiveA(self, objfun, requests, rundir, baseurl, paramsC):
        return objfun('test', 'test_secret',
                      self.study, rundir, paramsC, scenario=self.scenario,
                      url_base=baseurl)

    def test_num_active_params(self, objectiveA):
        assert objectiveA.num_active_params == 2

    def test_lower_bounds(self, objectiveA):
        assert numpy.all(
            objectiveA.lower_bounds == numpy.array((-1, -5)))

    def test_upper_bounds(self, objectiveA):
        assert numpy.all(
            objectiveA.upper_bounds == numpy.array((1, 0)))

    def test_values2params_fail(self, objectiveA):
        with pytest.raises(RuntimeError):
            objectiveA.values2params((0, ))
        with pytest.raises(RuntimeError):
            objectiveA.values2params((0, 1, 3, 4))

    def test_values2params_const(self, objectiveA):
        assert objectiveA.values2params((0, 2)) == {
            'a': 0, 'b': 1, 'c': 2}

    def test_active_parameters(self, objectiveA):
        assert list(objectiveA.active_parameters.keys()) == ['a', 'c']

    def test_constant_parameters(self, objectiveA):
        assert list(objectiveA.constant_parameters.keys()) == ['b']


class TestObjectiveFunctionNew(TestObjectiveFunctionBase):
    def test_setDefaultScenario(self, objectiveA):
        name = 'default_scenario'
        objectiveA.setDefaultScenario(name)
        assert objectiveA._scenario == name

    def test_setDefaultScenario_existing(
            self, requests_mock, baseurl, objectiveA):
        name = 'scenario'
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/create_scenario',
            status_code=409)
        objectiveA.setDefaultScenario(name)
        assert objectiveA._scenario == name

    def test_setDefaultScenario_fail(
            self, requests_mock, baseurl, objectiveA):
        name = 'scenario'
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/create_scenario',
            status_code=400)
        with pytest.raises(RuntimeError):
            objectiveA.setDefaultScenario(name)


class TestObjectiveFunctionScenario(TestObjectiveFunctionBase):
    scenario = "scenario"

    @pytest.fixture
    def requests(self, objfun, requests_mock, baseurl, rundir, paramsA):
        requests_mock.register_uri(
            'GET', baseurl + 'token', json={'token': 'some_token'})
        requests_mock.register_uri(
            'GET', baseurl + f'studies/{self.study}/parameters',
            status_code=404)
        requests_mock.register_uri(
            'POST', baseurl + 'create_study', status_code=201)
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/create_scenario',
            status_code=201)
        requests_mock.register_uri(
            'GET', baseurl + f'studies/{self.study}/scenarios/{self.scenario}'
            '/runs/1/state', status_code=404)
        requests_mock.register_uri(
            'PUT', baseurl + f'studies/{self.study}/scenarios/{self.scenario}'
            '/runs/1/state', status_code=404)
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/scenarios/{self.scenario}'
            '/runs/with_state', status_code=404)

    def test_getState_none(self, objectiveA):
        with pytest.raises(LookupError):
            objectiveA.getState(1)

    def test_setState_none(self, objectiveA):
        with pytest.raises(LookupError):
            objectiveA.setState(1, LookupState.ACTIVE)

    def test_get_with_state_none(self, objectiveA):
        with pytest.raises(LookupError):
            objectiveA.get_with_state(LookupState.NEW)

    def test_get_new_none(self, objectiveA):
        with pytest.raises(NoNewRun):
            objectiveA.get_new()
