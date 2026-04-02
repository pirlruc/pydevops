"""Allow ``python -m scripts.quality_gates``."""

from scripts.quality_gates.engine import main

if __name__ == "__main__":
    raise SystemExit(main())
