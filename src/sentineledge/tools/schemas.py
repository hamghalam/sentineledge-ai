from pydantic import BaseModel, ConfigDict, Field


class CalculatorArgs(BaseModel):
    """Validated input schema for the calculator tool."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    expression: str = Field(
        min_length=1,
        max_length=100,
    )