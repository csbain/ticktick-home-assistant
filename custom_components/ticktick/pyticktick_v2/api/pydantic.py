"""Custom Pydantic utilities.

Based on pyticktick v0.3.0 by Seb Pretzer (MIT License).
"""

from __future__ import annotations

import types
from inspect import isclass
from typing import Any, Union, get_origin

from pydantic import BaseModel, ConfigDict


def _is_union(annotation: type[Any]) -> bool:
    """Check if annotation is a Union type."""
    return get_origin(annotation) in {Union, types.UnionType}


def _issubclass_safe(
    cls: Any,
    class_or_tuple: type[Any] | tuple[type[Any], ...],
) -> bool:
    """Safe issubclass that doesn't raise TypeError."""
    try:
        return isclass(cls) and issubclass(cls, class_or_tuple)
    except TypeError:
        return False


def _check_field_for_submodel(
    annotation: type[Any] | None,
    **config_kwargs: Any,
) -> None:
    """Check if field is a Pydantic model and update its config."""
    if annotation is None:
        return
    if isinstance(annotation, types.GenericAlias):
        _origin = annotation.__origin__
        _args = annotation.__args__
        if _origin is list and _issubclass_safe(_args[0], BaseModel):
            update_model_config(_args[0], **config_kwargs)
        elif _origin is dict and _issubclass_safe(_args[1], BaseModel):
            update_model_config(_args[1], **config_kwargs)
    elif _is_union(annotation):
        for _arg in annotation.__args__:
            _check_field_for_submodel(_arg, **config_kwargs)
    elif _issubclass_safe(annotation, BaseModel):
        update_model_config(annotation, **config_kwargs)


def update_model_config(model: type[BaseModel], **config_kwargs: Any) -> None:
    """Dynamically update a Pydantic model config, including nested submodels.

    Args:
        model: The Pydantic model to update.
        **config_kwargs: Key-value pairs to update the model config with.
            Should be values found in pydantic.ConfigDict.

    Raises:
        ValueError: If no config key-value pairs are provided.
    """
    if len(config_kwargs) == 0:
        msg = "`update_model_config()` requires at least 1 Model Config key-value pair argument"
        raise ValueError(msg)

    for field in model.__pydantic_fields__.values():
        _check_field_for_submodel(field.annotation, **config_kwargs)

    model.model_config.update(ConfigDict(**config_kwargs))
    model.model_rebuild(force=True)
