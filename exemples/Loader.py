import time
from epitools.core.utilities import EpiLoader

with EpiLoader("Testing loader", width=40):
    time.sleep(10)