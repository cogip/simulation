# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: PB_Actuators.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x12PB_Actuators.proto\"\x92\x01\n\x08PB_Servo\x12%\n\x05group\x18\x01 \x01(\x0e\x32\x16.PB_ActuatorsGroupEnum\x12\r\n\x05order\x18\x02 \x01(\r\x12\x12\n\nis_blocked\x18\x03 \x01(\x08\x12\x19\n\x02id\x18\x04 \x01(\x0e\x32\r.PB_ServoEnum\x12\x10\n\x08position\x18\x05 \x01(\r\x12\x0f\n\x07\x63ommand\x18\x06 \x01(\r\"\x98\x01\n\x07PB_Pump\x12%\n\x05group\x18\x01 \x01(\x0e\x32\x16.PB_ActuatorsGroupEnum\x12\r\n\x05order\x18\x02 \x01(\r\x12\x12\n\nis_blocked\x18\x03 \x01(\x08\x12\x18\n\x02id\x18\x04 \x01(\x0e\x32\x0c.PB_PumpEnum\x12\x11\n\tactivated\x18\x05 \x01(\x08\x12\x16\n\x0eunder_pressure\x18\x06 \x01(\x08\"\x9a\x01\n\x15PB_PositionalActuator\x12%\n\x05group\x18\x01 \x01(\x0e\x32\x16.PB_ActuatorsGroupEnum\x12\r\n\x05order\x18\x02 \x01(\r\x12\x12\n\nis_blocked\x18\x03 \x01(\x08\x12&\n\x02id\x18\x04 \x01(\x0e\x32\x1a.PB_PositionalActuatorEnum\x12\x0f\n\x07\x63ommand\x18\x05 \x01(\x05\"\x8a\x01\n\x10PB_ActuatorState\x12\x1b\n\x06servos\x18\x01 \x01(\x0b\x32\t.PB_ServoH\x00\x12\x19\n\x05pumps\x18\x02 \x01(\x0b\x32\x08.PB_PumpH\x00\x12\x36\n\x14positional_actuators\x18\x03 \x01(\x0b\x32\x16.PB_PositionalActuatorH\x00\x42\x06\n\x04type\"}\n\x11PB_ActuatorsState\x12\x19\n\x06servos\x18\x01 \x03(\x0b\x32\t.PB_Servo\x12\x17\n\x05pumps\x18\x02 \x03(\x0b\x32\x08.PB_Pump\x12\x34\n\x14positional_actuators\x18\x03 \x03(\x0b\x32\x16.PB_PositionalActuator\"K\n\x0fPB_ServoCommand\x12\x19\n\x02id\x18\x01 \x01(\x0e\x32\r.PB_ServoEnum\x12\x0f\n\x07\x63ommand\x18\x02 \x01(\r\x12\x0c\n\x04time\x18\x03 \x01(\r\";\n\x0ePB_PumpCommand\x12\x18\n\x02id\x18\x01 \x01(\x0e\x32\x0c.PB_PumpEnum\x12\x0f\n\x07\x63ommand\x18\x02 \x01(\x08\"W\n\x1cPB_PositionalActuatorCommand\x12&\n\x02id\x18\x01 \x01(\x0e\x32\x1a.PB_PositionalActuatorEnum\x12\x0f\n\x07\x63ommand\x18\x02 \x01(\x05\"\xa1\x01\n\x12PB_ActuatorCommand\x12!\n\x05servo\x18\x01 \x01(\x0b\x32\x10.PB_ServoCommandH\x00\x12\x1f\n\x04pump\x18\x02 \x01(\x0b\x32\x0f.PB_PumpCommandH\x00\x12<\n\x13positional_actuator\x18\x03 \x01(\x0b\x32\x1d.PB_PositionalActuatorCommandH\x00\x42\t\n\x07\x63ommand*;\n\x14PB_ActuatorsTypeEnum\x12\t\n\x05SERVO\x10\x00\x12\x08\n\x04PUMP\x10\x01\x12\x0e\n\nPOSITIONAL\x10\x02*%\n\x15PB_ActuatorsGroupEnum\x12\x0c\n\x08NO_GROUP\x10\x00*h\n\x0cPB_ServoEnum\x12\x12\n\x0eLXSERVO_UNUSED\x10\x00\x12\x17\n\x13LXSERVO_BALL_SWITCH\x10\x01\x12\x15\n\x11LXSERVO_RIGHT_ARM\x10\x02\x12\x14\n\x10LXSERVO_LEFT_ARM\x10\x04*4\n\x0bPB_PumpEnum\x12\x12\n\x0ePUMP_RIGHT_ARM\x10\x00\x12\x11\n\rPUMP_LEFT_ARM\x10\x01*\xf5\x01\n\x19PB_PositionalActuatorEnum\x12\x16\n\x12MOTOR_CENTRAL_LIFT\x10\x00\x12\x1b\n\x17MOTOR_CONVEYOR_LAUNCHER\x10\x01\x12\x14\n\x10ONOFF_LED_PANELS\x10\x02\x12\x1a\n\x16\x41NALOGSERVO_CHERRY_ARM\x10\x03\x12\x1a\n\x16\x41NALOGSERVO_CHERRY_ESC\x10\x04\x12\x1e\n\x1a\x41NALOGSERVO_CHERRY_RELEASE\x10\x05\x12\x1a\n\x16LXMOTOR_RIGHT_ARM_LIFT\x10\x06\x12\x19\n\x15LXMOTOR_LEFT_ARM_LIFT\x10\x07\x62\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'PB_Actuators_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _PB_ACTUATORSTYPEENUM._serialized_start=1142
  _PB_ACTUATORSTYPEENUM._serialized_end=1201
  _PB_ACTUATORSGROUPENUM._serialized_start=1203
  _PB_ACTUATORSGROUPENUM._serialized_end=1240
  _PB_SERVOENUM._serialized_start=1242
  _PB_SERVOENUM._serialized_end=1346
  _PB_PUMPENUM._serialized_start=1348
  _PB_PUMPENUM._serialized_end=1400
  _PB_POSITIONALACTUATORENUM._serialized_start=1403
  _PB_POSITIONALACTUATORENUM._serialized_end=1648
  _PB_SERVO._serialized_start=23
  _PB_SERVO._serialized_end=169
  _PB_PUMP._serialized_start=172
  _PB_PUMP._serialized_end=324
  _PB_POSITIONALACTUATOR._serialized_start=327
  _PB_POSITIONALACTUATOR._serialized_end=481
  _PB_ACTUATORSTATE._serialized_start=484
  _PB_ACTUATORSTATE._serialized_end=622
  _PB_ACTUATORSSTATE._serialized_start=624
  _PB_ACTUATORSSTATE._serialized_end=749
  _PB_SERVOCOMMAND._serialized_start=751
  _PB_SERVOCOMMAND._serialized_end=826
  _PB_PUMPCOMMAND._serialized_start=828
  _PB_PUMPCOMMAND._serialized_end=887
  _PB_POSITIONALACTUATORCOMMAND._serialized_start=889
  _PB_POSITIONALACTUATORCOMMAND._serialized_end=976
  _PB_ACTUATORCOMMAND._serialized_start=979
  _PB_ACTUATORCOMMAND._serialized_end=1140
# @@protoc_insertion_point(module_scope)
