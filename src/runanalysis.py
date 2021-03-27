# Calculate statistics for each run of the simulation
from typing import List, Union

import numpy as np
from numpy.core.fromnumeric import shape, var
import pandas as pd

from models import Inspector, Workstation

def calculate_statistics_workstation(workstations: List[Workstation], iteration: int, sim_duration: Union[int, float]) -> pd.DataFrame:
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
  pandas.Dataframe:
    A dataframe with the calculated statistics for each run
  '''
  workstation_array = np.empty(shape=(len(workstations),), dtype=object)

  # Calculate statistics for workstations
  for i in range(len(workstations)):
    workstation = workstations[i]

    # Calculate mean and variance of workstation processing time
    if (workstation.total_amount_assembled < 0):
      processing_time = np.asarray(workstation.processing_time)
      mean = processing_time.mean()
      variance = processing_time.var()
    else:
      mean = np.nan
      variance = np.nan

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

    workstation_array[i] = workstation_series
  
  return workstation_series


def calculate_statistics(inspectors: List[Inspector], workstations: List[Workstation], sim_duration: Union[int, float]):
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