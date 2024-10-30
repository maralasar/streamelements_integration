import importlib
import logging
from urllib.parse import ParseResult

_logger = logging.getLogger(__name__)


def extend_url_path(url: ParseResult, *path):
    """A small function that expends the path of an url

    Args:
        url (ParseResult): The url to be adjusted
        *path: Additional elements that should be added to the url's path

    Returns:
        Adjusted url ("https://example.org" -> "https://example.org/awesome/path)

    Examples:
        >>> url = urllib.parse.urlparse("https://example.org")
        >>> extend_url_path(url, "awesome", "path")
        "https://example.org/awesome/path
    """
    if not isinstance(url, ParseResult):
        raise TypeError("url must be a ParseResult")
    for p in path:
        if not isinstance(p, str):
            raise TypeError("*path must be a str")

    extension = "/".join(path)
    return url._replace(path=url.path + f"/{extension}")


def factory(module_class_string, super_cls: type = None, **kwargs):
    """Import a single class from a module defined and instantiates the
    according class using kwargs

    Args:
        module_class_string: full name of the class to create an object of
        super_cls: expected super class for validity, None if bypass
        **kwargs: parameters to pass

    Returns: Instantiated class
    """
    module_name, class_name = module_class_string.rsplit(".", 1)
    module = importlib.import_module(module_name)
    assert hasattr(module, class_name), "class {} is not in {}".format(class_name, module_name)
    _logger.debug('reading class {} from module {}'.format(class_name, module_name))
    cls = getattr(module, class_name)
    if super_cls is not None:
        assert issubclass(cls, super_cls), f"class {class_name} should inherit from {super_cls.__name__}"
    _logger.debug(f'initialising {class_name} with params {kwargs}')
    obj = cls(**kwargs)
    return obj
