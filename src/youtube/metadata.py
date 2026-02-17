"""
Metadata Generator - Generates YouTube video metadata (title, description, tags)
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
import re

import yaml

from src.utils.logger import get_logger

logger = get_logger(__name__)


class MetadataGenerator:
    """
    Generates optimized metadata for YouTube videos including:
    - SEO-optimized titles
    - Detailed descriptions
    - Relevant tags
    - Category selection
    """

    def __init__(self, config_path: str = "config/youtube_config.yaml"):
        """
        Initialize metadata generator.

        Args:
            config_path: Path to YouTube configuration
        """
        self.config = self._load_config(config_path)

        logger.info("MetadataGenerator initialized")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load YouTube configuration"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Failed to load config: {e}")
            return {}

    def generate(
        self,
        headlines: List[str],
        date: str = None,
        language: str = "en",
        sources: List[str] = None,
        custom_tags: List[str] = None,
        pdf_link: str = None,
        pdf_filename: str = None
    ) -> Dict[str, Any]:
        """
        Generate complete metadata for a video.

        Args:
            headlines: List of news headlines covered
            date: Video date
            language: Language code
            sources: List of news sources used
            custom_tags: Additional custom tags
            pdf_link: Google Drive shareable link for the PDF study notes
            pdf_filename: Local filename of the PDF (fallback if no Drive link)

        Returns:
            Dictionary with title, description, tags, category
        """
        date = date or datetime.now().strftime("%B %d, %Y")
        sources = sources or []
        custom_tags = custom_tags or []

        # Get language name
        language_names = {
            "en": "English",
            "hi": "Hindi",
            "ta": "Tamil",
            "te": "Telugu"
        }
        language_name = language_names.get(language, "English")

        # Generate title
        title = self._generate_title(date, language_name, headlines)

        # Generate description (with PDF section)
        description = self._generate_description(
            date=date,
            language=language_name,
            headlines=headlines,
            sources=sources,
            pdf_link=pdf_link,
            pdf_filename=pdf_filename
        )

        # Generate tags
        tags = self._generate_tags(
            headlines=headlines,
            language=language,
            custom_tags=custom_tags
        )

        # Get category
        category_id = self.config.get("channel", {}).get("defaults", {}).get("category_id", "25")

        return {
            "title": title,
            "description": description,
            "tags": tags,
            "category_id": category_id,
            "language": language,
            "privacy_status": self.config.get("channel", {}).get("defaults", {}).get("privacy_status", "public"),
            "made_for_kids": self.config.get("channel", {}).get("defaults", {}).get("made_for_kids", False)
        }

    def _generate_title(
        self,
        date: str,
        language: str,
        headlines: List[str]
    ) -> str:
        """Generate SEO-optimized title"""
        metadata_config = self.config.get("metadata", {})
        titles_config = metadata_config.get("titles", {})

        # Get template for language
        lang_code = language[:2].lower()
        template = titles_config.get(lang_code, titles_config.get("en", ""))

        if template:
            title = template.format(date=date, language=language)
        else:
            # Default format
            title = f"Current Affairs {date} | Today's Top News | Daily News Update"

        # Ensure title is within YouTube's limit (100 chars)
        if len(title) > 100:
            title = title[:97] + "..."

        return title

    def _generate_description(
        self,
        date: str,
        language: str,
        headlines: List[str],
        sources: List[str],
        pdf_link: str = None,
        pdf_filename: str = None
    ) -> str:
        """Generate detailed description with PDF download section."""
        metadata_config = self.config.get("metadata", {})
        template = metadata_config.get("description", "")

        # Format topics list
        topics_list = "\n".join([f"• {headline}" for headline in headlines[:10]])

        # Format sources list
        sources_list = "\n".join([f"• {source}" for source in set(sources)])

        # Generate topic tags
        topic_tags = self._extract_topic_tags(headlines)

        # Build PDF section
        pdf_section = self._build_pdf_section(pdf_link, pdf_filename)

        if template:
            description = template.format(
                date=date,
                language=language,
                topics=topics_list,
                sources=sources_list,
                topic_tags=" ".join(topic_tags)
            )
            # Append PDF section after template content
            description = description.rstrip() + "\n\n" + pdf_section
        else:
            # Default description
            description = f"""Daily Current Affairs for {date} | Current Affairs Academy
Language: {language}

📌 Topics Covered Today:
{topics_list}

{pdf_section}
📰 News Sources:
{sources_list}

🔔 Subscribe for daily current affairs updates!
📚 Like & Share to help fellow aspirants!

#CurrentAffairs #DailyNews #UPSC #CurrentAffairsAcademy #StudyNotes
"""

        # YouTube description limit is 5000 chars
        if len(description) > 5000:
            description = description[:4997] + "..."

        return description

    def _build_pdf_section(
        self,
        pdf_link: str = None,
        pdf_filename: str = None
    ) -> str:
        """Build the PDF study notes section for video description."""
        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "📄 FREE PDF STUDY NOTES - CURRENT AFFAIRS ACADEMY",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "Download the Complete Study Notes PDF for this video:",
            "✅ Full detailed coverage (much more than the video!)",
            "✅ In-depth analysis with background & context",
            "✅ Important Terms & Definitions",
            "✅ UPSC Prelims & Mains relevance tags",
            "✅ Quick Revision section with key facts",
            "✅ 20+ Practice Questions (MCQ + Descriptive)",
            "",
        ]

        if pdf_link:
            lines.append(f"🔗 Download PDF: {pdf_link}")
        elif pdf_filename:
            lines.append("🔗 PDF Study Notes: Check the pinned comment for download link")
        else:
            lines.append("🔗 PDF Study Notes: Available - check pinned comment!")

        lines.extend([
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
        ])

        return "\n".join(lines)

    def _generate_tags(
        self,
        headlines: List[str],
        language: str,
        custom_tags: List[str]
    ) -> List[str]:
        """Generate relevant tags"""
        tags = []

        # Default tags from config
        metadata_config = self.config.get("metadata", {})
        default_tags = metadata_config.get("tags", [])
        tags.extend(default_tags)

        # Language-specific tags
        language_tags = metadata_config.get("language_tags", {}).get(language, [])
        tags.extend(language_tags)

        # Extract tags from headlines
        headline_tags = self._extract_topic_tags(headlines)
        tags.extend(headline_tags)

        # Add custom tags
        tags.extend(custom_tags)

        # Add date-based tags
        today = datetime.now()
        tags.extend([
            f"news {today.strftime('%B %Y')}",
            f"current affairs {today.strftime('%B %Y')}",
            f"news {today.strftime('%d %B %Y')}"
        ])

        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in tags:
            tag_lower = tag.lower()
            if tag_lower not in seen:
                seen.add(tag_lower)
                unique_tags.append(tag)

        # YouTube allows up to 500 characters total for tags
        # And recommends 5-8 tags
        final_tags = []
        total_chars = 0
        for tag in unique_tags[:30]:  # Max 30 tags
            if total_chars + len(tag) + 1 <= 500:
                final_tags.append(tag)
                total_chars += len(tag) + 1  # +1 for comma separator

        return final_tags

    def _extract_topic_tags(self, headlines: List[str]) -> List[str]:
        """Extract relevant topic tags from headlines"""
        tags = []

        # Keywords to look for
        topic_keywords = {
            "india": ["india", "indian", "modi", "delhi", "parliament"],
            "economy": ["economy", "gdp", "inflation", "rbi", "market", "stock"],
            "politics": ["election", "minister", "government", "bjp", "congress"],
            "international": ["us", "china", "russia", "pakistan", "world"],
            "science": ["space", "isro", "satellite", "research", "technology"],
            "sports": ["cricket", "ipl", "football", "olympics", "sports"],
        }

        # Check headlines for keywords
        all_text = " ".join(headlines).lower()

        for topic, keywords in topic_keywords.items():
            for keyword in keywords:
                if keyword in all_text:
                    tags.append(f"#{topic}")
                    tags.append(f"{topic} news")
                    break

        # Extract proper nouns (simple heuristic)
        for headline in headlines:
            words = headline.split()
            for word in words:
                # Check if word starts with capital and is significant
                if word[0].isupper() and len(word) > 3:
                    # Clean the word
                    clean_word = re.sub(r'[^\w]', '', word)
                    if len(clean_word) > 3:
                        tags.append(clean_word.lower())

        return list(set(tags))[:15]  # Limit to 15 topic tags

    def generate_from_script(
        self,
        script_title: str,
        script_date: str,
        script_language: str,
        article_titles: List[str],
        article_sources: List[str],
        pdf_link: str = None,
        pdf_filename: str = None
    ) -> Dict[str, Any]:
        """
        Generate metadata from script information.

        Args:
            script_title: Script title
            script_date: Script date
            script_language: Script language
            article_titles: List of article titles
            article_sources: List of article sources
            pdf_link: Google Drive link to PDF study notes
            pdf_filename: Local filename of the PDF

        Returns:
            Metadata dictionary
        """
        return self.generate(
            headlines=article_titles,
            date=script_date,
            language=script_language,
            sources=article_sources,
            pdf_link=pdf_link,
            pdf_filename=pdf_filename
        )


# CLI interface for testing
if __name__ == "__main__":
    print("\n=== Metadata Generator Test ===\n")

    generator = MetadataGenerator()

    test_headlines = [
        "India Launches New Space Mission to Mars",
        "Government Announces Major Economic Reforms",
        "Cricket World Cup: India Defeats Australia",
        "PM Modi Addresses UN General Assembly",
        "RBI Keeps Interest Rates Unchanged"
    ]

    test_sources = [
        "Times of India",
        "The Hindu",
        "NDTV",
        "BBC News"
    ]

    metadata = generator.generate(
        headlines=test_headlines,
        language="en",
        sources=test_sources
    )

    print(f"Title: {metadata['title']}")
    print(f"\nTags ({len(metadata['tags'])}):")
    print(", ".join(metadata['tags'][:10]))
    print(f"\nDescription:\n{metadata['description'][:500]}...")
