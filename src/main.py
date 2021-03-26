import random
from typing import List

import numpy as np
from numpy.core.fromnumeric import mean

import simpy

from models import Buffer, Component, Inspector, Workstation

# Control constants
SEED = 12345
BUFFER_SIZE = 2
SIM_TIME = 480 # 8 hour shift?
ITERATIONS = 5


def get_means() -> dict:
  '''Get a dictionary of all the means from the data for each file'''
  means = dict()

  data = np.fromfile('./data/servinsp1.dat', dtype=np.float64, sep="\n")
  means[Component.C1.name] = np.mean(data)

  data = np.fromfile('./data/servinsp22.dat', dtype=np.float64, sep="\n")
  means[Component.C2.name] = np.mean(data)

  data = np.fromfile('./data/servinsp1.dat', dtype=np.float64, sep="\n")
  means[Component.C3.name] = np.mean(data)

  data = np.fromfile('./data/ws1.dat', dtype=np.float64, sep="\n")
  means['ws1'] = np.mean(data)

  data = np.fromfile('./data/ws2.dat', dtype=np.float64, sep="\n")
  means['ws2'] = np.mean(data)

  data = np.fromfile('./data/ws3.dat', dtype=np.float64, sep="\n")
  means['ws3'] = np.mean(data)

  return means


def run_iteration(seed: int, means: dict):
  '''
  Run a single iteration for the simulation. Creates a new environment each time
  ...
  Parameters
  ----------
  seed: int
    The seed to be used for the random generation
  means: dict
    The means to use for the random expovariate functions
  '''

  # Set up random generation
  random.seed(seed)

  # Set up environment
  main_env = simpy.Environment()
  
  # Set up components
  # Init buffer for workstation 1
  b1c1 = Buffer(id='w1c1', env=main_env, accepts=Component.C1, capacity=BUFFER_SIZE, init=0)
  
  # Init buffers for workstation 2
  b2c1 = Buffer(id='w2c1', env=main_env, accepts=Component.C1, capacity=BUFFER_SIZE, init=0)
  b2c2 = Buffer(id='w2c2', env=main_env, accepts=Component.C2, capacity=BUFFER_SIZE, init=0)
  
  # Init buffers for workstation 3
  b3c1 = Buffer(id='w3c1', env=main_env, accepts=Component.C1, capacity=BUFFER_SIZE, init=0)
  b3c3 = Buffer(id='w3c3', env=main_env, accepts=Component.C3, capacity=BUFFER_SIZE, init=0)

  # Init workstations
  w1 = Workstation(id=1, env=main_env, buffers=[b1c1], mean=means['ws1'])
  w2 = Workstation(id=2, env=main_env, buffers=[b2c1, b2c2], mean=means['ws2'])
  w3 = Workstation(id=3, env=main_env, buffers=[b3c1, b3c3], mean=means['ws3'])

  workstation_list: List[Workstation] = [w1, w2, w3]

  # Init inspectors
  inspector_one = Inspector(
    id=1, 
    env=main_env, 
    components=[Component.C1], 
    buffers=[b1c1, b2c1, b3c1], 
    means={ key: means[key] for key in [Component.C1.name] }
  )
  
  inspector_two = Inspector(
    id=2, 
    env=main_env, 
    components=[Component.C2, Component.C3], 
    buffers=[b2c2, b3c3], 
    means={ key: means[key] for key in [Component.C2.name, Component.C3.name] }
  )

  inspector_list: List[Inspector] = [inspector_one, inspector_two]


  # Set up workstation processes
  for workstation in workstation_list:
    main_env.process(workstation.main_loop())
  
  # Set up inspector processes
  for inspector in inspector_list:
    main_env.process(inspector.main_loop())

  # Start simulation
  main_env.run(until=SIM_TIME)
  print('total amount assembled = %d' % w1.total_amount_assembled)




if __name__ == '__main__':
  # Set up random generation
  random.seed(SEED)

  # Get means for RNG
  means = get_means()

  # Create a list of seeds to use
  seed_list = [random.getrandbits(32) for iteration in range(ITERATIONS)]

  for seed in seed_list:
    run_iteration(seed=seed, means=means)
