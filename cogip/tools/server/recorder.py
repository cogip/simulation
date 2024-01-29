import asyncio
import json
import logging
import os
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict

from cogip.utils.singleton import Singleton
from . import logger


class GameRecordFileHandler(RotatingFileHandler):
    """
    Log handler specific to the game recorder, using record filenames
    with timestamps defined at the creation of the log file.
    """
    def __init__(self, root_dir="/var/tmp/cogip", backupCount=20):
        """Class constructor"""
        self._root_dir = Path(root_dir).resolve()
        self._root_dir.mkdir(parents=True, exist_ok=True)
        super().__init__(
            filename=self.newBaseFilename(),
            mode='a', maxBytes=0, backupCount=backupCount, encoding=None, delay=False
        )

    def newBaseFilename(self) -> str:
        """
        Create a log filename based on current time.
        """
        current_time = int(time.time())
        time_tuple = time.localtime(current_time)
        return f"{self._root_dir}/game-{time.strftime('%Y-%m-%d_%H-%M-%S', time_tuple)}.log"

    def doRollover(self):
        """
        Create a new record file and clean-up old files.
        """
        if self.stream:
            self.stream.close()
            self.stream = None

        current_record_file = Path(self.baseFilename)
        if current_record_file.exists() and current_record_file.stat().st_size == 0:
            current_record_file.unlink()

        self.baseFilename = self.newBaseFilename()

        if self.backupCount > 0:
            record_files = sorted(self._root_dir.glob('*.log'))
            if len(record_files) > self.backupCount:
                for _ in range(len(record_files) - self.backupCount):
                    record_files.pop(0).unlink(missing_ok=True)

        if not self.delay:
            self.stream = self._open()


class GameRecorder(metaclass=Singleton):
    def __init__(self):
        self._game_recorder = logging.getLogger('GameRecorder')
        self._game_recorder.setLevel(logging.INFO)
        self._game_recorder.propagate = False
        self._loop = asyncio.get_running_loop()
        self._record_dir = os.environ.get("SERVER_RECORD_DIR", "/var/tmp/cogip")
        self._recording = False

        try:
            self._record_handler = GameRecordFileHandler(self._record_dir)
            self._game_recorder.addHandler(self._record_handler)
        except OSError:
            logger.warning(f"Failed to record games in directory '{self._record_dir}'")
            self._record_handler = None

    @property
    def recording(self) -> bool:
        return self._recording

    @recording.setter
    def recording(self, enabled: bool) -> None:
        self._recording = enabled

    def record(self, record: Dict[str, Any]) -> None:
        """
        Write a record in the current record file.
        Do it only the the robot the game has started.
        """
        if self._record_handler and self._recording:
            self._game_recorder.info(json.dumps(record))

    async def async_record(self, record: Dict[str, Any]) -> None:
        """
        Async version of [`record()`][cogip.tools.server.recorder.GameRecorder.record] .
        """
        await self._loop.run_in_executor(None, self.record, record)

    def do_rollover(self) -> None:
        """
        Switch to a new record file.
        """
        if self._record_handler:
            self._record_handler.doRollover()

    async def async_do_rollover(self) -> None:
        """
        Async version of [`record()`][cogip.tools.server.recorder.GameRecorder.do_rollover] .
        """
        await self._loop.run_in_executor(None, self._record_handler.doRollover)
