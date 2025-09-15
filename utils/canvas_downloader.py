import os
import re
from .file_utils import make_valid_filename, download_file_from_url
from .page_parser import extract_canvas_file_links


def download_page_files(canvas, course_id, page_url, module_dir, canvas_base_url):
    """Download files linked within a Canvas page."""
    try:
        course = canvas.get_course(course_id)
        page = course.get_page(page_url)
        
        if not hasattr(page, 'body') or not page.body:
            return 0
        
        print(f"    Scanning page '{page.title}' for file links...")
        file_links = extract_canvas_file_links(page.body, canvas_base_url)
        
        if not file_links:
            print(f"      No file links found in page")
            return 0
        
        print(f"      Found {len(file_links)} file link(s)")
        files_downloaded = 0
        
        # Create pages subdirectory
        pages_dir = os.path.join(module_dir, "pages")
        
        for file_info in file_links:
            try:
                # Use file_id if available to get proper file object
                if file_info.get('file_id'):
                    try:
                        file_obj = course.get_file(file_info['file_id'])
                        filename = make_valid_filename(file_obj.display_name)
                        download_url = file_obj.url
                        print(f"      Found file: {filename} (ID: {file_info['file_id']})")
                    except Exception as e:
                        print(f"      ❌ Could not get file object for ID {file_info['file_id']}: {e}")
                        # Fallback to extracted info
                        filename = make_valid_filename(file_info['filename'])
                        download_url = file_info['url']
                else:
                    filename = make_valid_filename(file_info['filename'])
                    download_url = file_info['url']
                
                file_path = os.path.join(pages_dir, filename)
                
                if not os.path.exists(file_path):
                    if download_file_from_url(download_url, file_path, filename):
                        files_downloaded += 1
                else:
                    print(f"      File already exists: {filename}")
                    files_downloaded += 1
                    
            except Exception as e:
                print(f"      ❌ Error downloading file from page: {e}")
        
        return files_downloaded
        
    except Exception as e:
        print(f"    ❌ Error processing page: {e}")
        return 0


def download_module_files(canvas, course_id, module_id, canvas_base_url, output_dir="./downloads"):
    """Download all files from a specific module."""
    try:
        course = canvas.get_course(course_id)
        module = course.get_module(module_id)
        
        print(f"\nDownloading files from module: {module.name}")
        print("=" * 60)
        
        # Create output directory structure
        course_name = make_valid_filename(course.name)
        module_name = make_valid_filename(module.name)
        module_dir = os.path.join(output_dir, course_name, "modules", module_name)
        files_dir = os.path.join(module_dir, "files")
        
        # Get module items
        module_items = module.get_module_items()
        file_count = 0
        
        for item in module_items:
            item_type = getattr(item, 'type', '')
            
            if item_type == "File":
                try:
                    print(f"  Processing File: {item.title}")
                    # Get the actual file object
                    file_obj = course.get_file(item.content_id)
                    filename = make_valid_filename(file_obj.display_name)
                    file_path = os.path.join(files_dir, filename)
                    
                    if not os.path.exists(file_path):
                        if download_file_from_url(file_obj.url, file_path, filename):
                            file_count += 1
                    else:
                        print(f"    File already exists: {filename}")
                        file_count += 1
                        
                except Exception as e:
                    print(f"    ❌ Error downloading file {item.title}: {e}")
            
            elif item_type == "Page":
                try:
                    print(f"  Processing Page: {item.title}")
                    # Extract page URL from the item's URL
                    page_url = getattr(item, 'page_url', None)
                    if not page_url and hasattr(item, 'url'):
                        # Extract page slug from full URL
                        url_parts = item.url.split('/')
                        if 'pages' in url_parts:
                            page_index = url_parts.index('pages')
                            if page_index + 1 < len(url_parts):
                                page_url = url_parts[page_index + 1]
                    
                    if page_url:
                        page_files = download_page_files(canvas, course_id, page_url, module_dir, canvas_base_url)
                        file_count += page_files
                    else:
                        print(f"    ⚠️ Could not determine page URL for: {item.title}")
                        
                except Exception as e:
                    print(f"    ❌ Error processing page {item.title}: {e}")
        
        print(f"\n✓ Module download complete. {file_count} files processed.")
        if file_count > 0:
            print(f"Files saved to: {module_dir}")
            
    except Exception as e:
        print(f"Error downloading module files: {e}")


def download_all_module_files(canvas, course_id, canvas_base_url, output_dir="./downloads"):
    """Download files from all modules in a course."""
    try:
        course = canvas.get_course(course_id)
        print(f"\nDownloading files from all modules in: {course.name}")
        print("=" * 60)
        
        modules = course.get_modules()
        modules_list = list(modules)
        
        if not modules_list:
            print("No modules found in this course.")
            return
                
        total_files = 0
        for module in modules_list:
            print(f"\n--- Processing Module: {module.name} ---")
            
            # Create output directory structure
            course_name = make_valid_filename(course.name)
            module_name = make_valid_filename(module.name)
            module_dir = os.path.join(output_dir, course_name, "modules", module_name)
            files_dir = os.path.join(module_dir, "files")
            
            # Get module items
            module_items = module.get_module_items()
            module_file_count = 0
            
            for item in module_items:
                item_type = getattr(item, 'type', '')
                
                if item_type == "File":
                    try:
                        print(f"  Processing File: {item.title}")
                        # Get the actual file object
                        file_obj = course.get_file(item.content_id)
                        filename = make_valid_filename(file_obj.display_name)
                        file_path = os.path.join(files_dir, filename)
                        
                        if not os.path.exists(file_path):
                            if download_file_from_url(file_obj.url, file_path, filename):
                                module_file_count += 1
                                total_files += 1
                        else:
                            print(f"    File already exists: {filename}")
                            module_file_count += 1
                            total_files += 1
                            
                    except Exception as e:
                        print(f"    ❌ Error downloading file {item.title}: {e}")
                
                elif item_type == "Page":
                    try:
                        print(f"  Processing Page: {item.title}")
                        # Extract page URL from the item's URL
                        page_url = getattr(item, 'page_url', None)
                        if not page_url and hasattr(item, 'url'):
                            # Extract page slug from full URL
                            url_parts = item.url.split('/')
                            if 'pages' in url_parts:
                                page_index = url_parts.index('pages')
                                if page_index + 1 < len(url_parts):
                                    page_url = url_parts[page_index + 1]
                        
                        if page_url:
                            page_files = download_page_files(canvas, course_id, page_url, module_dir, canvas_base_url)
                            module_file_count += page_files
                            total_files += page_files
                        else:
                            print(f"    ⚠️ Could not determine page URL for: {item.title}")
                            
                    except Exception as e:
                        print(f"    ❌ Error processing page {item.title}: {e}")
            
            if module_file_count > 0:
                print(f"  ✓ {module_file_count} files from this module")
            else:
                print(f"  No files found in this module")
        
        print(f"\n🎉 All modules download complete!")
        print(f"Total files processed: {total_files}")
        if total_files > 0:
            course_name = make_valid_filename(course.name)
            print(f"Files saved to: {os.path.join(output_dir, course_name, 'modules')}")
            
    except Exception as e:
        print(f"Error downloading all module files: {e}")