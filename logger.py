import logging
from logging.handlers import TimedRotatingFileHandler


class LoggerConfigurator:
    def __init__(self, log_file, when='midnight', interval=1, backup_count=7, log_level=logging.WARNING):
        self.log_file = log_file
        self.when = when
        self.interval = interval
        self.backup_count = backup_count
        self.log_level = log_level

    def configure(self):
        logger = logging.getLogger()
        logger.setLevel(self.log_level)

        handler = TimedRotatingFileHandler(
            self.log_file, when=self.when, interval=self.interval, backupCount=self.backup_count, encoding='utf-8')

        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        logger.addHandler(handler)
