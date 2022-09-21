import logging


logger = logging.getLogger(__name__)


def handle_error(msg, exception=True):
    if exception:
        raise RuntimeError(msg)
    else:
        logger.info(msg)
