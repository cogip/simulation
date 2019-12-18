import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s][%(name)s][%(threadName)s] %(levelname)s: %(message)s')

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
# ch = logging.StreamHandler()
# ch.setLevel(logging.INFO)
# formatter = logging.Formatter('[%(asctime)s][%(name)s][%(threadName)s] %(levelname)s: %(message)s')
# ch.setFormatter(formatter)
# logger.addHandler(ch)

logger.info("START")
