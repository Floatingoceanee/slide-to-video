"""
TTS Engine Management CLI

This module provides command-line utilities for managing and testing TTS engines.
It can be run directly or imported for programmatic use.

Usage:
    python -m slide_to_video.tts_engine.cli list
    python -m slide_to_video.tts_engine.cli info local
    python -m slide_to_video.tts_engine.cli test mock --config '{}'
"""

import argparse
import json
import sys
from typing import Dict, Any

from .registery import (
    get_all_engine_names,
    get_engine_info,
    list_all_engines,
    auto_discover_engines,
    validate_engine_config,
)
from .testing import run_engine_tests


def cmd_list(args) -> None:
    """List all available TTS engines."""
    # Auto-discover engines first
    discovered = auto_discover_engines()
    if discovered > 0:
        print(f"Auto-discovered {discovered} engine modules")

    engines = get_all_engine_names()
    if not engines:
        print("No TTS engines found.")
        return

    print("Available TTS Engines:")
    print("=" * 40)

    if args.verbose:
        # Show detailed info for each engine
        all_info = list_all_engines()
        for name in sorted(engines):
            info = all_info.get(name, {})
            print(f"\n{name}:")
            if "error" in info:
                print(f"  Error: {info['error']}")
            else:
                print(f"  Description: {info.get('description', 'N/A')}")
                print(
                    f"  Supported Languages: {', '.join(info.get('supported_languages', []))}"
                )
                print(
                    f"  Supported Formats: {', '.join(info.get('supported_formats', []))}"
                )
                print(f"  Parallel Support: {info.get('supports_parallel', 'Unknown')}")
                if info.get("required_config"):
                    print(f"  Required Config: {', '.join(info['required_config'])}")
    else:
        # Simple list
        for name in sorted(engines):
            print(f"  - {name}")


def cmd_info(args) -> None:
    """Show detailed information about a specific engine."""
    engine_name = args.engine

    try:
        info = get_engine_info(engine_name)

        print(f"Engine Information: {engine_name}")
        print("=" * 50)

        for key, value in info.items():
            if isinstance(value, list):
                print(f"{key.replace('_', ' ').title()}: {', '.join(map(str, value))}")
            else:
                print(f"{key.replace('_', ' ').title()}: {value}")

        if args.json:
            print(f"\nJSON Output:")
            print(json.dumps(info, indent=2))

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_test(args) -> None:
    """Test a TTS engine with the provided configuration."""
    engine_name = args.engine

    # Parse configuration
    try:
        if args.config:
            config = json.loads(args.config)
        elif args.config_file:
            with open(args.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            print("Error: Must provide either --config or --config-file")
            sys.exit(1)

    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error parsing configuration: {e}")
        sys.exit(1)

    # Validate configuration first
    if args.validate_only:
        errors = validate_engine_config(engine_name, config)
        if errors:
            print("Configuration validation failed:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
        else:
            print("Configuration is valid!")
            return

    # Run tests
    try:
        print(f"Testing engine: {engine_name}")
        print(f"Configuration: {json.dumps(config, indent=2)}")
        print()

        results = run_engine_tests(engine_name, config, verbose=True)

        # Save results if requested
        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)
            print(f"\nResults saved to: {args.output}")

        # Exit with error code if tests failed
        if results["summary"]["failed"] > 0:
            sys.exit(1)

    except Exception as e:
        print(f"Test failed with error: {e}")
        sys.exit(1)


def cmd_validate_config(args) -> None:
    """Validate configuration for an engine without running tests."""
    engine_name = args.engine

    try:
        if args.config:
            config = json.loads(args.config)
        elif args.config_file:
            with open(args.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            print("Error: Must provide either --config or --config-file")
            sys.exit(1)

    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error parsing configuration: {e}")
        sys.exit(1)

    errors = validate_engine_config(engine_name, config)

    if errors:
        print("Configuration validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("✓ Configuration is valid!")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="TTS Engine Management CLI", prog="tts-engine-cli"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List all available engines")
    list_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed information for each engine",
    )
    list_parser.set_defaults(func=cmd_list)

    # Info command
    info_parser = subparsers.add_parser("info", help="Show detailed engine information")
    info_parser.add_argument("engine", help="Name of the engine")
    info_parser.add_argument(
        "--json", action="store_true", help="Also output information in JSON format"
    )
    info_parser.set_defaults(func=cmd_info)

    # Test command
    test_parser = subparsers.add_parser("test", help="Test an engine")
    test_parser.add_argument("engine", help="Name of the engine to test")

    config_group = test_parser.add_mutually_exclusive_group(required=True)
    config_group.add_argument("--config", help="Configuration as JSON string")
    config_group.add_argument("--config-file", help="Path to configuration JSON file")

    test_parser.add_argument("--output", help="Save test results to file")
    test_parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate configuration, do not run tests",
    )
    test_parser.set_defaults(func=cmd_test)

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate engine configuration"
    )
    validate_parser.add_argument("engine", help="Name of the engine")

    validate_config_group = validate_parser.add_mutually_exclusive_group(required=True)
    validate_config_group.add_argument("--config", help="Configuration as JSON string")
    validate_config_group.add_argument(
        "--config-file", help="Path to configuration JSON file"
    )

    validate_parser.set_defaults(func=cmd_validate_config)

    # Parse and execute
    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
