# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: PB_PathPose.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import PB_Pose_pb2 as PB__Pose__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x11PB_PathPose.proto\x1a\rPB_Pose.proto\"\xaf\x01\n\x0bPB_PathPose\x12\x16\n\x04pose\x18\x01 \x01(\x0b\x32\x08.PB_Pose\x12\x1e\n\x16max_speed_ratio_linear\x18\x02 \x01(\r\x12\x1f\n\x17max_speed_ratio_angular\x18\x03 \x01(\r\x12\x15\n\rallow_reverse\x18\x04 \x01(\x08\x12\x1c\n\x14\x62ypass_anti_blocking\x18\x05 \x01(\x08\x12\x12\n\ntimeout_ms\x18\x06 \x01(\rb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'PB_PathPose_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _PB_PATHPOSE._serialized_start=37
  _PB_PATHPOSE._serialized_end=212
# @@protoc_insertion_point(module_scope)
