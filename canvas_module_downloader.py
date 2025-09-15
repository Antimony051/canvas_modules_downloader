#!/usr/bin/env python3

import argparse
import sys
from canvasapi import Canvas
from canvasapi.exceptions import InvalidAccessToken, Unauthorized, CanvasException

# Import our utility modules
from utils.config import load_credentials
from utils.canvas_downloader import download_module_files, download_all_module_files


def list_course_modules(canvas, course_id, canvas_base_url, output_dir="./downloads"):
    """List all modules for a specific course and allow downloading."""
    try:
        course = canvas.get_course(course_id)
        print(f"\nModules for: {course.name} (ID: {course_id})")
        print("=" * 60)
        
        modules = course.get_modules()
        modules_list = list(modules)
        
        if not modules_list:
            print("No modules found in this course.")
            return
        
        print(f"Found {len(modules_list)} modules:\n")
        print(f"{'#':<4} {'Module ID':<12} {'Module Name'}")
        print("-" * 55)
        
        for i, module in enumerate(modules_list, 1):
            module_id = getattr(module, 'id', 'N/A')
            module_name = getattr(module, 'name', 'Unnamed Module')
            print(f"{i:<4} {module_id:<12} {module_name}")
        
        # Module selection for download
        print("\n" + "="*60)
        print("Download Options:")
        print("• Enter module number (1-{}) to download files from that module".format(len(modules_list)))
        print("• Enter 'all' to download files from all modules")
        print("• Enter 'q' to quit")
        
        try:
            selection = input("\nYour choice: ").strip()
            
            if selection.lower() == 'q':
                print("Goodbye!")
                return
            elif selection.lower() == 'all':
                download_all_module_files(canvas, course_id, canvas_base_url, output_dir)
                return
            
            # Try to parse as module number
            try:
                module_num = int(selection)
                if 1 <= module_num <= len(modules_list):
                    selected_module = modules_list[module_num - 1]
                    download_module_files(canvas, course_id, selected_module.id, canvas_base_url, output_dir)
                else:
                    print("Invalid module number. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number, 'all', or 'q'.")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            
    except Exception as e:
        print(f"Error fetching modules for course {course_id}: {e}")


def main():
    parser = argparse.ArgumentParser(description="List Canvas courses and download module files")
    parser.add_argument("-c", "--config", default="credentials.yaml", 
                       help="Path to YAML credentials file (default: credentials.yaml)")
    parser.add_argument("--course-id", type=int,
                       help="Show modules for specific course ID (skip course selection)")
    parser.add_argument("-o", "--output", default="./downloads",
                       help="Output directory for downloaded files (default: ./downloads)")
    
    args = parser.parse_args()
    
    # Load credentials
    creds = load_credentials(args.config)
    
    # Validate required credentials
    required = ["API_URL", "API_KEY", "USER_ID"]
    missing = [k for k in required if not creds.get(k)]
    
    if missing:
        print(f"Error: {args.config} is missing required field(s): {', '.join(missing)}.")
        print("Please create the YAML file with the following structure:\n"
              "API_URL: https://<your>.instructure.com\n"
              "API_KEY: <your key>\n"
              "USER_ID: 123456\n")
        sys.exit(1)
    
    # Extract credentials
    API_URL = creds["API_URL"].strip().rstrip('/')
    API_KEY = creds["API_KEY"].strip()
    USER_ID = creds["USER_ID"]
    
    print("Connecting to Canvas...")
    
    try:
        # Initialize Canvas API
        canvas = Canvas(API_URL, API_KEY)
        
        # Test authentication
        user = canvas.get_current_user()
        print(f"Successfully authenticated as: {user.name} (ID: {user.id})\n")
        
        if user.id != USER_ID:
            print(f"Warning: Authenticated user ID ({user.id}) does not match configured USER_ID ({USER_ID})\n")
        
        # Get all courses (active and completed)
        print("Fetching courses...")
        courses_lists = [
            canvas.get_courses(enrollment_state="active", include="term"),
            canvas.get_courses(enrollment_state="completed", include="term")
        ]
        
        all_courses = []
        for courses in courses_lists:
            for course in courses:
                if hasattr(course, "name") and hasattr(course, "id"):
                    # Get term name if available
                    term_name = ""
                    if hasattr(course, "term") and hasattr(course.term, "name"):
                        term_name = course.term.name
                    
                    all_courses.append({
                        'id': course.id,
                        'name': course.name,
                        'term': term_name,
                        'course_code': getattr(course, 'course_code', '')
                    })
        
        # Sort by term and then by name
        all_courses.sort(key=lambda x: (x['term'], x['name']))
        
        # If specific course ID provided, show modules for that course only
        if args.course_id:
            list_course_modules(canvas, args.course_id, API_URL, args.output)
            return
        
        print(f"Found {len(all_courses)} courses:\n")
        print(f"{'#':<4} {'Course ID':<10} {'Term':<20} {'Course Name'}")
        print("-" * 85)
        
        current_term = None
        for i, course in enumerate(all_courses, 1):
            # Print term header when it changes
            if course['term'] != current_term:
                current_term = course['term']
                if current_term:
                    print(f"\n--- {current_term} ---")
                else:
                    print(f"\n--- No Term Information ---")
            
            # Combine course code and name for friendly display
            friendly_name = course['name']
            if course['course_code'] and course['course_code'] != course['name']:
                friendly_name = f"{course['course_code']}: {course['name']}"
            
            print(f"{i:<4} {course['id']:<10} {course['term']:<20} {friendly_name}")
        
        # Interactive course selection
        print("\n" + "="*60)
        try:
            selection = input("Enter course number (1-{}) or course ID to view modules (or 'q' to quit): ".format(len(all_courses)))
            
            if selection.lower() == 'q':
                print("Goodbye!")
                return
            
            # Try to parse as course number first
            try:
                course_num = int(selection)
                if 1 <= course_num <= len(all_courses):
                    selected_course = all_courses[course_num - 1]
                    list_course_modules(canvas, selected_course['id'], API_URL, args.output)
                    return
            except ValueError:
                pass
            
            # Try to parse as course ID
            try:
                course_id = int(selection)
                list_course_modules(canvas, course_id, API_URL, args.output)
            except ValueError:
                print("Invalid input. Please enter a number.")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
        
    except InvalidAccessToken:
        print("ERROR: Invalid Canvas API token. Please check your credentials.yaml file.")
        sys.exit(1)
    except Unauthorized:
        print("ERROR: Not authorized. Please check your Canvas API token permissions.")
        sys.exit(1)
    except CanvasException as e:
        print(f"ERROR: Canvas API error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()