import logging

from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv(), verbose=False)

logging.basicConfig(
    level=logging.INFO,  # logging.DEBUG
    format='[%(asctime)s][%(name)s][%(threadName)s] %(levelname)s: %(message)s')

logger = logging.getLogger(__name__)
