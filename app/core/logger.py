import logging
from pythonjsonlogger import jsonlogger

def setup_logger(name="gamepulse"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Prevent adding handlers multiple times in dev
    if not logger.handlers:
        logHandler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(levelname)s %(name)s %(message)s'
        )
        logHandler.setFormatter(formatter)
        logger.addHandler(logHandler)
        
    return logger

logger = setup_logger()
