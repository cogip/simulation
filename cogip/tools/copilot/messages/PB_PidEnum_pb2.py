# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: PB_PidEnum.proto

from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='PB_PidEnum.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x10PB_PidEnum.proto*d\n\nPB_PidEnum\x12\x13\n\x0fLINEAR_POSE_PID\x10\x00\x12\x14\n\x10\x41NGULAR_POSE_PID\x10\x01\x12\x14\n\x10LINEAR_SPEED_PID\x10\x02\x12\x15\n\x11\x41NGULAR_SPEED_PID\x10\x03\x62\x06proto3'
)

_PB_PIDENUM = _descriptor.EnumDescriptor(
  name='PB_PidEnum',
  full_name='PB_PidEnum',
  filename=None,
  file=DESCRIPTOR,
  create_key=_descriptor._internal_create_key,
  values=[
    _descriptor.EnumValueDescriptor(
      name='LINEAR_POSE_PID', index=0, number=0,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='ANGULAR_POSE_PID', index=1, number=1,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='LINEAR_SPEED_PID', index=2, number=2,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='ANGULAR_SPEED_PID', index=3, number=3,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=20,
  serialized_end=120,
)
_sym_db.RegisterEnumDescriptor(_PB_PIDENUM)

PB_PidEnum = enum_type_wrapper.EnumTypeWrapper(_PB_PIDENUM)
LINEAR_POSE_PID = 0
ANGULAR_POSE_PID = 1
LINEAR_SPEED_PID = 2
ANGULAR_SPEED_PID = 3


DESCRIPTOR.enum_types_by_name['PB_PidEnum'] = _PB_PIDENUM
_sym_db.RegisterFileDescriptor(DESCRIPTOR)


# @@protoc_insertion_point(module_scope)
