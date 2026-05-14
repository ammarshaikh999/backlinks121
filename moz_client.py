import os
import requests
from tenacity import retry, stop_after_attempt, wait_exponential


class MozClient:
    """
    Supports both:
    1) MOZ_TOKEN via x-moz-token header
    2) MOZ_ACCESS_ID + MOZ_SECRET_KEY via Basic Auth fallback
    """
    BASE_URL = "https://lsapi.seomoz.com/v2"

    def __init__(self, timeout: int = 60):
        self.timeout = timeout
        self.token = os.getenv("MOZ_TOKEN", "").strip()
        self.access_id = os.getenv("MOZ_ACCESS_ID", "").strip()
        self.secret_key = os.getenv("MOZ_SECRET_KEY", "").strip()

        if not self.token and not (self.access_id and self.secret_key):
            raise ValueError(
                "Missing Moz credentials. Set MOZ_TOKEN or MOZ_ACCESS_ID + MOZ_SECRET_KEY in .env"
            )

    def _headers(self) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "BacklinkPipeline/1.0",
        }
        if self.token:
            headers["x-moz-token"] = self.token
        return headers

    def _auth(self):
        if self.access_id and self.secret_key:
            return (self.access_id, self.secret_key)
        return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def url_metrics(self, targets: list[str]) -> dict:
        """POST /url_metrics — fetch DA, PA, spam score, etc."""
        url = f"{self.BASE_URL}/url_metrics"
        payload = {"targets": targets}
        response = requests.post(
            url,
            json=payload,
            headers=self._headers(),
            auth=self._auth(),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def link_intersect(self, targets: list[str], competitors: list[str], limit: int = 50) -> dict:
        """Optional: find common backlinks between targets and competitors."""
        url = f"{self.BASE_URL}/link_intersect"
        payload = {
            "targets": targets,
            "competitors": competitors,
            "limit": limit,
        }
        response = requests.post(
            url,
            json=payload,
            headers=self._headers(),
            auth=self._auth(),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()
