#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Translation compilation utility for Medical Spytool
This script extracts translation strings and compiles translation files
"""

import os
import sys
import click
from pathlib import Path
from flask_babel import gettext
from babel.messages.frontend import CommandLineInterface


@click.group()
def cli():
    """Medical Spytool translation management."""
    pass


@cli.command()
def extract():
    """Extract translatable strings from the app and create POT file."""
    root_path = Path(__file__).resolve().parent
    babel_cfg = root_path / "babel.cfg"
    translations_dir = root_path / "backend" / "translations"

    if not babel_cfg.exists():
        click.echo(f"Error: babel.cfg not found at {babel_cfg}", err=True)
        sys.exit(1)

    if not translations_dir.exists():
        os.makedirs(translations_dir, exist_ok=True)
        click.echo(f"Created translations directory at {translations_dir}")

    click.echo("Extracting translatable strings...")
    sys.argv = [
        "pybabel",
        "extract",
        "-F",
        str(babel_cfg),
        "--keywords=_",
        "--keywords=gettext",
        "--keywords=ngettext",
        "-o",
        str(translations_dir / "messages.pot"),
        "backend",
    ]
    CommandLineInterface().run(sys.argv)
    click.echo("Extraction complete. POT file created.")


@cli.command()
@click.argument("lang")
def init(lang):
    """Initialize a new language."""
    root_path = Path(__file__).resolve().parent
    translations_dir = root_path / "backend" / "translations"
    pot_file = translations_dir / "messages.pot"

    if not pot_file.exists():
        click.echo("POT file not found. Run 'extract' first.", err=True)
        sys.exit(1)

    click.echo(f"Initializing translations for language '{lang}'...")
    sys.argv = ["pybabel", "init", "-i", str(pot_file), "-d", str(translations_dir), "-l", lang]
    CommandLineInterface().run(sys.argv)
    click.echo(f"Initialization complete. Edit {translations_dir}/{lang}/LC_MESSAGES/messages.po")


@cli.command()
def update():
    """Update all language catalogs from the POT file."""
    root_path = Path(__file__).resolve().parent
    translations_dir = root_path / "backend" / "translations"
    pot_file = translations_dir / "messages.pot"

    if not pot_file.exists():
        click.echo("POT file not found. Run 'extract' first.", err=True)
        sys.exit(1)

    click.echo("Updating all language translations...")
    sys.argv = ["pybabel", "update", "-i", str(pot_file), "-d", str(translations_dir)]
    CommandLineInterface().run(sys.argv)
    click.echo("Update complete. Edit the PO files as needed.")


@cli.command()
def compile():
    """Compile all translation catalogs to MO files."""
    root_path = Path(__file__).resolve().parent
    translations_dir = root_path / "backend" / "translations"

    if not translations_dir.exists():
        click.echo("Translations directory not found.", err=True)
        sys.exit(1)

    click.echo("Compiling translation files...")
    sys.argv = ["pybabel", "compile", "-d", str(translations_dir)]
    CommandLineInterface().run(sys.argv)
    click.echo("Compilation complete. MO files created.")


if __name__ == "__main__":
    cli()
