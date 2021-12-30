# Protobuf Messages

Protobuf messages exchanged between `mcu-firmware`and the `Copilot` are defined in `mcu-firmware`.

To generate Python classes using `protoc`, all files need to be in this directory.

Since `mcu-firmware` is embedded as a Git submodule, we just create symbolic links
of `*.proto` files here.

Generated files need to be commited since there is no compilation process in Python.

Update these files with `protoc --python_out=. *.proto`
