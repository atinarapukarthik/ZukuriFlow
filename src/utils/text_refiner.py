"""
TextRefiner - Wispr-style text refinement with technical jargon mapping
"""

from typing import Dict
import re


class TextRefiner:
    """
    Advanced text refinement engine with grammar fixes and technical term mapping.

    Implements Wispr-style enhancements:
    - Auto-capitalization
    - Smart punctuation
    - Technical jargon standardization
    """

    # Technical jargon mapping (lowercase -> proper form)
    JARGON_MAP: Dict[str, str] = {
        # Programming Languages
        "python": "Python",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "java": "Java",
        "golang": "Go",
        "rust": "Rust",
        "kotlin": "Kotlin",
        "swift": "Swift",

        # AI/ML Terms
        "rag": "RAG",
        "llm": "LLM",
        "gpt": "GPT",
        "openai": "OpenAI",
        "langchain": "LangChain",
        "langgraph": "LangGraph",
        "hugging face": "Hugging Face",
        "pytorch": "PyTorch",
        "tensorflow": "TensorFlow",

        # Databases
        "sql": "SQL",
        "nosql": "NoSQL",
        "postgresql": "PostgreSQL",
        "mysql": "MySQL",
        "mongodb": "MongoDB",
        "redis": "Redis",
        "elasticsearch": "Elasticsearch",

        # Web/APIs
        "api": "API",
        "rest": "REST",
        "restful": "RESTful",
        "graphql": "GraphQL",
        "json": "JSON",
        "xml": "XML",
        "yaml": "YAML",
        "http": "HTTP",
        "https": "HTTPS",
        "websocket": "WebSocket",

        # DevOps/Cloud
        "aws": "AWS",
        "azure": "Azure",
        "gcp": "GCP",
        "docker": "Docker",
        "kubernetes": "Kubernetes",
        "k8s": "K8s",
        "ci/cd": "CI/CD",
        "cicd": "CI/CD",
        "devops": "DevOps",
        "nginx": "Nginx",
        "apache": "Apache",

        # Frameworks
        "react": "React",
        "vue": "Vue",
        "angular": "Angular",
        "django": "Django",
        "flask": "Flask",
        "fastapi": "FastAPI",
        "nextjs": "Next.js",
        "next.js": "Next.js",

        # Professional Terms
        "sde": "SDE",
        "ui": "UI",
        "ux": "UX",
        "seo": "SEO",
        "mvp": "MVP",
        "poc": "POC",
        "sdk": "SDK",
        "ide": "IDE",
        "cli": "CLI",
        "gui": "GUI",

        # Version Control
        "git": "Git",
        "github": "GitHub",
        "gitlab": "GitLab",
        "bitbucket": "Bitbucket",

        # Other
        "oauth": "OAuth",
        "jwt": "JWT",
        "ssl": "SSL",
        "tls": "TLS",
        "cdn": "CDN",
        "dns": "DNS",
        "ssh": "SSH",
        "ftp": "FTP",
        "vpn": "VPN",
    }

    def __init__(self, custom_jargon: Dict[str, str] = None) -> None:
        """
        Initialize TextRefiner with optional custom jargon mappings.

        Args:
            custom_jargon: Additional jargon mappings to extend the default dictionary
        """
        self.jargon_map = self.JARGON_MAP.copy()

        if custom_jargon:
            self.jargon_map.update(custom_jargon)

        print(
            f"📝 TextRefiner initialized with {len(self.jargon_map)} jargon mappings")

    def refine(self, text: str) -> str:
        """
        Apply all refinement steps to the text.

        Args:
            text: Raw transcription text

        Returns:
            Refined and formatted text
        """
        if not text or not text.strip():
            return ""

        refined = text.strip()

        # Step 1: Apply technical jargon mapping
        refined = self._apply_jargon_mapping(refined)

        # Step 2: Fix spacing
        refined = self._fix_spacing(refined)

        # Step 3: Auto-capitalize sentences
        refined = self._capitalize_sentences(refined)

        # Step 4: Add ending punctuation
        refined = self._add_ending_punctuation(refined)

        # Step 5: Fix common contractions
        refined = self._fix_contractions(refined)

        return refined

    def _apply_jargon_mapping(self, text: str) -> str:
        """
        Replace technical terms with proper capitalization.

        Uses word boundaries to avoid partial matches.
        """
        result = text

        for term_lower, term_proper in self.jargon_map.items():
            # Use word boundaries for accurate matching
            pattern = r'\b' + re.escape(term_lower) + r'\b'
            result = re.sub(pattern, term_proper, result, flags=re.IGNORECASE)

        return result

    def _fix_spacing(self, text: str) -> str:
        """Fix common spacing issues."""
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)

        # Remove space before punctuation
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)

        # Ensure space after punctuation
        text = re.sub(r'([.,!?;:])([A-Za-z])', r'\1 \2', text)

        return text.strip()

    def _capitalize_sentences(self, text: str) -> str:
        """
        Capitalize the first letter of each sentence.
        """
        # Capitalize first character
        if text:
            text = text[0].upper() + text[1:]

        # Capitalize after sentence endings (. ! ?)
        text = re.sub(
            r'([.!?])\s+([a-z])',
            lambda m: m.group(1) + ' ' + m.group(2).upper(),
            text
        )

        return text

    def _add_ending_punctuation(self, text: str) -> str:
        """
        Add period at the end if no punctuation exists.
        """
        if text and text[-1] not in '.!?':
            text += '.'

        return text

    def _fix_contractions(self, text: str) -> str:
        """
        Fix common contractions that may be transcribed incorrectly.
        """
        contractions = {
            r'\bim\b': "I'm",
            r'\bive\b': "I've",
            r'\bill\b': "I'll",
            r'\bid\b': "I'd",
            r'\byoure\b': "you're",
            r'\byouve\b': "you've",
            r'\byoull\b': "you'll",
            r'\byoud\b': "you'd",
            r'\bhes\b': "he's",
            r'\bshes\b': "she's",
            r'\bits\b': "it's",
            r'\bwere\b': "we're",
            r'\bweve\b': "we've",
            r'\bwell\b': "we'll",
            r'\bwed\b': "we'd",
            r'\btheyre\b': "they're",
            r'\btheyve\b': "they've",
            r'\btheyll\b': "they'll",
            r'\btheyd\b': "they'd",
            r'\bdont\b': "don't",
            r'\bdoesnt\b': "doesn't",
            r'\bdidnt\b': "didn't",
            r'\bcant\b': "can't",
            r'\bcouldnt\b': "couldn't",
            r'\bwouldnt\b': "wouldn't",
            r'\bshouldnt\b': "shouldn't",
            r'\bwont\b': "won't",
            r'\bisnt\b': "isn't",
            r'\barent\b': "aren't",
            r'\bwasnt\b': "wasn't",
            r'\bwerent\b': "weren't",
            r'\bhasnt\b': "hasn't",
            r'\bhavent\b': "haven't",
            r'\bhadnt\b': "hadn't",
        }

        result = text
        for pattern, replacement in contractions.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        return result

    def add_custom_jargon(self, term: str, proper_form: str) -> None:
        """
        Add a custom jargon mapping at runtime.

        Args:
            term: Lowercase term to match
            proper_form: Proper capitalization/format
        """
        self.jargon_map[term.lower()] = proper_form
        print(f"✅ Added custom jargon: '{term}' -> '{proper_form}'")
