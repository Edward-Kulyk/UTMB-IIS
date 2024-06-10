from functools import wraps

from flask import request

from src.utils.logger.exception_logger import logger


def log_request(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        ip = request.remote_addr
        data = request.get_json() if request.is_json else request.form.to_dict()
        logger.info(f"Request from {ip} with data: {data}")
        return func(*args, **kwargs)

    return wrapper
