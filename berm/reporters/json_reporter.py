"""JSON reporter for machine-readable output."""

import json
from typing import List

from berm.models.violation import Violation
from berm.security import sanitize_for_output


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
        # Convert violations to dictionaries with sanitized content
        violations_data = []
        for violation in violations:
            # Sanitize for JSON context (though json.dumps handles most escaping)
            violations_data.append(
                {
                    "rule_id": sanitize_for_output(violation.rule_id, context="json"),
                    "rule_name": sanitize_for_output(violation.rule_name, context="json"),
                    "resource_name": sanitize_for_output(violation.resource_name, context="json"),
                    "resource_type": sanitize_for_output(violation.resource_type, context="json"),
                    "severity": violation.severity,
                    "message": sanitize_for_output(violation.message, context="json"),
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
