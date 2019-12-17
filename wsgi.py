# Note! Current wsgi file was created for production. 
# During development can use run.py.
  
import sys, os

# To include the application's path in the Python search path
sys.path.insert(1, os.path.dirname(__file__))

from anagrammer import app as application

