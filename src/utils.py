import datetime
import logging
from logging.handlers import RotatingFileHandler
import os

class Logger:
    def __init__(self, nome="simulador_scada", pasta_logs="logs"):
        self.logger = logging.getLogger(nome)
        self.logger.setLevel(logging.DEBUG)

        # evita criar handlers duplicados
        if not self.logger.handlers:
            if not os.path.exists(pasta_logs):
                os.makedirs(pasta_logs)

            formato = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )

            # console
            console = logging.StreamHandler()
            console.setLevel(logging.DEBUG)
            console.setFormatter(formato)

            # arquivo
            data = datetime.date.today().strftime("%Y-%m-%d")
            arquivo = RotatingFileHandler(
                os.path.join(pasta_logs, f"{nome}_{data}.log"),
                maxBytes=5_000_000,
                backupCount=5
            )
            arquivo.setLevel(logging.DEBUG)
            arquivo.setFormatter(formato)

            self.logger.addHandler(console)
            self.logger.addHandler(arquivo)

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs)
    
    def exception(self, msg, *args, exc_info=True, **kwargs):
        self.logger.error(msg, *args, exc_info=exc_info, **kwargs)
