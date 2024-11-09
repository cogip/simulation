#!/usr/bin/env python3
from cogip.cpp.example import PyExample


def main():
    """
    Example calling a function from a C++ class..

    During installation of cogip-tools, a script called `cogip-cpp-example`
    will be created using this function as entrypoint.
    """
    example = PyExample()
    print(example.get_message())


if __name__ == "__main__":
    main()
