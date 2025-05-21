#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedicalSpy - Accessibility Audit Tool
This script provides a comprehensive accessibility audit for the MedicalSpy application.
It checks HTML for common accessibility issues and provides recommendations for improvements.
"""

import os
import re
import sys
import argparse
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import defaultdict
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join("logs", f'accessibility_audit_{datetime.now().strftime("%Y%m%d")}.log')
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("accessibility_audit")


class AccessibilityAuditor:
    """Class to perform accessibility audits on web pages"""

    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.visited_urls = set()
        self.issues = defaultdict(list)
        self.total_pages = 0
        self.session = requests.Session()

    def check_page(self, url):
        """Check a single page for accessibility issues"""
        if url in self.visited_urls:
            return

        self.visited_urls.add(url)
        self.total_pages += 1

        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Failed to fetch {url}: Status code {response.status_code}")
                return

            soup = BeautifulSoup(response.text, "html.parser")
            self._check_images(soup, url)
            self._check_links(soup, url)
            self._check_forms(soup, url)
            self._check_headings(soup, url)
            self._check_landmarks(soup, url)
            self._check_aria_attributes(soup, url)
            self._check_keyboard_navigation(soup, url)
            self._check_color_contrast(soup, url)

            # Crawl additional pages if local
            if self._is_local_url(url):
                for link in soup.find_all("a", href=True):
                    next_url = urljoin(url, link["href"])
                    if (
                        self._is_local_url(next_url)
                        and next_url not in self.visited_urls
                        and not self._is_external_resource(next_url)
                    ):
                        self.check_page(next_url)

        except Exception as e:
            logger.error(f"Error checking {url}: {str(e)}")

    def _is_local_url(self, url):
        """Check if URL is part of the same application"""
        parsed_base = urlparse(self.base_url)
        parsed_url = urlparse(url)
        return parsed_url.netloc == parsed_base.netloc or not parsed_url.netloc

    def _is_external_resource(self, url):
        """Check if URL is a non-HTML resource"""
        extensions = [".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".ico"]
        path = urlparse(url).path.lower()
        return any(path.endswith(ext) for ext in extensions)

    def _check_images(self, soup, url):
        """Check images for alt text"""
        for img in soup.find_all("img"):
            if not img.get("alt"):
                self.issues[url].append(
                    {
                        "type": "Missing alt text",
                        "element": str(img)[:100] + "...",
                        "recommendation": "Add descriptive alt text to image",
                    }
                )

    def _check_links(self, soup, url):
        """Check links for accessibility issues"""
        for link in soup.find_all("a"):
            # Check for empty links
            if not link.text.strip() and not link.find("img"):
                self.issues[url].append(
                    {
                        "type": "Empty link",
                        "element": str(link)[:100] + "...",
                        "recommendation": "Add descriptive text to link",
                    }
                )

            # Check for generic link text
            if link.text.strip().lower() in ["click here", "mehr", "weiter", "hier klicken"]:
                self.issues[url].append(
                    {
                        "type": "Generic link text",
                        "element": str(link)[:100] + "...",
                        "recommendation": "Use more descriptive link text",
                    }
                )

    def _check_forms(self, soup, url):
        """Check form elements for accessibility issues"""
        for form in soup.find_all("form"):
            # Check for missing labels
            for input_field in form.find_all(["input", "select", "textarea"]):
                input_id = input_field.get("id")
                if input_id and not input_field.get("type") == "hidden":
                    if not soup.find("label", attrs={"for": input_id}):
                        self.issues[url].append(
                            {
                                "type": "Missing form label",
                                "element": str(input_field)[:100] + "...",
                                "recommendation": f'Add label for the input with id "{input_id}"',
                            }
                        )

    def _check_headings(self, soup, url):
        """Check heading structure"""
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        if not headings:
            self.issues[url].append(
                {
                    "type": "No headings",
                    "element": "Page",
                    "recommendation": "Add headings to structure content",
                }
            )

        # Check for h1
        if not soup.find("h1"):
            self.issues[url].append(
                {
                    "type": "Missing H1",
                    "element": "Page",
                    "recommendation": "Add a main H1 heading for the page",
                }
            )

        # Check heading hierarchy
        heading_levels = [int(h.name[1]) for h in headings]
        for i, level in enumerate(heading_levels):
            if i > 0 and level > heading_levels[i - 1] + 1:
                self.issues[url].append(
                    {
                        "type": "Skipped heading level",
                        "element": f"Found {headings[i].name} after {headings[i-1].name}",
                        "recommendation": "Maintain proper heading hierarchy",
                    }
                )

    def _check_landmarks(self, soup, url):
        """Check for proper landmark regions"""
        landmarks = {
            "header": soup.find("header"),
            "main": soup.find("main"),
            "footer": soup.find("footer"),
            "nav": soup.find("nav"),
        }

        for name, element in landmarks.items():
            if not element:
                self.issues[url].append(
                    {
                        "type": f"Missing {name} landmark",
                        "element": "Page",
                        "recommendation": f"Add semantic <{name}> element to improve accessibility",
                    }
                )

    def _check_aria_attributes(self, soup, url):
        """Check ARIA attributes usage"""
        elements_requiring_label = soup.find_all(
            attrs={"role": ["button", "tab", "checkbox", "radio"]}
        )
        for elem in elements_requiring_label:
            if not (elem.get("aria-label") or elem.get("aria-labelledby")):
                self.issues[url].append(
                    {
                        "type": "Missing ARIA label",
                        "element": str(elem)[:100] + "...",
                        "recommendation": f'Add aria-label or aria-labelledby to element with role "{elem.get("role")}"',
                    }
                )

    def _check_keyboard_navigation(self, soup, url):
        """Check keyboard navigation issues"""
        # Check for tabindex > 0 (generally a bad practice)
        for elem in soup.find_all(attrs={"tabindex": True}):
            try:
                if int(elem["tabindex"]) > 0:
                    self.issues[url].append(
                        {
                            "type": "Positive tabindex",
                            "element": str(elem)[:100] + "...",
                            "recommendation": "Avoid using tabindex > 0 as it disrupts natural tab order",
                        }
                    )
            except ValueError:
                pass  # Ignore invalid tabindex values

        # Check for missing keyboard handlers
        for elem in soup.find_all(attrs={"onclick": True}):
            if not elem.get("onkeydown") and not elem.get("onkeypress") and not elem.get("onkeyup"):
                elem_type = elem.name
                self.issues[url].append(
                    {
                        "type": "Missing keyboard handler",
                        "element": str(elem)[:100] + "...",
                        "recommendation": f"Add keyboard event handlers to {elem_type} element with onclick",
                    }
                )

    def _check_color_contrast(self, soup, url):
        """Flag potential color contrast issues (simplified check)"""
        # Note: This is just a suggestion - accurate contrast checking requires
        # computed styles which would need a browser automation tool like Selenium
        if "text-muted" in soup.text or "text-light" in soup.text:
            self.issues[url].append(
                {
                    "type": "Potential contrast issue",
                    "element": "Page uses text-muted or text-light classes",
                    "recommendation": "Verify that text colors have sufficient contrast with background",
                }
            )

    def generate_report(self):
        """Generate accessibility audit report"""
        print("\n===== ACCESSIBILITY AUDIT REPORT =====")
        print(f"Base URL: {self.base_url}")
        print(f"Pages scanned: {self.total_pages}")
        print(f"Pages with issues: {len(self.issues)}")
        print(f"Total issues found: {sum(len(issues) for issues in self.issues.values())}")
        print("\n--- ISSUES BY PAGE ---")

        for url, page_issues in sorted(self.issues.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"\n{url} ({len(page_issues)} issues):")
            for issue in page_issues:
                print(f"  - {issue['type']}")
                print(f"    Element: {issue['element']}")
                print(f"    Recommendation: {issue['recommendation']}")
                print()

        print("\n--- SUMMARY OF ISSUE TYPES ---")
        issue_types = defaultdict(int)
        for issues in self.issues.values():
            for issue in issues:
                issue_types[issue["type"]] += 1

        for issue_type, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True):
            print(f"- {issue_type}: {count} occurrences")

        print("\n===== END OF REPORT =====")


def main():
    """Main function for CLI usage"""
    parser = argparse.ArgumentParser(description="Accessibility Audit Tool for MedicalSpy")
    parser.add_argument("--url", default="http://localhost:5000", help="Base URL to audit")
    parser.add_argument("--page", help="Specific page to check (e.g., /search)")
    parser.add_argument("--output", help="Output file for report")
    args = parser.parse_args()

    auditor = AccessibilityAuditor(args.url)

    if args.page:
        url = urljoin(args.url, args.page)
        print(f"Checking single page: {url}")
        auditor.check_page(url)
    else:
        print(f"Starting accessibility audit from {args.url}")
        auditor.check_page(args.url)

    # Redirect output to file if specified
    if args.output:
        with open(args.output, "w") as f:
            sys.stdout = f
            auditor.generate_report()
            sys.stdout = sys.__stdout__
            print(f"Report saved to {args.output}")
    else:
        auditor.generate_report()


if __name__ == "__main__":
    main()
