import pytest
import numpy

from ObjectiveFunction_client import ObjectiveFunctionResidual

from test_ObjectiveFunction import (  # noqa: F401
    test_create_fail_create_study, test_create_fail_study,
    TestObjectiveFunctionExisting, TestObjectiveFunctionBase,
    TestObjectiveFunctionConstParam, TestObjectiveFunctionNew)
from test_ObjectiveFunction_misfit import \
    TestObjectiveFunctionScenarioMisfit as TOFSM


@pytest.fixture
def rundir(tmpdir_factory):
    res = tmpdir_factory.mktemp("objective_function_residual")
    return res


@pytest.fixture
def objfun():
    return ObjectiveFunctionResidual


@pytest.fixture
def result(rundir):
    scenario = rundir / 'scenario'
    scenario.mkdir()
    fname = scenario / 'residuals_1.npy'
    with open(fname, 'wb') as f:
        numpy.save(f, numpy.arange(10))
    return {'resname': 'residual',
            'dbname': 'value',
            'dbvalue': str(fname),
            'resvalue': numpy.arange(10)}


class TestObjectiveFunctionScenarioResidual(TOFSM):
    def _compare(self, a, b):
        assert numpy.all(a == b)

    def _not_equal(self, a, b):
        assert (a.size != b.size) or numpy.all(a != b)

    def test_set_result(
            self, requests_mock, baseurl, objectiveA, valuesA, result):
        super().test_set_result(
            requests_mock, baseurl, objectiveA, valuesA, result)
        assert objectiveA.num_residuals == 10
