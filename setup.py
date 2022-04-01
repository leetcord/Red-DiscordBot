import os 
import sys 
from setuptools import setup 

if os .getenv ("TOX_BLUE",False )and sys .version_info >=(3 ,10 ):
# That's not fair!
    setup (python_requires =">=3.8.1")
else :
# No, it is I who have been trying my best.
    setup ()
