#!/usr/bin/env python3

import argparse
import sys

import requests

from utils.config import load_credentials
from utils.canvas_api import CanvasAPI
from utils.canvas_downloader import download_course_files


def list_course_modules(api: CanvasAPI, course_id: int, output_dir="./downloads"):
    """List all modules for a specific course and allow downloading."""
    try:
        course = api.get_course(course_id)
        print(f"\nModules for: {course['name']} (ID: {course_id})")
        print("=" * 60)

        modules = api.get_modules(course_id)

        if not modules:
            print("No modules found in this course.")
            return

        print(f"Found {len(modules)} modules:\n")
        print(f"{'#':<4} {'Module ID':<12} {'Module Name'}")
        print("-" * 55)

        for i, mod in enumerate(modules, 1):
            print(f"{i:<4} {mod['id']:<12} {mod['name']}")

        # Module selection for download
        print("\n" + "=" * 60)
        print("Download Options:")
        print(f"  Enter module number (1-{len(modules)}) to download files from that module")
        print("  Enter 'all' to download files from all modules")
        print("  Enter 'q' to quit")

        try:
            selection = input("\nYour choice: ").strip()

            if selection.lower() == "q":
                print("Goodbye!")
                return
            elif selection.lower() == "all":
                download_course_files(api, course_id, output_dir)
                return

            try:
                module_num = int(selection)
                if 1 <= module_num <= len(modules):
                    selected = modules[module_num - 1]
                    download_course_files(
                        api, course_id, output_dir,
                        module_ids={selected["id"]},
                    )
                else:
                    print("Invalid module number. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number, 'all', or 'q'.")

        except KeyboardInterrupt:
            print("\nGoodbye!")

    except Exception as e:
        print(f"Error fetching modules for course {course_id}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="List Canvas courses and download module files"
    )
    parser.add_argument(
        "-c", "--config", default="credentials.yaml",
        help="Path to YAML credentials file (default: credentials.yaml)",
    )
    parser.add_argument(
        "--course-id", type=int,
        help="Show modules for specific course ID (skip course selection)",
    )
    parser.add_argument(
        "-o", "--output", default="./downloads",
        help="Output directory for downloaded files (default: ./downloads)",
    )

    args = parser.parse_args()

    # Load credentials
    creds = load_credentials(args.config)

    required = ["API_URL", "API_KEY"]
    missing = [k for k in required if not creds.get(k)]
    if missing:
        print(f"Error: {args.config} is missing required field(s): {', '.join(missing)}.")
        print(
            "Please create the YAML file with the following structure:\n"
            "API_URL: https://<your>.instructure.com\n"
            "API_KEY: <your key>\n"
        )
        sys.exit(1)

    API_URL = creds["API_URL"].strip().rstrip("/")
    API_KEY = creds["API_KEY"].strip()

    print("Connecting to Canvas...")

    try:
        api = CanvasAPI(API_URL, API_KEY)

        # Test authentication
        user = api.get_current_user()
        print(f"Successfully authenticated as: {user['name']} (ID: {user['id']})\n")

        # If specific course ID provided, jump straight to modules
        if args.course_id:
            list_course_modules(api, args.course_id, args.output)
            return

        # Fetch all courses (active + completed)
        print("Fetching courses...")
        all_courses = []
        for state in ("active", "completed"):
            for c in api.get_courses(enrollment_state=state, include="term"):
                if "name" in c and "id" in c:
                    term = c.get("term", {})
                    term_name = term.get("name", "") if isinstance(term, dict) else ""
                    all_courses.append({
                        "id": c["id"],
                        "name": c["name"],
                        "term": term_name,
                        "course_code": c.get("course_code", ""),
                    })

        # Sort by term then name
        all_courses.sort(key=lambda x: (x["term"], x["name"]))

        print(f"Found {len(all_courses)} courses:\n")
        print(f"{'#':<4} {'Course ID':<10} {'Term':<20} {'Course Name'}")
        print("-" * 85)

        current_term = None
        for i, course in enumerate(all_courses, 1):
            if course["term"] != current_term:
                current_term = course["term"]
                print(f"\n--- {current_term or 'No Term Information'} ---")

            friendly_name = course["name"]
            if course["course_code"] and course["course_code"] != course["name"]:
                friendly_name = f"{course['course_code']}: {course['name']}"

            print(f"{i:<4} {course['id']:<10} {course['term']:<20} {friendly_name}")

        # Interactive course selection
        print("\n" + "=" * 60)
        try:
            selection = input(
                f"Enter course number (1-{len(all_courses)}) or course ID to view modules (or 'q' to quit): "
            )

            if selection.lower() == "q":
                print("Goodbye!")
                return

            try:
                course_num = int(selection)
                if 1 <= course_num <= len(all_courses):
                    selected = all_courses[course_num - 1]
                    list_course_modules(api, selected["id"], args.output)
                    return
            except ValueError:
                pass

            try:
                course_id = int(selection)
                list_course_modules(api, course_id, args.output)
            except ValueError:
                print("Invalid input. Please enter a number.")

        except KeyboardInterrupt:
            print("\nGoodbye!")

    except requests.HTTPError as e:
        if e.response.status_code == 401:
            print("ERROR: Invalid or unauthorized Canvas API token.")
        else:
            print(f"ERROR: Canvas API error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
