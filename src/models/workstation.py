import logging
import random
from typing import Generator, List, Union

import simpy
from simpy import Environment

import numpy

from .buffer import Buffer


class Workstation(object):
  def __init__(self, id: int, env: Environment, buffers: List[Buffer], mean: float, start_recording: Union[int, float]=0) -> None:
    super().__init__()
    self.id = id
    self.env = env
    self.buffers = buffers
    self.mean = mean
    self.start_recording = start_recording

    # Stats for analysis
    self.total_amount_assembled = 0
    self.wait_time = []
    self.processing_time = []
    self.wait = 0
    self.start = 0
    self.end = 0


  def get_assembly_time(self) -> float:
    '''Get the assembly time for a component'''
    return random.expovariate(1 / self.mean)


  def get_components(self) -> Generator:
    '''Wait for all buffers to have at least one component ready for production'''
    if not self.buffers:
      raise RuntimeError('Workstation has no component buffers')
    
    logging.debug('workstation {} finished assembly at {}'.format(self.id, self.env.now))
    self.wait = self.env.now
    component_ready_events = [buffer.get(amount=1) for buffer in self.buffers]
    yield self.env.all_of(component_ready_events)

  
  def assemble(self) -> Generator:
    '''Assemble a product from components.'''
    logging.debug('workstation {} starting assembly at {}'.format(self.id, self.env.now))
    self.start = self.env.now
    yield self.env.timeout(self.get_assembly_time())
    self.end = self.env.now
    
    logging.debug('workstation {} finished assembly at {}'.format(self.id, self.env.now))
  

  def record_stats(self) -> None:
    '''Record stats in data'''
    self.total_amount_assembled += 1
    self.wait_time.append(-self.wait+self.start)
    self.processing_time.append(self.end-self.start)


  def main_loop(self) -> None:
    '''Main sequence loop for Workstation.'''
    while True:
      yield self.env.process(self.get_components())
      yield self.env.process(self.assemble())
      if (self.env.now >= self.start_recording):
        self.record_stats()
      

    


