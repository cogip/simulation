import logging
from pathlib import Path
import time


class GameRecordFileHandler(logging.handlers.RotatingFileHandler):
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
        if current_record_file.stat().st_size == 0:
            current_record_file.unlink()

        self.baseFilename = self.newBaseFilename()

        if self.backupCount > 0:
            record_files = sorted(self._root_dir.glob('*.log'))
            if len(record_files) > self.backupCount:
                for _ in range(len(record_files) - self.backupCount):
                    record_files.pop(0).unlink(missing_ok=True)

        if not self.delay:
            self.stream = self._open()
