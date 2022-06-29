=================================
 ObjectiveFunction Configuration
=================================

Simulations run within the ObjectiveFunction framework are stored in a hierarchy:
 * A **study** defines a group of simulations run with the same set of parameters. Each parameter has a name and is defined by type (integer of float) and an upper and lower bound. 
 * Each study consists of a number of **scenarios**. Scenarios are distinguished from each other by some other configuration. For example, in the case of a climate model this might be different CO2 forcing.
 * Each scenario holds a number of actual model **runs** where the parameters are varied within their bounds.

Configuration
=============
The Objective Function is configured via a nested ini style configuration file

::
   
   [setup]
      app = string() # the name of ObjectiveFunction app
      # the URL of the ObjectiveFunction server
      baseurl = string(default=http://localhost:5000/api/)
      study = string() # the name of the study
      scenario = string() # the name of the scenario
      basedir = string() # the base directory
      objfun = string(default=misfit)

   [parameters]
      [[float_parameters]]
        [[[float_param_A]]]
          value = float() # the default value
          min = float() # the minimum value allowed
          max = float() # the maximum value allowed
          resolution = float(default=1e-6) # the resolution of the parameter
          constant = boolean(default=False) # if set to True the parameter is
                                             # not optimised for
      [[integer_parameters]]
        [[[int_param_A]]]
          value = integer() # the default value
          min = integer() # the minimum value allowed
          max = integer() # the maximum value allowed
          constant = boolean(default=False) # if set to True the parameter is
                                            # not optimised for

   [targets]
      target_A = float
				
In the ``setup`` section communication with the Objective Function server is configured and the ``study`` and ``scenario`` names are set. The ``basedir`` determines where files are stored on the local file system.

In the ``parameters`` section the parameters are defined. There are two subsections one for float parameters and one for integer parameters. The parameter name is specified in the section name. Float parameters are scaled to the interval [min, max] and internally stored as integers. The minimum and maximum values are also used as bounds by the optimisation procedure. Both float and integer parameters have a default value which is used as starting value for the optimiser. If ``constant`` is set to ``True`` then the parameter does not take part in the optimisation procedure and is fixed. The set of parameters (the names, minimum and maximum value and resolution) need to be the same for all scenarios of one study.

The ``target`` section contains the targets used by a simulated observation type Objective Function. The list of targets has to be the same for all simulations of one study, although their values can change.
      

Secret
------
The Objective Function client communicates with the Objective Function server via HTTP. All interaction with the server is authenticated using the ``appname`` and associated ``secret``. The secret can be passed on the command line or stored in an ini style file called ``.objfun_secrets``. The Objective Function client looks for the secret file in the present working directory or the home directory. The secret file uses an ini file style format with the app name as section, eg

::

   [app_name]
   secret=secret_associated_with_app_name


Interacting with the Objective Function Server
==============================================
The Objective Function client comes with a command line program that can be used to interact with the server.

::

   usage: objfun-manage [-h] [-b BASEURL] [-a APP] [-p PASSWORD] [-c CONFIG]
                        [-s STUDY] [-d DELETE_STUDY] [-S SCENARIO]
                        [-D DELETE_SCENARIO]

   optional arguments:
     -h, --help            show this help message and exit
     -b BASEURL, --baseurl BASEURL
                           API url
     -a APP, --app APP     the ObjectiveFunction app
     -p PASSWORD, --password PASSWORD
                           the password for the app
     -c CONFIG, --config CONFIG
                           config file to read
     -s STUDY, --study STUDY
                           get all scenarios for a particular study
     -d DELETE_STUDY, --delete-study DELETE_STUDY
                           delete a study
     -S SCENARIO, --scenario SCENARIO
                           get all runs for a particular scenario
     -D DELETE_SCENARIO, --delete-scenario DELETE_SCENARIO
                           delete a particular scenario

The program allows you to interact with the server by either specifying the base URL, app name and password on the command line or by using a configuration file. By default the program will show a list of studies associated with the application together with the number of scenarios. The program shows the list of scenarios if the study is specified on the command line. It shows the list of runs if the scenario is also specified. The program can be also used to delete a scenario including all its runs or an entire study (including all scenarios and runs).
