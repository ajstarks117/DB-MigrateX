DB-MigrateX (schema-migration-manager)

This project provides a small migration manager for SQL schema changes.

Dependencies
- Python 3.8+ recommended (some packages may not have wheels for very new Python versions)
- See `requirements.txt` for pinned packages. Notably:
  - PyYAML==6.0 is required by the migration parser.

Installing dependencies

On Windows, installing PyYAML may try to build from source and fail if a matching binary wheel isn't available for your Python version. If you see errors like "Failed to build PyYAML", try one of the following:

1) Use a supported Python version that has prebuilt wheels (e.g., 3.11).
2) Install a binary wheel for PyYAML that matches your Python version/architecture.
   Example (replace with actual wheel file):

   .\venv\Scripts\python.exe -m pip install PyYAML-6.0-cp311-cp311-win_amd64.whl

3) Install the required C build tools (Visual Studio Build Tools) so pip can compile the package.

4) Alternatively, if you don't want to install system-level build tools, run the project in a container or a different environment that already has PyYAML.

Running tests

Set PYTHONPATH to the repository root and run pytest (PowerShell):

$env:PYTHONPATH = (Get-Location).Path; pytest -q

If pytest fails with "No module named 'yaml'", install PyYAML in the environment used to run tests (see notes above).
