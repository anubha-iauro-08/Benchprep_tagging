import json
import logging
import re
from typing import Any, Dict, List

from generator_model_handler import GeneratorModelHandler
from snowflake_scraper import SnowflakeScraper

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

    def run_snowflake_try_flow(self) -> List[Dict[str, Any]]:
        """
        Executes the tag extraction flow using the new snowflake_try.py logic.
        This method is a separate entry point that handles the different
        DataFrame schemas returned by the `dataframes_from_snowflake_try_logic` method.
        """
        logger.info("Starting tag extraction with snowflake_try.py logic...")
        
        # Fetch dataframes with the snowflake_try.py logic
        dfs = self.scraper.dataframes_from_snowflake_try_logic()

        items: List[Dict[str, Any]] = []
        # The order is: [questions_df, readings_df, flash_cards_df]
        content_types = ["question", "reading", "flashcard"]
        
        for i, df in enumerate(dfs):
            for row in df.collect():
                # Dynamically determine content type and compose source text
                content_type = content_types[i]
                clean_text = self._clean_text(self._compose_try_source_text(row, content_type))
                
                # We can't get all fields from the new dataframes, so we'll
                # create a simplified dict for the next steps.
                items.append({
                    "content_type": content_type,
                    "content": self._compose_try_source_text(row, content_type),
                    "clean_text": clean_text
                })

        logger.info("Prepared %d cleaned items using snowflake_try.py logic", len(items))
        return self.extract_tags_parallel(items)

    def _compose_source_text(self, r: Dict[str, Any]) -> str:
        """Compose a small header + body to ground the LLM."""
        ctype = (r.get("content_type") or "content").strip()
        name = (r.get("name") or "").strip()
        body = (r.get("content") or "").strip()
        header = f"[{ctype.upper()}] {name}\n" if name else f"[{ctype.upper()}]\n"
        return f"{header}{body}"
    
    def _compose_try_source_text(self, row, content_type: str) -> str:
        """
        Adapts the source text composition for the new snowflake_try.py logic.
        Combines content from different column names based on the content type.
        """
        # Checks for question/answer content first
        if hasattr(row, "QUESTION_CONTENT") and hasattr(row, "ANSWER_CONTENT"):
            q_content = getattr(row, "QUESTION_CONTENT", "")
            a_content = getattr(row, "ANSWER_CONTENT", "")
            return f"QUESTION:\n{q_content}\n\nANSWER:\n{a_content}"
        # Then checks for term/definition content
        elif hasattr(row, "TERM") and hasattr(row, "DEFINITION"):
            term = getattr(row, "TERM", "")
            definition = getattr(row, "DEFINITION", "")
            return f"TERM:\n{term}\n\nDEFINITION:\n{definition}"
        # Fallback to general content if specific columns are not found
        else:
            content = getattr(row, "CONTENT", "")
            return content

    def _clean_text(self, text: str) -> str:
        """
        Cleans text content by stripping HTML tags, removing extra whitespace,
        and replacing specific newline characters.
        """
        if not text:
            return ""
        
        # Remove HTML tags
        cleanr = re.compile("<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});")
        cleantext = re.sub(cleanr, "", text)
        
        # Remove multiple newlines and replace with single space
        cleantext = re.sub(r"[\n\r]+", " ", cleantext)
        
        # Remove extra whitespaces
        cleantext = re.sub(r"\s+", " ", cleantext).strip()

        return cleantext

    # -------- Step 3: Extract Tags ----------
    def extract_tags(self, clean_text: str, content_type: str) -> Dict[str, Any]:
        """
        Prompts LLM to extract tags (JSON output)
        """
        logger.info("Attempting to extract tags for content_type=%s", content_type)
        return self.generator.generate_response(self._create_tag_extraction_prompt(clean_text))

    def _create_tag_extraction_prompt(self, content: str) -> str:
        """
        Creates a prompt for the LLM to extract tags.
        """
        return f"""
You are a tagging expert. Your task is to extract relevant tags from the given content.
The tags should be structured as a JSON object with the following fields:

{{
  "main_topic": "string",
  "category": "string",
  "tags": [
    {{"topic": "string",
      "coverage": "one of thoroughly_explained | briefly_mentioned | mentioned_prerequisite",
      "depth": "one of introductory | moderate | in-depth"
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
            
            # Extract JSON string from the response and convert to a dictionary
            if isinstance(tags, str):
                json_match = re.search(r'```json\n(.*?)\n```', tags, re.DOTALL)
                if json_match:
                    try:
                        tags = json.loads(json_match.group(1).strip())
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode JSON from response: {e}")
                        tags = {}  # Set to an empty dict on error
                else:
                    tags = {} # Set to an empty dict if no JSON is found
            
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

    def close(self):
        """
        Close Snowflake session
        """
        self.scraper.close()