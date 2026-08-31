# Header-only library: the kernels must be inlinable into their callers, which a shared library
# built without LTO would prevent. There is nothing to compile and nothing to install.
add_library(geometry_cpp INTERFACE)
target_include_directories(
    geometry_cpp
    INTERFACE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${PROJECT_SOURCE_DIR}/cogip/cpp/libraries/models/include
)

# Generate library with source code and binding.
nanobind_add_module(
    geometry
    NB_SHARED STABLE_ABI LTO
    binding.cpp
)
target_link_libraries(geometry PUBLIC geometry_cpp)
set_target_properties(geometry PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/..)

# Install the library.
install(
    TARGETS geometry
    LIBRARY DESTINATION cogip/cpp/libraries
)

# Generate stub files that are needed to enable static type checking and autocompletion in Python IDEs.
nanobind_add_stub(
    geometry_stub
    MODULE cogip.cpp.libraries.geometry
    OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/__init__.pyi
    MARKER_FILE ${CMAKE_CURRENT_BINARY_DIR}/py.typed
    PYTHON_PATH ${CMAKE_BINARY_DIR}
    VERBOSE
    INSTALL_TIME
)

# Copy stub files into the source directory.
# so it will be available if the package is installed in editable mode (default mode).
install(
    FILES ${CMAKE_CURRENT_BINARY_DIR}/__init__.pyi ${CMAKE_CURRENT_BINARY_DIR}/py.typed
    DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}
)

# Copy stub files into the install directory so it will be added to the wheel package.
install(
    FILES ${CMAKE_CURRENT_BINARY_DIR}/py.typed
    DESTINATION cogip/cpp/libraries
)
install(
    FILES ${CMAKE_CURRENT_BINARY_DIR}/__init__.pyi
    RENAME geometry.pyi
    DESTINATION cogip/cpp/libraries
)
