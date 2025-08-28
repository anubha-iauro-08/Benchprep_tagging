import json
import logging
import re
from typing import Any, Dict, List

from generator_model_handler import GeneratorModelHandler
from snowflake_scraper import SnowflakeScraper  # your scraper from the snippet

logger = logging.getLogger(__name__)


class Gen_AI_Tagextractor:
    """
    End-to-end tag extraction pipeline using a SINGLE shared config for:
      - SnowflakeScraper (Snowflake conn + BATCH_SIZE)
      - GeneratorModelHandler (LLM provider/model config)

    Flow:
      1) Fetch (first N tenants via scraper) -> Snowpark DataFrames
      2) Normalize/Clean content
      3) Prompt LLM for tags (JSON)
      4) Return array with tenant/content IDs + tags
    """

    def __init__(self, config: dict) -> None:
        """
        Args:
            config: One common config for both scraper and generator.
                    Must include Snowflake connection + BATCH_SIZE,
                    and generator platform/model settings.
        """
        # SAME config object for both
        self.config = config
        self.scraper = SnowflakeScraper(config)
        self.generator = GeneratorModelHandler(config)

    # -------- Step 1 + 2: Fetch & Clean ----------
    def process(self) -> List[Dict[str, Any]]:
        """
        Uses scraper.dataframes_for_first_n_tenants() to fetch readings, questions, flashcards
        for the first N tenants, then cleans text.

        Returns list of dicts:
          {
            tenant_id, content_id, content_type,
            content_package_id, content_package_title,
            name, content, content_sha, parent_content_id (optional),
            clean_text
          }
        """
        logger.info("Fetching dataframes for first N tenants (shared config.BATCH_SIZE if provided)")
        dfs = self.scraper.dataframes_for_first_n_tenants()  # [readings_df, questions_df, flash_cards_df]

        items: List[Dict[str, Any]] = []
        for df in dfs:
            for row in df.collect():
                # Read columns by name (your factories standardize these)
                r = {
                    "tenant_id": getattr(row, "TENANT_ID", None),
                    "content_package_title": getattr(row, "CONTENT_PACKAGE_TITLE", None),
                    "content_package_id": getattr(row, "CONTENT_PACKAGE_ID", None),
                    "content_type": getattr(row, "CONTENT_TYPE", None),  # "reading" | "question" | "flashcard"
                    "content_id": getattr(row, "CONTENT_ID", None),
                    "name": getattr(row, "NAME", None),
                    "content": getattr(row, "CONTENT", None),
                    "content_sha": getattr(row, "CONTENT_SHA", None),
                    "parent_content_id": getattr(row, "PARENT_CONTENT_ID", None),
                }
                r["clean_text"] = self._clean_text(self._compose_source_text(r))
                items.append(r)

        logger.info("Prepared %d cleaned items", len(items))
        return items

    def _compose_source_text(self, r: Dict[str, Any]) -> str:
        """Compose a small header + body to ground the LLM."""
        ctype = (r.get("content_type") or "content").strip()
        name = (r.get("name") or "").strip()
        body = (r.get("content") or "").strip()
        header = f"[{ctype.upper()}] {name}\n" if name else f"[{ctype.upper()}]\n"
        return f"{header}{body}"

    def _clean_text(self, text: str) -> str:
        """Strip HTML, normalize URLs, collapse whitespace, lowercase."""
        if not text:
            return ""
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"https?://\S+", "URL", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text.lower()

    # -------- Step 4: Prompting & Tag Generation ----------
    def extract_tags(self, cleaned_text: str, content_type: str) -> Dict[str, Any]:
        """Send structured prompt; parse strict JSON; fall back to raw_response."""
        prompt = self._build_prompt(cleaned_text, content_type)
        resp = self.generator.generate_response(prompt)

        # string or object with .content
        payload = resp if isinstance(resp, str) else getattr(resp, "content", resp)
        try:
            return json.loads(payload) if isinstance(payload, str) else payload
        except (TypeError, json.JSONDecodeError):
            logger.warning("Model did not return valid JSON; returning raw_response")
            return {"raw_response": payload}

    def _build_prompt(self, content: str, content_type: str) -> str:
        return f"""You are an expert in educational content structuring and semantic tagging.
Your task is to analyze the given content ({content_type}) and extract a structured set of tags to support a content-based recommendation engine. These tags will help build a knowledge graph for sequencing and recommending learnables.
Return the output in the following JSON format:
{{
  "main_topic": "The most specific and central topic discussed or assessed in the content.",
  "category": "The general domain or subject area this content falls under (e.g., AI, Biology, Ethics, Mathematics).",
  "topics": [
    {{
      "name": "Name of the sub-topic or concept",
      "coverage": "thoroughly_explained | briefly_mentioned | mentioned_prerequisite",
      "depth": "introductory | moderate | in-depth"
    }}
  ]
}}

Instructions:
- The main_topic should reflect the primary subject.
- The category should reflect the broad field or discipline.
- Each topic should have:
  - a clear and specific name,
  - coverage level: one of "thoroughly_explained", "briefly_mentioned", or "mentioned_prerequisite",
  - explanation depth: one of "introductory", "moderate", or "in-depth".

Content:
{content}"""

    # -------- Batch interface (serial; swap to ThreadPool for true parallel) ----------
    def extract_tags_parallel(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        For each cleaned item, run tag extraction and keep IDs.
        Output rows look like:
          { tenant_id, content_id, content_type, tags: {...} }
        """
        out: List[Dict[str, Any]] = []
        for r in items:
            tags = self.extract_tags(r.get("clean_text", "") or "", r.get("content_type", "content") or "content")
            out.append({
                "tenant_id": r.get("tenant_id"),
                "content_id": r.get("content_id"),
                "content_type": r.get("content_type"),
                "tags": tags
            })
        return out

    # -------- Convenience: full run ----------
    def run(self) -> List[Dict[str, Any]]:
        processed = self.process()
        return self.extract_tags_parallel(processed)

    def close(self) -> None:
        try:
            self.scraper.close()
        except Exception:
            pass