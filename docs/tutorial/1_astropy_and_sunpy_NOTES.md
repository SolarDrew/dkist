---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.11.5
kernelspec:
  display_name: Python 3
  language: python
  name: python3
  ---
# Astropy and SunPy - A Quick Primer
## Coordinates
### Spectral Coordinates

{obj}`astropy.coordinates.SpectralCoord` is a `Quantity` like object which also holds information about the observer and target coordinates and relative velocities.

```{note}
Use of `SpectralCoord` with solar data is still experimental so not all features may work, or be accurate.
```

```{code-cell} python
from astropy.coordinates import SpectralCoord
from sunpy.coordinates import get_earth
```

`SpectralCoord` does not automatically make the HPC coordinate 3D, but wants the distance, so we do it explicitly:

```{code-cell} python
hpc2 = hpc1.make_3d()
```

Now we can construct our spectral coordinate with both a target and an observer
```{code-cell} python
spc = SpectralCoord(586.3 * u.nm, target=hpc2, observer=get_earth(time=hpc2.obstime))
spc
```

We can show the full details of the spectral coord (working around a bug in astropy):
```{code-cell} python
print(repr(spc))
```

## World Coordinate System

One of the other core components of the ecosystem provided by Astropy is the {obj}`astropy.wcs` package which provides tools for mapping pixel to world coordinates and world to pixel.
When loading a FITS file with complete (and standard compliant) WCS metadata we can create an `astropy.wcs.WCS` object.
For the this example we will use some sunpy sample data from AIA.

```{code-cell} python
import sunpy.coordinates
```

To read this FITS file we will use {obj}`astropy.io.fits` (you can also use `sunpy` for this).

```{code-cell} python
from astropy.io import fits

hdu_list = fits.open("../data/VISP_2022_10_24T19_47_33_218_00630205_I_BEOGN_L1.fits")
```

We can now access the header of the second HDU:
```{code-cell} python
hdu_list[1].header
```

Using this header we can create a `astropy.wcs.WCS` object:
```{code-cell} python
from astropy.wcs import WCS

wcs = WCS(hdu_list[1].header)
wcs
```

This WCS object allows us to convert between pixel and world coordinates, for example:

```{code-cell} python
wcs.pixel_to_world(1024, 400, 1)
```

This call returns a {obj}`astropy.coordinates.SkyCoord` object (which needs sunpy to be imported), we will come onto this more later.

We can also convert between pixel and plain numbers:

```{code-cell} python
wcs.pixel_to_world_values(1024, 400, 1)
```

The units for these values are given by:

```{code-cell} python
wcs.world_axis_units
```


The WCS also has information about what the world axes represent:

```{code-cell} python
wcs.world_axis_physical_types
```

We can also inspect the correlation between the world axes and pixel axes:

```{code-cell} python
wcs.axis_correlation_matrix
```

This correlation matrix has the world dimensions as rows, and the pixel dimensions as columns.
As we have a 2D image here, with two pixel and two world axes where both are coupled together.
This means that to calculate either latitude or longitude you need both pixel coordinates.
