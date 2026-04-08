class EapiConfigError(ValueError):
    """Raised when a Nornir host cannot be mapped to eAPI settings.

    Subclass of ValueError so callers may catch broadly with ValueError
    or narrowly with EapiConfigError.
    """
