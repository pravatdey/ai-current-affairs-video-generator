"""
Script Writer - Generates complete video scripts from news articles
"""

import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from .llm_client import LLMClient
from .prompt_templates import PromptTemplates
from src.scraper.base_scraper import NewsArticle
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ScriptSegment:
    """A segment of the video script"""
    type: str  # intro, news, transition, conclusion, topic_header, key_points
    content: str
    duration_estimate: float = 0.0  # in seconds
    article: Optional[NewsArticle] = None
    # UPSC-specific fields
    key_points: List[str] = field(default_factory=list)
    exam_relevance: str = ""  # PRELIMS, MAINS, BOTH
    subject_category: str = ""  # Polity, Economy, IR, etc.
    important_terms: Dict[str, str] = field(default_factory=dict)
    timestamp: str = ""  # Video timestamp marker


@dataclass
class VideoScript:
    """Complete video script with UPSC enhancements"""
    title: str
    date: str
    language: str
    segments: List[ScriptSegment] = field(default_factory=list)
    total_duration: float = 0.0
    word_count: int = 0
    article_count: int = 0
    # UPSC-specific metadata
    subjects_covered: List[str] = field(default_factory=list)
    prelims_topics: List[str] = field(default_factory=list)
    mains_topics: List[str] = field(default_factory=list)

    def get_full_script(self) -> str:
        """Get the full script as a single string"""
        parts = []
        for segment in self.segments:
            parts.append(segment.content)
        return "\n\n".join(parts)

    def get_script_for_tts(self) -> str:
        """Get script optimized for TTS (single continuous text)"""
        parts = []
        for segment in self.segments:
            # Clean up for TTS
            content = segment.content
            # Ensure proper sentence endings
            if content and not content.rstrip().endswith(('.', '!', '?')):
                content = content.rstrip() + "."
            parts.append(content)

        return " ".join(parts)

    def get_all_key_points(self) -> List[Dict[str, Any]]:
        """Get all key points for PDF notes and video overlays"""
        all_points = []
        for segment in self.segments:
            if segment.key_points:
                all_points.append({
                    'article_title': segment.article.title if segment.article else '',
                    'key_points': segment.key_points,
                    'exam_relevance': segment.exam_relevance,
                    'subject': segment.subject_category,
                    'timestamp': segment.timestamp
                })
        return all_points

    def get_timestamps(self) -> List[Dict[str, str]]:
        """Get video timestamps for all segments"""
        timestamps = []
        current_time = 0
        for segment in self.segments:
            if segment.type == 'news':
                minutes = int(current_time // 60)
                seconds = int(current_time % 60)
                timestamps.append({
                    'time': f"{minutes:02d}:{seconds:02d}",
                    'title': segment.article.title if segment.article else 'Topic',
                    'subject': segment.subject_category
                })
            current_time += segment.duration_estimate
        return timestamps


class ScriptWriter:
    """
    Generates UPSC-focused video scripts from news articles using LLM.
    Optimized for competitive exam preparation content.
    """

    # Average speaking rate (words per minute) - slightly slower for educational content
    WORDS_PER_MINUTE = 140  # Slower pace for educational content

    # UPSC subject categories for classification
    SUBJECT_KEYWORDS = {
        'Polity': ['parliament', 'constitution', 'judiciary', 'election', 'bill', 'amendment', 'supreme court', 'governor', 'president', 'cabinet'],
        'Economy': ['gdp', 'inflation', 'rbi', 'fiscal', 'budget', 'tax', 'gst', 'trade', 'bank', 'finance', 'niti aayog'],
        'International Relations': ['un', 'g20', 'brics', 'china', 'pakistan', 'usa', 'bilateral', 'summit', 'treaty', 'diplomat'],
        'Environment': ['climate', 'pollution', 'biodiversity', 'forest', 'wildlife', 'conservation', 'renewable', 'emission'],
        'Science & Technology': ['isro', 'space', 'satellite', 'ai', 'technology', 'digital', 'cyber', 'research', 'innovation'],
        'Social Issues': ['poverty', 'education', 'health', 'women', 'child', 'welfare', 'caste', 'tribe'],
        'Security': ['terrorism', 'border', 'defence', 'army', 'cyber security', 'naxal'],
        'Geography': ['earthquake', 'cyclone', 'monsoon', 'river', 'mountain', 'flood', 'drought'],
        'History': ['heritage', 'archaeological', 'ancient', 'medieval', 'freedom', 'independence']
    }

    def __init__(
        self,
        llm_provider: str = "groq",
        llm_config: Dict[str, Any] = None,
        target_duration_minutes: int = 25,  # Default 25 minutes for UPSC
        upsc_mode: bool = True
    ):
        """
        Initialize script writer for UPSC content.

        Args:
            llm_provider: LLM provider to use ("groq" or "ollama")
            llm_config: Configuration for LLM client
            target_duration_minutes: Target video duration (default 25 min for UPSC)
            upsc_mode: Enable UPSC-specific content generation
        """
        llm_config = llm_config or {}
        self.llm = LLMClient(provider=llm_provider, **llm_config)
        self.target_duration = max(target_duration_minutes, 25)  # Minimum 25 minutes
        self.upsc_mode = upsc_mode

        # Use UPSC-specific system prompt
        self.system_prompt = PromptTemplates.SYSTEM_PROMPT

        # Calculate word targets for 25+ minute educational content
        self.target_words = self.target_duration * self.WORDS_PER_MINUTE

        # Adjusted distribution for educational content
        self.intro_words = int(self.target_words * 0.06)  # 6% for intro
        self.conclusion_words = int(self.target_words * 0.06)  # 6% for conclusion
        self.news_words = self.target_words - self.intro_words - self.conclusion_words

        logger.info(
            f"Initialized ScriptWriter (UPSC Mode): {self.target_duration}min, "
            f"~{self.target_words} words total, ~{self.news_words} words for content"
        )

    def _classify_subject(self, article: NewsArticle) -> Tuple[str, str]:
        """
        Classify article into UPSC subject category and exam relevance.

        Returns:
            Tuple of (subject_category, exam_relevance)
        """
        content = f"{article.title} {article.summary or ''} {article.content or ''}".lower()

        scores = {}
        for subject, keywords in self.SUBJECT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in content)
            scores[subject] = score

        if scores:
            best_subject = max(scores.keys(), key=lambda k: scores[k])
            if scores[best_subject] > 0:
                # Determine exam relevance
                if any(kw in content for kw in ['statistics', 'data', 'figure', 'number', 'launched', 'inaugurated']):
                    exam_relevance = "BOTH"
                elif any(kw in content for kw in ['analysis', 'impact', 'significance', 'implications']):
                    exam_relevance = "MAINS"
                else:
                    exam_relevance = "PRELIMS"

                return best_subject, exam_relevance

        return "Current Affairs", "BOTH"

    def generate_script(
        self,
        articles: List[NewsArticle],
        language: str = "English",
        date: str = None
    ) -> VideoScript:
        """
        Generate a complete UPSC-focused video script from articles.

        Args:
            articles: List of news articles to include
            language: Language for the script
            date: Date for the video (defaults to today)

        Returns:
            VideoScript object with UPSC enhancements
        """
        if not articles:
            raise ValueError("No articles provided for script generation")

        date = date or datetime.now().strftime("%B %d, %Y")

        logger.info(f"Generating UPSC script for {len(articles)} articles in {language}")

        # Create script object with UPSC metadata
        script = VideoScript(
            title=f"UPSC Daily Current Affairs - {date}",
            date=date,
            language=language,
            article_count=len(articles)
        )

        # Classify all articles by subject
        subjects_covered = set()
        prelims_topics = []
        mains_topics = []

        for article in articles:
            subject, relevance = self._classify_subject(article)
            subjects_covered.add(subject)
            if relevance in ['PRELIMS', 'BOTH']:
                prelims_topics.append(article.title)
            if relevance in ['MAINS', 'BOTH']:
                mains_topics.append(article.title)

        script.subjects_covered = list(subjects_covered)
        script.prelims_topics = prelims_topics
        script.mains_topics = mains_topics

        # Calculate words per news item (more words per item for depth)
        # For 25 min video with 8-10 articles, each topic gets ~400-500 words
        min_words_per_item = 350  # Minimum for proper UPSC coverage
        words_per_item = max(int(self.news_words / len(articles)), min_words_per_item)

        # Track cumulative time for timestamps
        cumulative_time = 0.0

        # 1. Generate Introduction
        intro = self._generate_intro(articles, date, language)
        intro.timestamp = "00:00"
        script.segments.append(intro)
        cumulative_time += intro.duration_estimate

        # 2. Generate News Items with UPSC enhancements
        for i, article in enumerate(articles):
            # Add topic header/transition
            subject, exam_relevance = self._classify_subject(article)

            if i > 0:
                # Add transition
                transition = ScriptSegment(
                    type="transition",
                    content=PromptTemplates.get_transition(i),
                    duration_estimate=3.0
                )
                script.segments.append(transition)
                cumulative_time += 3.0

            # Generate comprehensive news segment
            news_segment = self._generate_news_segment(
                article=article,
                language=language,
                word_count=words_per_item
            )

            # Add UPSC metadata to segment
            news_segment.subject_category = subject
            news_segment.exam_relevance = exam_relevance
            news_segment.timestamp = f"{int(cumulative_time // 60):02d}:{int(cumulative_time % 60):02d}"

            # Extract key points if in UPSC mode
            if self.upsc_mode:
                news_segment.key_points = self._extract_key_points(article)
                news_segment.important_terms = self._extract_important_terms(article)

            script.segments.append(news_segment)
            cumulative_time += news_segment.duration_estimate

        # 3. Generate Conclusion with UPSC focus
        topics = [a.title for a in articles]
        conclusion = self._generate_conclusion(
            date=date,
            language=language,
            story_count=len(articles),
            topics=topics
        )
        conclusion.timestamp = f"{int(cumulative_time // 60):02d}:{int(cumulative_time % 60):02d}"
        script.segments.append(conclusion)

        # Calculate totals
        script.word_count = sum(
            len(seg.content.split()) for seg in script.segments
        )
        script.total_duration = script.word_count / self.WORDS_PER_MINUTE * 60

        logger.info(
            f"UPSC Script generated: {script.word_count} words, "
            f"~{script.total_duration/60:.1f} minutes, "
            f"Subjects: {', '.join(script.subjects_covered)}"
        )

        return script

    def _extract_key_points(self, article: NewsArticle) -> List[str]:
        """Extract key points for video overlays and PDF notes."""
        try:
            prompt = PromptTemplates.get_key_points_prompt(
                f"{article.title}\n{article.content or article.summary or ''}"
            )

            response = self.llm.generate(
                prompt=prompt,
                max_tokens=600,
                temperature=0.3
            )

            # Parse key points from response
            points = []
            for line in response.split('\n'):
                if line.strip().startswith('POINT:'):
                    point = line.replace('POINT:', '').strip()
                    if point:
                        points.append(point)

            return points[:5]  # Max 5 key points
        except Exception as e:
            logger.warning(f"Failed to extract key points: {e}")
            return []

    def _extract_important_terms(self, article: NewsArticle) -> Dict[str, str]:
        """Extract important terms and abbreviations."""
        content = f"{article.title} {article.content or article.summary or ''}"

        # Find common patterns like abbreviations
        import re
        terms = {}

        # Find patterns like "ABC (Full Form)" or "Full Form (ABC)"
        patterns = [
            r'([A-Z]{2,6})\s*\(([^)]+)\)',  # ABC (Full Form)
            r'([^(]+)\s*\(([A-Z]{2,6})\)',  # Full Form (ABC)
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches[:5]:  # Limit to 5 terms
                if len(match[0]) < 50 and len(match[1]) < 50:
                    terms[match[0].strip()] = match[1].strip()

        return terms

    def _generate_intro(
        self,
        articles: List[NewsArticle],
        date: str,
        language: str
    ) -> ScriptSegment:
        """Generate introduction segment"""
        topics = [a.title for a in articles[:5]]

        prompt = PromptTemplates.get_intro_prompt(
            date=date,
            language=language,
            topics=topics,
            duration=self.target_duration,
            intro_words=self.intro_words
        )

        content = self.llm.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
            max_tokens=500,
            temperature=0.7
        )

        # Clean up content
        content = self._clean_script_content(content)

        return ScriptSegment(
            type="intro",
            content=content,
            duration_estimate=len(content.split()) / self.WORDS_PER_MINUTE * 60
        )

    def _generate_news_segment(
        self,
        article: NewsArticle,
        language: str,
        word_count: int
    ) -> ScriptSegment:
        """Generate a single news segment"""
        prompt = PromptTemplates.get_news_item_prompt(
            title=article.title,
            source=article.source,
            summary=article.summary or "",
            content=article.content or article.summary or "",
            language=language,
            word_count=word_count
        )

        content = self.llm.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
            max_tokens=word_count * 2,  # Allow some flexibility
            temperature=0.6
        )

        # Clean up content
        content = self._clean_script_content(content)

        return ScriptSegment(
            type="news",
            content=content,
            duration_estimate=len(content.split()) / self.WORDS_PER_MINUTE * 60,
            article=article
        )

    def _generate_conclusion(
        self,
        date: str,
        language: str,
        story_count: int,
        topics: List[str]
    ) -> ScriptSegment:
        """Generate conclusion segment"""
        prompt = PromptTemplates.get_conclusion_prompt(
            date=date,
            language=language,
            story_count=story_count,
            topics=topics,
            conclusion_words=self.conclusion_words
        )

        content = self.llm.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
            max_tokens=300,
            temperature=0.7
        )

        # Clean up content
        content = self._clean_script_content(content)

        return ScriptSegment(
            type="conclusion",
            content=content,
            duration_estimate=len(content.split()) / self.WORDS_PER_MINUTE * 60
        )

    def _clean_script_content(self, content: str) -> str:
        """Clean and format script content for TTS"""
        if not content:
            return ""

        # Remove markdown formatting
        content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)  # Bold
        content = re.sub(r'\*(.+?)\*', r'\1', content)  # Italic
        content = re.sub(r'#+ ', '', content)  # Headers

        # Remove bullet points and numbering
        content = re.sub(r'^\s*[-*•]\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*\d+\.\s*', '', content, flags=re.MULTILINE)

        # Remove extra whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = re.sub(r' {2,}', ' ', content)

        # Ensure proper sentence endings
        content = content.strip()

        return content

    def translate_script(
        self,
        script: VideoScript,
        target_language: str
    ) -> VideoScript:
        """
        Translate script to another language.

        Args:
            script: Script to translate
            target_language: Target language name

        Returns:
            Translated VideoScript
        """
        logger.info(f"Translating script to {target_language}")

        translated_segments = []

        for segment in script.segments:
            if segment.type == "transition":
                # Keep transitions as-is or translate simply
                translated_content = segment.content
            else:
                # Translate using LLM
                prompt = PromptTemplates.get_translation_prompt(
                    script=segment.content,
                    target_language=target_language
                )

                translated_content = self.llm.generate(
                    prompt=prompt,
                    max_tokens=len(segment.content.split()) * 3,
                    temperature=0.3
                )

                translated_content = self._clean_script_content(translated_content)

            translated_segments.append(ScriptSegment(
                type=segment.type,
                content=translated_content,
                duration_estimate=segment.duration_estimate,
                article=segment.article
            ))

        return VideoScript(
            title=script.title,
            date=script.date,
            language=target_language,
            segments=translated_segments,
            total_duration=script.total_duration,
            word_count=sum(len(s.content.split()) for s in translated_segments),
            article_count=script.article_count
        )

    def save_script(self, script: VideoScript, output_path: str) -> None:
        """
        Save script to file.

        Args:
            script: Script to save
            output_path: Output file path
        """
        from pathlib import Path

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# {script.title}\n")
            f.write(f"Date: {script.date}\n")
            f.write(f"Language: {script.language}\n")
            f.write(f"Duration: ~{script.total_duration/60:.1f} minutes\n")
            f.write(f"Word Count: {script.word_count}\n")
            f.write(f"Articles: {script.article_count}\n")
            f.write("\n" + "="*50 + "\n\n")

            for i, segment in enumerate(script.segments, 1):
                f.write(f"## Segment {i}: {segment.type.upper()}\n")
                if segment.article:
                    f.write(f"Source: {segment.article.source}\n")
                f.write(f"Duration: ~{segment.duration_estimate:.0f}s\n\n")
                f.write(segment.content)
                f.write("\n\n" + "-"*30 + "\n\n")

        logger.info(f"Script saved to: {output_path}")


# CLI interface for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Script Writer CLI")
    parser.add_argument("--test", action="store_true", help="Run test generation")
    parser.add_argument("--provider", type=str, default="groq", help="LLM provider")

    args = parser.parse_args()

    if args.test:
        print("\n=== Running Script Writer Test ===\n")

        # Create test articles
        test_articles = [
            NewsArticle(
                title="India Launches New Space Mission",
                url="https://example.com/1",
                source="Test News",
                category="science",
                summary="India successfully launched a new satellite mission today, marking another milestone in the country's space program.",
                content="India successfully launched a new satellite mission today, marking another milestone in the country's space program. The satellite will help improve communication services across rural areas."
            ),
            NewsArticle(
                title="Government Announces New Economic Policy",
                url="https://example.com/2",
                source="Test News",
                category="economy",
                summary="The government today announced a new economic policy aimed at boosting growth and reducing inflation.",
                content="The government today announced a new economic policy aimed at boosting growth and reducing inflation. The policy includes tax reforms and increased spending on infrastructure."
            )
        ]

        try:
            writer = ScriptWriter(llm_provider=args.provider, target_duration_minutes=5)
            script = writer.generate_script(test_articles, language="English")

            print(f"Title: {script.title}")
            print(f"Duration: ~{script.total_duration/60:.1f} minutes")
            print(f"Word Count: {script.word_count}")
            print(f"\n{'='*50}\n")
            print(script.get_full_script())

        except Exception as e:
            print(f"Error: {e}")
            print("\nMake sure you have set up the LLM provider:")
            print("  - For Groq: Set GROQ_API_KEY environment variable")
            print("  - For Ollama: Run 'ollama serve' and pull a model")
