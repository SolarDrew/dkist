"""
Search attributes which are specific to the `dkist.net.DKISTClient`.

Other attributes provided by `sunpy.net.attrs` are supported by the client.
"""
from typing import Literal

import astropy.units as _u  # noqa: ICN001

import sunpy.net._attrs as _sunpy_attrs
from sunpy.coordinates.frames import Helioprojective as _Helioprojective
from sunpy.coordinates.utils import get_rectangle_coordinates as _get_rectangle_coordinates
from sunpy.net.attr import DataAttr as _DataAttr
from sunpy.net.attr import Range as _Range
from sunpy.net.attr import SimpleAttr as _SimpleAttr
from sunpy.net.attr import or_

__all__ = [
    "BoundingBox",
    "BrowseMovie",
    "Dataset",
    "EmbargoEndTime",
    "Embargoed",
    "Experiment",
    "ExposureTime",
    "FriedParameter",
    "HeaderVersion",
    "InstrumentProgramExecutionID",
    "ObservingProgramExecutionID",
    "Page",
    "PageSize",
    "PolarimetricAccuracy",
    "Product",
    "Proposal",
    "Recipe",
    "SpatialSampling",
    "SpectralSampling",
    "Status",
    "SummitSoftwareVersion",
    "TargetType",
    "TemporalSampling",
    "WorkflowName",
    "WorkflowVersion",
]


# SimpleAttrs

class PageSize(_SimpleAttr):
    """
    The number of search results to return.

    Parameters
    ----------
    page_size
    """
    def __init__(self, page_size: int):
        super().__init__(page_size)


class Page(_SimpleAttr):
    """
    The page of results to show

    Parameters
    ----------
    page
    """
    def __init__(self, page: int):
        super().__init__(page)


# datasetIds [array]
class Dataset(_SimpleAttr):
    """
    Unique identifier for a dataset.

    .. warning::

        Only datasets with a Status of "ACTIVE" are returned by
        default. If a Dataset is recalibrated, it will get a new
        Dataset ID and the old one will no longer be marked as
        "ACTIVE".
        To search for the latest calibration of your data search by
        `~dkist.net.attrs.Product` instead.  To search for a Dataset
        ID irrespective of its Status use ``a.dkist.Status("any")``.

    Parameters
    ----------
    dataset_id
        A random unique identifier for a dataset.
    """
    def __init__(self, dataset_id: str):
        super().__init__(dataset_id)


# primaryExperimentIds [array]
class Experiment(_SimpleAttr):
    """
    Unique identifier for a grouping of observations that meet the same scientific goal.

    .. note::

        One `~dkist.net.attrs.Proposal` can consist of many
        `~dkist.net.attrs.Experiment` which can consist of many products.

    Parameters
    ----------
    experiment_id
        A unique identifier for an experiment.
    """
    def __init__(self, experiment_id: str):
        super().__init__(experiment_id)


# primaryProposalIds [array]
class Proposal(_SimpleAttr):
    """
    Unique identifier for a proposal.

    .. note::

        One `~dkist.net.attrs.Proposal` can consist of many
        `~dkist.net.attrs.Experiment` which can consist of many products.

    Parameters
    ----------
    proposal_id
        A unique identifier for a proposal.
    """
    def __init__(self, proposal_id: str):
        super().__init__(proposal_id)


# targetTypes [array]
class TargetType(_SimpleAttr):
    """
    Name for the object observed by a dataset.

    Parameters
    ----------
    target_type
        A controlled string describing the target object.
    """
    def __init__(self, target_type: str):
        super().__init__(target_type)


# recipeId [array]
class Recipe(_SimpleAttr):
    """
    Unique identifier for a calibration pipeline.

    Parameters
    ----------
    recipe_id
        A unique identifier for the calibration pipeline.
    """
    def __init__(self, recipe_id: str):
        super().__init__(recipe_id)


# isEmbargoed
class Embargoed(_SimpleAttr):
    """
    Current embargo status of a dataset.

    Parameters
    ----------
    is_embargoed
        A boolean determining if a dataset currently under embargo.
    """
    def __init__(self, is_embargoed: bool):
        if isinstance(is_embargoed, str):
            if is_embargoed.lower() == "false":
                is_embargoed = False
            elif is_embargoed.lower() == "true":
                is_embargoed = True
            else:
                raise ValueError("is_embargoed must be either True or False")
        elif not isinstance(is_embargoed, bool):
            raise ValueError("is_embargoed must be either True or False")
        super().__init__(is_embargoed)


# Range Attrs


# qualityAverageFriedParameterMin, qualityAverageFriedParameterMax
class FriedParameter(_Range):
    """
    The average Fried parameter of a dataset.

    Parameters
    ----------
    friedmin
        The minimum value of the average fried parameter to search between.

    friedmax
        The maximum value of the average fried parameter to search between.
    """
    @_u.quantity_input
    def __init__(self, friedmin: _u.Quantity[_u.cm], friedmax: _u.Quantity[_u.cm]):
        super().__init__(friedmin, friedmax)

    def collides(self, other):
        return isinstance(other, self.__class__)


# qualityAveragePolarimetricAccuracyMin, qualityAverageFriedParameterMax
class PolarimetricAccuracy(_Range):
    """
    The average polarimetric accuracy of a dataset.
    """
    def collides(self, other):
        return isinstance(other, self.__class__)


# exposureTimeMin, exposureTimeMax
class ExposureTime(_Range):
    """
    Most common exposure time of the calibrated data frames within the dataset.

    Parameters
    ----------
    expmin
        The minimum exposure time.
    expmax
        The maximum exposure time.
    """
    @_u.quantity_input
    def __init__(self, expmin: _u.Quantity[_u.s], expmax: _u.Quantity[_u.s]):
        super().__init__(expmin, expmax)

    def collides(self, other):
        return isinstance(other, self.__class__)


# embargoEndDateMin, embargoEndDateMax
class EmbargoEndTime(_sunpy_attrs.Time):
    """
    The time at which an embargo on the dataset lapses.

    Parameters
    ----------
    start : time-like
        The start time in a format parseable by `~sunpy.time.parse_time` or
        a `sunpy.time.TimeRange` object.
    end : time-like
        The end time of the range.
    """
    def __init__(self, start, end=None):
        super().__init__(start, end)


# browseMovieUrl & browseMovieObjectKey
class BrowseMovie(_DataAttr):
    """
    The identifier for a browse move associated with a dataset.

    Parameters
    ----------
    movieurl
        The movieurl to match.
    movieobjectkey
        The movieobjectkey (filename) to match.
    """
    def __init__(self, *, movieurl: str = None, movieobjectkey: str = None):
        if movieurl is None and movieobjectkey is None:
            raise ValueError("Either movieurl or movieobjectkey must be specified")
        self.movieurl = movieurl
        self.movieobjectkey = movieobjectkey

    def collides(self, other):
        return isinstance(other, self.__class__)


# rectangleContainedByBoundingBox, rectangleContainingBoundingBox, rectangleIntersectingBoundingBox
class BoundingBox(_DataAttr):
    """
    The dataset bounding box in spatial coordinates.

    Parameters
    ----------
    bottom_left : `~astropy.coordinates.BaseCoordinateFrame` or `~astropy.coordinates.SkyCoord`
        The bottom-left coordinate of the rectangle.
        Supports passing both the bottom left and top right coordinates by passing with a shape of ``(2,)``.
    top_right : `~astropy.coordinates.BaseCoordinateFrame` or `~astropy.coordinates.SkyCoord`, optional
        The top-right coordinate of the rectangle.
        If in a different frame than ``bottom_left`` and all required metadata for frame conversion is present,
        ``top_right`` will be transformed to ``bottom_left`` frame.
    width : `~astropy.units.Quantity`, optional
        The width of the rectangle.
        Must be omitted if the coordinates of both corners have been specified.
    height : `~astropy.units.Quantity`, optional
        The height of the rectangle.
        Must be omitted if the coordinates of both corners have been specified.
    search : {"containing", "contained", "intersecting"}, optional
        The type of search to perform, defaults to ``"containing"``. A
        "containing" search, is where the specified search box fully contains
        the dataset bounding box, a "contained" search is where the specified
        search box is fully contained by the dataset bounding box and
        "intersecting" is where there is any intersection of the search and
        dataset boxes.

    Notes
    -----
    The dataset search is performed only with the latitude and longitude
    coordinate in helioprojective coordinates at the observatory at the time of
    the observation. This search API is not designed to provide the ability to
    search based on fully specified coordinate frames, however, if used
    correctly the SunPy coordinate transformations can be used to do limited
    searches in other frames.
    The coordinates specified to this search attribute are converted to a
    helioprojective frame with Earth as the observer
    (``sunpy.coordinates.Helioprojective(observer="earth")``).
    Therefore any input which is convertible to this frame is acceptable.
    However, it is important to consider how these coordinates will be
    interpreted. The coordinates will not be interpreted **at the time of the
    observation**, they will be interpreted as an inertial point in space at
    the time specified when passed to this function. This means that if you for
    instance pass a heliographic coordinate to this attribute for Jan 1st
    2020, but you search for a dataset on Jan 1st 2025, it will use the
    helioprojective coordinate equivalent to the heliographic coordinate passed
    as seen by an observer on Earth **on Jan 1st 2020**.
    """

    def __init__(self, bottom_left, *, top_right=None, width: _u.Quantity[_u.deg] = None,
                 height: _u.Quantity[_u.deg] = None, search: str = "containing"):
        bottom_left, top_right = _get_rectangle_coordinates(bottom_left,
                                                            top_right=top_right,
                                                            width=width, height=height)
        bottom_left = bottom_left.transform_to(_Helioprojective(observer="earth"))
        top_right = top_right.transform_to(_Helioprojective(observer="earth"))

        self.hpc_bounding_box_arcsec = ((float(bottom_left.Tx.to_value(_u.arcsec)),
                                         float(bottom_left.Ty.to_value(_u.arcsec))),
                                        (float(top_right.Tx.to_value(_u.arcsec)),
                                         float(top_right.Ty.to_value(_u.arcsec))))

        self.search_type = search

    def collides(self, other):
        return isinstance(other, self.__class__)

# averageDatasetSpectralSamplingMin, averageDatasetSpectralSamplingMax
class SpectralSampling(_Range):
    """
    The average spectral sampling of a dataset.

    Parameters
    ----------
    spectralmin
        The minimum value of the average spectral sampling to search between.

    spectralmax
        The maximum value of the average spectral sampling to search between.
    """
    @_u.quantity_input(equivalencies=_u.spectral())
    def __init__(self, spectralmin: _u.Quantity[_u.nm], spectralmax: _u.Quantity[_u.nm]):
        super().__init__(spectralmin, spectralmax)

    def collides(self, other):
        return isinstance(other, self.__class__)

# averageDatasetSpatialSamplingMin, averageDatasetSpatialSamplingMax
class SpatialSampling(_Range):
    """
    The average spatial sampling of a dataset.

    Parameters
    ----------
    spatialmin
        The minimum value of the average spatial sampling to search between.

    spatialmax
        The maximum value of the average spatial sampling to search between.
    """
    @_u.quantity_input
    def __init__(self, spatialmin: _u.Quantity[_u.arcsec/_u.pix], spatialmax: _u.Quantity[_u.arcsec/_u.pix]):
        super().__init__(spatialmin, spatialmax)

    def collides(self, other):
        return isinstance(other, self.__class__)


# averageDatasetTemporalSamplingMin, averageDatasetTemporalSamplingMax
class TemporalSampling(_Range):
    """
    The average temporal sampling of a dataset.

    Parameters
    ----------
    temporalmin
        The minimum value of the average temporal sampling to search between.

    temporalmax
        The maximum value of the average temporal sampling to search between.
    """
    @_u.quantity_input
    def __init__(self, temporalmin: _u.Quantity[_u.s], temporalmax: _u.Quantity[_u.s]):
        super().__init__(temporalmin, temporalmax)

    def collides(self, other):
        return isinstance(other, self.__class__)


# highLevelSoftwareVersion
class SummitSoftwareVersion(_SimpleAttr):
    """
    Version of the software used to record the data at the summit.

    Parameters
    ----------
    version
        Version of the software to search for.
    """
    def __init__(self, version: str):
        super().__init__(version)


# workflowName
class WorkflowName(_SimpleAttr):
    """
    Name of the calibration workflow used.

    Parameters
    ----------
    workflow_name
        Name of the workflow.
    """
    def __init__(self, workflow_name: str):
        super().__init__(workflow_name)


# workflowVersion
class WorkflowVersion(_SimpleAttr):
    """
    Version of the calibration workflow used.

    Parameters
    ----------
    workflow
        Version of the workflow.
    """
    def __init__(self, workflow: str):
        super().__init__(workflow)


# observingProgramExecutionId
class ObservingProgramExecutionID(_SimpleAttr):
    """
    Execution ID of the Observing Program.

    Parameters
    ----------
    obs_program
    """
    def __init__(self, obs_program: str):
        super().__init__(obs_program)


# instrumentProgramExecutionId
class InstrumentProgramExecutionID(_SimpleAttr):
    """
    Execution ID of the Instrument Program

    Parameters
    ----------
    instr_program
    """
    def __init__(self, instr_program: str):
        super().__init__(instr_program)


# headerVersion
class HeaderVersion(_SimpleAttr):
    """
    Header Specification Version

    Parameters
    ----------
    version
    """
    def __init__(self, version: str):
        super().__init__(version)


#productIds
class Product(_SimpleAttr):
    """
    Unique identifier for a set of science frames

    The Product ID identifies a unique set of data over multiple
    recalibrations.  When data is recalibrated it will get a new
    Dataset ID, but the Product ID will remain the same.

    Parameters
    ----------
    product_id
        A unique identifier for a product.
    """
    def __init__(self, product_id: str):
        super().__init__(product_id)


#status
class Status(_SimpleAttr):
    """
    Dataset Status

    Parameters
    ----------
    status
        The status of the dataset, can be one of ``ACTIVE``,
        ``DEPRECATED`` or ``REMOVED`` or ``any`` to search for all three.
    """
    def __new__(cls, status: Literal["ACTIVE", "DEPRECATED", "REMOVED", "any"]):
        if status == "any":
            return or_(*map(Status, ["ACTIVE", "DEPRECATED", "REMOVED"]))
        return super().__new__(cls, status)

    def __init__(self, status: Literal["ACTIVE", "DEPRECATED", "REMOVED"]):
        super().__init__(status)
