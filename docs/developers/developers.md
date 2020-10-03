# Developer's Documentation

This documentation provides information for developers who would like to contribute
to the project.
It tries to explain how modules are organised and how `PySide2` and `Qt3D` are used.

The simulator is developped in Python 3.8+, using [`Pyside2`](https://doc.qt.io/qtforpython/contents.html), the Qt for Python package.

The 3D view is based on the [`Qt3D framework`](https://doc.qt.io/qt-5/qt3d-overview.html).
To have a better understanding of the code, it is important to understand Qt concepts
like Signals and Slots, and the Qt3D [Entity Component System](https://doc.qt.io/qt-5.9/qt3d-overview.html#qt-3d-ecs-implementation) (ECS).

Here are some interesting blogs and docs to understand the Qt3D architecture:

  - <https://doc.qt.io/qt-5/qt3d-overview.html#qt-3d-architecture>
  - <https://www.kdab.com/overview-qt3d-2-0-part-1/>
  - <https://www.kdab.com/overview-qt3d-2-0-part-2/>
  - <https://www.linkedin.com/pulse/3d-visualisation-using-qt3d-part-1-guido-piasenza/>
  - <https://www.linkedin.com/pulse/3d-visualisation-using-qt3d-part-2-guido-piasenza/>
  - <https://www.linkedin.com/pulse/3d-visualisation-using-qt3d-part-3-guido-piasenza/>
