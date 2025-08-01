import re
import warnings
import importlib.resources as importlib_resources
from pathlib import Path
from functools import cache, singledispatch
from collections import defaultdict

from packaging.version import Version
from parfive import Results

import asdf

import dkist
from dkist.io.asdf.entry_points import get_extensions as get_dkist_extensions
from dkist.utils.exceptions import DKISTOutOfDateError, DKISTUserWarning

try:
    # first try to import from asdf.exceptions for asdf 2.15+
    from asdf.exceptions import ValidationError
except ImportError:
    # fall back to top level asdf for older versions of asdf
    from asdf import ValidationError


ASDF_FILENAME_PATTERN = re.compile(
    r"^(?P<instrument>[A-Z-]+)_L1_(?P<timestamp>\d{8}T\d{6})_(?P<datasetid>[A-Z]{5,})(?P<suffix>_user_tools|_metadata)?.asdf$"
)
DKIST_EXTENSION_REGEX = re.compile(r"asdf:\/\/dkist\.nso\.edu\/dkist\/extensions\/dkist-\d{1,}\.\d{1,}\.\d{1,}")


@singledispatch
def load_dataset(target, *, ignore_version_mismatch=False):
    """
    Load a DKIST dataset from a variety of inputs.

    This function loads one or more DKIST ASDF files into `dkist.Dataset` or
    `dkist.TiledDataset` classes. It can take a variety of inputs (listed below)
    and will either return a single object or a list of objects if multiple
    datasets are loaded.

    Parameters
    ----------
    target : {types}
        The location of one or more ASDF files.

        {types_list}

    Returns
    -------
    datasets
        An instance of `dkist.Dataset` or `dkist.TiledDataset` or a list thereof.

    Examples
    --------

    >>> import dkist

    >>> dkist.load_dataset("/path/to/VISP_L1_ABCDE.asdf")  # doctest: +SKIP

    >>> dkist.load_dataset("/path/to/ABCDE/")  # doctest: +SKIP

    >>> dkist.load_dataset(Path("/path/to/ABCDE"))  # doctest: +SKIP

    >>> from dkist.data.sample import VISP_BKPLX  # doctest: +REMOTE_DATA
    >>> print(dkist.load_dataset(VISP_BKPLX))  # doctest: +REMOTE_DATA
    This VISP Dataset consists of 1700 frames.
    Files are stored in ...VISP_BKPLX
    <BLANKLINE>
    This calibration has Dataset ID BKPLX.
    The unique identifier for the input observe frames (Product ID) is (no ProductID).
    <BLANKLINE>
    This Dataset has 4 pixel and 5 world dimensions.
    <BLANKLINE>
    The data are represented by a <class 'dask.array.core.Array'> object:
    dask.array<reshape, shape=(4, 425, 980, 2554), dtype=float64, chunksize=(1, 1, 980, 2554), chunktype=numpy.ndarray>
    <BLANKLINE>
    Array Dim  Axis Name                Data size  Bounds
            0  polarization state               4  None
            1  raster scan step number        425  None
            2  dispersion axis                980  None
            3  spatial along slit            2554  None
    <BLANKLINE>
    World Dim  Axis Name                  Physical Type                   Units
            4  stokes                     phys.polarization.stokes        unknown
            3  time                       time                            s
            2  helioprojective latitude   custom:pos.helioprojective.lat  arcsec
            1  wavelength                 em.wl                           nm
            0  helioprojective longitude  custom:pos.helioprojective.lon  arcsec
    <BLANKLINE>
    Correlation between pixel and world axes:
    <BLANKLINE>
                              |                      PIXEL DIMENSIONS
                              |   spatial    |  dispersion  | raster scan  | polarization
             WORLD DIMENSIONS |  along slit  |     axis     | step number  |    state
    ------------------------- | ------------ | ------------ | ------------ | ------------
    helioprojective longitude |      x       |              |      x       |
                   wavelength |              |      x       |              |
     helioprojective latitude |      x       |              |      x       |
                         time |              |              |      x       |
                       stokes |              |              |              |      x
    """
    known_types = _known_types_docs().keys()
    raise TypeError(f"Input type {type(target).__name__} not recognised. It must be one of {', '.join(known_types)}.")


@load_dataset.register
def _load_from_results(results: Results, *, ignore_version_mismatch=False):
    """
    The results from a call to ``Fido.fetch``, all results must be valid DKIST ASDF files.
    """
    return _load_from_iterable(results)


@load_dataset.register
def _load_from_iterable(iterable: tuple | list, *, ignore_version_mismatch=False):
    """
    A list or tuple of valid inputs to ``load_dataset``.
    """
    datasets = [load_dataset(item) for item in iterable]
    if len(datasets) == 1:
        return datasets[0]
    return datasets


@load_dataset.register
def _load_from_string(path: str, *, ignore_version_mismatch=False):
    """
    A string representing a directory or an ASDF file.
    """
    # TODO Adjust this to accept URLs as well
    return _load_from_path(Path(path))


@load_dataset.register
def _load_from_path(path: Path, *, ignore_version_mismatch=False):
    """
    A path object representing a directory or an ASDF file.
    """
    path = path.expanduser()
    if not path.is_dir():
        if not path.exists():
            raise ValueError(f"{path} does not exist.")
        return _load_from_asdf(path, ignore_version_mismatch=ignore_version_mismatch)

    return _load_from_directory(path, ignore_version_mismatch=ignore_version_mismatch)


def _load_from_directory(directory, *, ignore_version_mismatch=False):
    """
    Construct a `~dkist.dataset.Dataset` from a directory containing one (or
    more) ASDF files and a collection of FITS files.

    ASDF files have the generic pattern:

    ``{instrument}_L1_{start_time:%Y%m%dT%H%M%S}_{dataset_id}[_{suffix}].asdf``

    where the ``_{suffix}`` on the end may be absent or one of a few different
    suffixes which have been used at different times.  When searching a
    directory for one or more ASDF file to load we should attempt to only load
    one per dataset ID by selecting files in suffix order.

    The order of suffixes are (from newest used to oldest):

    - ``_metadata``
    - ``_user_tools``
    - None

    The algorithm used to find ASDF files to load in a directory is therefore:

    - Glob the directory for all ASDF files
    - Group all results by the filename up to and including the dataset id in the filename
    - Ignore any ASDF files with an old suffix if a new suffix is present
    - Throw a warning to the user if any ASDF files with older suffixes are found
    """
    base_path = Path(directory).expanduser()
    asdf_files = tuple(base_path.glob("*.asdf"))

    if not asdf_files:
        raise ValueError(f"No asdf file found in directory {base_path}.")

    if len(asdf_files) == 1:
        return _load_from_asdf(asdf_files[0], ignore_version_mismatch=ignore_version_mismatch)

    candidates = []
    asdfs_to_load = []
    for filepath in asdf_files:
        filename = filepath.name

        # If the asdf file doesn't match the data center pattern then we load it
        # as it's probably a custom user file
        if ASDF_FILENAME_PATTERN.match(filename) is None:
            asdfs_to_load.append(filepath)
            continue

        # All the matches have to be checked
        candidates.append(filepath)

    # If we only have one match load it
    if len(candidates) == 1:
        asdfs_to_load += candidates
    else:
        # Now we group by prefix
        matches = [ASDF_FILENAME_PATTERN.match(fp.name) for fp in candidates]
        grouped = defaultdict(list)
        for m in matches:
            prefix = m.string.removesuffix(".asdf").removesuffix(m.group("suffix") or "")
            grouped[prefix].append(m.group("suffix"))

        # Now we select the best suffix for each prefix
        for prefix, suffixes in grouped.items():
            if "_metadata" in suffixes:
                asdfs_to_load.append(base_path / f"{prefix}_metadata.asdf")
            elif "_user_tools" in suffixes:
                asdfs_to_load.append(base_path / f"{prefix}_user_tools.asdf")
            elif None in suffixes:
                asdfs_to_load.append(base_path / f"{prefix}.asdf")
            else:
                # This branch should never be hit because the regex enumerates the suffixes
                raise ValueError("Unknown suffix encountered.")  # pragma: no cover

    # Throw a warning if we have skipped any files
    if ignored_files := set(asdf_files).difference(asdfs_to_load):
        warnings.warn(
            f"ASDF files with old names ({', '.join([a.name for a in ignored_files])}) "
            "were found in this directory and ignored. You may want to delete these files.",
            DKISTUserWarning,
        )

    if len(asdfs_to_load) == 1:
        return _load_from_asdf(asdfs_to_load[0], ignore_version_mismatch=ignore_version_mismatch)

    return _load_from_iterable(asdfs_to_load, ignore_version_mismatch=ignore_version_mismatch)


def _load_from_asdf(filepath, *, ignore_version_mismatch=False):
    """
    Construct a dataset object from a filepath of a suitable asdf file.
    """
    from dkist.dataset import TiledDataset  # noqa: PLC0415

    filepath = Path(filepath).expanduser()
    base_path = filepath.parent
    try:
        with importlib_resources.as_file(
            importlib_resources.files("dkist.io") / "level_1_dataset_schema.yaml"
        ) as schema_path:
            with asdf.open(filepath, custom_schema=schema_path.as_posix(), lazy_load=False, memmap=False) as ff:
                if not ignore_version_mismatch:
                    _check_dkist_version(filepath, ff)
                ds = ff.tree["dataset"]
                ds.meta["history"] = ff.tree["history"]
                if isinstance(ds, TiledDataset):
                    for sub in ds.flat:
                        sub.files.basepath = base_path
                else:
                    ds.files.basepath = base_path
                return ds

    except ValidationError as e:
        err = f"This file is not a valid DKIST Level 1 asdf file, it fails validation with: {e.message}."
        raise TypeError(err) from e


@cache
def _get_dkist_uris():
    return [e.extension_uri for e in get_dkist_extensions()]


def _check_dkist_version(filepath, asdf_file):
    """
    Throw an error if the asdf versions are wrong.
    """
    matching_extensions = [
        ext
        for ext in asdf_file.tree["history"]["extensions"]
        if DKIST_EXTENSION_REGEX.match(ext.get("extension_uri", ""))
    ]

    if not matching_extensions or len(matching_extensions) > 1:
        dkist.log.info("Failed to validate dkist version used by asdf file {asdf_file}.")
        return

    dkist_uris = _get_dkist_uris()

    # If the extension URI is in the currently available extensions then we are ok
    if (dkist_ext_uri := matching_extensions[0]["extension_uri"]) in dkist_uris:
        return

    more_info_msg = (
        "\nFrom time to time metadata ASDF files provided by the DKIST data center need to require "
        "newer versions of the dkist library to support new instruments or new features.\n"
        "See https://docs.dkist.nso.edu/projects/python-tools/en/stable/howto_guides/asdf_version_requirements.html for more details."
    )

    current_version = Version(dkist.__version__)
    # This is the msg if we can't ascertain the dkist version used to write the file
    msg = (
        f"This file references a a version of the dkist ASDF extension {dkist_ext_uri} which is not available in "
        f"this version of the dkist package ({current_version}) you probably need to upgrade the dkist package."
    )
    if matching_extensions[0].get("software"):
        asdf_dkist_version = Version(matching_extensions[0]["software"]["version"])
        # If somehow we end up here and the version is newer, we will
        # return the generic message so as to not confuse people
        if current_version < asdf_dkist_version:
            msg = (
                f"The asdf file you are trying to read ({filepath}) was written with "
                f"dkist version {asdf_dkist_version} and you have {current_version} installed."
            )

    raise DKISTOutOfDateError(msg + more_info_msg)


def _known_types_docs():
    known_types = load_dataset.registry.copy()
    known_types.pop(object)
    known_types_docs = {}
    for t, func in known_types.items():
        name = t.__qualname__
        if t.__module__ != "builtins":
            name = f"{t.__module__}.{name}"
        known_types_docs[name] = func.__doc__.strip()
    return known_types_docs


def _formatted_types_docstring(known_types):
    lines = [f"| `{fqn}` - {doc}" for fqn, doc in known_types.items()]
    return "\n        ".join(lines)


load_dataset.__doc__ = load_dataset.__doc__.format(
    types_list=_formatted_types_docstring(_known_types_docs()),
    types=", ".join([f"`{t}`" for t in _known_types_docs().keys()]),
)
