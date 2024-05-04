import PB_Command_pb2 as _PB_Command_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PB_Menu(_message.Message):
    __slots__ = ["entries", "name"]
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    entries: _containers.RepeatedCompositeFieldContainer[_PB_Command_pb2.PB_Command]
    name: str
    def __init__(self, name: _Optional[str] = ..., entries: _Optional[_Iterable[_Union[_PB_Command_pb2.PB_Command, _Mapping]]] = ...) -> None: ...
