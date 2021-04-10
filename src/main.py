import argparse
import logging
import random
import time
from typing import List
import sys

import numpy as np

import simpy
from simpy.core import T

from models import Buffer, Component, Inspector, Workstation, workstation
import runanalysis

# Control constants

BUFFER_SIZE = 2

# Control constants (will be set later by argument parser)
# SEED = 12345
# SIM_TIME = 43800 # 8 hour shift?
# ITERATIONS = 200

w1_wait_time = []
w2_wait_time = []
w3_wait_time = []

w1_processing_time = []
w2_processing_time = []
w3_processing_time = []

workstation_finishing_times = {}


def parse_arguments():
  '''Parse arguments from the command line'''
  parser = argparse.ArgumentParser()
  parser.add_argument('-i', '--iterations', type=int, default=200)
  parser.add_argument('-d', '--duration', type=int, default=480)
  parser.add_argument('-s', '--seed', type=int, default=12345)
  parser.add_argument('-w', '--wait', type=int, default=1000)

  # Create global control constants
  global ITERATIONS, SIM_TIME, SEED, START_RECORDING

  # Set globals with command line arguments
  args = parser.parse_args()
  ITERATIONS = args.iterations
  SIM_TIME = args.duration
  SEED = args.seed
  START_RECORDING = args.wait


def init_logging() -> None:
  '''Init logging for system'''
  format = "%(asctime)s: %(message)s"
  logging.basicConfig(format=format, level=logging.INFO, stream=sys.stdout, datefmt='%H:%M:%S')


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


def print_progress_bar (iteration: int, total: int, prefix: str='', suffix: str='', decimals: int= 1, length: int=100, fill: str='█', printEnd: str="\r"):
  """
  Call in a loop to create terminal progress bar
  @params:
      iteration   - Required  : current iteration (Int)
      total       - Required  : total iterations (Int)
      prefix      - Optional  : prefix string (Str)
      suffix      - Optional  : suffix string (Str)
      decimals    - Optional  : positive number of decimals in percent complete (Int)
      length      - Optional  : character length of bar (Int)
      fill        - Optional  : bar fill character (Str)
      printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
  """
  percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
  filledLength = int(length * iteration // total)
  bar = fill * filledLength + '-' * (length - filledLength)
  print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
  # Print New Line on Complete
  if iteration == total: 
      print('\n')

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
  w1 = Workstation(id=1, env=main_env, buffers=[b1c1], mean=means['ws1'], start_recording=START_RECORDING)
  w2 = Workstation(id=2, env=main_env, buffers=[b2c1, b2c2], mean=means['ws2'], start_recording=START_RECORDING)
  w3 = Workstation(id=3, env=main_env, buffers=[b3c1, b3c3], mean=means['ws3'], start_recording=START_RECORDING)

  workstation_list: List[Workstation] = [w1, w2, w3]

  # Init inspectors
  inspector_one = Inspector(
    id=1, 
    env=main_env, 
    components=[Component.C1], 
    buffers=[b1c1, b2c1, b3c1], 
    means={ key: means[key] for key in [Component.C1.name] },
    start_recording=START_RECORDING
  )
  
  inspector_two = Inspector(
    id=2, 
    env=main_env, 
    components=[Component.C2, Component.C3], 
    buffers=[b2c2, b3c3], 
    means={ key: means[key] for key in [Component.C2.name, Component.C3.name] },
    start_recording=START_RECORDING
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

  workstation_finishing_times[w1.id] = w1.component_finish_times
  workstation_finishing_times[w2.id] = w2.component_finish_times
  workstation_finishing_times[w3.id] = w3.component_finish_times


  # Calculate stats for workstation for this iteration
  workstation_stats[iteration] = runanalysis.calc_stats_workstation(
    workstation_list=workstation_list,
    iteration=iteration,
    sim_duration=SIM_TIME,
    start_recording=START_RECORDING
  )

  # Calculate stats for inspector for this iteration
  inspector_stats[iteration] = runanalysis.calc_stats_inspector(
    inspector_list=inspector_list,
    iteration=iteration,
    sim_duration=SIM_TIME,
    start_recording=START_RECORDING
  )



if __name__ == '__main__':
  # Parse command line arguments
  parse_arguments()
  
  # Set up random generation
  random.seed(SEED)

  # Set up logging
  init_logging()

  # Get means for RNG
  means = init_means()

  # Create a list of seeds to use
  seed_list = [random.getrandbits(32) for iteration in range(ITERATIONS)]

  # Create empty numpy arrays for storing statistics from each simulation iteration
  workstation_stats = np.empty(shape=(ITERATIONS, ), dtype=object)
  inspector_stats = np.empty(shape=(ITERATIONS, ), dtype=object)

  start_time = time.time()
  logging.info('Running the simulation with seed={seed}, iterations={iters} duration={duration}, wait={wait}'.format(seed=SEED, iters=ITERATIONS, duration=SIM_TIME, wait=START_RECORDING))

  for index, seed in enumerate(seed_list):
    run_iteration(seed=seed, means=means, iteration=index)
    print_progress_bar(iteration=index, total=ITERATIONS, prefix='Progress:', length=50)

  # Calculate stats for whole run
  ws_df = runanalysis.create_df_workstations(run_data=workstation_stats)
  insp_df = runanalysis.create_df_inspectors(run_data=inspector_stats)
  

  ws_idle_replication = runanalysis.calculate_workstation_replications(
    data=ws_df,
    column='utilization',
    criterion_percentage=0.01,
    iterations=ITERATIONS
  )

  ws_idle_means = runanalysis.calculate_workstation_means(
    data=ws_df,
    column='utilization',
    iterations=ITERATIONS
  )

  ws_throughput_replication = runanalysis.calculate_workstation_replications(
    data=ws_df,
    column='throughput',
    criterion_percentage=0.01,
    iterations=ITERATIONS
  )

  ws_throughput_means = runanalysis.calculate_workstation_means(
    data=ws_df,
    column='throughput',
    iterations=ITERATIONS
  )

  insp_idle_replication = runanalysis.calculate_inspector_replications(
    data=insp_df[insp_df.index % 3 != 2],   # Filter out every third row (as that row contains duplicate info for this calculation)
    group_col='inspector_id',
    column='utilization',
    criterion_percentage=0.01,
    iterations=ITERATIONS
  )

  insp_idle_means = runanalysis.calculate_inspector_means(
    data=insp_df[insp_df.index % 3 != 2],   # Filter out every third row (as that row contains duplicate info for this calculation)
    group_col='inspector_id',
    column='utilization',
    iterations=ITERATIONS
  )

  insp_throughput_replication = runanalysis.calculate_inspector_replications(
    data=insp_df,
    group_col='component_id',
    column='component_throughput',
    criterion_percentage=0.01,
    iterations=ITERATIONS
  )

  insp_throughput_means = runanalysis.calculate_inspector_means(
    data=insp_df,
    group_col='component_id',
    column='component_throughput',
    iterations=ITERATIONS
  )

  
  logging.info('Workstation Utilization Replications Calculations:\n{data}\n'.format( 
    data=ws_idle_replication
  ))

  logging.info('Workstation Utilization Means Calculations:\n{data}\n'.format(
    data=ws_idle_means
  ))

  logging.info('Workstation Throughput Replications Calculations:\n{data}\n'.format( 
    data=ws_throughput_replication
  ))

  logging.info('Workstation Throughput Means Calculations:\n{data}\n'.format( 
    data=ws_throughput_means
  ))

  logging.info('Inspector Utilization Replication Calculations:\n{data}\n'.format( 
    data=insp_idle_replication
  ))

  logging.info('Inspector Utilization Means Calculations:\n{data}\n'.format( 
    data=insp_idle_means
  ))

  logging.info('Inspector Throughput Replications Calculations:\n{data}\n'.format( 
    data=insp_throughput_replication
  ))

  logging.info('Inspector Throughput Means Calculations:\n{data}\n'.format( 
    data=insp_throughput_means
  ))


  logging.info('{measurement} for {source}: {quantity}'.format(
    measurement='Average Processing Time',
    source='Workstation 1',
    quantity=ws_df.query('workstation_id==1')['processing_time_mean'].mean(skipna=True)
  ))

  logging.info('{measurement} for {source}: {quantity}'.format(
    measurement='Average Processing Time',
    source='Workstation 2',
    quantity=ws_df.query('workstation_id==2')['processing_time_mean'].mean(skipna=True)
  ))

  logging.info('{measurement} for {source}: {quantity}'.format(
    measurement='Average Processing Time',
    source='Workstation 3',
    quantity=ws_df.query('workstation_id==3')['processing_time_mean'].mean(skipna=True)
  ))

  logging.info('{measurement} for {source}: {quantity}'.format(
    measurement='Average Throughput',
    source='Inspector 2, component 2',
    quantity=insp_df.query("component_id==2")['component_throughput'].mean(skipna=True)
  ))

  logging.info('{measurement} for {source}: {quantity}'.format(
    measurement='Average Throughput per hour',
    source='Workstation 1',
    quantity=(ws_df.query("workstation_id==1")['throughput'].mean(skipna=True) / (SIM_TIME / 60))
  ))

  logging.info('{measurement} for {source}: {quantity}'.format(
    measurement='Average Throughput per hour',
    source='Workstation 2',
    quantity=(ws_df.query("workstation_id==2")['throughput'].mean(skipna=True) / (SIM_TIME / 60))
  ))

  logging.info('{measurement} for {source}: {quantity}'.format(
    measurement='Average Throughput per hour',
    source='Workstation 3',
    quantity=(ws_df.query("workstation_id==3")['throughput'].mean(skipna=True) / (SIM_TIME / 60))
  ))

  # print('Average processing time:{}'.format(numpy.mean(np.hstack(w1_processing_time).mean())))
  end_time = time.time()
  logging.info('elapsed time for {} iterations is {}'.format(ITERATIONS, end_time-start_time))
