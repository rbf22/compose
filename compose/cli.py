# compose/cli.py
import sys
from .engine import build

def main():
    if len(sys.argv) < 3:
        print("Usage: compose build <file.md> --config <config.yml>")
        return
    md_path = sys.argv[2]
    cfg_path = sys.argv[4]
    build(md_path, cfg_path)

if __name__ == "__main__":
    main()
