import time
from episia.core.utilities import EpiLoader

with EpiLoader("Testing loader", width=40):
    time.sleep(10)