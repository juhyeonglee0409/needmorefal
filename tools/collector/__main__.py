"""Allow running as: python -m tools.collector collect --config ..."""

from .collector import main

raise SystemExit(main())
