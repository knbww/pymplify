"""Public exception hierarchy shared across independent packages."""


class PymplifyError(Exception):
    """Base class for errors deliberately raised by Pymplify."""


class ConfigurationError(PymplifyError, ValueError):
    """Input or options cannot be used; the caller can correct them."""


class MissingDependencyError(PymplifyError, ImportError):
    """A requested backend is absent from the environment."""


class BackendError(PymplifyError, RuntimeError):
    """An upstream operation failed; inspect __cause__ for its original error."""


class AdapterNotFoundError(PymplifyError, LookupError):
    """The requested adapter is not registered in this catalog."""


class OperationNotFoundError(PymplifyError, LookupError):
    """An adapter does not provide the requested operation."""


class AdapterLoadError(PymplifyError, ImportError):
    """An installed adapter entry point could not be loaded or validated."""
