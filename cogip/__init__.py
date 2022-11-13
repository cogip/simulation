import logging

from dotenv import load_dotenv, find_dotenv


# add devtools `debug` function to builtins
try:
    from devtools import debug
except ImportError:
    pass
else:
    __builtins__['debug'] = debug


load_dotenv(find_dotenv(), verbose=False)

logging.basicConfig(
    level=logging.INFO,  # logging.DEBUG
    format='[%(asctime)s][%(name)s][%(threadName)s] %(levelname)s: %(message)s')

logger = logging.getLogger(__name__)
