# compose/cli.py
import sys
import time
import os
from .engine import build
from .linter import lint_file

def main():
    if len(sys.argv) < 2:
        print("Usage: compose <command> [options]")
        print("Commands:")
        print("  build <file.md> --config <config.toml>  Build document")
        print("  lint <file.md>                         Lint markdown file")
        print("  watch <file.md> --config <config.toml> Watch and rebuild on changes")
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
        if len(sys.argv) < 3:
            print("Usage: compose lint <file.md>")
            return
        md_path = sys.argv[2]
        issues = lint_file(md_path)
        if issues:
            print(f"Found {len(issues)} issues:")
            for issue in issues:
                print(f"  {issue}")
            sys.exit(1)  # Non-zero exit for lint failures
        else:
            print("No issues found.")
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
