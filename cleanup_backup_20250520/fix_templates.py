#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Template Fixer

This script fixes template issues in the base.html file.
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("template_fix.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("TemplateFix")


def fix_base_template():
    """Fix the base.html template to use the correct URL endpoints"""
    base_template_path = Path("backend/templates/base.html")

    if not base_template_path.exists():
        logger.error(f"Base template not found: {base_template_path}")
        return False

    try:
        with open(base_template_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Fix the URL endpoint for the main index page
        fixed_content = content.replace(
            "href=\"{{ url_for('index') }}\"", "href=\"{{ url_for('main.index') }}\""
        )

        # Also fix any other similar issues with simple endpoints
        fixed_content = fixed_content.replace(
            "href=\"{{ url_for('search') }}\"", "href=\"{{ url_for('main.search') }}\""
        )

        fixed_content = fixed_content.replace(
            "href=\"{{ url_for('about') }}\"", "href=\"{{ url_for('main.about') }}\""
        )

        fixed_content = fixed_content.replace(
            "href=\"{{ url_for('export') }}\"", "href=\"{{ url_for('main.export') }}\""
        )

        fixed_content = fixed_content.replace(
            "href=\"{{ url_for('settings') }}\"", "href=\"{{ url_for('main.settings') }}\""
        )

        fixed_content = fixed_content.replace(
            "href=\"{{ url_for('login') }}\"", "href=\"{{ url_for('auth.login') }}\""
        )

        fixed_content = fixed_content.replace(
            "href=\"{{ url_for('logout') }}\"", "href=\"{{ url_for('auth.logout') }}\""
        )

        fixed_content = fixed_content.replace(
            "href=\"{{ url_for('register') }}\"", "href=\"{{ url_for('auth.register') }}\""
        )

        # Write the fixed content back to the file
        with open(base_template_path, "w", encoding="utf-8") as f:
            f.write(fixed_content)

        logger.info(f"Fixed base template: {base_template_path}")
        return True

    except Exception as e:
        logger.error(f"Error fixing base template: {e}")
        return False


def main():
    """Main function to fix templates"""
    print("\n" + "=" * 80)
    print("{:^80}".format("MEDICAL SPYTOOL - TEMPLATE FIXER"))
    print("=" * 80 + "\n")

    if fix_base_template():
        print("✅ Base template fixed successfully")
    else:
        print("❌ Error fixing base template")

    print("\n" + "=" * 80)
    print("{:^80}".format("TEMPLATE FIX COMPLETED"))
    print("=" * 80 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
