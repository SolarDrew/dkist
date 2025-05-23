from pathlib import Path

import dask.array as da
import numpy as np
import pytest
from numpy.testing import assert_allclose

from dkist.data.test import rootdir
from dkist.io.dask.striped_array import FileManager, StripedExternalArray, StripedExternalArrayView

eitdir = Path(rootdir) / "EIT"


@pytest.fixture
def file_manager(eit_dataset):
    """
    A file manager
    """
    return eit_dataset.files._fm


@pytest.fixture
def loader_array(file_manager):
    """
    An array of external array references.
    """
    return file_manager._striped_external_array.loader_array


def test_load_and_slicing(file_manager, loader_array):
    ext_shape = np.array(loader_array, dtype=object).shape
    assert file_manager._striped_external_array.loader_array.shape == ext_shape
    assert file_manager.output_shape == (*list(ext_shape), 128, 128)

    array = file_manager._generate_array().compute()
    assert isinstance(array, np.ndarray)
    # Validate the data is actually loaded from the FITS
    assert not np.isnan(array).all()

    sliced_manager = file_manager[5:8]
    ext_shape = np.array(loader_array[5:8], dtype=object).shape
    assert sliced_manager._striped_external_array.loader_array.shape == ext_shape
    assert sliced_manager.output_shape == (*list(ext_shape), 128, 128)


def test_filenames(file_manager, loader_array):
    assert len(file_manager.filenames) == len(loader_array)
    assert (file_manager.filenames == file_manager._striped_external_array.fileuri_array.flatten()).all()


def test_dask(file_manager, loader_array):
    ext_shape = np.array(loader_array, dtype=object).shape
    assert file_manager._striped_external_array.loader_array.shape == ext_shape
    assert file_manager.output_shape == (*list(ext_shape), 128, 128)

    assert isinstance(file_manager._generate_array(), da.Array)
    assert_allclose(file_manager._generate_array(), np.array(file_manager._generate_array()))


def test_collection_getitem(tmpdir, file_manager):
    assert isinstance(file_manager._striped_external_array, StripedExternalArray)
    assert isinstance(file_manager[0], FileManager)
    assert isinstance(file_manager[0]._striped_external_array, StripedExternalArrayView)
    assert isinstance(file_manager[1], FileManager)
    assert isinstance(file_manager[1]._striped_external_array, StripedExternalArrayView)
    assert len(file_manager[0]._striped_external_array) == len(file_manager[1]._striped_external_array) == 1


def test_basepath_change(file_manager):
    file_manager.basepath = None
    array = file_manager._generate_array()
    assert np.isnan(array).all()
    file_manager.basepath = eitdir
    assert not np.isnan(array).any()


def test_sliced_basepath_change(file_manager):
    file_manager.basepath = None
    array = file_manager._generate_array()
    assert np.isnan(array).all()

    sub_array = array[3:4]
    file_manager.basepath = eitdir
    assert not np.isnan(sub_array).any()
    assert not np.isnan(array).any()


def test_file_manager_cube_slice(eit_dataset):
    """
    Slice the cube and then see that the file manager is a new instance sharing the same base path.
    """
    ds = eit_dataset
    assert ds.files is not None

    sds = ds[5:7]

    # Check that we haven't made a copy
    assert ds.files is not sds.files

    # Assert that we have copied the value of basepath
    assert ds.files.basepath == sds.files.basepath

    sds = ds[0]

    # Check that we haven't made a copy
    assert ds.files is not sds.files

    # Assert that we have copied the value of basepath
    assert ds.files.basepath == sds.files.basepath

    # TODO: Decide on the desired behaviour here.
    ## Running sds.download() here would affect the parent cubes data, because
    ## the base paths are the same.

    # If we set a new basepath on the parent cube the sub-cube shouldn't update
    # ds.files.basepath = "test1"
    # assert ds.files.basepath != sds.files.basepath

    ## Running ds.download() or sds.download() here wouldn't affect the other
    ## one now as the base paths have diverged.

    # Correspondingly changing the base path on the sub cube shouldn't change the parent cube
    # sds.files.basepath = "test2"
    # assert ds.files.basepath == Path("test1")


def test_file_manager_direct_slice(eit_dataset):
    """
    Assert that slicing the file_manager directly doesn't create a copy.
    """
    ds = eit_dataset
    assert ds.files is not None

    sub_file = ds.files[5]

    # Demonstrate that any operation on a directly sliced file manager also
    # affect the parent object.
    assert sub_file.basepath == ds.files.basepath

    ds.files.basepath = "test1"
    assert sub_file.basepath == ds.files.basepath

    sub_file.basepath = "test2"
    assert sub_file.basepath == ds.files.basepath


def test_reprs(file_manager):
    assert str(len(file_manager)) in repr(file_manager)
    assert str(file_manager.shape) in repr(file_manager)

    sea = file_manager._striped_external_array
    assert str(len(sea)) in repr(sea)
    assert str(sea.shape) in repr(sea)

    sliced_file_manager = file_manager[4:6]
    sliced_sea = sliced_file_manager._striped_external_array
    assert str(len(sliced_sea)) in repr(sliced_sea)
    assert str(sliced_sea.shape) in repr(sliced_sea)
    assert str(sea) in repr(sliced_sea)
