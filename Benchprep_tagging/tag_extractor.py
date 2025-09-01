import json
import logging
import re
from typing import Any, Dict


from generator_model_handler import GeneratorModelHandler  # keep your LLM wrapper

logger = logging.getLogger(__name__)

class Gen_AI_Tagextractor_LLMOnly:
    """
    Tag extraction pipeline without Snowflake.
    Provide raw text + content_type directly.
    """

    def __init__(self, config: dict) -> None:
        self.config = config
        self.generator = GeneratorModelHandler(config)

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
        """Send cleaned text to LLM and parse tags."""
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