from typing import Generic, TypeVar

from pydantic import BaseModel, field_validator, model_validator

T = TypeVar("T")


class StrippedModel(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def strip_strings(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value


class NonEmptyUpdateModel(StrippedModel):
    @model_validator(mode="after")
    def validate_has_update_fields(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        null_fields = [field for field in self.model_fields_set if getattr(self, field) is None]
        if null_fields:
            fields = ", ".join(sorted(null_fields))
            raise ValueError(f"Update field(s) cannot be null: {fields}")
        return self


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "OK"
    data: T | None = None
