import logging


def logger_setup(name: str = __name__) -> logging.Logger:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )

    logger = logging.getLogger(__name__)

    return logger
