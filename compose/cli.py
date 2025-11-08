# compose/cli.py
import sys
import time
import os
from pathlib import Path
from .engine import build
from .lint.config import LintConfig, find_project_config_with_lint
from .lint.linter import MarkdownLinter, format_violations
from .lint.filefinder import MarkdownFileFinder


def main():
    if len(sys.argv) < 2:
        print("Usage: compose <command> [options]")
        print("Commands:")
        print("  build <file.md> --config <config.toml>  Build document")
        print("  lint <path> [--config <config.toml>]    Lint markdown files")
        print("  watch <file.md> --config <config.toml>  Watch and rebuild on changes")
        return

    command = sys.argv[1]

    if command == 'build':
        if len(sys.argv) < 5:
            print("Usage: compose build <file.md> --config <config.toml>")
            return
        md_path = sys.argv[2]
        cfg_path = sys.argv[4]
        build(md_path, cfg_path)
    elif command == 'lint':
        lint_command()
    elif command == 'watch':
        if len(sys.argv) < 5:
            print("Usage: compose watch <file.md> --config <config.toml>")
            return
        md_path = sys.argv[2]
        cfg_path = sys.argv[4]
        watch_and_build(md_path, cfg_path)
    else:
        print(f"Unknown command: {command}")
        print("Available commands: build, lint, watch")
        sys.exit(1)


def lint_command():
    """Handle the lint command"""
    # Parse arguments
    args = sys.argv[2:]
    config_path = None
    paths = []

    i = 0
    while i < len(args):
        if args[i] == '--config' and i + 1 < len(args):
            config_path = args[i + 1]
            i += 2
        else:
            paths.append(args[i])
            i += 1

    if not paths:
        print("Usage: compose lint <path> [--config <config.toml>]")
        print("  <path> can be a file or directory")
        print("  --config specifies the linter configuration file")
        return

    # Load configuration
    if config_path:
        try:
            config = LintConfig.load_from_file(config_path)
        except Exception as e:
            print(f"Error loading config: {e}")
            sys.exit(1)
    else:
        # Prefer [lint] in the project TOML in current directory
        project_toml = find_project_config_with_lint()
        if project_toml:
            try:
                config = LintConfig.load_from_file(project_toml)
                print(f"Using lint config from: {project_toml} [lint]")
            except Exception as e:
                print(f"Warning: Could not load lint config from {project_toml}: {e}")
                config = LintConfig.create_default()
        else:
            # No [lint] section found in project; use defaults
            config = LintConfig.create_default()

    # Find markdown files
    all_files = []
    for path in paths:
        files = MarkdownFileFinder.find_files(path)
        all_files.extend(files)

    if not all_files:
        print("No Markdown files found.")
        return

    # Create linter and run
    linter = MarkdownLinter(config)
    results = linter.lint_files(all_files)

    # Output results
    if results:
        output = format_violations(results, "standard")
        print(output)
        sys.exit(1)  # Non-zero exit for lint failures
    else:
        print(f"✓ Linted {len(all_files)} files. No issues found.")


def watch_and_build(md_path: str, cfg_path: str):
    """Watch files for changes and rebuild automatically"""
    print(f"Watching {md_path} and {cfg_path} for changes...")
    print("Press Ctrl+C to stop watching")

    # Get initial modification times
    try:
        md_mtime = os.path.getmtime(md_path)
        cfg_mtime = os.path.getmtime(cfg_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    build_count = 0

    try:
        while True:
            time.sleep(0.5)  # Check every 500ms

            try:
                new_md_mtime = os.path.getmtime(md_path)
                new_cfg_mtime = os.path.getmtime(cfg_path)

                if new_md_mtime != md_mtime or new_cfg_mtime != cfg_mtime:
                    build_count += 1
                    print(f"\n--- Build #{build_count} ---")
                    try:
                        build(md_path, cfg_path)
                        print("✓ Build successful")
                    except Exception as e:
                        print(f"✗ Build failed: {e}")

                    # Update modification times
                    md_mtime = new_md_mtime
                    cfg_mtime = new_cfg_mtime

            except FileNotFoundError:
                # File was deleted, wait for it to be recreated
                pass
            except Exception as e:
                print(f"Watch error: {e}")

    except KeyboardInterrupt:
        print("\nStopped watching.")

if __name__ == "__main__":
    main()
