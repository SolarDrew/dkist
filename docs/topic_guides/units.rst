.._dkist:topic-guides:units:

Astropy units
=============

The `astropy.units` package is used throughout the Python Tools and in several of its dependencies, such as `sunpy`.
This guide will describe some features of `units` that it is useful to know about while using the Python Tools.
For more detail on using `astropy.units` you should see the `astropy.units` `documentation <https://docs.astropy.org/en/stable/units>`__.

Equivalencies
-------------

As described in :ref:`dkist:tutorial:astropy-and-sunpy`, `Quantity` objects can be converted from one unit to another, for example:

.. code-block:: python

   speed = 10 * u.m / u.min
   speed.to(u.km/u.h)

However, this only works for basic conversions with a conversion factor, such as between miles and kilometers.
In cases such as converting a wavelength to a frequency this style of conversion will fail because the units are not considered compatible.

.. code-block:: python

   (656.281 * u.nm).to(u.Hz)  # Fails because they are not compatible

However we can make use of a spectral *equivalency* to indicate the link between the units:

.. code-block:: python

   (656.281 * u.nm).to(u.Hz, equivalencies=u.spectral())

Constants
---------

Astropy also provides a `constants` sub-package which defines many useful physical constants using the units/quantities framework.
This makes it very straightforward to include such constants in your calculations.

.. code-block:: python

   from astropy.constants import M_sun, c # Solar mass, speed of light
   E = 3 * M_sun * c ** 2
   E.to(u.J)
