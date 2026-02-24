"""Thin REST API client for Canvas LMS with Bearer token auth and pagination."""

import re
import requests


class CanvasAPI:
    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_token}"})

    # ── helpers ──────────────────────────────────────────────────────

    def _get(self, path, **kwargs) -> requests.Response:
        """Single GET request. Raises on HTTP error."""
        url = f"{self.base_url}/api/v1{path}" if path.startswith("/") else path
        resp = self.session.get(url, **kwargs)
        resp.raise_for_status()
        return resp

    def _get_paginated(self, path, params=None) -> list:
        """Follow rel='next' Link headers, collect all JSON results."""
        params = dict(params or {})
        params.setdefault("per_page", 100)
        url = f"{self.base_url}/api/v1{path}"
        results = []
        while url:
            resp = self.session.get(url, params=params)
            resp.raise_for_status()
            results.extend(resp.json())
            # Only use params on the first request; subsequent URLs include them
            params = None
            url = self._next_link(resp)
        return results

    @staticmethod
    def _next_link(resp: requests.Response) -> str | None:
        """Parse Link header for rel='next'."""
        link_header = resp.headers.get("Link", "")
        match = re.search(r'<([^>]+)>;\s*rel="next"', link_header)
        return match.group(1) if match else None

    # ── auth ─────────────────────────────────────────────────────────

    def get_current_user(self) -> dict:
        return self._get("/users/self").json()

    # ── courses ──────────────────────────────────────────────────────

    def get_courses(self, enrollment_state="active", include=None) -> list[dict]:
        params = {"enrollment_state": enrollment_state}
        if include:
            params["include[]"] = include
        return self._get_paginated("/courses", params)

    def get_course(self, course_id) -> dict:
        return self._get(f"/courses/{course_id}").json()

    # ── modules ──────────────────────────────────────────────────────

    def get_modules(self, course_id) -> list[dict]:
        return self._get_paginated(f"/courses/{course_id}/modules")

    def get_module_items(self, course_id, module_id) -> list[dict]:
        return self._get_paginated(
            f"/courses/{course_id}/modules/{module_id}/items"
        )

    # ── content (for HTML parsing) ───────────────────────────────────

    def get_page(self, course_id, page_url) -> dict:
        return self._get(f"/courses/{course_id}/pages/{page_url}").json()

    def get_assignment(self, course_id, assignment_id) -> dict:
        return self._get(
            f"/courses/{course_id}/assignments/{assignment_id}"
        ).json()

    def get_discussion_topic(self, course_id, topic_id) -> dict:
        return self._get(
            f"/courses/{course_id}/discussion_topics/{topic_id}"
        ).json()

    # ── files (two-tier resolution) ──────────────────────────────────

    def get_file(self, file_id) -> dict | None:
        """GET /api/v1/files/{file_id} — returns None on 403/404."""
        try:
            return self._get(f"/files/{file_id}").json()
        except requests.HTTPError as e:
            if e.response.status_code in (403, 404):
                return None
            raise

    def get_file_public_url(self, file_id) -> str | None:
        """GET /api/v1/files/{file_id}/public_url — returns the signed URL string or None."""
        try:
            data = self._get(f"/files/{file_id}/public_url").json()
            return data.get("public_url")
        except requests.HTTPError as e:
            if e.response.status_code in (403, 404):
                return None
            raise

    # ── folders ──────────────────────────────────────────────────────

    def get_folders(self, course_id) -> list[dict]:
        return self._get_paginated(f"/courses/{course_id}/folders")
