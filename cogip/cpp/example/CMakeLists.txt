# Include directories
include_directories(
    include
)

# Source files
set(SOURCES
    example.cpp
)

# Create shared library example.so
add_library(libexample STATIC ${SOURCES})
target_compile_options(libexample PRIVATE -fPIC)

# Add the cython transpile step
cython_transpile(
    example.pyx
    LANGUAGE CXX
    CYTHON_ARGS --cplus -3
    OUTPUT_VARIABLE LIBEXAMPLE
)

# Define the Python extension using Cython
python_add_library(example MODULE "${LIBEXAMPLE}" WITH_SOABI)

target_link_libraries(example PRIVATE libexample Python::Module)

install(
    TARGETS example
    LIBRARY DESTINATION cogip/cpp/
)
