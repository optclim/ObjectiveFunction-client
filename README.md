[![Documentation Status](https://readthedocs.org/projects/objectivefunction-client/badge/?version=latest)](https://objectivefunction-client.readthedocs.io/en/latest/?badge=latest)
[![test package ObjectiveFunction-client](https://github.com/optclim/ObjectiveFunction-client/actions/workflows/pythonapp.yml/badge.svg)](https://github.com/optclim/ObjectiveFunction-client/actions/workflows/pythonapp.yml)

# ObjectiveFunction-client
The ObjectiveFunction-client is part of the Optclim3 blackbox optimisation framework. It provides a set of python proxy classes that communicate with the [ObjectiveFunction-server](https://github.com/optclim/ObjectiveFunction-server).


## testing
The package comes with an extensive set of unit tests. Run the tests using
```
python3 -m pytest
```
You can also get information on coverage running
```
python3 -m pytest --cov=ObjectiveFunction_client tests/
```
