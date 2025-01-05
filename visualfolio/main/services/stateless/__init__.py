"""
This directory is dedicated to stateless and app-specific functionality.

Stateless: No database models are imported within this directory. All functionality
operates without requiring read or write access to the database. Inputs are passed
as arguments, and outputs are returned directly.

App-specific: The functionality in this directory is designed to the specific requirements
of this project and is not intended to be reusable outside of it, as opposed to `main/utils`.
"""
