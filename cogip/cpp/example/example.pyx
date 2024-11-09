# example.pyx

# cython: profile=True

from libcpp.string cimport string

cdef extern from "example/example.hpp" namespace "":
    cdef cppclass Example:
        Example()
        string getMessage() const

# Wrapping PyExample class for Python
cdef class PyExample:
    cdef Example* cpp_instance

    def __cinit__(self):
        self.cpp_instance = new Example()

    def __dealloc__(self):
        del self.cpp_instance

    def get_message(self) -> str:
        cdef string message = self.cpp_instance.getMessage()
        return message.decode("utf-8")
