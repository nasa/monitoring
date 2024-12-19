import inspect
import os
from typing import Optional, Callable, Any
import logging
from monitoring.position_reporter.server import PositionReporter
from monitoring.monitorlib import auth

webapp = PositionReporter(__name__)


def import_environment_variable(
    var_name: str,
    required: bool = True,
    default: Optional[str] = None,
    mutator: Optional[Callable[[str], Any]] = None,
) -> None:
    """Import a value from a named environment variable into the webapp configuration.

    Args:
        var_name: Environment variable name (key).  Also used as the webapp configuration key for that variable.
        required: Whether the variable must be specified by the user.  If True, a ValueError will be raised if the
            variable is not specified by the user.  If False, the webapp configuration will not be populated if no
            default is provided.  If default is specified, the default value is treated as specification by the user.
        default: If the variable is not required, then use this value when it is not specified by the user.  The default
            value should be the string from the environment variable rather than the output of the mutator, if present.
        mutator: If specified, apply this function to the string value of the environment variable to obtain the
            variable to actually store in the configuration.
    """
    if var_name in os.environ:
        str_value = os.environ[var_name]
    elif default is not None:
        str_value = default
    elif required:
        stack = inspect.stack()
        raise ValueError(
            f"System cannot proceed because required environment variable '{var_name}' was not found.  Required from {stack[1].filename}:{stack[1].lineno}"
        )
    else:
        str_value = None

    if str_value is not None:
        webapp.config[var_name] = str_value if mutator is None else mutator(str_value)


def require_config_value(config_key: str) -> None:
    if config_key not in webapp.config:
        stack = inspect.stack()
        raise ValueError(
            f"System cannot proceed because required configuration key '{config_key}' was not found.  Required from {stack[1].filename}:{stack[1].lineno}"
        )


fmt = "%(asctime)s, %(filename)s:%(lineno)-4s | %(message)s"
datefmt = "%Y-%m-%d:%H:%M:%S"
# Configure the root logger
logging.basicConfig(format=fmt, datefmt=datefmt, level=logging.INFO)

AUTH_SPEC = "POS_REP_AUTH_SPEC"
import_environment_variable(AUTH_SPEC)
require_config_value(AUTH_SPEC)

msg = (
    "################################################################################\n"
    + "################################ Configuration  ################################\n"
    + "\n".join("## {}: {}".format(key, webapp.config[key]) for key in webapp.config)
    + "\n"
    + "################################################################################"
)
logging.info("Configuration:\n" + msg)

auth_client = auth.make_auth_adapter(webapp.config[AUTH_SPEC])


def get_auth_client():
    return auth_client


from monitoring.position_reporter import routes
