# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: PB_Mode.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='PB_Mode.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n\rPB_Mode.proto*\xac\x01\n\x07PB_Mode\x12\x12\n\x0e\x43TRL_MODE_STOP\x10\x00\x12\x12\n\x0e\x43TRL_MODE_IDLE\x10\x01\x12\x15\n\x11\x43TRL_MODE_BLOCKED\x10\x02\x12\x15\n\x11\x43TRL_MODE_RUNNING\x10\x03\x12\x1b\n\x17\x43TRL_MODE_RUNNING_SPEED\x10\x04\x12\x19\n\x15\x43TRL_MODE_PASSTHROUGH\x10\x05\x12\x13\n\x0f\x43TRL_MODE_NUMOF\x10\x06\x62\x06proto3')
)

_PB_MODE = _descriptor.EnumDescriptor(
  name='PB_Mode',
  full_name='PB_Mode',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='CTRL_MODE_STOP', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='CTRL_MODE_IDLE', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='CTRL_MODE_BLOCKED', index=2, number=2,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='CTRL_MODE_RUNNING', index=3, number=3,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='CTRL_MODE_RUNNING_SPEED', index=4, number=4,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='CTRL_MODE_PASSTHROUGH', index=5, number=5,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='CTRL_MODE_NUMOF', index=6, number=6,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=18,
  serialized_end=190,
)
_sym_db.RegisterEnumDescriptor(_PB_MODE)

PB_Mode = enum_type_wrapper.EnumTypeWrapper(_PB_MODE)
CTRL_MODE_STOP = 0
CTRL_MODE_IDLE = 1
CTRL_MODE_BLOCKED = 2
CTRL_MODE_RUNNING = 3
CTRL_MODE_RUNNING_SPEED = 4
CTRL_MODE_PASSTHROUGH = 5
CTRL_MODE_NUMOF = 6


DESCRIPTOR.enum_types_by_name['PB_Mode'] = _PB_MODE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)


# @@protoc_insertion_point(module_scope)
