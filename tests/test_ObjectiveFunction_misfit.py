import pytest

from ObjectiveFunction_client import ObjectiveFunctionMisfit
from ObjectiveFunction_client import LookupState

from test_ObjectiveFunction import (  # noqa: F401
    test_create_fail_create_study, test_create_fail_study,
    TestObjectiveFunctionExisting, TestObjectiveFunctionBase,
    TestObjectiveFunctionConstParam, TestObjectiveFunctionNew)
from test_ObjectiveFunction import TestObjectiveFunctionScenario as TOFS


@pytest.fixture
def rundir(tmpdir_factory):
    res = tmpdir_factory.mktemp("objective_function")
    return res


@pytest.fixture
def objfun():
    return ObjectiveFunctionMisfit


@pytest.fixture
def result():
    return ('misfit', 10)


class TestObjectiveFunctionScenarioMisfit(TOFS):
    def test_get_result_completed(
            self, requests_mock, baseurl, objectiveA, valuesA, result):
        resname, misfit = result
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/scenarios/'
            f'{self.scenario}/lookup_run',
            status_code=201, json={
                'state': LookupState.COMPLETED.name,
                resname: misfit})
        res = objectiveA.get_result(valuesA)
        assert res['state'] == LookupState.COMPLETED
        assert res[resname] == misfit

    def test_get_result(
            self, requests_mock, baseurl, objectiveA, valuesA, result):
        resname, misfit = result
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/scenarios/'
            f'{self.scenario}/lookup_run',
            status_code=201, json={
                'state': LookupState.ACTIVE.name,
                resname: misfit})
        res = objectiveA.get_result(valuesA)
        assert res['state'] == LookupState.ACTIVE
        assert res[resname] != misfit

    def test_call(self, requests_mock, baseurl, objectiveA, result):
        resname, misfit = result
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/scenarios/'
            f'{self.scenario}/lookup_run',
            status_code=201, json={
                'state': LookupState.COMPLETED.name,
                resname: misfit})
        assert objectiveA((0, 1, -2)) == misfit

    def test_set_data(self, objectiveA, result):
        resname, misfit = result
        assert objectiveA._set_data('x', misfit) == {resname: misfit}

    @pytest.mark.parametrize("code", [400, 403])
    def test_set_result_fail(
            self, requests_mock, baseurl, objectiveA, valuesA, result, code):
        resname, misfit = result
        runid = 1
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/scenarios/'
            f'{self.scenario}/get_run',
            status_code=201, json={
                'state': LookupState.ACTIVE.name,
                'id': runid})
        requests_mock.register_uri(
            'PUT', baseurl + f'studies/{self.study}/scenarios/'
            f'{self.scenario}/runs/{runid}/value', status_code=code)
        with pytest.raises(RuntimeError):
            objectiveA.set_result(valuesA, misfit)

    def test_set_result(
            self, requests_mock, baseurl, objectiveA, valuesA, result):
        resname, misfit = result
        runid = 1
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/scenarios/'
            f'{self.scenario}/get_run',
            status_code=201, json={
                'state': LookupState.ACTIVE.name,
                'id': runid})
        requests_mock.register_uri(
            'PUT', baseurl + f'studies/{self.study}/scenarios/'
            f'{self.scenario}/runs/{runid}/value', status_code=201)

        objectiveA.set_result(valuesA, misfit)

    @pytest.mark.parametrize("state",
                             [LookupState.PROVISIONAL, LookupState.NEW,
                              LookupState.ACTIVE, LookupState.COMPLETED])
    def test_set_result_forced(
            self, requests_mock, baseurl, objectiveA, valuesA, result, state):
        resname, misfit = result
        runid = 1
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/scenarios/'
            f'{self.scenario}/get_run',
            status_code=201, json={
                'state': state.name,
                'id': runid})
        requests_mock.register_uri(
            'PUT', baseurl + f'studies/{self.study}/scenarios/'
            f'{self.scenario}/runs/{runid}/value', status_code=201)

        objectiveA.set_result(valuesA, misfit, force=True)
