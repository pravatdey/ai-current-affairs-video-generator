"""
PDF Notes Generator - Creates study notes for UPSC/competitive exam preparation
"""

import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, ListFlowable, ListItem, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .content_extractor import ExtractedContent, KeyPoint, UPSCRelevance
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TopicNote:
    """A single topic's notes"""
    title: str
    summary: str
    key_points: List[KeyPoint]
    upsc_relevance: UPSCRelevance
    important_terms: Dict[str, str]
    practice_questions: List[str]
    related_topics: List[str]
    image_path: Optional[str] = None
    timestamp: str = ""  # Video timestamp reference


@dataclass
class StudyNote:
    """Complete study notes for a video/class"""
    title: str
    date: str
    topics: List[TopicNote]
    video_duration: float = 0.0
    video_path: Optional[str] = None
    language: str = "English"
    additional_resources: List[str] = field(default_factory=list)


class PDFNotesGenerator:
    """
    Generates comprehensive PDF study notes optimized for UPSC preparation.
    """

    # Color scheme for UPSC notes
    COLORS = {
        'primary': colors.HexColor('#1a365d'),      # Dark blue
        'secondary': colors.HexColor('#2c5282'),    # Medium blue
        'accent': colors.HexColor('#ed8936'),       # Orange
        'success': colors.HexColor('#38a169'),      # Green
        'warning': colors.HexColor('#d69e2e'),      # Yellow
        'danger': colors.HexColor('#e53e3e'),       # Red
        'light': colors.HexColor('#f7fafc'),        # Light gray
        'dark': colors.HexColor('#1a202c'),         # Dark gray
        'prelims': colors.HexColor('#3182ce'),      # Blue for Prelims
        'mains': colors.HexColor('#805ad5'),        # Purple for Mains
    }

    def __init__(self, output_dir: str = "output/notes"):
        """
        Initialize PDF notes generator.

        Args:
            output_dir: Directory to save generated PDFs
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize styles
        self.styles = self._create_styles()

        logger.info(f"PDFNotesGenerator initialized. Output: {self.output_dir}")

    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        """Create custom paragraph styles for the PDF."""
        base_styles = getSampleStyleSheet()

        custom_styles = {
            'MainTitle': ParagraphStyle(
                'MainTitle',
                parent=base_styles['Heading1'],
                fontSize=24,
                textColor=self.COLORS['primary'],
                spaceAfter=20,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            ),
            'SubTitle': ParagraphStyle(
                'SubTitle',
                parent=base_styles['Normal'],
                fontSize=14,
                textColor=self.COLORS['secondary'],
                spaceAfter=30,
                alignment=TA_CENTER
            ),
            'TopicTitle': ParagraphStyle(
                'TopicTitle',
                parent=base_styles['Heading2'],
                fontSize=16,
                textColor=self.COLORS['primary'],
                spaceBefore=20,
                spaceAfter=10,
                fontName='Helvetica-Bold',
                borderWidth=1,
                borderColor=self.COLORS['primary'],
                borderPadding=5
            ),
            'SectionHeader': ParagraphStyle(
                'SectionHeader',
                parent=base_styles['Heading3'],
                fontSize=12,
                textColor=self.COLORS['secondary'],
                spaceBefore=15,
                spaceAfter=8,
                fontName='Helvetica-Bold'
            ),
            'KeyPoint': ParagraphStyle(
                'KeyPoint',
                parent=base_styles['Normal'],
                fontSize=10,
                textColor=self.COLORS['dark'],
                spaceBefore=5,
                spaceAfter=5,
                leftIndent=15,
                bulletIndent=5
            ),
            'BodyText': ParagraphStyle(
                'BodyText',
                parent=base_styles['Normal'],
                fontSize=10,
                textColor=self.COLORS['dark'],
                spaceBefore=5,
                spaceAfter=5,
                alignment=TA_JUSTIFY
            ),
            'Term': ParagraphStyle(
                'Term',
                parent=base_styles['Normal'],
                fontSize=10,
                textColor=self.COLORS['primary'],
                fontName='Helvetica-Bold'
            ),
            'Definition': ParagraphStyle(
                'Definition',
                parent=base_styles['Normal'],
                fontSize=10,
                textColor=self.COLORS['dark'],
                leftIndent=15
            ),
            'Question': ParagraphStyle(
                'Question',
                parent=base_styles['Normal'],
                fontSize=10,
                textColor=self.COLORS['secondary'],
                spaceBefore=8,
                spaceAfter=5,
                leftIndent=10,
                fontName='Helvetica-Oblique'
            ),
            'Tag': ParagraphStyle(
                'Tag',
                parent=base_styles['Normal'],
                fontSize=8,
                textColor=colors.white,
                alignment=TA_CENTER
            ),
            'Footer': ParagraphStyle(
                'Footer',
                parent=base_styles['Normal'],
                fontSize=8,
                textColor=self.COLORS['secondary'],
                alignment=TA_CENTER
            ),
            'Timestamp': ParagraphStyle(
                'Timestamp',
                parent=base_styles['Normal'],
                fontSize=9,
                textColor=self.COLORS['accent'],
                fontName='Helvetica-Oblique'
            ),
            'Important': ParagraphStyle(
                'Important',
                parent=base_styles['Normal'],
                fontSize=10,
                textColor=self.COLORS['danger'],
                fontName='Helvetica-Bold',
                spaceBefore=10,
                spaceAfter=10,
                borderWidth=1,
                borderColor=self.COLORS['danger'],
                borderPadding=8,
                backColor=colors.HexColor('#fff5f5')
            )
        }

        return custom_styles

    def generate_notes(
        self,
        study_note: StudyNote,
        include_images: bool = True,
        include_questions: bool = True
    ) -> str:
        """
        Generate comprehensive PDF study notes.

        Args:
            study_note: StudyNote object with all content
            include_images: Whether to include images
            include_questions: Whether to include practice questions

        Returns:
            Path to generated PDF file
        """
        # Generate filename
        date_str = datetime.now().strftime("%Y%m%d")
        safe_title = "".join(c for c in study_note.title if c.isalnum() or c in ' -_')[:50]
        filename = f"{date_str}_{safe_title.replace(' ', '_')}_Notes.pdf"
        output_path = self.output_dir / filename

        logger.info(f"Generating PDF notes: {filename}")

        # Create document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        # Build content
        story = []

        # Title Page
        story.extend(self._create_title_page(study_note))

        # Table of Contents
        story.extend(self._create_toc(study_note))

        # Topics
        for i, topic in enumerate(study_note.topics, 1):
            story.extend(self._create_topic_section(
                topic, i, include_images, include_questions
            ))

        # Summary Section
        story.extend(self._create_summary_section(study_note))

        # Quick Revision Section
        story.extend(self._create_quick_revision(study_note))

        # Resources Section
        if study_note.additional_resources:
            story.extend(self._create_resources_section(study_note))

        # Build PDF
        try:
            doc.build(story)
            logger.info(f"PDF generated successfully: {output_path}")
            return str(output_path)
        except Exception as e:
            logger.error(f"Failed to generate PDF: {e}")
            raise

    def _create_title_page(self, study_note: StudyNote) -> List:
        """Create title page elements."""
        elements = []

        # Add spacing at top
        elements.append(Spacer(1, 2*inch))

        # Main title
        elements.append(Paragraph(
            f"<b>UPSC CURRENT AFFAIRS</b>",
            self.styles['MainTitle']
        ))

        # Date and title
        elements.append(Paragraph(
            f"{study_note.title}",
            self.styles['SubTitle']
        ))

        elements.append(Paragraph(
            f"Date: {study_note.date}",
            self.styles['SubTitle']
        ))

        elements.append(Spacer(1, 0.5*inch))

        # Info box
        info_data = [
            ['Total Topics', str(len(study_note.topics))],
            ['Language', study_note.language],
            ['Video Duration', f"{study_note.video_duration/60:.0f} minutes" if study_note.video_duration else "N/A"]
        ]

        info_table = Table(info_data, colWidths=[2.5*inch, 2.5*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.COLORS['light']),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.COLORS['dark']),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, self.COLORS['secondary'])
        ]))
        elements.append(info_table)

        elements.append(Spacer(1, 1*inch))

        # Exam relevance summary
        prelims_count = sum(
            1 for t in study_note.topics
            if t.upsc_relevance and t.upsc_relevance.exam_relevance.value in ['prelims', 'both']
        )
        mains_count = sum(
            1 for t in study_note.topics
            if t.upsc_relevance and t.upsc_relevance.exam_relevance.value in ['mains', 'both']
        )

        relevance_text = f"""
        <b>Exam Relevance:</b><br/>
        Prelims Important: {prelims_count} topics<br/>
        Mains Important: {mains_count} topics
        """
        elements.append(Paragraph(relevance_text, self.styles['BodyText']))

        elements.append(PageBreak())

        return elements

    def _create_toc(self, study_note: StudyNote) -> List:
        """Create table of contents."""
        elements = []

        elements.append(Paragraph(
            "Table of Contents",
            self.styles['TopicTitle']
        ))

        elements.append(Spacer(1, 0.3*inch))

        toc_data = []
        for i, topic in enumerate(study_note.topics, 1):
            # Create subject tag
            subject = topic.upsc_relevance.subject.value if topic.upsc_relevance else "Current Affairs"
            toc_data.append([
                f"{i}.",
                topic.title[:60] + "..." if len(topic.title) > 60 else topic.title,
                subject
            ])

        if toc_data:
            toc_table = Table(toc_data, colWidths=[0.4*inch, 4*inch, 1.5*inch])
            toc_table.setStyle(TableStyle([
                ('TEXTCOLOR', (0, 0), (-1, -1), self.COLORS['dark']),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('LINEBELOW', (0, 0), (-1, -2), 0.5, self.COLORS['light']),
                ('BACKGROUND', (2, 0), (2, -1), self.COLORS['light']),
            ]))
            elements.append(toc_table)

        elements.append(PageBreak())

        return elements

    def _create_topic_section(
        self,
        topic: TopicNote,
        topic_num: int,
        include_images: bool,
        include_questions: bool
    ) -> List:
        """Create a topic section."""
        elements = []

        # Topic header with number
        elements.append(Paragraph(
            f"Topic {topic_num}: {topic.title}",
            self.styles['TopicTitle']
        ))

        # UPSC Relevance tags
        if topic.upsc_relevance:
            elements.extend(self._create_relevance_tags(topic.upsc_relevance))

        # Video timestamp if available
        if topic.timestamp:
            elements.append(Paragraph(
                f"Video Timestamp: {topic.timestamp}",
                self.styles['Timestamp']
            ))

        elements.append(Spacer(1, 0.2*inch))

        # Summary
        elements.append(Paragraph(
            "<b>Summary:</b>",
            self.styles['SectionHeader']
        ))
        elements.append(Paragraph(
            topic.summary,
            self.styles['BodyText']
        ))

        # Key Points
        if topic.key_points:
            elements.append(Paragraph(
                "<b>Key Points:</b>",
                self.styles['SectionHeader']
            ))
            elements.extend(self._create_key_points_list(topic.key_points))

        # Important Terms
        if topic.important_terms:
            elements.append(Paragraph(
                "<b>Important Terms:</b>",
                self.styles['SectionHeader']
            ))
            elements.extend(self._create_terms_table(topic.important_terms))

        # Practice Questions
        if include_questions and topic.practice_questions:
            elements.append(Paragraph(
                "<b>Practice Questions:</b>",
                self.styles['SectionHeader']
            ))
            for q in topic.practice_questions:
                elements.append(Paragraph(f"Q: {q}", self.styles['Question']))

        # Related Topics for further study
        if topic.related_topics:
            elements.append(Paragraph(
                "<b>Related Topics for Study:</b>",
                self.styles['SectionHeader']
            ))
            related_text = " | ".join(topic.related_topics)
            elements.append(Paragraph(related_text, self.styles['BodyText']))

        # Add horizontal rule before next topic
        elements.append(Spacer(1, 0.3*inch))
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=self.COLORS['light'],
            spaceBefore=10,
            spaceAfter=10
        ))

        return elements

    def _create_relevance_tags(self, relevance: UPSCRelevance) -> List:
        """Create UPSC relevance tags."""
        elements = []

        # Create tag data
        tags = []

        # Subject tag
        tags.append(('Subject', relevance.subject.value, self.COLORS['primary']))

        # Exam relevance tag
        if relevance.exam_relevance.value == 'prelims':
            tags.append(('Exam', 'PRELIMS', self.COLORS['prelims']))
        elif relevance.exam_relevance.value == 'mains':
            tags.append(('Exam', 'MAINS', self.COLORS['mains']))
        else:
            tags.append(('Exam', 'PRELIMS + MAINS', self.COLORS['accent']))

        # Mains paper tag
        if relevance.mains_paper:
            tags.append(('Paper', relevance.mains_paper, self.COLORS['secondary']))

        # Create tags table
        tag_cells = []
        for label, value, color in tags:
            tag_cells.append(f"{label}: {value}")

        tag_text = " | ".join(tag_cells)
        elements.append(Paragraph(
            f"<font color='#666666' size='9'>{tag_text}</font>",
            self.styles['BodyText']
        ))

        return elements

    def _create_key_points_list(self, key_points: List[KeyPoint]) -> List:
        """Create formatted list of key points."""
        elements = []

        for i, kp in enumerate(key_points, 1):
            # Main point
            point_text = f"<b>{i}.</b> {kp.text}"

            # Add dates if present
            if kp.dates:
                point_text += f" <font color='#d69e2e'>[Dates: {', '.join(kp.dates)}]</font>"

            # Add figures if present
            if kp.figures:
                point_text += f" <font color='#38a169'>[Facts: {', '.join(kp.figures)}]</font>"

            elements.append(Paragraph(point_text, self.styles['KeyPoint']))

            # Related facts as sub-points
            if kp.related_facts:
                for fact in kp.related_facts:
                    elements.append(Paragraph(
                        f"    - {fact}",
                        self.styles['BodyText']
                    ))

        return elements

    def _create_terms_table(self, terms: Dict[str, str]) -> List:
        """Create table of important terms."""
        elements = []

        term_data = [['Term', 'Definition']]
        for term, definition in terms.items():
            term_data.append([term, definition])

        if len(term_data) > 1:
            term_table = Table(term_data, colWidths=[1.5*inch, 4.5*inch])
            term_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['primary']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (0, -1), self.COLORS['light']),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, self.COLORS['secondary']),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(term_table)

        return elements

    def _create_summary_section(self, study_note: StudyNote) -> List:
        """Create overall summary section."""
        elements = []

        elements.append(PageBreak())

        elements.append(Paragraph(
            "Summary of Today's Current Affairs",
            self.styles['TopicTitle']
        ))

        elements.append(Spacer(1, 0.2*inch))

        # Create summary points
        for i, topic in enumerate(study_note.topics, 1):
            summary_text = f"<b>{i}. {topic.title}:</b> {topic.summary[:200]}..."
            elements.append(Paragraph(summary_text, self.styles['BodyText']))
            elements.append(Spacer(1, 0.1*inch))

        return elements

    def _create_quick_revision(self, study_note: StudyNote) -> List:
        """Create quick revision section with all key facts."""
        elements = []

        elements.append(PageBreak())

        elements.append(Paragraph(
            "Quick Revision - Key Facts",
            self.styles['TopicTitle']
        ))

        elements.append(Paragraph(
            "<i>Use this section for last-minute revision before exams</i>",
            self.styles['BodyText']
        ))

        elements.append(Spacer(1, 0.2*inch))

        # Collect all key points across topics
        fact_num = 1
        for topic in study_note.topics:
            for kp in topic.key_points[:2]:  # Top 2 points per topic
                elements.append(Paragraph(
                    f"<b>{fact_num}.</b> {kp.text}",
                    self.styles['KeyPoint']
                ))
                fact_num += 1

        # Important numbers/statistics box
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph(
            "<b>Important Numbers & Statistics:</b>",
            self.styles['SectionHeader']
        ))

        figures = []
        for topic in study_note.topics:
            for kp in topic.key_points:
                figures.extend(kp.figures)

        if figures:
            figures_text = " | ".join(set(figures)[:15])  # Unique, max 15
            elements.append(Paragraph(figures_text, self.styles['BodyText']))
        else:
            elements.append(Paragraph(
                "No specific statistics in today's topics.",
                self.styles['BodyText']
            ))

        return elements

    def _create_resources_section(self, study_note: StudyNote) -> List:
        """Create additional resources section."""
        elements = []

        elements.append(Spacer(1, 0.5*inch))

        elements.append(Paragraph(
            "Additional Resources",
            self.styles['SectionHeader']
        ))

        for resource in study_note.additional_resources:
            elements.append(Paragraph(f"- {resource}", self.styles['BodyText']))

        return elements

    def generate_from_extracted_content(
        self,
        extracted_contents: List[ExtractedContent],
        title: str,
        date: str = None,
        video_duration: float = 0.0
    ) -> str:
        """
        Generate PDF from list of ExtractedContent objects.

        Args:
            extracted_contents: List of extracted content
            title: Title for the notes
            date: Date string
            video_duration: Video duration in seconds

        Returns:
            Path to generated PDF
        """
        date = date or datetime.now().strftime("%B %d, %Y")

        # Convert ExtractedContent to TopicNote
        topics = []
        for i, content in enumerate(extracted_contents):
            # Calculate approximate timestamp
            timestamp = f"{(i * video_duration / len(extracted_contents) / 60):.0f}:00" if video_duration else ""

            topic = TopicNote(
                title=content.article.title,
                summary=content.summary,
                key_points=content.key_points,
                upsc_relevance=content.upsc_relevance,
                important_terms=content.important_terms,
                practice_questions=content.practice_questions,
                related_topics=content.related_topics,
                timestamp=timestamp
            )
            topics.append(topic)

        # Create StudyNote
        study_note = StudyNote(
            title=title,
            date=date,
            topics=topics,
            video_duration=video_duration
        )

        return self.generate_notes(study_note)


# CLI interface for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PDF Notes Generator CLI")
    parser.add_argument("--test", action="store_true", help="Run test generation")

    args = parser.parse_args()

    if args.test:
        print("\n=== Running PDF Notes Generator Test ===\n")

        from .content_extractor import KeyPoint, UPSCRelevance, SubjectCategory, ExamRelevance

        # Create test data
        test_topic = TopicNote(
            title="India Launches New Space Mission to Study Sun",
            summary="ISRO successfully launched Aditya-L1, India's first solar observation mission. The spacecraft will study the Sun's corona and solar winds from the L1 Lagrange point.",
            key_points=[
                KeyPoint(
                    text="Aditya-L1 is India's first dedicated solar observation mission",
                    importance=5,
                    dates=["September 2, 2023"],
                    figures=["1.5 million km from Earth"]
                ),
                KeyPoint(
                    text="The spacecraft will be placed at the L1 Lagrange point",
                    importance=4,
                    related_facts=["L1 point allows continuous observation of the Sun"]
                )
            ],
            upsc_relevance=UPSCRelevance(
                subject=SubjectCategory.SCIENCE_TECH,
                exam_relevance=ExamRelevance.BOTH,
                syllabus_topic="Space Technology",
                mains_paper="GS3",
                important_for=["UPSC CSE", "ISRO"]
            ),
            important_terms={
                "L1 Lagrange Point": "A gravitationally stable point between Earth and Sun",
                "Corona": "The outermost layer of the Sun's atmosphere",
                "Solar Wind": "Stream of charged particles from the Sun"
            },
            practice_questions=[
                "Discuss the significance of Aditya-L1 mission for India's space program.",
                "What are Lagrange points? Explain their importance in space missions."
            ],
            related_topics=["ISRO Missions", "Space Technology", "Chandrayaan-3"],
            timestamp="5:30"
        )

        test_note = StudyNote(
            title="Daily Current Affairs",
            date="September 2, 2023",
            topics=[test_topic],
            video_duration=1500.0  # 25 minutes
        )

        try:
            generator = PDFNotesGenerator()
            pdf_path = generator.generate_notes(test_note)
            print(f"\nSuccess! PDF generated: {pdf_path}")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
