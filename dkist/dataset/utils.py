"""
Helper functions for the Dataset class.
"""

import numpy as np

import gwcs

__all__ = ["dataset_info_str"]


def dataset_info_str(ds):
    # Check for an attribute that only appears on TiledDataset
    # Not using isinstance to avoid circular import
    is_tiled = hasattr(ds, "combined_headers")
    dstype = type(ds).__name__
    if is_tiled:
        tile_shape = ds.shape
        ds = ds[0, 0]
    wcs = ds.wcs.low_level_wcs

    # Array dimensions table

    instr = ds.inventory.get("instrument", "")
    if instr:
        instr += " "

    if is_tiled:
        s = f"This {dstype} consists of an array of {tile_shape} Dataset objects\n\n"
        s += f"Each {instr}Dataset has {wcs.pixel_n_dim} pixel and {wcs.world_n_dim} world dimensions\n\n"
    else:
        s = f"This {instr}Dataset has {wcs.pixel_n_dim} pixel and {wcs.world_n_dim} world dimensions\n\n"
    s += f"{ds.data}\n\n"

    array_shape = wcs.array_shape or (0,)
    pixel_shape = wcs.pixel_shape or (None,) * wcs.pixel_n_dim

    # Find largest between header size and value length
    if hasattr(wcs, "pixel_axis_names"):
        pixel_axis_names = wcs.pixel_axis_names
    elif isinstance(wcs, gwcs.WCS):
        pixel_axis_names = wcs.input_frame.axes_names
    else:
        pixel_axis_names = [""] * wcs.pixel_n_dim

    pixel_dim_width = max(9, len(str(wcs.pixel_n_dim)))
    pixel_nam_width = max(9, max(len(x) for x in pixel_axis_names))
    pixel_siz_width = max(9, len(str(max(array_shape))))

    s += (("{0:" + str(pixel_dim_width) + "s}").format("Array Dim") + "  " +
            ("{0:" + str(pixel_nam_width) + "s}").format("Axis Name") + "  " +
            ("{0:" + str(pixel_siz_width) + "s}").format("Data size") + "  " +
            "Bounds\n")

    for ipix in range(ds.wcs.pixel_n_dim):
        s += (("{0:" + str(pixel_dim_width) + "d}").format(ipix) + "  " +
                ("{0:" + str(pixel_nam_width) + "s}").format(pixel_axis_names[::-1][ipix] or "None") + "  " +
                (" " * 5 + str(None) if pixel_shape[::-1][ipix] is None else
                ("{0:" + str(pixel_siz_width) + "d}").format(pixel_shape[::-1][ipix])) + "  " +
                "{:s}".format(str(None if wcs.pixel_bounds is None else wcs.pixel_bounds[::-1][ipix]) + "\n"))
    s += "\n"

    # World dimensions table

    # Find largest between header size and value length
    world_dim_width = max(9, len(str(wcs.world_n_dim)))
    world_nam_width = max(9, max(len(x) if x is not None else 0 for x in wcs.world_axis_names))
    world_typ_width = max(13, max(len(x) if x is not None else 0 for x in wcs.world_axis_physical_types))

    s += (("{0:" + str(world_dim_width) + "s}").format("World Dim") + "  " +
            ("{0:" + str(world_nam_width) + "s}").format("Axis Name") + "  " +
            ("{0:" + str(world_typ_width) + "s}").format("Physical Type") + "  " +
            "Units\n")

    for iwrl in range(wcs.world_n_dim):

        name = wcs.world_axis_names[::-1][iwrl] or "None"
        typ = wcs.world_axis_physical_types[::-1][iwrl] or "None"
        unit = wcs.world_axis_units[::-1][iwrl] or "unknown"

        s += (("{0:" + str(world_dim_width) + "d}").format(iwrl) + "  " +
                ("{0:" + str(world_nam_width) + "s}").format(name) + "  " +
                ("{0:" + str(world_typ_width) + "s}").format(typ) + "  " +
                "{:s}".format(unit + "\n"))

    s += "\n"

    # Axis correlation matrix

    pixel_dim_width = max(3, len(str(wcs.world_n_dim)))

    s += "Correlation between array and world axes:\n\n"

    s += _get_pp_matrix(ds.wcs)

    # Make sure we get rid of the extra whitespace at the end of some lines
    return "\n".join([line.rstrip() for line in s.splitlines()])


def _get_pp_matrix(wcs):
    slen = np.max([len(line) for line in list(wcs.world_axis_names) + list(wcs.pixel_axis_names)])
    mstr = wcs.axis_correlation_matrix.astype(f"<U{slen}")
    mstr = np.insert(mstr, 0, wcs.pixel_axis_names, axis=0)
    world = ["", *list(wcs.world_axis_names)]
    mstr = np.insert(mstr, 0, world, axis=1)
    for i, col in enumerate(mstr.T):
        wid = np.max([len(a) for a in col])
        mstr[:, i] = np.char.rjust(col, wid)
    print(np.array_str(mstr, max_line_width=1000))


def extract_pc_matrix(headers, naxes=None):
    """
    Given an astropy table of headers extract one or more PC matrices.
    """
    if naxes is None:
        naxes = headers[0]["NAXIS"]
    keys = []
    for i, j in np.ndindex((naxes, naxes)):
        keys.append(f"PC{i+1}_{j+1}")

    sub = headers[keys]

    return np.array(np.array(headers[keys]).tolist()).reshape(len(sub), naxes, naxes)
