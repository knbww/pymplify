"""Public exception hierarchy shared across independent packages."""


class PymplifyError(Exception):
    """Base class for errors deliberately raised by Pymplify."""


class ConfigurationError(PymplifyError, ValueError):
    """Input or options cannot be used; the caller can correct them."""


class MissingDependencyError(PymplifyError, ImportError):
    """A requested backend is absent from the environment."""


class BackendError(PymplifyError, RuntimeError):
    """An upstream operation failed; inspect __cause__ for its original error."""
