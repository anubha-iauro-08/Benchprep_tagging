import json
import logging
import re
from typing import Any, Dict, List

# Import your Snowflake scraper and factory classes
from snowflake_scraper import SnowflakeScraper
from generator_model_handler import GeneratorModelHandler

logger = logging.getLogger(__name__)


class Gen_AI_Tagextractor:
    """
    End-to-end tag extraction pipeline using a SINGLE shared config for:
      - SnowflakeScraper (Snowflake conn + BATCH_SIZE)
      - GeneratorModelHandler (LLM provider/model config)

    Flow:
      1) Fetch dataframes from Snowflake using the scraper
      2) Normalize/Clean content
      3) Prompt LLM for tags (JSON)
      4) Return array with content details + tags
    """

    def __init__(self, config: dict) -> None:
        """
        Args:
            config: One common config for both scraper and generator.
                    Must include Snowflake connection + BATCH_SIZE,
                    and generator platform/model settings.
        """
        self.config = config
        self.scraper = SnowflakeScraper(config)
        self.generator = GeneratorModelHandler(config)

    def _compose_try_source_text(self, row, content_type: str) -> str:
        """
        Adapts the source text composition for the new snowflake_try.py logic.
        """
        if content_type == "question":
            question = getattr(row, "QUESTION_CONTENT", "")
            answer = getattr(row, "ANSWER_CONTENT", "")
            return f"[QUESTION]\nQuestion: {question}\nAnswer: {answer}"
        elif content_type == "reading":
            content = getattr(row, "CONTENT", "")
            return f"[READING]\n{content}"
        elif content_type == "flashcard":
            term = getattr(row, "TERM", "")
            definition = getattr(row, "DEFINITION", "")
            return f"[FLASHCARD]\nTerm: {term}\nDefinition: {definition}"
        else:
            return ""

    def _clean_text(self, text: str) -> str:
        """Strip HTML, normalize URLs, collapse whitespace, lowercase."""
        if not text:
            return ""
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"https?://\S+", "URL", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text.lower()

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

Content:
{content}"""

    def extract_tags(self, raw_text: str, content_type: str) -> Dict[str, Any]:
        """Send structured prompt; parse strict JSON; fall back to raw_response."""
        cleaned_text = self._clean_text(raw_text)
        print("Cleaned text:", cleaned_text[:500])  # Print first 500 chars for brevity
        prompt = self._build_prompt(cleaned_text, content_type)

        resp = self.generator.generate_response(prompt)

        payload = resp if isinstance(resp, str) else getattr(resp, "content", resp)

        # Use regex to find and extract the JSON content from the markdown block
        json_match = re.search(r'```json\s*(\{.*\})\s*```', payload, re.DOTALL)
        if json_match:
            json_string = json_match.group(1)
        else:
            json_string = payload

        try:
            return json.loads(json_string) if isinstance(json_string, str) else json_string
        except (TypeError, json.JSONDecodeError):
            logger.warning("Model did not return valid JSON; returning raw_response")
            return {"raw_response": payload}
            
    def run_snowflake_flow(self) -> List[Dict[str, Any]]:
        """
        Executes the tag extraction flow by fetching data from Snowflake and
        then processing it with the LLM.
        """
        logger.info("Starting tag extraction pipeline with Snowflake data source.")
        
        # Step 1: Fetch dataframes from Snowflake
        dfs = self.scraper.dataframes_from_snowflake_try_logic()

        items: List[Dict[str, Any]] = []
        content_types = ["question", "reading", "flashcard"]
        
        for i, df in enumerate(dfs):
            for row in df.collect():
                content_type = content_types[i]
                raw_text = self._compose_try_source_text(row, content_type)
                
                # Step 2 & 3: Clean and extract tags for each item
                tags = self.extract_tags(raw_text, content_type)
                
                items.append({
                    "content_type": content_type,
                    "tags": tags
                })

        logger.info("Pipeline finished. Processed %d items.", len(items))
        return items

    def close(self) -> None:
        """
        Close the Snowflake session.
        """
        try:
            self.scraper.close()
        except Exception:
            pass