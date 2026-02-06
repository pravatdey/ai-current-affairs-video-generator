"""
Prompt Templates for News Script Generation
Optimized for UPSC/Competitive Exam Preparation
"""

from typing import List, Dict, Any


class PromptTemplates:
    """Collection of prompt templates for script generation"""

    # System prompt for the news anchor persona - UPSC focused
    SYSTEM_PROMPT = """You are a professional current affairs educator specializing in UPSC and competitive exam preparation.
Your job is to present news in an engaging, educational, and comprehensive manner suitable for serious exam aspirants.

Guidelines:
- Be professional, authoritative, and educational
- Use clear language but don't oversimplify - treat viewers as intelligent aspirants
- Present facts with context - explain WHY something matters for India
- Connect current events to UPSC syllabus topics (Polity, Economy, IR, Environment, etc.)
- Mention relevant constitutional provisions, acts, or policies when applicable
- Include important dates, names, figures, and statistics
- Explain the significance for Prelims (factual) and Mains (analytical)
- Add historical context or background when it aids understanding
- Use smooth transitions between news items
- Keep sentences clear and suitable for spoken delivery
- Explain technical terms and abbreviations
- Maintain educational integrity - accuracy is paramount

The script should be suitable for text-to-speech conversion and educational content."""

    # UPSC-specific system prompt for detailed analysis
    UPSC_SYSTEM_PROMPT = """You are an expert UPSC mentor and current affairs analyst.
Your role is to analyze news for competitive exam relevance and create comprehensive educational content.

Your analysis should:
1. Identify the UPSC relevance (Prelims factual points vs Mains analytical aspects)
2. Connect to relevant GS papers (GS1: History/Geography/Society, GS2: Polity/IR/Governance, GS3: Economy/Environment/S&T/Security, GS4: Ethics)
3. Link to static portions of the syllabus
4. Highlight potential question angles
5. Note important facts, figures, dates, and names
6. Provide background context from Indian perspective
7. Mention related government schemes or policies
8. Include constitutional/legal framework when applicable

Focus on depth of analysis while maintaining clarity."""

    # Introduction template - UPSC focused
    INTRO_TEMPLATE = """Write an engaging introduction for a {duration}-minute UPSC current affairs video.

Date: {date}
Language: {language}
Topics to be covered: {topic_list}

The introduction should:
1. Greet the viewers warmly (address them as "aspirants" or "future civil servants")
2. Mention it's a comprehensive daily current affairs session for UPSC preparation
3. Briefly preview the major topics and their exam relevance
4. Highlight if any topic is particularly important for upcoming exams
5. Encourage viewers to take notes
6. Be approximately {intro_words} words

Write only the introduction script, no headers or labels."""

    # News item template - UPSC focused with detailed analysis
    NEWS_ITEM_TEMPLATE = """Write a comprehensive educational segment for UPSC aspirants on the following topic.

Headline: {title}
Source: {source}
Summary: {summary}
Full Content: {content}

Requirements:
- Length: {word_count} words approximately
- Language: {language}

Structure your segment as follows:
1. INTRODUCTION (What happened - clear headline statement)
2. BACKGROUND (Why is this important? What led to this?)
3. KEY DETAILS (Important facts, figures, dates, names - be specific)
4. UPSC RELEVANCE (Which paper? Prelims/Mains angle? Related syllabus topics)
5. ANALYSIS (Impact on India, various stakeholders, multiple perspectives)
6. GOVERNMENT'S ROLE (Related policies, schemes, constitutional provisions if any)
7. WAY FORWARD (Future implications, what aspirants should remember)

Additional Guidelines:
- Include all important statistics and data points
- Mention full names of people and organizations (with abbreviations)
- Connect to related static topics from UPSC syllabus
- Highlight potential Prelims MCQ points
- Provide analytical angles for Mains answers
- Use short, clear sentences suitable for speaking
- Be educational but engaging

Write only the news script, no headers or labels."""

    # Transition templates between news items
    TRANSITIONS = [
        "Moving on to our next story...",
        "In other news...",
        "Now, let's turn our attention to...",
        "Next up...",
        "Shifting gears to...",
        "Also making headlines today...",
        "Another important development...",
        "Meanwhile...",
        "On a different note...",
        "Coming up next...",
    ]

    # Conclusion template - UPSC focused
    CONCLUSION_TEMPLATE = """Write a conclusion for a UPSC current affairs video session.

Date: {date}
Language: {language}
Number of stories covered: {story_count}
Main topics: {topic_list}

The conclusion should:
1. Provide a quick recap of major topics covered
2. Highlight 2-3 most important points to remember for exams
3. Remind viewers about the PDF notes available in description
4. Encourage them to practice related PYQs (Previous Year Questions)
5. Motivate them for their preparation journey
6. Thank viewers and ask them to subscribe for daily updates
7. Wish them success in their preparation
8. Be approximately {conclusion_words} words

Write only the conclusion script, no headers or labels."""

    # Translation prompt
    TRANSLATION_TEMPLATE = """Translate the following news script to {target_language}.

Requirements:
- Maintain the professional news anchor tone
- Keep the meaning and context intact
- Use natural {target_language} expressions
- Keep it suitable for spoken delivery
- Don't translate proper nouns that are commonly used in English

Script to translate:
{script}

Write only the translated script, no headers or labels."""

    # Summary generation for long articles
    SUMMARY_TEMPLATE = """Summarize the following news article in {max_words} words or less.

Article:
{content}

Requirements:
- Capture all key facts
- Include important names, dates, and figures
- Maintain objectivity
- Write in complete sentences

Write only the summary, no headers or labels."""

    # Script improvement prompt
    IMPROVE_SCRIPT_TEMPLATE = """Improve the following news script for better spoken delivery.

Current script:
{script}

Improvements needed:
- Break long sentences into shorter ones
- Remove complex words and replace with simpler alternatives
- Add natural pauses (indicated by commas)
- Ensure smooth flow between sentences
- Make it sound more conversational while staying professional
- Target length: {target_words} words

Write only the improved script, no headers or labels."""

    @classmethod
    def get_intro_prompt(
        cls,
        date: str,
        language: str,
        topics: List[str],
        duration: int = 10,
        intro_words: int = 100
    ) -> str:
        """Generate introduction prompt"""
        topic_list = ", ".join(topics[:5])  # First 5 topics
        return cls.INTRO_TEMPLATE.format(
            date=date,
            language=language,
            topic_list=topic_list,
            duration=duration,
            intro_words=intro_words
        )

    @classmethod
    def get_news_item_prompt(
        cls,
        title: str,
        source: str,
        summary: str,
        content: str,
        language: str = "English",
        word_count: int = 150
    ) -> str:
        """Generate news item prompt"""
        # Truncate content if too long
        max_content = 2000
        if len(content) > max_content:
            content = content[:max_content] + "..."

        return cls.NEWS_ITEM_TEMPLATE.format(
            title=title,
            source=source,
            summary=summary[:500] if summary else "",
            content=content,
            language=language,
            word_count=word_count
        )

    @classmethod
    def get_transition(cls, index: int = 0) -> str:
        """Get a transition phrase"""
        return cls.TRANSITIONS[index % len(cls.TRANSITIONS)]

    @classmethod
    def get_conclusion_prompt(
        cls,
        date: str,
        language: str,
        story_count: int,
        topics: List[str],
        conclusion_words: int = 80
    ) -> str:
        """Generate conclusion prompt"""
        topic_list = ", ".join(topics[:5])
        return cls.CONCLUSION_TEMPLATE.format(
            date=date,
            language=language,
            story_count=story_count,
            topic_list=topic_list,
            conclusion_words=conclusion_words
        )

    @classmethod
    def get_translation_prompt(cls, script: str, target_language: str) -> str:
        """Generate translation prompt"""
        return cls.TRANSLATION_TEMPLATE.format(
            script=script,
            target_language=target_language
        )

    @classmethod
    def get_summary_prompt(cls, content: str, max_words: int = 100) -> str:
        """Generate summary prompt"""
        return cls.SUMMARY_TEMPLATE.format(
            content=content[:5000],  # Limit content length
            max_words=max_words
        )

    @classmethod
    def get_improve_prompt(cls, script: str, target_words: int) -> str:
        """Generate script improvement prompt"""
        return cls.IMPROVE_SCRIPT_TEMPLATE.format(
            script=script,
            target_words=target_words
        )

    # ===================== UPSC-SPECIFIC TEMPLATES =====================

    # Key points extraction for video overlays
    KEY_POINTS_TEMPLATE = """Extract the most important exam-relevant points from this news content for UPSC preparation.

Content: {content}

Extract exactly 5 key points that are:
1. Factually important for Prelims (names, dates, numbers, organizations)
2. Analytically important for Mains (impact, significance, implications)

Format each point as:
POINT: [concise key point - max 15 words]
TYPE: [PRELIMS/MAINS/BOTH]
CATEGORY: [Polity/Economy/IR/Environment/S&T/Social/Security/Geography/History]

Focus on exam-worthy facts that could appear in questions."""

    # Practice questions generation
    PRACTICE_QUESTIONS_TEMPLATE = """Generate UPSC-style practice questions based on this news.

Title: {title}
Content: {content}
Subject: {subject}

Create:

1. PRELIMS MCQ:
Generate one high-quality multiple choice question with 4 options (a, b, c, d).
Mark the correct answer. Make it similar to actual UPSC Prelims difficulty.

2. MAINS QUESTION (GS Paper):
Generate one analytical question suitable for UPSC Mains (150-200 word answer expected).
Include directive words like Discuss/Analyze/Examine/Critically evaluate.

3. CURRENT AFFAIRS QUESTION:
Generate one factual question that tests basic awareness of this news.

Format:
PRELIMS:
Q: [question]
a) [option]
b) [option]
c) [option]
d) [option]
Answer: [correct option letter]

MAINS:
Q: [question]

CURRENT AFFAIRS:
Q: [question]"""

    # Static GK connection template
    STATIC_LINK_TEMPLATE = """Identify static/background topics that UPSC aspirants should study to better understand this current affairs news.

News: {title}
Content: {content}

List 3-5 related static topics from UPSC syllabus that provide background knowledge.
Format:
TOPIC: [topic name]
RELEVANCE: [how it connects to this news]
GS_PAPER: [GS1/GS2/GS3/GS4]"""

    # Comprehensive analysis for Mains
    MAINS_ANALYSIS_TEMPLATE = """Provide a comprehensive Mains-level analysis of this news for UPSC preparation.

Topic: {title}
Content: {content}

Structure your analysis:

1. INTRODUCTION (2-3 sentences contextualizing the issue)

2. BACKGROUND
- Historical context
- Previous developments
- Relevant policies/schemes

3. CURRENT DEVELOPMENT
- What has happened
- Key stakeholders
- Important provisions/features

4. MULTIPLE PERSPECTIVES
- Government's view
- Opposition/critics' view
- Expert opinions
- International perspective (if applicable)

5. IMPACT ANALYSIS
- Economic impact
- Social impact
- Political/governance impact
- Environmental impact (if applicable)

6. CONSTITUTIONAL/LEGAL FRAMEWORK
- Relevant constitutional provisions
- Acts/laws involved
- Institutional mechanisms

7. CHALLENGES
- Implementation challenges
- Structural issues
- Resource constraints

8. WAY FORWARD
- Suggested reforms
- Best practices (national/international)
- Expert recommendations

9. CONCLUSION (2-3 sentences summarizing significance)

This analysis should help aspirants write a comprehensive Mains answer on this topic."""

    @classmethod
    def get_key_points_prompt(cls, content: str) -> str:
        """Generate key points extraction prompt"""
        return cls.KEY_POINTS_TEMPLATE.format(content=content[:3000])

    @classmethod
    def get_practice_questions_prompt(
        cls,
        title: str,
        content: str,
        subject: str = "Current Affairs"
    ) -> str:
        """Generate practice questions prompt"""
        return cls.PRACTICE_QUESTIONS_TEMPLATE.format(
            title=title,
            content=content[:2500],
            subject=subject
        )

    @classmethod
    def get_static_link_prompt(cls, title: str, content: str) -> str:
        """Generate static GK connection prompt"""
        return cls.STATIC_LINK_TEMPLATE.format(
            title=title,
            content=content[:2000]
        )

    @classmethod
    def get_mains_analysis_prompt(cls, title: str, content: str) -> str:
        """Generate comprehensive Mains analysis prompt"""
        return cls.MAINS_ANALYSIS_TEMPLATE.format(
            title=title,
            content=content[:4000]
        )
