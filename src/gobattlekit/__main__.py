#!/usr/bin/env python
# Locale patch and logging setup live in gobattlekit.app at module scope, so
# importing app applies them before any screen code runs.
from gobattlekit.app import main
main().main_loop()

