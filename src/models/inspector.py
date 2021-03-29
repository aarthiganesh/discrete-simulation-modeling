import logging
import random
from typing import Generator, List

import simpy
from simpy import Environment

from .buffer import Buffer
from .component import Component

class Inspector(object):
  def __init__(self, id: int,  env: Environment, components: List[Component], buffers: List[Buffer], means: dict) -> None:
    super().__init__()
    self.id = id
    self.env = env
    self.buffers = buffers
    self.components = components
    self.means = means
    self.start = 0
    self.end = 0
    self.wait_time = []
    # self.inspection_time = []
    self.inspection_time = {component.name:list() for component in components}
    self.total_amount_inspected = {component.name:0 for component in components}


  def get_random_component(self) -> Component:
    '''Return a random component for the inspector to inspect'''
    return random.choice(self.components)
    self.start = self.env.now


  def get_inspection_time(self, component: Component) -> float:
    '''Get the inspection time for a specific component'''
    return random.expovariate(1 / self.means[component.name])
  
  
  def inspect_component(self) -> Generator:
    '''Retrieve a new component and inspect it'''
    # randomly select a component from within the list of inspectable components
    component = self.get_random_component()

    # Get inspection time
    inspection_time = self.get_inspection_time(component)

    # Add inspection time to list
    self.inspection_time[component.name].append(inspection_time)
    
    # inspect the component
    yield self.env.timeout(inspection_time)
    logging.debug('inspector {} inspected component {} at {}'.format(self.id, component.name, self.env.now))
    return component # Return the component so it can be placed in the correct buffer


  def add_component_to_buffer(self, component: Component) -> Generator:
    '''Add the component to the correct buffer'''
    # Routing policy for inspector 1
    # Inspector 1 exclusively handles component 1
    if component == Component.C1:
      # Find the buffer with the least number of components
      # So long as the inspector's buffer list is sorted by priority (highest first),
      # this will always favor the highest priority buffer in case of a tie.
      most_empty_buffer = self.buffers[0]
      for buffer in self.buffers:
        if buffer.level < most_empty_buffer.level:
          most_empty_buffer = buffer
      
      # Test if all the buffers are full
      if most_empty_buffer.level == most_empty_buffer.capacity:
        # Wait until at least one buffer is ready
        buffer_ready_events = [buffer.put(amount=1) for buffer in self.buffers]
        start_time = self.env.now
        result = yield self.env.any_of(buffer_ready_events)
        end_time = self.env.now
        
        # Add wait time to list
        self.wait_time.append(self.end - self.start)
        logging.debug('result of wait for inspector is {}, time={}'.format(result, end_time-start_time))

      # If buffer has space, add directly to that buffer
      else:
        self.start = self.env.now
        yield most_empty_buffer.put(amount=1)
        self.end = self.env.now

        # Add wait time to list
        self.wait_time.append(self.end - self.start)
    

    # Routing policy for inspector 2
    # Inspector 2 exclusively handles components C2 and C3 (only)
    else:
      # Create list of buffers that will accept a component
      buffer_list = list(filter(lambda x: (x.will_accept(component)), self.buffers))
      if len(buffer_list) > 0:
        self.start = self.env.now
        yield buffer_list[0].put(amount=1)
        self.end = self.env.now

        # Add wait time to list
        self.wait_time.append(self.end - self.start)
        logging.debug('inspector 2 put component {} in buffer {} at {}'.format(component.name, buffer_list[0].id, self.env.now))
    

    # At end, increment counter
    self.total_amount_inspected[component.name] += 1
  

  def main_loop(self) -> None:
    '''Main sequence loop for Inspector'''
    while True:
      component = yield self.env.process(self.inspect_component())
      yield self.env.process(self.add_component_to_buffer(component))
