import pytest
from ObjectiveFunction_client import ParameterFloat


def test_parameter_bad_range():
    """check that misordering of min/max value is caught"""
    with pytest.raises(ValueError):
        ParameterFloat(1.5, 2, 1)


def test_parameter_value_outside_range():
    """check that value outside range is caught"""
    with pytest.raises(ValueError):
        ParameterFloat(5, 1, 3)


def test_parameter_bad_resolution():
    """check what happens when resolution is small"""
    with pytest.raises(ValueError):
        ParameterFloat(0, -1e12, 1e12, resolution=1e-10)


@pytest.fixture
def param():
    return ParameterFloat(0, -10, 20, resolution=1)


def test_param_attribs(param):
    """check that we get expected attributes"""
    assert param.value == 0
    assert param.minv == -10
    assert param.maxv == 20
    assert param.resolution == 1
    assert param.constant is False


def test_param_to_dict(param):
    """check conversion to dictionary"""
    assert param.to_dict == {'type': 'float',
                             'resolution': param.resolution,
                             'minv': param.minv,
                             'maxv': param.maxv}


def test_param_assign_value(param):
    """check value assignment works"""
    v = 5
    param.value = v
    assert param.value == v


def test_param_assing_value_outside_range(param):
    """check value outside range is caught"""
    for v in [-11, 21]:
        with pytest.raises(ValueError):
            param.value = v


def test_transform_wrong_value(param):
    """check that ValueError is raised when wrong value given"""
    with pytest.raises(ValueError):
        param.transform(-15)
    with pytest.raises(ValueError):
        param.transform(21)


def test_inv_transform_wrong_value(param):
    with pytest.raises(ValueError):
        param.inv_transform(-1)
    with pytest.raises(ValueError):
        param.inv_transform(31)


testdata = [
    (-10., 0, -10),
    (-9.6, 0, -10),
    (0, 10, 0),
    (-0.5, 10, 0),
    (19, 29, 19),
    (20, 30, 20)]


@pytest.mark.parametrize("value,transformed,rounded", testdata)
def test_transform1(param, value, transformed, rounded):
    assert param.transform(value) == transformed
    assert abs(param.inv_transform(transformed) - rounded) < 1e-10


@pytest.fixture
def param2():
    return ParameterFloat(0, -1, 2.5, resolution=1e-5)


testdata2 = [
    (-1., 0, -1.),
    (2.5, 350000, 2.5),
    (0.75, 175000, 0.75),
    (1., 200000, 1.)]


@pytest.mark.parametrize("value,transformed,rounded", testdata2)
def test_transform2(param2, value, transformed, rounded):
    assert param2.transform(value) == transformed
    assert abs(param2.inv_transform(transformed) - rounded) < 1e-10


def test_eq(paramSet):
    for p in paramSet:
        assert (paramSet['af'] == paramSet[p]) is ('af' == p)
