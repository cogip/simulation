# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: PB_Coords.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='PB_Coords.proto',
  package='cogip.cogip_defs',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n\x0fPB_Coords.proto\x12\x10\x63ogip.cogip_defs\"!\n\tPB_Coords\x12\t\n\x01x\x18\x01 \x01(\x01\x12\t\n\x01y\x18\x02 \x01(\x01\x62\x06proto3')
)




_PB_COORDS = _descriptor.Descriptor(
  name='PB_Coords',
  full_name='cogip.cogip_defs.PB_Coords',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='x', full_name='cogip.cogip_defs.PB_Coords.x', index=0,
      number=1, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='y', full_name='cogip.cogip_defs.PB_Coords.y', index=1,
      number=2, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
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
  serialized_start=37,
  serialized_end=70,
)

DESCRIPTOR.message_types_by_name['PB_Coords'] = _PB_COORDS
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

PB_Coords = _reflection.GeneratedProtocolMessageType('PB_Coords', (_message.Message,), dict(
  DESCRIPTOR = _PB_COORDS,
  __module__ = 'PB_Coords_pb2'
  # @@protoc_insertion_point(class_scope:cogip.cogip_defs.PB_Coords)
  ))
_sym_db.RegisterMessage(PB_Coords)


# @@protoc_insertion_point(module_scope)
