import logging
import random
import time
from typing import List

import numpy as np
from numpy.core.fromnumeric import mean

import simpy
from simpy.core import T

import numpy

from models import Buffer, Component, Inspector, Workstation, workstation
import runanalysis

# Control constants
SEED = 12345
BUFFER_SIZE = 2
SIM_TIME = 480 # 8 hour shift?
ITERATIONS = 200

current_iteration = 0
w1_wait_time = []
w2_wait_time = []
w3_wait_time = []

w1_processing_time = []
w2_processing_time = []
w3_processing_time = []

workstation_stats = np.empty(shape=(ITERATIONS, ), dtype=object)


def init_logging() -> None:
  '''Init logging for system'''
  format = "%(asctime)s: %(message)s"
  logging.basicConfig(format=format, level=logging.INFO, datefmt='%H:%M:%S')



def init_means() -> dict:
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


def run_iteration(seed: int, means: dict, iteration:int):
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
  

  # Run simulation
  main_env.run(until=SIM_TIME)

  # Record values
  w1_wait_time.append(w1.wait_time)
  w2_wait_time.append(w2.wait_time)
  w3_wait_time.append(w3.wait_time)

  w1_processing_time.append(w1.processing_time)
  w2_processing_time.append(w2.processing_time)
  w3_processing_time.append(w3.processing_time)

  # print('w1 wait time: {}'.format(w1_wait_time))
  # print('w2 wait time: {}'.format(w2_wait_time))
  # print('w3 wait time: {}'.format(w3_wait_time))


  workstation_stats[iteration] = runanalysis.calc_stats_workstation(
    workstation_list=workstation_list,
    iteration=iteration,
    sim_duration=SIM_TIME
  )



if __name__ == '__main__':
  # Set up random generation
  random.seed(SEED)

  # Set up logging
  init_logging()

  # Get means for RNG
  means = init_means()

  # Create a list of seeds to use
  seed_list = [random.getrandbits(32) for iteration in range(ITERATIONS)]

  start_time = time.time()
  logging.info('Running {} iterations of the simulation'.format(ITERATIONS))

  for seed in seed_list:
    run_iteration(seed=seed, means=means, iteration=current_iteration)
    current_iteration += 1
    # print(current_iteration)

  
  # Calculate stats for whole run
  runanalysis.create_df_workstations(run_data=workstation_stats)


  logging.info('{measurement} for {source}: {quantity}'.format(
    measurement='Average Processing Time',
    source='Workstation 1',
    quantity=numpy.mean(np.hstack(w1_processing_time).mean())
  ))

  logging.info('{measurement} for {source}: {quantity}'.format(
    measurement='Average Processing Time',
    source='Workstation 2',
    quantity=numpy.mean(np.hstack(w2_processing_time).mean())
  ))

  logging.info('{measurement} for {source}: {quantity}'.format(
    measurement='Average Processing Time',
    source='Workstation 3',
    quantity=numpy.mean(np.hstack(w3_processing_time).mean())
  ))
  # print('Average processing time:{}'.format(numpy.mean(np.hstack(w1_processing_time).mean())))
  end_time = time.time()
  logging.info('elapsed time for {} iterations is {}'.format(ITERATIONS, end_time-start_time))
