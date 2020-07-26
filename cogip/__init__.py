import logging


logging.basicConfig(
    level=logging.INFO,  # logging.DEBUG
    format='[%(asctime)s][%(name)s][%(threadName)s] %(levelname)s: %(message)s')

logger = logging.getLogger(__name__)
