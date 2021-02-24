import random
from typing import Union

import simpy
from simpy import Container, Environment

from .component import Component


class Buffer(Container):
  def __init__(self, id: str, env: Environment, accepts: Component, capacity: Union[int, float], init: Union[int, float]=0):
    super().__init__(env=env, capacity=capacity, init=init)
    self.id = id
    self.accepts = accepts
  
  
  def will_accept(self, component: Component) -> bool:
    '''Test if this buffer will accept a certain component type'''
    if component == self.accepts:
      return True
    else:
      return False
  


