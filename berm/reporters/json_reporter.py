"""JSON reporter for machine-readable output."""

import json
from typing import List

from berm.models.violation import Violation


class JSONReporter:
    """Reports violations as JSON for machine processing.

    Outputs a structured JSON document with all violations,
    useful for integration with other tools and dashboards.
    """

    def report(self, violations: List[Violation]) -> None:
        """Report violations as JSON.

        Args:
            violations: List of violations to report
        """
        # Convert violations to dictionaries
        violations_data = []
        for violation in violations:
            violations_data.append(
                {
                    "rule_id": violation.rule_id,
                    "rule_name": violation.rule_name,
                    "resource_name": violation.resource_name,
                    "resource_type": violation.resource_type,
                    "severity": violation.severity,
                    "message": violation.message,
                    "location": violation.location,
                }
            )

        # Separate errors and warnings
        errors = [v for v in violations_data if v["severity"] == "error"]
        warnings = [v for v in violations_data if v["severity"] == "warning"]

        # Build output structure
        output = {
            "summary": {
                "total_violations": len(violations),
                "errors": len(errors),
                "warnings": len(warnings),
                "passed": len(violations) == 0,
            },
            "violations": violations_data,
        }

        # Print JSON
        print(json.dumps(output, indent=2))
