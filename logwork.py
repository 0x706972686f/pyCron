"""
MayDay - LogWork

Logwork is the function that tracks and logs any activities the workers
or MayDay writes.

It consists of two functions, a complex decorator (that can be added to a
function with @logwork), and a log_work function.

The decorater is incredibly useful for debugging, but hasn't been deployed.
If you use the decorater @logwork before a function, it'll record the 
input variables, the returned variables, and the time it took to run the function.

The log_work function simply records the text to the log file (that starts with MayDay_)

Changelog:
    2020-10-18  - Initial Version Created (v1 Alpha)

"""

import functools
import time
from loguru import logger

LOG_FILENAME = "MayDay_{time:YYYY-MM-DD}.log"
logger.add(LOG_FILENAME, format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}", rotation="1 days", retention="2 months", compression="zip", enqueue=True)
logger.remove(0)


def logwork(*, entry=True, exit=True, level="DEBUG"):
    def wrapper(func):
        name=func.__name__

        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            logger_ = logger.opt(depth=1)
            if entry:
                logger_.log(level, "Entering '{} (args={}, kwargs={})", name, args, kwargs)
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            logger.debug("Function '{}' executed in {:f} s", name, end-start)
            if exit:
                logger_.log(level, "Exiting '{} (result={})", name, result)
            return result
        return wrapped
    return wrapper


def log_work(data):
    logger.debug(data)