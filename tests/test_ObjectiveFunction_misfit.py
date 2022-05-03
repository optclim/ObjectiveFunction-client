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
    return {'resname': 'misfit',
            'dbname': 'misfit',
            'dbvalue': 10,
            'resvalue': 10}


class TestObjectiveFunctionScenarioMisfit(TOFS):
    def _compare(self, a, b):
        assert a == b

    def _not_equal(self, a, b):
        assert a != b

    def test_get_result_completed(
            self, requests_mock, baseurl, objectiveA, valuesA, result):
        resname = result['resname']
        resval = result['resvalue']
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/scenarios/'
            f'{self.scenario}/lookup_run',
            status_code=201, json={
                'state': LookupState.COMPLETED.name,
                result['dbname']: result['dbvalue']})
        res = objectiveA.get_result(valuesA)
        assert res['state'] == LookupState.COMPLETED
        self._compare(res[resname], resval)

    def test_get_result(
            self, requests_mock, baseurl, objectiveA, valuesA, result):
        resname = result['resname']
        resval = result['resvalue']
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/scenarios/'
            f'{self.scenario}/lookup_run',
            status_code=201, json={
                'state': LookupState.ACTIVE.name,
                result['dbname']: result['dbvalue']})
        res = objectiveA.get_result(valuesA)
        assert res['state'] == LookupState.ACTIVE
        self._not_equal(res[resname], resval)

    def test_call(self, requests_mock, baseurl, objectiveA, result):
        resval = result['resvalue']
        requests_mock.register_uri(
            'POST', baseurl + f'studies/{self.study}/scenarios/'
            f'{self.scenario}/lookup_run',
            status_code=201, json={
                'state': LookupState.COMPLETED.name,
                result['dbname']: result['dbvalue']})
        self._compare(objectiveA((0, 1, -2)), resval)

    def test_set_data(self, objectiveA, result):
        assert objectiveA._set_data(
            {'id': 1}, result['resvalue']) == {
                result['dbname']: result['dbvalue']}

    @pytest.mark.parametrize("code", [400, 403])
    def test_set_result_fail(
            self, requests_mock, baseurl, objectiveA, valuesA, result, code):
        resval = result['resvalue']
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
            objectiveA.set_result(valuesA, resval)

    def test_set_result(
            self, requests_mock, baseurl, objectiveA, valuesA, result):
        resval = result['resvalue']
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

        objectiveA.set_result(valuesA, resval)

    @pytest.mark.parametrize("state",
                             [LookupState.PROVISIONAL, LookupState.NEW,
                              LookupState.ACTIVE, LookupState.COMPLETED])
    def test_set_result_forced(
            self, requests_mock, baseurl, objectiveA, valuesA, result, state):
        resval = result['resvalue']
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

        objectiveA.set_result(valuesA, resval, force=True)
