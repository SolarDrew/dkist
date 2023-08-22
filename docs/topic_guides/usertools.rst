.. _dkist:topic-guides:usertools:

What to Expect from the DKIST Python Tools
==========================================

The `dkist` package is developed by the DKIST Data Center team, and it is designed to make it easy to obtain and use DKIST data in Python.
To achieve this goal the `dkist` package only provides DKIST specific functionality as plugins and extensions to the wider `sunpy` and scientific Python ecosystem.
This means that there *isn't actually a lot of code* in the `dkist` package, and most of the development effort required to support DKIST data happened in packages such as `ndcube`, `sunpy` and `astropy`.

The upshot of this when using the DKIST Python tools is that you will mostly not be (directly) using functionality provided by the `dkist` package.
You will need to be familiar with the other packages in the ecosystem to make use of the tools provided here.

DKIST and the Scientific Python Ecosystem
-----------------------------------------

Python is a modular language, which allows you to build, distribute and import custom libraries for specialist functionality on top of what's provided by the language itself.
This being the case, a significant body of third-party code has grown up over the last couple of decades to form a core set of scientific libraries which are commonly used for a scientific analysis.
Chief among these are `numpy`, `scipy` and `matplotlib`.
Specifically in the fields of astronomy and solar physics, the go-to libraries are `astropy` and `sunpy`.

These packages, along with NDCube, are the core components of the DKIST tools.
There are many parts of these packages which are useful when working with DKIST data, which you should explore on their respective documentation pages.
The main things you will need to be familiar with are the {obj}`sunpy.net.Fido` and {obj}`ndcube.NDCube` classes.
Additionally you will find it useful to have some knowledge of `astropy.units`, `astropy.wcs`, `astropy.coordinates` and `sunpy.coordinates`.
These topics are all covered in the :ref:`dkist:tutorial:index`.

Technical Details
-----------------

What the `dkist` package provides is the following:

* A subclass of `ndcube.NDCube` which hooks into our ASDF schemas and provides access to the table of FITS headers and the `dkist.io.FileManager` object.
* A client class for `sunpy.net.Fido` which transparently loads on import of `dkist.net` and allows Fido to search the DKIST data center.
* A set of helper functions to transfer files from the data center via `Globus <https://globus.org/>`__, the way to call this is the `~dkist.io.FileManager.download` of the `dkist.Dataset.files` property.

This facilitates search, retrieval and loading of level 1 data using the functionality provided by `sunpy` and `ndcube`.
It is expected that any community developed analysis software that is explicitly DKIST specific will also be included in the `dkist` package in the future.
