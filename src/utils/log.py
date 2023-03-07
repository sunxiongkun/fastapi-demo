import json
import logging
import logging.config
import logging.handlers
from traceback import format_exc, print_exc

from pythonjsonlogger import jsonlogger


class TracebackFormatExcFilter(logging.Filter):

    def filter(self, record):
        format_exc_str = format_exc()
        traceback_format_exc = json.dumps(format_exc_str)
        if isinstance(record.msg, dict):
            record.msg['traceback_format_exc'] = traceback_format_exc
        else:
            record.msg = '{} traceback_format_exc={}'.format(record.msg, traceback_format_exc)
        return True


def update_logging_config(config=None):
    default_format = "[%(levelname)s %(asctime)s %(msecs)s %(name)s:%(lineno)d] <%(process)d|%(threadName)s> %(message)s"
    default_level = 'INFO'
    default_formatter = 'json'
    config = config if config else {}
    level = config.get('level', default_level)
    formatter = config.get('formatter', default_formatter)

    level_config = {'': default_level}
    if isinstance(level, dict):
        for name, _level in level.items():
            _level = _level.upper()
            if name in ['', 'root']:
                level_config[''] = _level
            else:
                level_config[name] = _level
    elif isinstance(level, str):
        level_config[''] = level.upper()

    config['format'] = config.get('format', default_format)
    config['datefmt'] = config.get('datefmt', '%Y-%m-%dT%H:%M:%S%z')
    config['_logging_config'] = config.get('_logging_config', {})
    rename_fields = {"asctime": "time", "levelname": "level", "message": "msg", "process": "pid",
                     "threadName": "thread"}
    rename_fields.update(config.get('rename_fields', {}))

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "exclude_level": {
                "()": "pip._internal.utils.logging.MaxLevelFilter",
                "level": 40
            },
            "traceback_format_exc": {
                "()": TracebackFormatExcFilter,
            }
        },
        "formatters": {
            "str": {
                "class": "logging.Formatter",
                "format": config['format'],
                "datefmt": config['datefmt'],
            },
            "json": {
                "()": jsonlogger.JsonFormatter,
                "format": config['format'],
                "datefmt": config['datefmt'],
                "rename_fields": rename_fields,
                "json_ensure_ascii": False,
            },
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "pip._internal.utils.logging.ColorizedStreamHandler",
                "stream": "ext://sys.stdout",
                "filters": [
                    "exclude_level"
                ],
                "formatter": formatter
            },
            "console_errors": {
                "level": "ERROR",
                "filters": [
                    "traceback_format_exc"
                ],
                "class": "pip._internal.utils.logging.ColorizedStreamHandler",
                "stream": "ext://sys.stderr",
                "formatter": formatter
            }
        },
        "default_handlers": [
            "console",
            "console_errors"
        ],

    }
    loggers = {
        "": {
            "level": level_config.pop(''),
            "handlers": "cfg://default_handlers"
        },
    }
    for name, _level in level_config.items():
        loggers[name] = {
            'level': _level
        }
    logging_config['loggers'] = loggers

    logging_config.update(config['_logging_config'])
    logging.config.dictConfig(logging_config)
