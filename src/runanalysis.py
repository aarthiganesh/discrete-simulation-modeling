# Calculate statistics for each run of the simulation
import logging
from typing import List, Union

import numpy as np
from numpy.core.fromnumeric import shape, var
import pandas as pd

from models import Inspector, Workstation

def calc_stats_workstation(workstation_list: List[Workstation], iteration: int, sim_duration: Union[int, float]) -> np.ndarray:
  '''
  Calculate statistics for all workstations for a single simulation iteration. 
  ...
  Parameters
  ----------
  workstations: List[Workstation]
    List of all workstation models used for the current simulation run
  iteration: int
    Current iteration of the simulation
  sim_duration: Union[int, float]
    Amount of minutes in the simulation run
  
  Returns
  ----------
  numpy.array:
    A 2d numpy array with each row as the statistics for one of the workstations
  '''
  workstation_array = np.empty(shape=(len(workstation_list),), dtype=object)

  # Calculate statistics for workstations
  for index, workstation in enumerate(workstation_list):

    # TODO: check for case if has started assembly but has not finished?
    # Check if workstation has assembled anything
    if (workstation.total_amount_assembled == 0):
      if workstation.start != 0:
        logging.error('Iteration {}: ws{} started assembly but did not finish'.format(iteration, workstation.id))
      # If nothing was assembled by the workstation, set specific values
      mean = np.nan,
      variance = np.nan,
      throughput = 0 # Fractional if not complete at end of iteration??
      total_idle_time = sim_duration - workstation.start
      utilization = 0 #?? fix this later???
      average_idle_length = sim_duration - workstation.start

    else:
      # Calculate mean and variance of workstation processing time
      processing_time = np.asarray(workstation.processing_time)
      mean = processing_time.mean()
      variance = processing_time.var()

      # Calculate overall throughput
      throughput = workstation.total_amount_assembled

      # Calculate total idle time
      wait_time = np.asarray(workstation.wait_time)
      total_idle_time = wait_time.sum()

      # Calculate utilization
      utilization = (sim_duration - total_idle_time) / sim_duration

      # Calculate average idle length
      wait_time[wait_time == 0] = np.nan  # Set all zero values to nan 
      average_idle_length = np.nanmean(wait_time)
    
    
    # Store all values in pandas Series
    # ws_stats = np.array(
    #   [iteration, workstation.id, mean, variance, throughput, 
    #   total_idle_time, utilization, average_idle_length],
    #   dtype=[('iteration', 'i4'), 
    #          ('workstation_id', 'i4'), 
    #          ('processing_time_mean', 'f8'), 
    #          ('processing_time_variance', 'f8'),
    #          ('throughput', 'i4'),
    #          ('total_idle_time', 'f8'),
    #          ('utilization', 'f8'),
    #          ('average_idle_length', 'f8')]
    # )
    # workstation_array[index] = ws_stats

    workstation_series = pd.Series({
      'iteration': iteration,
      'workstation_id': workstation.id,
      'processing_time_mean': mean,
      'processing_time_variance': variance,
      'throughput': throughput,
      'total_idle_time': total_idle_time,
      'utilization': utilization,
      'average_idle_length': average_idle_length
    })

    workstation_array[index] = workstation_series.to_numpy()
    
  return np.stack(workstation_array)


def calc_stats_inspector(inspectors: List[Inspector], workstations: List[Workstation], sim_duration: Union[int, float]):
  '''
  Calculate statistics for each run. 
  ...
  Parameters
  ----------
  inspectors: List[Inspectors]
    List of all inspector models used for the current simulation run
  workstations: List[Workstation]
    List of all workstation models used for the current simulation run
  sim_duration: Union[int, float]
    Amount of minutes in the simulation run
  '''

  # Calculate statistics for inspectors
  for inspector in inspectors:
    pass


def create_df_workstations(run_data: np.ndarray) -> pd.DataFrame:
  '''
  Create a dataframe to store all workstation stats for each simulation iteration 
  '''
  # Flatten array into pandas dataframe
  return pd.DataFrame(
    data=np.vstack(run_data), 
    columns=['iteration', 'workstation_id', 'processing_time_mean', 
             'processing_time_variance', 'throughput', 'total_idle_time', 
             'utilization', 'average_idle_length']
  )


