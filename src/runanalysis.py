# Calculate statistics for each run of the simulation
import logging
import math
from os import stat
from typing import List, Union

import numpy as np
from numpy.core.fromnumeric import shape, var
import pandas as pd
import scipy.stats as stats

from models import Inspector, Workstation

def calc_stats_workstation(workstation_list: List[Workstation], iteration: int, sim_duration: Union[int, float], start_recording: Union[int, float]=0) -> np.ndarray:
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
      total_idle_time = (sim_duration - start_recording) - workstation.start
      utilization = 0 #?? fix this later???
      average_idle_length = (sim_duration - start_recording) - workstation.start

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
      utilization = ((sim_duration - start_recording)  - total_idle_time) / (sim_duration - start_recording)

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


def calc_stats_inspector(inspector_list: List[Inspector], iteration: int, sim_duration: Union[int, float], start_recording: Union[int, float]=0):
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
    utilization = ((sim_duration - start_recording) - total_idle_time) / (sim_duration - start_recording)
    

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
        processing_time = np.asarray(inspector.inspection_times[component.name])
        mean = processing_time.mean()
        variance = processing_time.var()

        # Calculate overall throughput for specific component
        throughput = inspector.total_amount_inspected[component.name]

      # Create series for this inspector and this component
      inspector_series = pd.Series({
        'iteration': iteration,
        'inspector_id': inspector.id,
        'component_id': component.value,
        'component_inspection_time_mean': pd.to_numeric(mean, errors='coerce'),
        'component_inspection_time_variance': pd.to_numeric(variance, errors='coerce'),
        'component_throughput': throughput,
        'total_idle_time': total_idle_time,
        'utilization': utilization,
        'average_idle_length': average_idle_length
      }, dtype='float')

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
        'component_throughput', 'total_idle_time', 'utilization', 'average_idle_length'],
    dtype='float'
  )

  # Convert (nan,) tuple to just NaN
  # df['processing_time_mean'] = pd.to_numeric(df['processing_time_mean'], errors='coerce')
  # df['processing_time_variance'] = pd.to_numeric(df['processing_time_variance'], errors='coerce')

  return df.astype('float')


def calculate_inspector_utilization(inspector_data: pd.DataFrame) -> pd.DataFrame:
  '''
  Create a dataframe showing the utilization for each inspector

  Args:
    inspector_data: Dataframe of information from each run for the inspector

  Returns:
    df: Dataframe containing the inspector, R value, mean, standard deviation, 
    standard error and half interval for the utilization of each inspector
  '''
  df = pd.DataFrame(
    columns=['inspector', 'component', 'R', 'mean', 'std_dev', 'std_err', 'half_interval']
  )

  df['inspector'] = [1, 2]
  df['component'] = ['C1', 'C2, C3']
  df['R'] = [len(inspector_data.groupby('iteration')['iteration'].unique()), len(inspector_data.groupby('iteration')['iteration'].unique())]
  df['mean'] = inspector_data.groupby('inspector_id')['utilization'].mean()
  df['std_dev'] = inspector_data.groupby('inspector_id')['utilization'].std()
  df['std_err'] = df.apply(lambda row: row['R'] / math.sqrt(row['std_dev']), axis=1)



def calculate_workstation_replications(data: pd.DataFrame, column: str, criterion_percentage: float, iterations: int) -> pd.DataFrame:
  '''
  Create a dataframe showing the number of iterations required to find the mean value
  with the given error criterion for the given column

  Args:
    data (pd.Dataframe): Dataframe of workstation data from each run of the workstation
    column (str): the column in the workstation dataframe on which to perform the calculations
    criterion_percentage: The percentage of the calculated mean to be usedfor the error criterion t
    iterations (int): number of iterations used in this simulation
  
  Returns:
    df: Dataframe containing the workstation id, number of runs, mean, standard deviation, 
    standard error and half interval for the value of interest of each workstation
  '''
  df = pd.DataFrame(
    columns=['R', 'mean', 'std_dev', 'error_criterion', 'num_replications']
  )

  df['mean'] = data.groupby('workstation_id')[column].mean()
  df['std_dev'] = data.groupby('workstation_id')[column].std()
  df['error_criterion'] = df.apply(lambda row: row['mean'] * criterion_percentage, axis=1)
  df['num_replications'] = df.apply(lambda row: ((row['std_dev'] * stats.norm.ppf(1-(0.05/2))) / row['error_criterion']) ** 2, axis=1)
  df['R'] = np.repeat(iterations, 3).tolist()

  return df



def calculate_workstation_means(data: pd.DataFrame, column: str, iterations: int) -> pd.DataFrame:
  '''
  Create a dataframe showing mean, standard deviation, standard error and half interval
  for a given column

  Args:
    data (pd.Dataframe): Dataframe of workstation data from each run of the workstation
    column (str): the column in the workstation dataframe on which to perform the calculations
    iterations (int): number of iterations used in this simulation
  
  Returns:
    df: Dataframe containing the workstation id, number of runs, mean, standard deviation, 
    standard error and half interval for the value of interest of each workstation
  '''
  df = pd.DataFrame(
    columns=['workstation', 'R', 'mean', 'std_dev', 'std_err', 'half_interval']
  )

  df['mean'] = data.groupby('workstation_id')[column].mean()
  df['std_dev'] = data.groupby('workstation_id')[column].std()
  df['std_err'] = data.groupby('workstation_id')[column].sem()
  df['workstation'] = [1, 2, 3]
  df['R'] = np.repeat(iterations, 3).tolist()
  df['half_interval'] = df.apply(lambda row: stats.t.ppf(1-0.025, df=(iterations-1)) * row['std_err'], axis=1)

  # df = ws_df.groupby('workstation_id')[column].agg(['count', 'mean', 'std', 'sem'])

  return df
