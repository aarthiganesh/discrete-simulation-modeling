# discrete-simulation-modeling


# Installation
## Prepare virtual environment
If your version of python is 3.3 or newer, then the `venv` module should be used to manage the packages for this project. The virtual environment can be created by going to the project's directory and running the following command:
```
python3 -m venv env
```

## Activating the virtual environment
To activate the virtual environment, run the following command in the main project directory:
```
source env/bin/activate
```
If the virtual environment was activated correctly, you should see the name of the virtual environment next to the command line prompt i.e. `(env) $`

## Installing packages
Once the virtual environment is activated and running, the packages needed to run the program can be installed to the virtual environment by running the following command in the main project directory:
```
(env) $ pip install -r requirements.txt
```

# Running the Program
The program can be run with the following command: 
```
(env) $ python3 src/main.py
```