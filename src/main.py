import random
from typing import List

import simpy

from models import Buffer, Component, Inspector, Workstation

# Control constants
SEED = 12345
BUFFER_SIZE = 2
SIM_TIME = 100


if __name__ == '__main__':
  # Set up random generation
  random.seed(SEED)

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
  w1 = Workstation(id=1, env=main_env, buffers=[b1c1])
  w2 = Workstation(id=2, env=main_env, buffers=[b2c1, b2c2])
  w3 = Workstation(id=3, env=main_env, buffers=[b3c1, b3c3])

  workstation_list: List[Workstation] = [w1, w2, w3]

  # Init inspectors
  inspector_one = Inspector(id=1, env=main_env, components=[Component.C1], buffers=[b1c1, b2c1, b3c1])
  inspector_two = Inspector(id=2, env=main_env, components=[Component.C2, Component.C3], buffers=[b2c2, b3c3])

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
