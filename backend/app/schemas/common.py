from pydantic import BaseModel, ConfigDict, Field


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class FilterBase(BaseModel):
    query: str | None = None


class APIResponse(BaseModel):
    success: bool = True
    message: str = "OK"
    data: dict | list | None = None

    model_config = ConfigDict(from_attributes=True)
