"""Base model for pyticktick v2 API models."""

from __future__ import annotations

from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ModelWrapValidatorHandler,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic_core import InitErrorDetails, PydanticCustomError


class BaseModelV2(BaseModel):
    """Base model for all v2 API models."""

    model_config = ConfigDict(
        extra="forbid",
        validate_by_name=True,
        validate_by_alias=True,
    )

    @field_validator("*", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Any) -> Any:
        """Convert empty strings to None."""
        if isinstance(v, str) and len(v) == 0:
            return None
        return v

    @model_validator(mode="wrap")
    @classmethod
    def override_forbid_extra_message_injector(
        cls,
        data: Any,
        handler: ModelWrapValidatorHandler["BaseModelV2"],
    ) -> "BaseModelV2":
        """Provide a better error message for extra fields."""
        try:
            return handler(data)
        except ValidationError as e:
            errors = []
            for error_dict in e.errors():
                if error_dict.get("type") in (
                    "extra_forbidden",
                    "custom_pyticktick_extra_forbidden",
                ):
                    _type: str | PydanticCustomError = PydanticCustomError(
                        "custom_pyticktick_extra_forbidden",
                        "Extra inputs are not permitted by default. Please set `override_forbid_extra` to `True` if you believe the TickTick API has diverged from the model.",
                    )
                else:
                    _type = error_dict["type"]

                init_error_details: InitErrorDetails = {
                    "type": _type,
                    "input": error_dict["input"],
                }
                if "loc" in error_dict:
                    init_error_details["loc"] = error_dict["loc"]
                if "ctx" in error_dict:
                    init_error_details["ctx"] = error_dict["ctx"]

                errors.append(init_error_details)

            raise ValidationError.from_exception_data(e.title, errors) from e
