"""Command-line interface for Berm policy engine."""

import sys
from pathlib import Path
from typing import Optional

import click

from berm import __version__
from berm.evaluators.simple import SimpleEvaluator
from berm.loaders.rules import RuleLoadError, load_rules
from berm.loaders.terraform import TerraformPlanLoadError, load_terraform_plan
from berm.reporters import get_reporter


@click.group()
@click.version_option(version=__version__, prog_name="berm")
def cli() -> None:
    """Berm - Policy Engine for CI/CD Pipelines.

    Guide teams toward infrastructure best practices without blocking velocity.
    """
    pass


@cli.command()
@click.argument("plan_file", type=click.Path(exists=True))
@click.option(
    "--rules-dir",
    "-r",
    default=".berm",
    help="Directory containing policy rules (default: .berm)",
    type=click.Path(exists=True),
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["terminal", "github", "json"], case_sensitive=False),
    default="terminal",
    help="Output format (default: terminal)",
)
@click.option(
    "--strict",
    is_flag=True,
    help="Treat warnings as errors (fail on any violation)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
def check(
    plan_file: str,
    rules_dir: str,
    format: str,
    strict: bool,
    verbose: bool,
) -> None:
    """Check a Terraform plan against policy rules.

    PLAN_FILE: Path to Terraform plan JSON file (from 'terraform show -json plan.tfplan')

    Examples:

        berm check plan.json

        berm check plan.json --rules-dir .berm --format github

        berm check plan.json --strict
    """
    exit_code = run_check(plan_file, rules_dir, format, strict, verbose)
    sys.exit(exit_code)


@cli.command()
@click.option(
    "--rules",
    "-r",
    required=True,
    help="Directory containing policy rules",
    type=click.Path(exists=True),
)
@click.option(
    "--plan",
    "-p",
    required=True,
    help="Path to Terraform plan JSON file",
    type=click.Path(exists=True),
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["terminal", "github", "json"], case_sensitive=False),
    default="terminal",
    help="Output format (default: terminal)",
)
@click.option(
    "--strict",
    is_flag=True,
    help="Treat warnings as errors (fail on any violation)",
)
def test(
    rules: str,
    plan: str,
    format: str,
    strict: bool,
) -> None:
    """Test policy rules against a Terraform plan.

    Explicit version of 'check' command for local testing and development.

    Examples:

        berm test --rules examples/rules --plan examples/plans/plan.json

        berm test -r .berm -p plan.json --format json
    """
    exit_code = run_check(plan, rules, format, strict, verbose=False)
    sys.exit(exit_code)


def run_check(
    plan_file: str,
    rules_dir: str,
    format: str,
    strict: bool,
    verbose: bool,
) -> int:
    """Run policy checks and return exit code.

    Args:
        plan_file: Path to Terraform plan JSON
        rules_dir: Directory containing rule files
        format: Output format (terminal, github, json)
        strict: Treat warnings as errors
        verbose: Enable verbose output

    Returns:
        Exit code: 0 = pass, 1 = violations found, 2 = error
    """
    try:
        # Load rules
        if verbose:
            click.echo(f"Loading rules from: {rules_dir}")

        rules = load_rules(rules_dir)

        if verbose:
            click.echo(f"Loaded {len(rules)} rule(s)")

        # Load Terraform plan
        if verbose:
            click.echo(f"Loading Terraform plan: {plan_file}")

        resources = load_terraform_plan(plan_file)

        if verbose:
            click.echo(f"Loaded {len(resources)} resource(s)")

        # Evaluate rules
        if verbose:
            click.echo("Evaluating policy rules...")

        evaluator = SimpleEvaluator()
        violations = evaluator.evaluate_all(rules, resources)

        # Report violations
        reporter = get_reporter(format)
        reporter.report(violations)

        # Determine exit code
        errors = [v for v in violations if v.is_error()]
        warnings = [v for v in violations if v.is_warning()]

        if errors:
            # Errors found - fail
            return 1
        elif warnings and strict:
            # Warnings in strict mode - fail
            return 1
        else:
            # No violations or only warnings in non-strict mode - pass
            return 0

    except RuleLoadError as e:
        click.echo(f"Error loading rules: {e}", err=True)
        return 2

    except TerraformPlanLoadError as e:
        click.echo(f"Error loading Terraform plan: {e}", err=True)
        return 2

    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        return 2


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
