# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: PB_State.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import PB_Mode_pb2 as PB__Mode__pb2
import PB_Coords_pb2 as PB__Coords__pb2
import PB_Pose_pb2 as PB__Pose__pb2
import PB_Polar_pb2 as PB__Polar__pb2
import PB_Obstacle_pb2 as PB__Obstacle__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='PB_State.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n\x0ePB_State.proto\x1a\rPB_Mode.proto\x1a\x0fPB_Coords.proto\x1a\rPB_Pose.proto\x1a\x0ePB_Polar.proto\x1a\x11PB_Obstacle.proto\"\xec\x01\n\x08PB_State\x12\x16\n\x04mode\x18\x01 \x01(\x0e\x32\x08.PB_Mode\x12\x1e\n\x0cpose_current\x18\x02 \x01(\x0b\x32\x08.PB_Pose\x12\x1c\n\npose_order\x18\x03 \x01(\x0b\x32\x08.PB_Pose\x12\r\n\x05\x63ycle\x18\x04 \x01(\r\x12 \n\rspeed_current\x18\x05 \x01(\x0b\x32\t.PB_Polar\x12\x1e\n\x0bspeed_order\x18\x06 \x01(\x0b\x32\t.PB_Polar\x12\x18\n\x04path\x18\x07 \x03(\x0b\x32\n.PB_Coords\x12\x1f\n\tobstacles\x18\x08 \x03(\x0b\x32\x0c.PB_Obstacleb\x06proto3')
  ,
  dependencies=[PB__Mode__pb2.DESCRIPTOR,PB__Coords__pb2.DESCRIPTOR,PB__Pose__pb2.DESCRIPTOR,PB__Polar__pb2.DESCRIPTOR,PB__Obstacle__pb2.DESCRIPTOR,])




_PB_STATE = _descriptor.Descriptor(
  name='PB_State',
  full_name='PB_State',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='mode', full_name='PB_State.mode', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='pose_current', full_name='PB_State.pose_current', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='pose_order', full_name='PB_State.pose_order', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='cycle', full_name='PB_State.cycle', index=3,
      number=4, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='speed_current', full_name='PB_State.speed_current', index=4,
      number=5, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='speed_order', full_name='PB_State.speed_order', index=5,
      number=6, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='path', full_name='PB_State.path', index=6,
      number=7, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='obstacles', full_name='PB_State.obstacles', index=7,
      number=8, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=101,
  serialized_end=337,
)

_PB_STATE.fields_by_name['mode'].enum_type = PB__Mode__pb2._PB_MODE
_PB_STATE.fields_by_name['pose_current'].message_type = PB__Pose__pb2._PB_POSE
_PB_STATE.fields_by_name['pose_order'].message_type = PB__Pose__pb2._PB_POSE
_PB_STATE.fields_by_name['speed_current'].message_type = PB__Polar__pb2._PB_POLAR
_PB_STATE.fields_by_name['speed_order'].message_type = PB__Polar__pb2._PB_POLAR
_PB_STATE.fields_by_name['path'].message_type = PB__Coords__pb2._PB_COORDS
_PB_STATE.fields_by_name['obstacles'].message_type = PB__Obstacle__pb2._PB_OBSTACLE
DESCRIPTOR.message_types_by_name['PB_State'] = _PB_STATE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

PB_State = _reflection.GeneratedProtocolMessageType('PB_State', (_message.Message,), dict(
  DESCRIPTOR = _PB_STATE,
  __module__ = 'PB_State_pb2'
  # @@protoc_insertion_point(class_scope:PB_State)
  ))
_sym_db.RegisterMessage(PB_State)


# @@protoc_insertion_point(module_scope)
