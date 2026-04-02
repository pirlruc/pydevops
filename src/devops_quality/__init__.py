"""DevOps Quality-as-a-Service helper package (minimal wheel for tagging / PyPI templates).

This namespace exists so ``uv build`` can produce distributions for versioned tags.
Application repositories consume quality logic from the checked-out ``scripts/`` tree
in CI rather than from this package directly.
"""

__version__ = "0.1.0"
