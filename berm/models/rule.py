"""Rule model for policy definitions."""

from typing import Literal
from pydantic import BaseModel, Field, field_validator


class Rule(BaseModel):
    """A policy rule that defines requirements for infrastructure resources.

    Rules are defined in JSON format and specify what properties resources
    must have to comply with organizational policies.

    Example:
        {
            "id": "s3-versioning-enabled",
            "name": "S3 buckets must have versioning enabled",
            "resource_type": "aws_s3_bucket",
            "severity": "error",
            "property": "versioning.enabled",
            "equals": true,
            "message": "S3 bucket {{resource_name}} must have versioning enabled"
        }
    """

    id: str = Field(
        ...,
        description="Unique identifier for the rule",
        min_length=1,
    )

    name: str = Field(
        ...,
        description="Human-readable name for the rule",
        min_length=1,
    )

    resource_type: str = Field(
        ...,
        description="Terraform resource type to check (e.g., 'aws_s3_bucket')",
        min_length=1,
    )

    severity: Literal["error", "warning"] = Field(
        ...,
        description="Severity level: 'error' blocks deployment, 'warning' is advisory",
    )

    property: str = Field(
        ...,
        description="Dot-notation path to the property to check (e.g., 'versioning.enabled')",
        min_length=1,
    )

    equals: bool | str | int | float | None = Field(
        ...,
        description="Expected value that the property should equal",
    )

    message: str = Field(
        ...,
        description="Error message to display when rule fails. Supports {{resource_name}} template.",
        min_length=1,
    )

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        """Ensure severity is either 'error' or 'warning'."""
        if v not in ("error", "warning"):
            raise ValueError(f"Severity must be 'error' or 'warning', got: {v}")
        return v

    def format_message(self, resource_name: str) -> str:
        """Format the rule message with resource context.

        Args:
            resource_name: Name of the resource that violated the rule

        Returns:
            Formatted message with template variables replaced
        """
        return self.message.replace("{{resource_name}}", resource_name)

    def __str__(self) -> str:
        """String representation of the rule."""
        return f"Rule({self.id}: {self.name})"

    def __repr__(self) -> str:
        """Detailed representation of the rule."""
        return (
            f"Rule(id='{self.id}', name='{self.name}', "
            f"resource_type='{self.resource_type}', severity='{self.severity}')"
        )
