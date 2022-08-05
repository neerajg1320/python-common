import base64
import logging


logger = logging.getLogger(__name__)


def encode_base64_bytes(input_bytes, debug=False):
    if debug:
        logger.info("type(input_bytes)={} input_bytes={}".format(type(input_bytes), input_bytes))

    message_encoded = base64.b64encode(input_bytes)

    if debug:
        logger.info("message_encoded={}".format(message_encoded))

    return message_encoded


def decode_base64_bytes(input_base64_bytes, debug=False):
    if debug:
        logger.info("type(input_base64_bytes)={} input_base64_bytes={}".format(type(input_base64_bytes), input_base64_bytes))

    message_decoded = base64.b64decode(input_base64_bytes)

    if debug:
        logger.info("message_decoded={}".format(message_decoded))

    return message_decoded
