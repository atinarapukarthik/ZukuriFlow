"""
TextRefiner - Wispr Flow Style Arrangement Logic
Solves the "arrangement" problem with technical jargon mapping.
"""

import re
import logging
from typing import Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextRefiner:
    """
    Refines transcribed text with technical jargon mapping and formatting.
    Implements Wispr Flow style arrangement for professional output.
    """

    # Technical mappings for case-sensitive jargon
    technical_mappings: Dict[str, str] = {
        # AI/ML Terms
        "rag": "RAG",
        "llm": "LLM",
        "gpt": "GPT",
        "nlp": "NLP",
        "ml": "ML",
        "ai": "AI",
        "langchain": "LangChain",
        "langgraph": "LangGraph",
        "openai": "OpenAI",
        "huggingface": "HuggingFace",
        # Programming Languages
        "python": "Python",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "golang": "Go",
        "rust": "Rust",
        "java": "Java",
        "kotlin": "Kotlin",
        "swift": "Swift",
        # Databases & Query Languages
        "sql": "SQL",
        "nosql": "NoSQL",
        "postgresql": "PostgreSQL",
        "mysql": "MySQL",
        "mongodb": "MongoDB",
        "redis": "Redis",
        # Web Frameworks
        "nextjs": "Next.js",
        "next.js": "Next.js",
        "reactjs": "React.js",
        "react": "React",
        "vuejs": "Vue.js",
        "vue": "Vue",
        "angular": "Angular",
        "fastapi": "FastAPI",
        "django": "Django",
        "flask": "Flask",
        # Professional Terms
        "sde": "SDE",
        "api": "API",
        "rest": "REST",
        "graphql": "GraphQL",
        "sdk": "SDK",
        "cli": "CLI",
        "ui": "UI",
        "ux": "UX",
        "devops": "DevOps",
        "cicd": "CI/CD",
        "ci/cd": "CI/CD",
        # Cloud & Infrastructure
        "aws": "AWS",
        "gcp": "GCP",
        "azure": "Azure",
        "docker": "Docker",
        "kubernetes": "Kubernetes",
        "k8s": "K8s",
        # Product Names
        "zukuriflow": "ZukuriFlow",
        "internshala": "Internshala",
        "github": "GitHub",
        "gitlab": "GitLab",
        "vscode": "VS Code",
    }

    def __init__(self) -> None:
        """Initialize the TextRefiner with technical mappings."""
        logger.info(
            f"TextRefiner initialized with {len(self.technical_mappings)} technical mappings"
        )

    def refine(self, text: str) -> str:
        """
        Refine transcribed text with arrangement and formatting.

        Applies the following transformations:
        1. Cleans leading/trailing whitespace
        2. Replaces technical words using the mapping dictionary
        3. Capitalizes the first letter of the string
        4. Appends a period if text doesn't end with punctuation

        Args:
            text: Raw transcription text

        Returns:
            str: Refined and formatted text
        """
        if not text:
            logger.warning("Empty text received for refinement")
            return ""

        # Step 1: Clean leading/trailing whitespace
        refined = text.strip()
        logger.debug(f"After whitespace cleanup: '{refined}'")

        if not refined:
            return ""

        # Step 2: Replace technical words using mapping
        refined = self._apply_technical_mappings(refined)
        logger.debug(f"After technical mappings: '{refined}'")

        # Step 3: Capitalize first letter
        refined = (
            refined[0].upper() + refined[1:] if len(refined) > 1 else refined.upper()
        )
        logger.debug(f"After capitalization: '{refined}'")

        # Step 4: Append period if no ending punctuation
        if refined[-1] not in ".!?":
            refined += "."
            logger.debug("Added period at end")

        logger.info(f"Refinement complete: '{text[:50]}...' -> '{refined[:50]}...'")
        return refined

    def _apply_technical_mappings(self, text: str) -> str:
        """
        Apply technical jargon mappings to the text.

        Args:
            text: Input text

        Returns:
            str: Text with technical terms properly capitalized
        """
        result = text

        for term_lower, term_proper in self.technical_mappings.items():
            # Use word boundaries for accurate matching
            pattern = r"\b" + re.escape(term_lower) + r"\b"
            result = re.sub(pattern, term_proper, result, flags=re.IGNORECASE)

        return result

    def add_mapping(self, term: str, proper_form: str) -> None:
        """
        Add a custom technical mapping at runtime.

        Args:
            term: Lowercase term to match
            proper_form: Proper capitalized form
        """
        self.technical_mappings[term.lower()] = proper_form
        logger.info(f"Added custom mapping: '{term}' -> '{proper_form}'")


# Standalone refine function for simple usage
def refine(text: str) -> str:
    """
    Wispr-style text cleaning function.

    Applies:
    1. Capitalize the first letter of the sentence
    2. Ensure technical terms are correctly cased
    3. Add ending punctuation if missing

    Args:
        text: Raw transcription text

    Returns:
        str: Refined and formatted text
    """
    # Capitalize the first letter of the sentence
    text = text.strip().capitalize()

    # Ensure technical terms are correctly cased
    mappings = {"sql": "SQL", "sde": "SDE", "rag": "RAG"}
    for wrong, correct in mappings.items():
        text = text.replace(wrong, correct)

    # Add ending punctuation if missing
    if not text.endswith((".", "?", "!")):
        text += "."
    return text
