"""Download flow: discover → resolve → download with completeness reporting."""

import os
import urllib.parse

from .canvas_api import CanvasAPI
from .file_utils import make_valid_filename, download_file_from_url
from .page_parser import extract_canvas_file_links


# ── Phase 1: Discover file IDs from module content ──────────────────

def _extract_file_ids_from_html(html, base_url):
    """Return set of file-ID strings found in HTML body."""
    if not html:
        return set()
    links = extract_canvas_file_links(html, base_url)
    return {fl["file_id"] for fl in links if fl.get("file_id")}


def discover_file_ids(api: CanvasAPI, course_id: int, module_ids=None):
    """Walk modules and collect every referenced file ID.

    Returns:
        discovered: dict  file_id → {"file_id": str, "sources": [str, ...]}
        module_map: dict  file_id → first module name it appeared in
    """
    modules = api.get_modules(course_id)
    discovered: dict[str, dict] = {}
    module_map: dict[str, str] = {}
    base_url = api.base_url

    for mod in modules:
        mod_id = mod["id"]
        mod_name = mod["name"]

        if module_ids is not None and mod_id not in module_ids:
            continue

        print(f"\n--- Scanning module: {mod_name} ---")
        items = api.get_module_items(course_id, mod_id)

        for item in items:
            item_type = item.get("type", "")
            title = item.get("title", "")

            if item_type == "File":
                fid = str(item["content_id"])
                _record(discovered, module_map, fid, f"File: {title}", mod_name)

            elif item_type == "Page":
                page_url = item.get("page_url")
                if not page_url:
                    continue
                print(f"  Scanning page: {title}")
                try:
                    page = api.get_page(course_id, page_url)
                    for fid in _extract_file_ids_from_html(page.get("body"), base_url):
                        _record(discovered, module_map, fid, f"Page: {title}", mod_name)
                except Exception as e:
                    print(f"    Warning: could not fetch page '{title}': {e}")

            elif item_type == "Assignment":
                print(f"  Scanning assignment: {title}")
                try:
                    assignment = api.get_assignment(course_id, item["content_id"])
                    for fid in _extract_file_ids_from_html(assignment.get("description"), base_url):
                        _record(discovered, module_map, fid, f"Assignment: {title}", mod_name)
                except Exception as e:
                    print(f"    Warning: could not fetch assignment '{title}': {e}")

            elif item_type == "Discussion":
                print(f"  Scanning discussion: {title}")
                try:
                    topic = api.get_discussion_topic(course_id, item["content_id"])
                    for fid in _extract_file_ids_from_html(topic.get("message"), base_url):
                        _record(discovered, module_map, fid, f"Discussion: {title}", mod_name)
                except Exception as e:
                    print(f"    Warning: could not fetch discussion '{title}': {e}")

    print(f"\nDiscovered {len(discovered)} unique file(s) across modules.")
    return discovered, module_map


def _record(discovered, module_map, file_id, source, module_name):
    """Add a file ID to the discovered dict, deduplicating."""
    if file_id not in discovered:
        discovered[file_id] = {"file_id": file_id, "sources": []}
        module_map[file_id] = module_name
    discovered[file_id]["sources"].append(source)


# ── Phase 2: Resolve file metadata ──────────────────────────────────

def resolve_file(api: CanvasAPI, file_id: str) -> dict | None:
    """Two-tier resolution: try file API, then public_url fallback."""
    # Tier 1 — full metadata (only use if url is non-empty; locked files have url="")
    meta = api.get_file(file_id)
    if meta and meta.get("url"):
        return {
            "display_name": meta["display_name"],
            "url": meta["url"],
            "folder_id": meta.get("folder_id"),
        }

    # Tier 2 — public_url fallback
    pub_url = api.get_file_public_url(file_id)
    if pub_url:
        raw_name = urllib.parse.urlparse(pub_url).path.split("/")[-1]
        filename = urllib.parse.unquote(raw_name)
        return {
            "display_name": filename,
            "url": pub_url,
            "folder_id": None,
        }

    name = meta["display_name"] if meta else f"ID {file_id}"
    print(f"    Warning: could not resolve {name} (file may be locked by instructor)")
    return None


# ── Phase 3: Download + organise ─────────────────────────────────────

def download_course_files(api: CanvasAPI, course_id: int, output_dir: str,
                          module_ids=None):
    """Full pipeline: discover → resolve → download → report."""
    course = api.get_course(course_id)
    course_name = make_valid_filename(course["name"])

    # 1. Discover
    discovered, module_map = discover_file_ids(api, course_id, module_ids)
    if not discovered:
        print("No files discovered.")
        return

    # 2. Resolve
    print("\nResolving file metadata...")
    resolved: dict[str, dict] = {}
    for fid in discovered:
        meta = resolve_file(api, fid)
        if meta:
            resolved[fid] = meta

    print(f"Resolved {len(resolved)}/{len(discovered)} file(s).")

    # 3. Build folder map
    folder_names: dict[int, str] = {}
    folder_file_counts: dict[str, int] = {}
    try:
        folders = api.get_folders(course_id)
        for f in folders:
            folder_names[f["id"]] = f["full_name"]
            folder_file_counts[f["full_name"]] = f.get("files_count", 0)
    except Exception as e:
        print(f"Warning: could not fetch folders: {e}")

    # 4. Download
    print("\nDownloading files...")
    downloaded = 0
    skipped = 0

    for fid, meta in resolved.items():
        filename = make_valid_filename(meta["display_name"])
        if not filename:
            filename = f"file_{fid}"

        # Decide subdirectory
        if meta["folder_id"] and meta["folder_id"] in folder_names:
            folder_full = folder_names[meta["folder_id"]]
            # Strip the leading "course files/" prefix if present
            rel = folder_full
            prefix = "course files/"
            if rel.lower().startswith(prefix):
                rel = rel[len(prefix):]
            rel = rel or "root"
            sub = os.path.join(course_name, "folders", make_valid_filename(rel))
        else:
            mod_name = module_map.get(fid, "unknown_module")
            sub = os.path.join(course_name, "modules", make_valid_filename(mod_name))

        file_path = os.path.join(output_dir, sub, filename)

        if os.path.exists(file_path):
            print(f"    File already exists: {filename}")
            skipped += 1
        else:
            if download_file_from_url(meta["url"], file_path, filename):
                downloaded += 1

    # 5. Completeness report
    print_completeness_report(folder_names, folder_file_counts, discovered, resolved)
    total = downloaded + skipped
    print(f"\n{downloaded} downloaded, {skipped} already existed, {total} total.")
    if total > 0:
        print(f"Files saved to: {os.path.join(output_dir, course_name)}")


def print_completeness_report(folder_names, folder_file_counts, discovered, resolved):
    """Print folder-level completeness summary."""
    if not folder_file_counts:
        return

    # Count discovered files per folder
    disc_per_folder: dict[str, int] = {}
    for fid, meta in resolved.items():
        folder_id = meta.get("folder_id")
        if folder_id and folder_id in folder_names:
            full = folder_names[folder_id]
        else:
            full = "(no folder)"
        disc_per_folder[full] = disc_per_folder.get(full, 0) + 1

    print("\nFolder Summary:")
    total_instructor = 0
    total_discovered = 0

    # Sort folders for consistent output, skip the root "course files" itself
    for full_name in sorted(folder_file_counts):
        count = folder_file_counts[full_name]
        if count == 0 and full_name not in disc_per_folder:
            continue
        prefix = "course files/"
        label = full_name
        if label.lower().startswith(prefix):
            label = label[len(prefix):]
        label = label or "root"
        disc = disc_per_folder.get(full_name, 0)
        total_instructor += count
        total_discovered += disc
        print(f"  {label:<20} -- {count} files (instructor) / {disc} discovered")

    print(f"  {'Total':<20} -- {total_instructor} files (instructor) / "
          f"{total_discovered} discovered / {len(resolved)} downloaded")
