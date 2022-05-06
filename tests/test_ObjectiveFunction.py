import pytest
import numpy

from ObjectiveFunction_client import LookupState
from ObjectiveFunction_client import ParameterFloat, ParameterInt
from ObjectiveFunction_client import Waiting, PreliminaryRun, NewRun, NoNewRun
from ObjectiveFunction_client.objective_function import ObjectiveFunction


@pytest.fixture
def rundir(tmpdir_factory):
    res = tmpdir_factory.mktemp("objective_function")
    return res


@pytest.fixture
def objfun(request_token):
    return ObjectiveFunction


def test_create_fail_create_study(
        objfun, requests_mock, rundir, baseurl, paramsA):
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
        'GET', baseurl + f'studies/study/parameters',
        status_code=400)
    with pytest.raises(RuntimeError):
        objfun('test', 'test_secret', "study", rundir, paramsA,
               url_base=baseurl)


class TestObjectiveFunctionExisting:
    scenario = None

    def test_no_params(self, objfun, requests_objfun_existing, baseurl, study):
        with pytest.raises(RuntimeError):
            objfun('test', 'test_secret', study, rundir, {},
                   scenario=self.scenario, url_base=baseurl)

    def test_existing_success(
            self, objfun, requests_objfun_existing, baseurl, study, paramsA):
        p = objfun('test', 'test_secret',
                   study, rundir, paramsA, scenario=self.scenario,
                   url_base=baseurl)
        assert p.study == study
        assert p._scenario == self.scenario

    def test_existing_fail_config(
            self, objfun, requests_objfun_existing, baseurl, study, paramsB):
        # wrong number of parameters in config
        with pytest.raises(RuntimeError):
            objfun('test', 'test_secret', study, rundir, paramsB,
                   scenario=self.scenario, url_base=baseurl)

    def test_existing_fail_config2(
            self, objfun, requests_objfun_existing, baseurl, study, paramsB):
        # wrong parameter name in config
        paramsB['d'] = ParameterFloat(15, 10, 20)
        with pytest.raises(RuntimeError):
            objfun('test', 'test_secret', study, rundir, paramsB,
                   scenario=self.scenario, url_base=baseurl)

    def test_existing_fail_wrong_type(
            self, objfun, requests_objfun_existing, baseurl, study, paramsB):
        # wrong parameter type in config
        paramsB['c'] = ParameterInt(15, 10, 20)
        with pytest.raises(RuntimeError):
            objfun('test', 'test_secret', study, rundir, paramsB,
                   scenario=self.scenario, url_base=baseurl)

    def test_existing_fail_db(
            self, objfun, requests_objfun_existing, baseurl, study, paramsA):
        paramsA['d'] = ParameterFloat(15, 10, 20)
        # wrong number of parameters in db
        with pytest.raises(RuntimeError):
            objfun('test', 'test_secret', study, rundir, paramsA,
                   scenario=self.scenario, url_base=baseurl)

    @pytest.mark.parametrize("minv,maxv,resolution",
                             [
                                 (-6, 0, 1e-6),
                                 (-5, 1, 1e-6),
                                 (-5, 0, 1e-7)])
    def test_existing_fail_wrong_values(
            self, objfun, requests_objfun_existing, baseurl, study,
            paramsB, minv, maxv, resolution):
        paramsB['c'] = ParameterFloat(minv, minv, maxv, resolution=resolution)
        with pytest.raises(RuntimeError):
            objfun('test', 'test_secret', study, rundir, paramsB,
                   scenario=self.scenario, url_base=baseurl)


class TestObjectiveFunctionBase:
    study = "study"
    scenario = None

    @pytest.fixture
    def objectiveA(
            self, objfun, requests_objfun_new, rundir, baseurl, paramsA):
        return objfun('test', 'test_secret',
                      self.study, rundir, paramsA, scenario=self.scenario,
                      url_base=baseurl)

    @pytest.fixture
    def vA(self):
        return {'a': 0., 'b': 0., 'c': -2}

    @pytest.fixture
    def ivA(self):
        return {'a': 1000000, 'b': 0, 'c': 3000000}

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

    def test_transform_parameters(self, objectiveA, vA, ivA):
        assert objectiveA._transform_parameters(vA) == ivA

    def test_inv_transform_parameters(self, objectiveA, vA, ivA):
        assert objectiveA._inv_transform_parameters(ivA) == vA


class TestObjectiveFunctionConstParam(TestObjectiveFunctionBase):
    @pytest.fixture
    def objectiveA(
            self, objfun, requests_objfun_new, rundir, baseurl, paramsC):
        return objfun('test', 'test_secret',
                      self.study, rundir, paramsC, scenario=self.scenario,
                      url_base=baseurl)

    @pytest.fixture
    def ivA(self):
        return {'a': 1000000, 'b': 10000000, 'c': 3000000}

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

    def test_params2values_excl(self, objectiveA):
        assert numpy.all(
            objectiveA.params2values(
                {'a': 0, 'b': 1, 'c': 2}, include_constant=False) == (0, 2))

    def test_active_parameters(self, objectiveA):
        assert list(objectiveA.active_parameters.keys()) == ['a', 'c']

    def test_constant_parameters(self, objectiveA):
        assert list(objectiveA.constant_parameters.keys()) == ['b']

    def test_inv_transform_parameters(self, objectiveA, vA, ivA):
        vA['b'] = objectiveA.parameters['b'].value
        assert objectiveA._inv_transform_parameters(ivA) == vA


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

    def test_get_run_by_id(self, requests_mock, baseurl, objectiveA):
        rid = 1
        requests_mock.register_uri(
            'GET',
            baseurl + f'studies/{self.study}/scenarios/{self.scenario}/'
            f'runs/{rid}',
            status_code=200, json=[1])
        objectiveA.get_run_by_id(rid)

    def test_get_run_by_id_fail(self, requests_mock, baseurl, objectiveA):
        rid = 1
        requests_mock.register_uri(
            'GET',
            baseurl + f'studies/{self.study}/scenarios/{self.scenario}/'
            f'runs/{rid}',
            status_code=400)
        with pytest.raises(RuntimeError):
            objectiveA.get_run_by_id(rid)

    def test_getState_none(self, requests_mock, baseurl, objectiveA):
        rid = 1
        requests_mock.register_uri(
            'GET', baseurl + f'studies/{self.study}/scenarios/{self.scenario}'
            f'/runs/{rid}/state', status_code=404)
        with pytest.raises(LookupError):
            objectiveA.getState(rid)

    def test_getState_fail(self, requests_mock, baseurl, objectiveA):
        rid = 1
        requests_mock.register_uri(
            'GET', baseurl + f'studies/{self.study}/scenarios/{self.scenario}'
            f'/runs/{rid}/state', status_code=400)
        with pytest.raises(RuntimeError):
            objectiveA.getState(rid)

    def test_getState(self, requests_mock, baseurl, objectiveA):
        rid = 1
        state = LookupState.NEW
        requests_mock.register_uri(
            'GET', baseurl + f'studies/{self.study}/scenarios/{self.scenario}'
            f'/runs/{rid}/state', status_code=200,
            json={'state': state.name})
        assert objectiveA.getState(rid) == state

    def test_setState_none(self, requests_mock, baseurl, objectiveA):
        requests_mock.register_uri(
            'PUT', baseurl + f'studies/{self.study}/scenarios/{self.scenario}'
            '/runs/1/state', status_code=404)
        with pytest.raises(LookupError):
            objectiveA.setState(1, LookupState.ACTIVE)

    def test_setState_fail(self, requests_mock, baseurl, objectiveA):
        requests_mock.register_uri(
            'PUT', baseurl + f'studies/{self.study}/scenarios/{self.scenario}'
            '/runs/1/state', status_code=400)
        with pytest.raises(RuntimeError):
            objectiveA.setState(1, LookupState.ACTIVE)

    def test_setState(self, requests_mock, baseurl, objectiveA):
        requests_mock.register_uri(
            'PUT', baseurl + f'studies/{self.study}/scenarios/{self.scenario}'
            '/runs/1/state', status_code=201)
        objectiveA.setState(1, LookupState.ACTIVE)

    def test_get_with_state_none(self, requests_mock, baseurl, objectiveA):
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/scenarios/{self.scenario}'
            '/runs/with_state', status_code=404)
        with pytest.raises(LookupError):
            objectiveA.get_with_state(LookupState.NEW)

    def test_get_with_state_fail(self, requests_mock, baseurl, objectiveA):
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/scenarios/{self.scenario}'
            '/runs/with_state', status_code=400)
        with pytest.raises(RuntimeError):
            objectiveA.get_with_state(LookupState.NEW)

    def test_get_with_state(self, requests_mock, baseurl, objectiveA, vA, ivA):
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/scenarios/{self.scenario}'
            '/runs/with_state', status_code=201,
            json={'values': ivA})
        res = objectiveA.get_with_state(LookupState.NEW)
        assert res == vA

    def test_get_with_state_with_id(
            self, requests_mock, baseurl, objectiveA, vA, ivA):
        rid = 1
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/scenarios/{self.scenario}'
            '/runs/with_state', status_code=201,
            json={'values': ivA, 'id': rid})
        res = objectiveA.get_with_state(LookupState.NEW, with_id=True)
        assert res == (rid, vA)

    def test_get_new_none(self, requests_mock, baseurl, objectiveA):
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/scenarios/{self.scenario}'
            '/runs/with_state', status_code=404)
        with pytest.raises(NoNewRun):
            objectiveA.get_new()

    def test_get_new(self, requests_mock, baseurl, objectiveA, vA, ivA):
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/scenarios/{self.scenario}'
            '/runs/with_state', status_code=201, json={'values': ivA})
        res = objectiveA.get_new()
        assert res == vA

    def test_get_run_fail(self, requests_mock, baseurl, objectiveA, valuesA):
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/scenarios/'
            f'{self.scenario}/get_run',
            status_code=400)
        with pytest.raises(RuntimeError):
            objectiveA.get_run(valuesA)

    def test_get_run(self, requests_mock, baseurl, objectiveA, valuesA):
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/scenarios/'
            f'{self.scenario}/get_run',
            status_code=201, json={'state': LookupState.ACTIVE.name})
        res = objectiveA.get_run(valuesA)
        assert res['state'] == LookupState.ACTIVE

    def test_lookup_run_fail(
            self, requests_mock, baseurl, objectiveA, valuesA):
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/scenarios/'
            f'{self.scenario}/lookup_run',
            status_code=400)
        with pytest.raises(RuntimeError):
            objectiveA.lookup_run(valuesA)

    def test_lookup_run(
            self, requests_mock, baseurl, objectiveA, valuesA):
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/scenarios/'
            f'{self.scenario}/lookup_run',
            status_code=201, json={'h': 1})
        objectiveA.lookup_run(valuesA)

    @pytest.mark.parametrize("res,excptn",
                             [
                                 ({'status': 'waiting'}, Waiting),
                                 ({'status': 'provisional'}, PreliminaryRun),
                                 ({'status': 'new'}, NewRun),
                                 ({'status': 'wrong'}, RuntimeError)])
    def test_get_result_event(
            self, requests_mock, baseurl, objectiveA, valuesA, res, excptn):
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/scenarios/'
            f'{self.scenario}/lookup_run',
            status_code=201, json=res)
        with pytest.raises(excptn):
            objectiveA.get_result(valuesA)

    def test_get_result(self, requests_mock, baseurl, objectiveA, valuesA):
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/scenarios/'
            f'{self.scenario}/lookup_run',
            status_code=201, json={'state': LookupState.ACTIVE.name})
        res = objectiveA.get_result(valuesA)
        assert res['state'] == LookupState.ACTIVE

    @pytest.mark.parametrize("state",
                             [LookupState.PROVISIONAL, LookupState.NEW,
                              LookupState.COMPLETED])
    def test_set_result_wrong_state(
            self, requests_mock, baseurl, objectiveA, valuesA, state):
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/scenarios/'
            f'{self.scenario}/get_run',
            status_code=201, json={'state': state.name,
                                   'id': 1,
                                   'value': 10})
        with pytest.raises(RuntimeError):
            objectiveA.set_result(valuesA, 'blub')

    def test_call_with_grad(self, objectiveA):
        with pytest.raises(RuntimeError):
            objectiveA([1, 2], numpy.zeros(2))

    def test_call(self, requests_mock, baseurl, objectiveA):
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/scenarios/'
            f'{self.scenario}/lookup_run',
            status_code=201, json={'state': LookupState.ACTIVE.name})
        res = objectiveA((0, 1, -2))
        assert res['state'] == LookupState.ACTIVE
