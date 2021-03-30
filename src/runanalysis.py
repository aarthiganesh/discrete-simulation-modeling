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
        logging.debug('Iteration {}: ws{} started assembly but did not finish'.format(iteration, workstation.id))
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


def calc_stats_inspector(inspector_list: List[Inspector], iteration: int, sim_duration: Union[int, float]):
  '''
  Calculate statistics for all inspectors for a single simulation iteration. 
  ...
  Parameters
  ----------
  inspector_list: List[Inspectors]
    List of all inspector models used for the current simulation run
  iteration: int
    Current iteration of the simulation
  sim_duration: Union[int, float]
    Amount of minutes in the simulation run
  
  Returns
  ----------
  numpy.array:
    A 2d numpy array with each row as the statistics for one of the inspectors
  '''
  # Get the total number of rows for the array
  total_entries = sum(len(inspector.components) for inspector in inspector_list)

  inspector_array = np.empty(shape=(total_entries,), dtype=object)

  current_index = 0
  # Calculate statistics for inspectors
  for inspector in inspector_list:

    # Calculate common values for all components
    # Calculate total idle time
    wait_time = np.asarray(inspector.wait_time)
    total_idle_time = wait_time.sum()

    # Calculate utilization
    utilization = (sim_duration - total_idle_time) / sim_duration

    # Calculate average idle length
    if (np.any(wait_time != 0.0)):
      wait_time[wait_time == 0] = np.nan  # Set all zero values to nan 
      average_idle_length = np.nanmean(wait_time)
    else:
      # If all wait times in array are zero, then machine was never idle. 
      average_idle_length = np.nan


    # Calculate statistics for each individual component for each inspector
    for component in inspector.components:
      # Check if inspector has inspected anything
      if (inspector.total_amount_inspected[component.name] == 0):
        if inspector.start != 0:
          logging.debug('Iteration {}: insp{} started inspection for component {} but did not finish'.format(iteration, inspector.id, component.name))
        # If nothing was inspected, set specific values
        mean = np.nan,
        variance = np.nan,
        throughput = 0 # Fractional if not complete at end of iteration?

      else:
        # Calculate mean and variance of inspector processing time
        processing_time = np.asarray(inspector.inspection_time[component.name])
        mean = processing_time.mean()
        variance = processing_time.var()

        # Calculate overall throughput for specific component
        throughput = inspector.total_amount_inspected[component.name]

      # Create series for this inspector and this component
      inspector_series = pd.Series({
        'iteration': iteration,
        'inspector_id': inspector.id,
        'component_id': component.name,
        'component_inspection_time_mean': mean,
        'component_inspection_time_variance': variance,
        'component_throughput': throughput,
        'total_idle_time': total_idle_time,
        'utilization': utilization,
        'average_idle_length': average_idle_length
      })

      # Save series to be returned
      inspector_array[current_index] = inspector_series.to_numpy()
      current_index += 1
    
  return np.stack(inspector_array)


def create_df_workstations(run_data: np.ndarray) -> pd.DataFrame:
  '''
  Create a dataframe to store all workstation stats for each simulation iteration 
  '''
  # Flatten array into pandas dataframe
  df = pd.DataFrame(
    data=np.vstack(run_data), 
    columns=['iteration', 'workstation_id', 'processing_time_mean', 
             'processing_time_variance', 'throughput', 'total_idle_time', 
             'utilization', 'average_idle_length']
  )

  # Convert (nan,) tuple to just NaN
  df['processing_time_mean'] = pd.to_numeric(df['processing_time_mean'], errors='coerce')
  df['processing_time_variance'] = pd.to_numeric(df['processing_time_variance'], errors='coerce')

  return df


def create_df_inspectors(run_data: np.ndarray) -> pd.DataFrame:
  '''
  Create a dataframe to store all inspector stats for each simulation iteration

  Args:
    run_data: array of all data produced in calc_stats_inspector
  
  Returns:
    df: Dataframe containing all data from all iterations
  '''
  # Flatten array into pandas dataframe
  df = pd.DataFrame(
    data=np.vstack(run_data), 
    columns=['iteration', 'inspector_id', 'component_id',
        'component_inspection_time_mean', 'component_inspection_time_variance',
        'component_throughput', 'total_idle_time', 'utilization', 'average_idle_length']
  )

  # Convert (nan,) tuple to just NaN
  # df['processing_time_mean'] = pd.to_numeric(df['processing_time_mean'], errors='coerce')
  # df['processing_time_variance'] = pd.to_numeric(df['processing_time_variance'], errors='coerce')

  return df

