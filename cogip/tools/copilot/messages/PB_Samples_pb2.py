# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: PB_Samples.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='PB_Samples.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n\x10PB_Samples.proto\"f\n\tPB_Sample\x12\t\n\x01x\x18\x01 \x01(\x02\x12\t\n\x01y\x18\x02 \x01(\x02\x12\t\n\x01z\x18\x03 \x01(\x02\x12\r\n\x05rot_x\x18\x04 \x01(\x02\x12\r\n\x05rot_y\x18\x05 \x01(\x02\x12\r\n\x05rot_z\x18\x06 \x01(\x02\x12\x0b\n\x03tag\x18\x07 \x01(\x05\">\n\nPB_Samples\x12\x1b\n\x07samples\x18\x01 \x03(\x0b\x32\n.PB_Sample\x12\x13\n\x0bhas_samples\x18\x02 \x01(\x08\x62\x06proto3')
)




_PB_SAMPLE = _descriptor.Descriptor(
  name='PB_Sample',
  full_name='PB_Sample',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='x', full_name='PB_Sample.x', index=0,
      number=1, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='y', full_name='PB_Sample.y', index=1,
      number=2, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='z', full_name='PB_Sample.z', index=2,
      number=3, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='rot_x', full_name='PB_Sample.rot_x', index=3,
      number=4, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='rot_y', full_name='PB_Sample.rot_y', index=4,
      number=5, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='rot_z', full_name='PB_Sample.rot_z', index=5,
      number=6, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='tag', full_name='PB_Sample.tag', index=6,
      number=7, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
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
  serialized_start=20,
  serialized_end=122,
)


_PB_SAMPLES = _descriptor.Descriptor(
  name='PB_Samples',
  full_name='PB_Samples',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='samples', full_name='PB_Samples.samples', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='has_samples', full_name='PB_Samples.has_samples', index=1,
      number=2, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
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
  serialized_start=124,
  serialized_end=186,
)

_PB_SAMPLES.fields_by_name['samples'].message_type = _PB_SAMPLE
DESCRIPTOR.message_types_by_name['PB_Sample'] = _PB_SAMPLE
DESCRIPTOR.message_types_by_name['PB_Samples'] = _PB_SAMPLES
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

PB_Sample = _reflection.GeneratedProtocolMessageType('PB_Sample', (_message.Message,), dict(
  DESCRIPTOR = _PB_SAMPLE,
  __module__ = 'PB_Samples_pb2'
  # @@protoc_insertion_point(class_scope:PB_Sample)
  ))
_sym_db.RegisterMessage(PB_Sample)

PB_Samples = _reflection.GeneratedProtocolMessageType('PB_Samples', (_message.Message,), dict(
  DESCRIPTOR = _PB_SAMPLES,
  __module__ = 'PB_Samples_pb2'
  # @@protoc_insertion_point(class_scope:PB_Samples)
  ))
_sym_db.RegisterMessage(PB_Samples)


# @@protoc_insertion_point(module_scope)