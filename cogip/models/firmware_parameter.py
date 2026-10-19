from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeInt,
    Strict,
    StrictBool,
    StrictFloat,
    StrictInt,
    ValidationInfo,
    field_validator,
)

from cogip.protobuf import (
    PB_ParameterDefinition,
    PB_ParameterGetRequest,
    PB_ParameterGetResponse,
    PB_ParameterResetRequest,
    PB_ParameterResetResponse,
    PB_ParameterSetRequest,
    PB_ParameterSetResponse,
    PB_ParameterStatus,
)
from cogip.utils.fnv1a import fnv1a_hash


class FirmwareParameterValidationFailed(Exception):
    """Exception raised when the firmware rejects a parameter value (out of range or read-only)."""


class FirmwareParameterNotFound(Exception):
    """Exception raised when the firmware does not know a parameter."""


class FirmwareParameterBase(BaseModel):
    """Base firmware parameter value, with the range accepted by the firmware.

    Subclasses declare `min` and `max` before `content`, so that the range is known
    when the content is validated.
    """

    model_config = ConfigDict(validate_assignment=True)

    @field_validator("content", check_fields=False)
    @classmethod
    def check_range(cls, content: Any, info: ValidationInfo) -> Any:
        """Reject a content outside the range accepted by the firmware."""
        minimum = info.data.get("min")
        maximum = info.data.get("max")

        if content is not None and minimum is not None and maximum is not None and not minimum <= content <= maximum:
            raise ValueError(f"{content} out of range [{minimum}, {maximum}]")

        return content


class FirmwareParameterFloat(FirmwareParameterBase):
    """Float firmware parameter value."""

    type: Literal["float"] = "float"
    min: StrictFloat
    max: StrictFloat
    content: StrictFloat | None = None


class FirmwareParameterDouble(FirmwareParameterBase):
    """Double firmware parameter value."""

    type: Literal["double"] = "double"
    min: StrictFloat
    max: StrictFloat
    content: StrictFloat | None = None


class FirmwareParameterInt32(FirmwareParameterBase):
    """Signed 32-bit integer firmware parameter value."""

    type: Literal["int32"] = "int32"
    min: StrictInt
    max: StrictInt
    content: StrictInt | None = None


class FirmwareParameterUInt32(FirmwareParameterBase):
    """Unsigned 32-bit integer firmware parameter value."""

    type: Literal["uint32"] = "uint32"
    min: Annotated[NonNegativeInt, Strict()]
    max: Annotated[NonNegativeInt, Strict()]
    content: Annotated[NonNegativeInt, Strict()] | None = None


class FirmwareParameterInt64(FirmwareParameterBase):
    """Signed 64-bit integer firmware parameter value."""

    type: Literal["int64"] = "int64"
    min: StrictInt
    max: StrictInt
    content: StrictInt | None = None


class FirmwareParameterUInt64(FirmwareParameterBase):
    """Unsigned 64-bit integer firmware parameter value."""

    type: Literal["uint64"] = "uint64"
    min: Annotated[NonNegativeInt, Strict()]
    max: Annotated[NonNegativeInt, Strict()]
    content: Annotated[NonNegativeInt, Strict()] | None = None


class FirmwareParameterBool(FirmwareParameterBase):
    """Boolean firmware parameter value."""

    type: Literal["bool"] = "bool"
    min: StrictBool
    max: StrictBool
    content: StrictBool | None = None


# Discriminated union of all firmware parameter value types
FirmwareParameterValueType = (
    FirmwareParameterFloat
    | FirmwareParameterDouble
    | FirmwareParameterInt32
    | FirmwareParameterUInt32
    | FirmwareParameterInt64
    | FirmwareParameterUInt64
    | FirmwareParameterBool
)


class FirmwareParameter(BaseModel):
    """Firmware parameter, as defined by the firmware.

    Attributes:
        name: The firmware parameter name, its FNV-1a hash addresses the firmware requests
        value_obj: The firmware parameter value object, with its type and accepted range
    """

    model_config = ConfigDict(validate_assignment=True)

    name: str
    value_obj: Annotated[FirmwareParameterValueType, Field(alias="value", discriminator="type")]

    def __hash__(self):
        return fnv1a_hash(self.name)

    @classmethod
    def from_definition(cls, definition: PB_ParameterDefinition) -> "FirmwareParameter":
        """Create a firmware parameter from its definition, its value stays unknown until read.

        The type is given by the oneof field set in the bounds.
        """
        which_field = definition.min.WhichOneof("value")

        return cls.model_validate(
            {
                "name": definition.name,
                "value": {
                    "type": which_field.removesuffix("_value"),
                    "min": getattr(definition.min, which_field),
                    "max": getattr(definition.max, which_field),
                },
            }
        )

    @property
    def value(self) -> float | int | bool | None:
        """Get the firmware parameter content value, None until read from the firmware."""
        return self.value_obj.content

    @value.setter
    def value(self, content: float | int | bool) -> None:
        """Set the firmware parameter content value, validated against its type and range."""
        self.value_obj.content = content

    def pb_copy(self, message: PB_ParameterGetRequest | PB_ParameterSetRequest | PB_ParameterResetRequest) -> None:
        """Copy values to Protobuf message"""
        message.key_hash = hash(self)

        if isinstance(message, PB_ParameterSetRequest):
            setattr(message.value, f"{self.value_obj.type}_value", self.value_obj.content)

    def pb_read(self, message: PB_ParameterGetResponse | PB_ParameterSetResponse | PB_ParameterResetResponse) -> None:
        """Read the value of a get response, or the status of a set or reset response.

        Raises:
            FirmwareParameterValidationFailed: If the firmware rejected the value
            FirmwareParameterNotFound: If the firmware does not know the parameter
        """
        if isinstance(message, PB_ParameterGetResponse):
            self.value_obj.content = getattr(message.value, message.value.WhichOneof("value"))
            return

        match message.status:
            case PB_ParameterStatus.VALIDATION_FAILED:
                raise FirmwareParameterValidationFailed(f"Firmware rejected '{self.name}' (out of range or read-only)")
            case PB_ParameterStatus.NOT_FOUND:
                raise FirmwareParameterNotFound(f"Firmware does not know '{self.name}'")
