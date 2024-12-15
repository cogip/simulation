#include "nanobind_example/nanobind_example.hpp"

#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <nanobind/stl/string.h>

namespace nb = nanobind;

NB_MODULE(nanobind_example, m) {
    // Create binding for the class.
    nb::class_<nanobind_example::NanobindExample>(m, "NanobindExample")
        // Binding for the constructor.
        .def(nb::init<>())
        // Binding for a simple function returning a string.
        .def("get_message", &nanobind_example::NanobindExample::getMessage)
        // Binding for a function returning a pointer to a multi-dimensional array. The pointer will be wrapped
        // in a numpy.ndarray in Python without memory copy between C and Python memory spaces.
        .def(
            "get_data",
            [](const nanobind_example::NanobindExample &self) -> nb::ndarray<uint16_t, nb::numpy, nb::shape<nanobind_example::NUM_DATA, 2>> {
                const auto &data = self.getData();
                return nb::ndarray<uint16_t, nb::numpy, nb::shape<nanobind_example::NUM_DATA, 2>>((void *)data);
            },
            nb::rv_policy::reference_internal
        );
}
