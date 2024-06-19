from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class PB_Command(_message.Message):
    __slots__ = ["cmd", "desc"]
    CMD_FIELD_NUMBER: _ClassVar[int]
    DESC_FIELD_NUMBER: _ClassVar[int]
    cmd: str
    desc: str
    def __init__(self, cmd: _Optional[str] = ..., desc: _Optional[str] = ...) -> None: ...
