"""A Python-based API for Using Renderbus cloud rendering service."""

from pkg_resources import DistributionNotFound, get_distribution

# Import local modules
from rayvision_houdini.constants import PACKAGE_NAME
from rayvision_log import init_logger

# Initialize the logger.
init_logger(PACKAGE_NAME)

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # Package is not installed.
    __version__ = '1.4.0'
