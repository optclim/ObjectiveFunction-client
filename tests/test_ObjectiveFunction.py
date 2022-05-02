import pytest
import numpy

from ObjectiveFunction_client import LookupState
from ObjectiveFunction_client import NoNewRun
from ObjectiveFunction_client.objective_function import ObjectiveFunction


@pytest.fixture
def rundir(tmpdir_factory):
    res = tmpdir_factory.mktemp("objective_function")
    return res


@pytest.fixture
def objfunA(requests_mock, baseurl, paramsA):
    study = 'test_study'
    scenario = 'test_scenario'
    requests_mock.register_uri(
        'GET', baseurl + 'token', json={'token': 'some_token'})
    requests_mock.register_uri(
        'GET', baseurl + f'studies/{study}/parameters',
        status_code=404)
    requests_mock.register_uri(
        'POST', baseurl + 'create_study', status_code=201)
    requests_mock.register_uri(
        'POST', baseurl + f'studies/{study}/create_scenario',
        status_code=201)

    p = ObjectiveFunction(
        'test', 'test_secret', study, 'basedir', paramsA, scenario=scenario,
        url_base=baseurl)
    return p


class TestObjectiveFunction:
    study = "study"

    @pytest.fixture
    def objfun(self):
        return ObjectiveFunction

    @pytest.fixture
    def objectiveA(self, objfun, requests_mock, baseurl, rundir, paramsA):
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
        return objfun('test', 'test_secret',
                      self.study, rundir, paramsA,
                      url_base=baseurl)

    def test_study_name(self, objectiveA):
        assert objectiveA.study == self.study

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

    def test_setDefaultScenario(self, objectiveA):
        name = 'default_scenario'
        objectiveA.setDefaultScenario(name)
        assert objectiveA._scenario == name
        #assert name in objectiveA.scenarios


class TestObjectiveFunctionScenario(TestObjectiveFunction):
    scenario = "scenario"

    @pytest.fixture
    def objectiveA(self, objfun, requests_mock, baseurl, rundir, paramsA):
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
        return objfun('test', 'test_secret',
                      self.study, rundir, paramsA, scenario=self.scenario,
                      url_base=baseurl)

    def test_scenario_name(self, objectiveA):
        assert objectiveA._scenario == self.scenario
        #assert name in objfunmem_scenario.scenarios

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
