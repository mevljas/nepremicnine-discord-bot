"""Module that logging logic."""

import logging
import logging.handlers
import re
import sys
from enum import Enum

import urllib3


class ColorCodes(Enum):
    """
    ANSI escape codes for colors.
    """

    GREY = "\x1b[38;21m"
    GREEN = "\x1b[1;32m"
    YELLOW = "\x1b[33;21m"
    RED = "\x1b[31;21m"
    BOLD_RED = "\x1b[31;1m"
    BLUE = "\x1b[1;34m"
    LIGHT_BLUE = "\x1b[1;36m"
    PURPLE = "\x1b[1;35m"
    RESET = "\x1b[0m"


class ColorizedArgsFormatter(logging.Formatter):
    """
    A formatter that colorizes log messages based on log level.
    """

    arg_colors = [ColorCodes.PURPLE, ColorCodes.LIGHT_BLUE]
    level_fields = ["levelname", "levelno"]
    level_to_color = {
        logging.DEBUG: ColorCodes.GREY,
        logging.INFO: ColorCodes.GREEN,
        logging.WARNING: ColorCodes.YELLOW,
        logging.ERROR: ColorCodes.RED,
        logging.CRITICAL: ColorCodes.BOLD_RED,
    }

    def __init__(self, fmt: str):
        super().__init__()
        self.level_to_formatter = {}

        def add_color_format(level: int):
            color = ColorizedArgsFormatter.level_to_color[level].value
            _format = fmt
            for fld in ColorizedArgsFormatter.level_fields:
                search = r"(%\(" + fld + r"\).*?s)"
                _format = re.sub(search, f"{color}\\1{ColorCodes.RESET.value}", _format)
            formatter = logging.Formatter(_format)
            self.level_to_formatter[level] = formatter

        add_color_format(logging.DEBUG)
        add_color_format(logging.INFO)
        add_color_format(logging.WARNING)
        add_color_format(logging.ERROR)
        add_color_format(logging.CRITICAL)

    @staticmethod
    def rewrite_record(record: logging.LogRecord):
        """

        :param record: Log record
        :return:
        """
        if not BraceFormatStyleFormatter.is_brace_format_style(record):
            return

        msg = record.msg
        msg = msg.replace("{", "_{{")
        msg = msg.replace("}", "_}}")
        placeholder_count = 0
        # add ANSI escape code for next alternating color before each formatting parameter
        # and reset color after it.
        while True:
            if "_{{" not in msg:
                break
            color_index = placeholder_count % len(ColorizedArgsFormatter.arg_colors)
            color = ColorizedArgsFormatter.arg_colors[color_index]
            msg = msg.replace("_{{", color + "{", 1)
            msg = msg.replace("_}}", "}" + ColorCodes.RESET.value, 1)
            placeholder_count += 1

        record.msg = msg.format(*record.args)
        record.args = []

    def format(self, record):
        orig_msg = record.msg
        orig_args = record.args
        formatter = self.level_to_formatter.get(record.levelno)
        self.rewrite_record(record)
        formatted = formatter.format(record)
        record.msg = orig_msg
        record.args = orig_args
        return formatted


class BraceFormatStyleFormatter(logging.Formatter):
    """
    A formatter that supports brace format style for log
    """

    def __init__(self, fmt: str):
        super().__init__()
        self.formatter = logging.Formatter(fmt)

    @staticmethod
    def is_brace_format_style(record: logging.LogRecord):
        """
        Check if the log record is in brace format style
        :param record: Log record
        :return:
        """
        if len(record.args) == 0:
            return False

        msg = record.msg
        if "%" in msg:
            return False

        count_of_start_param = msg.count("{")
        count_of_end_param = msg.count("}")

        if count_of_start_param != count_of_end_param:
            return False

        if count_of_start_param != len(record.args):
            return False

        return True

    @staticmethod
    def rewrite_record(record: logging.LogRecord):
        """Rewrite log record to support brace format style."""
        if not BraceFormatStyleFormatter.is_brace_format_style(record):
            return

        record.msg = record.msg.format(*record.args)
        record.args = []

    def format(self, record):
        orig_msg = record.msg
        orig_args = record.args
        self.rewrite_record(record)
        formatted = self.formatter.format(record)

        # restore log record to original state for other handlers
        record.msg = orig_msg
        record.args = orig_args
        return formatted


def init_logging():
    """
    Initializes logging.
    :return:
    """
    level = logging.INFO
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    console_level = "INFO"
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setLevel(console_level)
    console_format = "[%(asctime)s %(threadName)s %(levelname)s] %(message)s"
    colored_formatter = ColorizedArgsFormatter(console_format)
    console_handler.setFormatter(colored_formatter)
    root_logger.addHandler(console_handler)

    # file_handler = logging.FileHandler(filename="app.log", encoding="utf-8", mode="w")
    # file_level = "DEBUG"
    # file_handler.setLevel(file_level)
    # file_format = "[%(asctime)s %(threadName)s, %(levelname)s] %(message)s"
    # file_handler.setFormatter(BraceFormatStyleFormatter(file_format))
    # root_logger.addHandler(file_handler)
    logging.basicConfig(level=level, format=console_format)


init_logging()
logger = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
