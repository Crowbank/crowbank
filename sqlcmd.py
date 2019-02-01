from pypa.env import Environment
import sys

cmd = sys.argv[1]

env = Environment('prod')

env.execute(cmd)