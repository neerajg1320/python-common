from jsonschema import validate
from jsonschema.exceptions import ValidationError
import logging


logger = logging.getLogger(__name__)


def validate_with_schema(json, schema):
    is_valid = True
    try:
        validate(json, schema)
    except ValidationError as error:
        logger.info(error)
        is_valid = False
    return is_valid
