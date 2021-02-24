import configparser
import json
import os

from pkg_resources import resource_filename
from pyramid.settings import aslist
from pyramid.static import static_view


class _CachedFile:
    """
    Parses content from a file and caches the result.

    _CachedFile reads a file at a given path and parses the content using a
    provided loader.
    """

    def __init__(self, path, loader, auto_reload=False):
        """
        Create the CachedFile object.

        :param path: The path to the file to load.
        :param loader: A callable that will be passed the file object and
                       should return the parsed content.
        :param auto_reload: If True, the parsed content is discarded if the
                            mtime of the file changes.
        """

        self.path = self._find_file(path)
        self.loader = loader
        self._mtime = None
        self._cached = None
        self._auto_reload = auto_reload

    @classmethod
    def _find_file(cls, path):
        path = os.path.abspath(os.path.join(resource_filename("lms", "."), "..", path))

        if not os.path.isfile(path):
            raise FileNotFoundError(f"Expected to find a file at '{path}'")

        return path

    def load(self):
        """
        Return the current content of the file parsed with the loader.

        The file is loaded using the provided loader when this is called the
        first time or if auto-reload is enabled and the file changed since the
        last call to ``load()``.
        """
        if self._mtime and not self._auto_reload:
            return self._cached

        current_mtime = os.path.getmtime(self.path)
        if not self._mtime or self._mtime < current_mtime:  # pragma: no cover
            with open(self.path) as handle:
                self._cached = self.loader(handle)
                self._mtime = current_mtime
        return self._cached


class Environment:
    """
    Environment for generating URLs for Hypothesis' static assets.

    Static assets are grouped into named bundles, defined in an ini-format
    config file. The relative URL that should be used when serving a file from
    a bundle is defined in a JSON manifest file, which is generated by the
    static asset build pipeline.

    Environment reads the set of bundles from the config file
    and the mapping between the file path and the output URL
    from a JSON manifest file and provides the ability to retrieve the final
    URLs for a bundle via the urls() method.
    """

    def __init__(
        self, assets_base_url, bundle_config_path, manifest_path, auto_reload=False
    ):  # pragma: no cover
        """
        Construct an Environment from the given configuration files.

        :param assets_base_url: The URL at which assets will be served,
                                excluding the trailing slash.
        :param bundle_config_path: Asset bundles config file.
        :param manifest_path: JSON file mapping file paths in the bundle config
                              file to cache-busted URLs.
        :param auto_reload: If True the config and manifest files are
                            automatically reloaded if they change.
        """
        self.assets_base_url = assets_base_url
        self.manifest = _CachedFile(manifest_path, json.load, auto_reload=auto_reload)
        self.bundles = _CachedFile(
            bundle_config_path, _load_bundles, auto_reload=auto_reload
        )

    def files(self, bundle):  # pragma: no cover
        """Return the file paths for all files in a bundle."""
        bundles = self.bundles.load()
        return bundles[bundle]

    def urls(self, bundle):  # pragma: no cover
        """
        Return asset URLs for all files in a bundle.

        Returns the URLs at which all files in a bundle are served,
        read from the asset manifest.
        """
        bundles = self.bundles.load()

        return [self.url(path) for path in bundles[bundle]]

    def url(self, path):  # pragma: no cover
        """Return the cache-busted URL for an asset with a given path."""
        manifest = self.manifest.load()
        return "{}/{}".format(self.assets_base_url, manifest[path])


def _add_cors_header(wrapped):
    def wrapper(context, request):  # pragma: no cover
        # Add a CORS header to the response because static assets from
        # the sidebar are loaded into pages served by a different origin:
        # The domain hosting the page into which the sidebar has been injected
        # or embedded.
        #
        # Some browsers enforce cross-origin restrictions on certain types of
        # resources, eg. Firefox enforces same-domain policy for @font-face
        # unless a CORS header is provided.
        response = wrapped(context, request)
        response.headers.extend({"Access-Control-Allow-Origin": "*"})
        return response

    return wrapper


def _load_bundles(file_):  # pragma: no cover
    """Read an asset bundle config from a file object."""
    parser = configparser.ConfigParser()
    parser.read_file(file_)
    return {k: aslist(v) for k, v in parser.items("bundles")}


# Site assets
ASSETS_VIEW = _add_cors_header(
    static_view("lms:../build", cache_max_age=None, use_subpath=True)
)


def includeme(config):  # pragma: no cover
    config.add_view(route_name="assets", view=ASSETS_VIEW)

    assets_env = Environment(
        "/assets", "lms/assets.ini", "build/manifest.json", auto_reload=False
    )

    # We store the environment objects on the registry so that the Jinja2
    # integration can be configured in app.py
    config.registry["assets_env"] = assets_env
