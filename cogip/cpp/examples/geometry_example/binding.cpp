// Copyright (C) 2026 COGIP Robotics association <cogip35@gmail.com>
// This file is subject to the terms and conditions of the GNU Lesser
// General Public License v2.1. See the file LICENSE in the top level directory.

#include "geometry_example/geometry_example.hpp"

#include <nanobind/nanobind.h>

namespace nb = nanobind;

namespace geometry_example {

NB_MODULE(geometry_example, m) {
    m.def("run", &run, "Demonstrate the geometry library");
}

} // namespace geometry_example
