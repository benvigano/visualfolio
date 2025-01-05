"""
This directory is dedicated to stateless and reusable functionality.

Stateless: No database models are imported within this directory. All functionality
operates without requiring read or write access to the database. Inputs are passed
as arguments, and outputs are returned directly.

Generic: The functionality in this directory is not tied to the design of this project
and is intended to be reusable outside of it, as opposed to `services/stateless`.
"""
