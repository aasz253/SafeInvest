import sys
import os

os.chdir(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.main import app
from mangum import Mangum

handler = Mangum(app, lifespan="auto")
