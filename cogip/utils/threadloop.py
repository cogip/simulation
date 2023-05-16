import logging
import threading
import time


class ThreadLoop:
    """
    This class creates a thread to execute a function in loop and wait after
    the function until the defined loop interval is reached.
    A warning is emitted if the function duration is longer than the loop
    interval.
    """
    def __init__(self, name: str, interval: float, func, logger=False, args=None, kwargs=None):
        """
        Class constructor.

        Arguments:
            name: Name to identify the thread in the logs
            interval: time between each iteration of the loop, in seconds
            func: function to execute in the loop
            logger: an optional custom logger
            args: arguments of the function
            kwargs: named arguments of the function
        """
        self._name = name
        self._interval = interval
        self._func = func
        self._args = args or []
        self._kwargs = kwargs or {}
        self._thread = threading.Thread(target=self.repeat)
        self._cancel = False
        self._logger = logging.getLogger(f"ThreadLoop: {name}")

        if not isinstance(logger, bool):
            self._logger = logger
        else:
            if self._logger.level == logging.NOTSET:
                if logger:
                    self._logger.setLevel(logging.INFO)
                else:
                    self._logger.setLevel(logging.ERROR)
                self._logger.addHandler(logging.StreamHandler())

    @property
    def interval(self) -> float:
        return self._interval

    @interval.setter
    def interval(self, value: float) -> None:
        self._interval = value

    def repeat(self) -> None:
        """
        Loop function executed in the thread.
        """
        while not self._cancel:
            start = time.time()
            self._func(*self._args, **self._kwargs)
            now = time.time()
            duration = now - start
            if duration > self._interval:
                self._logger.warning(f"Function too long: {duration} > {self._interval}")
            else:
                wait = self._interval - duration
                time.sleep(wait)

    def start(self) -> None:
        """
        Start the thread loop.
        """
        if self._thread.is_alive():
            self._logger.warning(f"Already {'canceled' if self._cancel else 'running'}")
            return
        if self._cancel:
            self._thread = threading.Thread(target=self.repeat)
            self._cancel = False
        self._thread.start()

    def stop(self) -> None:
        """
        Stop the thread loop.
        """
        self._logger.debug("Stopping...")
        if self._thread.is_alive():
            self._cancel = True
            try:
                self._thread.join()
            except KeyboardInterrupt:
                pass
            self._logger.debug("Stopped.")
