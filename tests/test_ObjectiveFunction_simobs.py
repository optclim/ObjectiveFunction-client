import pytest
import pandas
import numpy
from functools import partial

from ObjectiveFunction_client import ObjectiveFunctionSimObs

from test_ObjectiveFunction import (  # noqa: F401
    test_create_fail_create_study, test_create_fail_study)

from test_ObjectiveFunction import TestObjectiveFunctionExisting as TOFExist
from test_ObjectiveFunction import TestObjectiveFunctionBase as TOFBase
from test_ObjectiveFunction import TestObjectiveFunctionConstParam as TOFConst
from test_ObjectiveFunction import TestObjectiveFunctionNew as TOFNew

from test_ObjectiveFunction_misfit import \
    TestObjectiveFunctionScenarioMisfit as TOFSM


@pytest.fixture
def rundir(tmpdir_factory):
    res = tmpdir_factory.mktemp("objective_function_simobs")
    return res


@pytest.fixture
def obsnames():
    return ['simA', 'simC', 'simB']


@pytest.fixture
def objfun(obsnames, request_token):
    return partial(ObjectiveFunctionSimObs, observationNames=obsnames)


@pytest.fixture
def requests_objfun_simobs_new(
        requests_objfun_new, requests_mock, study, baseurl):
    requests_mock.register_uri(
        'PUT', baseurl + f'studies/{study}/observation_names',
        status_code=201)


@pytest.fixture
def requests_objfun_existing(requests_mock, baseurl, study, obsnames, params):
    requests_mock.register_uri(
        'GET', baseurl + f'studies/{study}/parameters',
        status_code=200, json=params)
    requests_mock.register_uri(
        'POST', baseurl + 'create_study', status_code=201)
    requests_mock.register_uri(
        'POST', baseurl + f'studies/{study}/create_scenario',
        status_code=201)
    requests_mock.register_uri(
        'GET', baseurl + f'studies/{study}/observation_names',
        status_code=200, json={'obsnames': obsnames})


@pytest.fixture
def result(rundir, obsnames):
    scenario = rundir / 'scenario'
    scenario.mkdir()
    fname = scenario / 'simobs_1.json'
    data = pandas.Series(
        numpy.arange(len(obsnames), dtype=float) * 0.5,
        obsnames)
    data.to_json(fname)
    return {'resname': 'simobs',
            'dbname': 'value',
            'dbvalue': str(fname),
            'resvalue': data}


@pytest.mark.parametrize("status_code", [400, 404])
def test_create_fail_create_study_obsnames(
        objfun, requests_mock, requests_objfun_new, rundir, study,
        baseurl, paramsA, status_code):
    requests_mock.register_uri(
        'PUT', baseurl + f'studies/{study}/observation_names',
        status_code=status_code)
    with pytest.raises(RuntimeError):
        objfun('test', 'test_secret', "study", rundir, paramsA,
               url_base=baseurl)


class TestObjectiveFunctionExisting(TOFExist):
    def test_load_study_simobs_fail(
            self, objfun, requests_mock, requests_objfun_existing,
            baseurl, study, paramsA):
        requests_mock.register_uri(
            'GET', baseurl + f'studies/{study}/observation_names',
            status_code=400)
        with pytest.raises(RuntimeError):
            objfun('test', 'test_secret', study, rundir, paramsA,
                   scenario=self.scenario, url_base=baseurl)

    def test_load_study_fail_wrong_num_simobs(
            self, objfun, requests_mock, requests_objfun_existing,
            baseurl, study, paramsA, obsnames):
        requests_mock.register_uri(
            'GET', baseurl + f'studies/{study}/observation_names',
            status_code=200, json={'obsnames': obsnames[:-1]})
        with pytest.raises(RuntimeError):
            objfun('test', 'test_secret', study, rundir, paramsA,
                   scenario=self.scenario, url_base=baseurl)

    def test_load_study_fail_wrong_simobs_names(
            self, objfun, requests_mock, requests_objfun_existing,
            baseurl, study, paramsA, obsnames):
        obs = list(obsnames)
        obs[-1] = 'wrong'
        requests_mock.register_uri(
            'GET', baseurl + f'studies/{study}/observation_names',
            status_code=200, json={'obsnames': obs})
        with pytest.raises(RuntimeError):
            objfun('test', 'test_secret', study, rundir, paramsA,
                   scenario=self.scenario, url_base=baseurl)


class TestObjectiveFunctionBase(TOFBase):
    @pytest.fixture
    def objectiveA(
            self, objfun, requests_objfun_simobs_new, rundir,
            baseurl, paramsA):
        return objfun('test', 'test_secret',
                      self.study, rundir, paramsA, scenario=self.scenario,
                      url_base=baseurl)


class TestObjectiveFunctionConstParam(TOFConst):
    @pytest.fixture
    def objectiveA(
            self, objfun, requests_objfun_simobs_new, rundir,
            baseurl, paramsC):
        return objfun('test', 'test_secret',
                      self.study, rundir, paramsC, scenario=self.scenario,
                      url_base=baseurl)


class TestObjectiveFunctionNew(TOFNew, TestObjectiveFunctionBase):
    pass


class TestObjectiveFunctionScenarioSimObs(
        TOFSM, TestObjectiveFunctionBase):
    def _compare(self, a, b):
        assert numpy.all(a == b)

    def _not_equal(self, a, b):
        assert (a.size != b.size) or numpy.all(a != b)

    def test_set_result(
            self, requests_mock, baseurl, objectiveA, valuesA, result):
        super().test_set_result(
            requests_mock, baseurl, objectiveA, valuesA, result)
        assert objectiveA.num_residuals == 3
