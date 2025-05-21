#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - API Documentation Generator

This script analyzes the Flask routes in the MedicalSpy application and generates
comprehensive documentation about all available API endpoints. The documentation
can be output in Markdown or HTML format.
"""

import os
import re
import json
import inspect
import argparse
from pathlib import Path


def extract_routes_from_file(file_path):
    """
    Extract route information from a Python file

    Args:
        file_path (str): Path to the Python file

    Returns:
        list: List of route dictionaries with path, methods, function and docstring
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    routes = []

    # Pattern to match route decorators
    route_pattern = r'@(?:\w+_bp\.)?route\([\'"]([^\'"]+)[\'"](,\s*methods=\[([^\]]+)\])?\)'

    # Pattern to find function definitions
    func_pattern = r'def\s+(\w+)\([^)]*\):\s*(?:"""(.*?)""")?'

    # Find all route decorators
    for match in re.finditer(route_pattern, content, re.DOTALL):
        path = match.group(1)

        # Extract methods if available
        methods_str = match.group(3) if match.group(2) else "'GET'"
        methods = [m.strip().strip("'\"") for m in methods_str.split(",")]

        # Find the associated function (search after the route decorator)
        start_pos = match.end()
        func_match = re.search(func_pattern, content[start_pos:], re.DOTALL)

        if func_match:
            func_name = func_match.group(1)
            docstring = func_match.group(2).strip() if func_match.group(2) else ""

            # Analyze the docstring for parameters and responses
            params = []
            responses = []

            # Check for Swagger/Flasgger documentation
            swagger_match = re.search(r"---\s*(.*?)\s*(\n\s*$|\Z)", docstring, re.DOTALL)
            if swagger_match:
                try:
                    swagger_doc = swagger_match.group(1)
                    # Extract parameter information
                    param_match = re.search(
                        r"parameters:(.*?)(?:responses:|$)", swagger_doc, re.DOTALL
                    )
                    if param_match:
                        param_lines = param_match.group(1).strip().split("\n")
                        current_param = {}
                        for line in param_lines:
                            name_match = re.search(r"-\s*name:\s*(\w+)", line)
                            if name_match:
                                if current_param and "name" in current_param:
                                    params.append(current_param)
                                current_param = {"name": name_match.group(1)}

                            desc_match = re.search(r"description:\s*(.+)", line)
                            if desc_match and current_param:
                                current_param["description"] = desc_match.group(1)

                            type_match = re.search(r"type:\s*(\w+)", line)
                            if type_match and current_param:
                                current_param["type"] = type_match.group(1)

                        if current_param and "name" in current_param:
                            params.append(current_param)

                    # Extract response information
                    resp_match = re.search(r"responses:(.*?)(?:\w+:|$)", swagger_doc, re.DOTALL)
                    if resp_match:
                        resp_lines = resp_match.group(1).strip().split("\n")
                        current_resp = {}
                        for line in resp_lines:
                            code_match = re.search(r"(\d+):", line)
                            if code_match:
                                if current_resp and "code" in current_resp:
                                    responses.append(current_resp)
                                current_resp = {"code": code_match.group(1)}

                            desc_match = re.search(r"description:\s*(.+)", line)
                            if desc_match and current_resp:
                                current_resp["description"] = desc_match.group(1)

                        if current_resp and "code" in current_resp:
                            responses.append(current_resp)
                except:
                    # If parsing fails, just continue without the swagger info
                    pass

            routes.append(
                {
                    "path": path,
                    "methods": methods,
                    "function": func_name,
                    "docstring": docstring,
                    "file": file_path,
                    "parameters": params,
                    "responses": responses,
                }
            )

    return routes


def find_route_files(base_path):
    """
    Find all Python files that might contain routes

    Args:
        base_path (str): Base directory to search in

    Returns:
        list: Paths to Python files that might contain routes
    """
    route_files = []

    # Common patterns for files containing routes
    route_patterns = [r"app\.py$", r"routes\.py$", r"views\.py$", r"api\.py$", r"blueprint"]

    for root, _, files in os.walk(base_path):
        for filename in files:
            if filename.endswith(".py"):
                file_path = os.path.join(root, filename)
                # Check if the file matches any of our patterns
                if any(re.search(pattern, file_path) for pattern in route_patterns):
                    route_files.append(file_path)
                else:
                    # Also check files that might contain app.route or blueprint.route
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        try:
                            content = f.read()
                            if re.search(r"@.*route\(", content):
                                route_files.append(file_path)
                        except Exception as e:
                            print(f"Error reading {file_path}: {e}")

    return route_files


def generate_markdown(routes):
    """
    Generate Markdown documentation from extracted routes

    Args:
        routes (list): List of route dictionaries

    Returns:
        str: Markdown documentation
    """
    md = "# MedicalSpy API Documentation\n\n"
    md += "This document provides details about all API endpoints available in the MedicalSpy application.\n\n"

    # Group routes by their first path component
    grouped_routes = {}
    for route in routes:
        path = route["path"]
        components = path.strip("/").split("/")
        group = components[0] if components else "root"

        if group not in grouped_routes:
            grouped_routes[group] = []

        grouped_routes[group].append(route)

    # Generate a table of contents
    md += "## Table of Contents\n\n"
    for group in sorted(grouped_routes.keys()):
        md += f"- [{group.capitalize()}](#{group.lower()})\n"

    md += "\n"

    # Generate documentation for each group
    for group in sorted(grouped_routes.keys()):
        md += f"## {group.capitalize()}\n\n"

        for route in grouped_routes[group]:
            path = route["path"]
            methods = ", ".join(route["methods"])
            function = route["function"]
            docstring = route["docstring"]
            file_path = route["file"]

            md += f"### `{methods}` {path}\n\n"
            md += f"**Function:** `{function}`\n\n"
            md += f"**File:** `{os.path.relpath(file_path)}`\n\n"

            if docstring:
                # Remove any swagger YAML if present
                clean_docstring = re.sub(r"---.*?(\n\s*$|\Z)", "", docstring, flags=re.DOTALL)
                md += f"**Description:**\n\n{clean_docstring.strip()}\n\n"

            # Parameters section
            if route["parameters"]:
                md += "**Parameters:**\n\n"
                md += "| Name | Type | Description |\n"
                md += "|------|------|-------------|\n"

                for param in route["parameters"]:
                    name = param.get("name", "")
                    param_type = param.get("type", "")
                    description = param.get("description", "")
                    md += f"| {name} | {param_type} | {description} |\n"

                md += "\n"

            # Response section
            if route["responses"]:
                md += "**Responses:**\n\n"
                md += "| Code | Description |\n"
                md += "|------|-------------|\n"

                for resp in route["responses"]:
                    code = resp.get("code", "")
                    description = resp.get("description", "")
                    md += f"| {code} | {description} |\n"

                md += "\n"

            md += "---\n\n"

    return md


def generate_html(routes):
    """
    Generate HTML documentation from extracted routes

    Args:
        routes (list): List of route dictionaries

    Returns:
        str: HTML documentation
    """
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MedicalSpy API Documentation</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            border-bottom: 1px solid #eaecef;
            padding-bottom: 10px;
        }
        h2 {
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            padding-bottom: 7px;
            border-bottom: 1px solid #eaecef;
        }
        h3 {
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 16px;
        }
        th, td {
            text-align: left;
            padding: 8px;
            border: 1px solid #ddd;
        }
        th {
            background-color: #f2f2f2;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        code {
            font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
            padding: 0.2em 0.4em;
            margin: 0;
            background-color: rgba(27, 31, 35, 0.05);
            border-radius: 3px;
        }
        .http-method {
            display: inline-block;
            padding: 3px 6px;
            border-radius: 3px;
            color: white;
            font-weight: bold;
        }
        .get { background-color: #61affe; }
        .post { background-color: #49cc90; }
        .put { background-color: #fca130; }
        .delete { background-color: #f93e3e; }
        .endpoint {
            font-family: monospace;
            margin-left: 8px;
        }
        hr {
            margin: 20px 0;
            border: 0;
            border-top: 1px solid #eaecef;
        }
        pre {
            padding: 16px;
            overflow: auto;
            font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
            background-color: #f6f8fa;
            border-radius: 3px;
        }
        .toc {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .toc ul {
            padding-left: 20px;
        }
    </style>
</head>
<body>
    <h1>MedicalSpy API Documentation</h1>
    <p>This document provides details about all API endpoints available in the MedicalSpy application.</p>
    
    <div class="toc">
        <h2>Table of Contents</h2>
        <ul>
"""

    # Group routes by their first path component
    grouped_routes = {}
    for route in routes:
        path = route["path"]
        components = path.strip("/").split("/")
        group = components[0] if components else "root"

        if group not in grouped_routes:
            grouped_routes[group] = []

        grouped_routes[group].append(route)

    # Generate table of contents
    for group in sorted(grouped_routes.keys()):
        group_id = group.lower().replace(" ", "-")
        html += f'            <li><a href="#{group_id}">{group.capitalize()}</a></li>\n'

    html += """
        </ul>
    </div>
"""

    # Generate documentation for each group
    for group in sorted(grouped_routes.keys()):
        group_id = group.lower().replace(" ", "-")
        html += f'    <h2 id="{group_id}">{group.capitalize()}</h2>\n'

        for route in grouped_routes[group]:
            path = route["path"]
            methods = route["methods"]
            function = route["function"]
            docstring = route["docstring"]
            file_path = route["file"]

            html += '    <div class="endpoint-container">\n'
            html += "        <h3>"

            for method in methods:
                method_lower = method.lower()
                html += f'<span class="http-method {method_lower}">{method}</span>'

            html += f'<span class="endpoint">{path}</span></h3>\n'
            html += f"        <p><strong>Function:</strong> <code>{function}</code></p>\n"
            html += (
                f"        <p><strong>File:</strong> <code>{os.path.relpath(file_path)}</code></p>\n"
            )

            if docstring:
                # Remove any swagger YAML if present
                clean_docstring = re.sub(r"---.*?(\n\s*$|\Z)", "", docstring, flags=re.DOTALL)
                html += '        <div class="description">\n'
                html += "            <p><strong>Description:</strong></p>\n"
                html += f"            <pre>{clean_docstring.strip()}</pre>\n"
                html += "        </div>\n"

            # Parameters section
            if route["parameters"]:
                html += '        <div class="parameters">\n'
                html += "            <p><strong>Parameters:</strong></p>\n"
                html += "            <table>\n"
                html += "                <tr><th>Name</th><th>Type</th><th>Description</th></tr>\n"

                for param in route["parameters"]:
                    name = param.get("name", "")
                    param_type = param.get("type", "")
                    description = param.get("description", "")
                    html += f"                <tr><td>{name}</td><td>{param_type}</td><td>{description}</td></tr>\n"

                html += "            </table>\n"
                html += "        </div>\n"

            # Response section
            if route["responses"]:
                html += '        <div class="responses">\n'
                html += "            <p><strong>Responses:</strong></p>\n"
                html += "            <table>\n"
                html += "                <tr><th>Code</th><th>Description</th></tr>\n"

                for resp in route["responses"]:
                    code = resp.get("code", "")
                    description = resp.get("description", "")
                    html += f"                <tr><td>{code}</td><td>{description}</td></tr>\n"

                html += "            </table>\n"
                html += "        </div>\n"

            html += "        <hr>\n"
            html += "    </div>\n"

    html += """
</body>
</html>
"""

    return html


def main():
    parser = argparse.ArgumentParser(description="Generate API documentation for MedicalSpy")
    parser.add_argument(
        "--format",
        "-f",
        choices=["markdown", "html"],
        default="markdown",
        help="Output format (markdown or html)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="docs/API_DOCUMENTATION",
        help="Output file path without extension",
    )
    args = parser.parse_args()

    # Find the project root (where this script is located)
    script_path = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_path)

    print(f"Scanning for route files in {project_root}...")
    route_files = find_route_files(project_root)
    print(f"Found {len(route_files)} potential route files")

    all_routes = []
    for file_path in route_files:
        try:
            routes = extract_routes_from_file(file_path)
            if routes:
                print(f"Found {len(routes)} routes in {os.path.relpath(file_path)}")
                all_routes.extend(routes)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    print(f"Total routes found: {len(all_routes)}")

    # Generate documentation
    if args.format == "markdown":
        output = generate_markdown(all_routes)
        output_file = f"{args.output}.md"
    else:
        output = generate_html(all_routes)
        output_file = f"{args.output}.html"

    # Create the output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Write the output file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"Documentation generated: {output_file}")


if __name__ == "__main__":
    main()
