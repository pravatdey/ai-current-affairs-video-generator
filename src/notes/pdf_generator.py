"""
PDF Notes Generator - Creates comprehensive study notes for UPSC/competitive exam preparation
Current Affairs Academy - Detailed PDF with 20 practice questions
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
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, ListFlowable, ListItem, HRFlowable, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

from .content_extractor import ExtractedContent, KeyPoint, UPSCRelevance
from src.utils.logger import get_logger

logger = get_logger(__name__)

ACADEMY_NAME = "Current Affairs Academy"
ACADEMY_TAGLINE = "Your Daily Dose of Knowledge | UPSC | State PSC | Banking | SSC"


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
    detailed_analysis: str = ""        # Full detailed analysis (more than video)
    background_context: str = ""       # Background/historical context
    implications: str = ""             # Implications and significance
    image_path: Optional[str] = None
    timestamp: str = ""                # Video timestamp reference


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
    Generates comprehensive PDF study notes for Current Affairs Academy.
    Features:
    - Academy branding (Current Affairs Academy logo)
    - Full detailed content beyond the video
    - Consolidated 20 practice questions section
    - UPSC relevance tags
    - Quick revision section
    """

    # Color scheme - Academy brand colors
    COLORS = {
        'academy_primary': HexColor('#0A2E5C'),    # Deep navy blue
        'academy_secondary': HexColor('#C8372D'),  # Academy red
        'academy_gold': HexColor('#D4A017'),       # Gold accent
        'primary': HexColor('#1a365d'),            # Dark blue
        'secondary': HexColor('#2c5282'),          # Medium blue
        'accent': HexColor('#ed8936'),             # Orange
        'success': HexColor('#38a169'),            # Green
        'warning': HexColor('#d69e2e'),            # Yellow
        'danger': HexColor('#e53e3e'),             # Red
        'light': HexColor('#f7fafc'),              # Light gray
        'light_blue': HexColor('#EBF4FF'),         # Light blue bg
        'dark': HexColor('#1a202c'),               # Dark gray
        'prelims': HexColor('#3182ce'),            # Blue for Prelims
        'mains': HexColor('#805ad5'),              # Purple for Mains
        'question_bg': HexColor('#FFFBEB'),        # Light yellow for questions
        'section_bg': HexColor('#F0F7FF'),         # Light blue for sections
    }

    def __init__(self, output_dir: str = "output/notes"):
        """
        Initialize PDF notes generator.

        Args:
            output_dir: Directory to save generated PDFs
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.styles = self._create_styles()
        logger.info(f"PDFNotesGenerator initialized. Output: {self.output_dir}")

    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        """Create custom paragraph styles for the PDF."""
        base_styles = getSampleStyleSheet()

        custom_styles = {
            'AcademyTitle': ParagraphStyle(
                'AcademyTitle',
                parent=base_styles['Normal'],
                fontSize=28,
                textColor=colors.white,
                spaceAfter=6,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold',
                leading=34
            ),
            'AcademyTagline': ParagraphStyle(
                'AcademyTagline',
                parent=base_styles['Normal'],
                fontSize=10,
                textColor=HexColor('#FFD700'),
                spaceAfter=4,
                alignment=TA_CENTER,
                fontName='Helvetica-Oblique'
            ),
            'MainTitle': ParagraphStyle(
                'MainTitle',
                parent=base_styles['Heading1'],
                fontSize=22,
                textColor=self.COLORS['academy_primary'],
                spaceAfter=16,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            ),
            'SubTitle': ParagraphStyle(
                'SubTitle',
                parent=base_styles['Normal'],
                fontSize=13,
                textColor=self.COLORS['secondary'],
                spaceAfter=20,
                alignment=TA_CENTER
            ),
            'TopicTitle': ParagraphStyle(
                'TopicTitle',
                parent=base_styles['Heading2'],
                fontSize=15,
                textColor=self.COLORS['academy_primary'],
                spaceBefore=18,
                spaceAfter=8,
                fontName='Helvetica-Bold',
                borderWidth=1,
                borderColor=self.COLORS['academy_primary'],
                borderPadding=6,
                backColor=self.COLORS['section_bg']
            ),
            'SectionHeader': ParagraphStyle(
                'SectionHeader',
                parent=base_styles['Heading3'],
                fontSize=11,
                textColor=self.COLORS['secondary'],
                spaceBefore=12,
                spaceAfter=6,
                fontName='Helvetica-Bold'
            ),
            'DetailedText': ParagraphStyle(
                'DetailedText',
                parent=base_styles['Normal'],
                fontSize=10,
                textColor=self.COLORS['dark'],
                spaceBefore=4,
                spaceAfter=6,
                alignment=TA_JUSTIFY,
                leading=15
            ),
            'KeyPoint': ParagraphStyle(
                'KeyPoint',
                parent=base_styles['Normal'],
                fontSize=10,
                textColor=self.COLORS['dark'],
                spaceBefore=4,
                spaceAfter=4,
                leftIndent=12,
                bulletIndent=4
            ),
            'BodyText': ParagraphStyle(
                'BodyText',
                parent=base_styles['Normal'],
                fontSize=10,
                textColor=self.COLORS['dark'],
                spaceBefore=4,
                spaceAfter=4,
                alignment=TA_JUSTIFY
            ),
            'Term': ParagraphStyle(
                'Term',
                parent=base_styles['Normal'],
                fontSize=10,
                textColor=self.COLORS['academy_primary'],
                fontName='Helvetica-Bold'
            ),
            'Definition': ParagraphStyle(
                'Definition',
                parent=base_styles['Normal'],
                fontSize=10,
                textColor=self.COLORS['dark'],
                leftIndent=14
            ),
            'Question': ParagraphStyle(
                'Question',
                parent=base_styles['Normal'],
                fontSize=10,
                textColor=self.COLORS['dark'],
                spaceBefore=8,
                spaceAfter=4,
                leftIndent=8,
                leading=15
            ),
            'QuestionNumber': ParagraphStyle(
                'QuestionNumber',
                parent=base_styles['Normal'],
                fontSize=10,
                textColor=self.COLORS['academy_secondary'],
                spaceBefore=10,
                spaceAfter=2,
                fontName='Helvetica-Bold'
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
                spaceBefore=8,
                spaceAfter=8,
                borderWidth=1,
                borderColor=self.COLORS['danger'],
                borderPadding=6,
                backColor=HexColor('#fff5f5')
            ),
            'PracticeHeader': ParagraphStyle(
                'PracticeHeader',
                parent=base_styles['Normal'],
                fontSize=18,
                textColor=colors.white,
                spaceAfter=8,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            ),
            'AnswerSpace': ParagraphStyle(
                'AnswerSpace',
                parent=base_styles['Normal'],
                fontSize=9,
                textColor=HexColor('#888888'),
                spaceBefore=2,
                spaceAfter=6,
                leftIndent=20,
                fontName='Helvetica-Oblique'
            ),
        }

        return custom_styles

    def _create_academy_logo_banner(self) -> List:
        """Create Current Affairs Academy branding banner."""
        elements = []

        # Top banner with Academy colors
        banner_data = [['', ACADEMY_NAME, '']]
        banner_table = Table(banner_data, colWidths=[1*cm, 15*cm, 1*cm])
        banner_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.COLORS['academy_primary']),
            ('TEXTCOLOR', (1, 0), (1, 0), colors.white),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (1, 0), (1, 0), 22),
            ('TOPPADDING', (0, 0), (-1, -1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ]))
        elements.append(banner_table)

        # Gold accent strip
        accent_data = [['', ACADEMY_TAGLINE, '']]
        accent_table = Table(accent_data, colWidths=[1*cm, 15*cm, 1*cm])
        accent_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.COLORS['academy_secondary']),
            ('TEXTCOLOR', (1, 0), (1, 0), HexColor('#FFD700')),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Oblique'),
            ('FONTSIZE', (1, 0), (1, 0), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(accent_table)
        elements.append(Spacer(1, 0.2*inch))

        return elements

    def generate_notes(
        self,
        study_note: StudyNote,
        include_images: bool = True,
        include_questions: bool = True
    ) -> str:
        """
        Generate comprehensive PDF study notes with Academy branding.

        Args:
            study_note: StudyNote object with all content
            include_images: Whether to include images
            include_questions: Whether to include practice questions

        Returns:
            Path to generated PDF file
        """
        date_str = datetime.now().strftime("%Y%m%d")
        safe_title = "".join(c for c in study_note.title if c.isalnum() or c in ' -_')[:50]
        filename = f"{date_str}_{safe_title.replace(' ', '_')}_CurrentAffairsAcademy.pdf"
        output_path = self.output_dir / filename

        logger.info(f"Generating PDF notes: {filename}")

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=1.5*cm,
            bottomMargin=2*cm
        )

        story = []

        # Academy Logo Banner (appears on every section start)
        story.extend(self._create_academy_logo_banner())

        # Title Page
        story.extend(self._create_title_page(study_note))

        # Table of Contents
        story.extend(self._create_toc(study_note))

        # Detailed Topic Sections
        for i, topic in enumerate(study_note.topics, 1):
            story.extend(self._create_topic_section(
                topic, i, include_images, include_questions
            ))

        # Summary Section
        story.extend(self._create_summary_section(study_note))

        # Quick Revision Section
        story.extend(self._create_quick_revision(study_note))

        # Consolidated 20 Practice Questions Section
        if include_questions:
            story.extend(self._create_consolidated_questions_section(study_note))

        # Resources Section
        if study_note.additional_resources:
            story.extend(self._create_resources_section(study_note))

        # Footer page
        story.extend(self._create_footer_page(study_note))

        try:
            doc.build(story)
            logger.info(f"PDF generated successfully: {output_path}")
            return str(output_path)
        except Exception as e:
            logger.error(f"Failed to generate PDF: {e}")
            raise

    def _create_title_page(self, study_note: StudyNote) -> List:
        """Create title page with Academy branding."""
        elements = []

        elements.append(Spacer(1, 0.3*inch))

        # Document type label
        doc_type_data = [['DAILY CURRENT AFFAIRS - COMPLETE STUDY NOTES']]
        doc_type_table = Table(doc_type_data, colWidths=[17*cm])
        doc_type_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.COLORS['academy_primary']),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 13),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(doc_type_table)
        elements.append(Spacer(1, 0.2*inch))

        # Title
        elements.append(Paragraph(study_note.title, self.styles['MainTitle']))

        # Date
        elements.append(Paragraph(
            f"Date: {study_note.date}",
            self.styles['SubTitle']
        ))

        elements.append(Spacer(1, 0.3*inch))

        # Info box
        total_questions = sum(len(t.practice_questions) for t in study_note.topics)
        guaranteed_questions = max(20, total_questions)

        info_data = [
            ['Total Topics Covered', str(len(study_note.topics))],
            ['Language', study_note.language],
            ['Practice Questions', f"{guaranteed_questions}+ MCQ & Descriptive"],
            ['Video Duration', f"{study_note.video_duration/60:.0f} min" if study_note.video_duration else "N/A"],
            ['Content Type', 'Detailed (More than Video)'],
        ]

        info_table = Table(info_data, colWidths=[7*cm, 9*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.COLORS['academy_primary']),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('TEXTCOLOR', (1, 0), (1, -1), self.COLORS['dark']),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, self.COLORS['secondary']),
            ('BACKGROUND', (1, 0), (1, -1), self.COLORS['light_blue']),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1),
             [self.COLORS['academy_primary'], self.COLORS['academy_primary']]),
        ]))
        elements.append(info_table)

        elements.append(Spacer(1, 0.3*inch))

        # What's inside note
        inside_text = """<b>What's inside this PDF:</b><br/>
✔ <b>Complete detailed coverage</b> of all current affairs topics (more than the video)<br/>
✔ <b>In-depth analysis</b> with background context and implications<br/>
✔ <b>Important Terms</b> and their definitions for exam preparation<br/>
✔ <b>UPSC Relevance</b> tags (Prelims / Mains / Both) for each topic<br/>
✔ <b>Quick Revision</b> section with all key facts<br/>
✔ <b>20+ Practice Questions</b> (MCQ + Descriptive) for self-assessment<br/>
✔ <b>Previous Year Question</b> references where applicable"""

        inside_table = Table([[Paragraph(inside_text, self.styles['BodyText'])]],
                             colWidths=[17*cm])
        inside_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.COLORS['section_bg']),
            ('BOX', (0, 0), (-1, -1), 1.5, self.COLORS['academy_primary']),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(inside_table)

        elements.append(Spacer(1, 0.2*inch))

        # Exam relevance summary
        prelims_count = sum(
            1 for t in study_note.topics
            if t.upsc_relevance and t.upsc_relevance.exam_relevance.value in ['prelims', 'both']
        )
        mains_count = sum(
            1 for t in study_note.topics
            if t.upsc_relevance and t.upsc_relevance.exam_relevance.value in ['mains', 'both']
        )

        exam_data = [
            ['Prelims Important', f"{prelims_count} topics", 'Mains Important', f"{mains_count} topics"]
        ]
        exam_table = Table(exam_data, colWidths=[4*cm, 4.5*cm, 4*cm, 4.5*cm])
        exam_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), self.COLORS['prelims']),
            ('BACKGROUND', (2, 0), (2, 0), self.COLORS['mains']),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
            ('TEXTCOLOR', (2, 0), (2, 0), colors.white),
            ('TEXTCOLOR', (1, 0), (1, 0), self.COLORS['prelims']),
            ('TEXTCOLOR', (3, 0), (3, 0), self.COLORS['mains']),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (3, 0), (3, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, self.COLORS['light']),
        ]))
        elements.append(exam_table)

        elements.append(PageBreak())
        return elements

    def _create_toc(self, study_note: StudyNote) -> List:
        """Create table of contents."""
        elements = []

        elements.extend(self._create_academy_logo_banner())

        elements.append(Paragraph(
            "TABLE OF CONTENTS",
            self.styles['TopicTitle']
        ))
        elements.append(Spacer(1, 0.2*inch))

        toc_data = [['#', 'Topic', 'Subject', 'Exam']]
        for i, topic in enumerate(study_note.topics, 1):
            subject = topic.upsc_relevance.subject.value if topic.upsc_relevance else "Current Affairs"
            exam = topic.upsc_relevance.exam_relevance.value.upper() if topic.upsc_relevance else "BOTH"
            toc_data.append([
                str(i),
                topic.title[:55] + "..." if len(topic.title) > 55 else topic.title,
                subject[:20],
                exam
            ])

        # Add special sections to TOC
        toc_data.append(['', 'Summary of Today\'s Current Affairs', '', ''])
        toc_data.append(['', 'Quick Revision - Key Facts', '', ''])
        toc_data.append(['', '20 Practice Questions', '', ''])

        if toc_data:
            toc_table = Table(toc_data, colWidths=[0.7*cm, 9*cm, 4.5*cm, 2.5*cm])
            toc_table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['academy_primary']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                # Data rows
                ('TEXTCOLOR', (0, 1), (-1, -1), self.COLORS['dark']),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (3, 0), (3, -1), 'CENTER'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
                ('TOPPADDING', (0, 0), (-1, -1), 7),
                ('LINEBELOW', (0, 0), (-1, -2), 0.5, self.COLORS['light']),
                ('BACKGROUND', (2, 1), (2, -1), self.COLORS['light']),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                 [colors.white, self.COLORS['section_bg']]),
                # Highlight special sections
                ('FONTNAME', (1, -2), (1, -1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (1, -2), (1, -1), self.COLORS['academy_secondary']),
                ('FONTNAME', (1, -3), (1, -3), 'Helvetica-Bold'),
                ('TEXTCOLOR', (1, -3), (1, -3), self.COLORS['academy_secondary']),
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
        """Create a detailed topic section."""
        elements = []

        elements.extend(self._create_academy_logo_banner())

        # Topic header
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

        elements.append(Spacer(1, 0.15*inch))

        # 1. Summary (detailed, not condensed)
        elements.append(Paragraph("<b>Overview:</b>", self.styles['SectionHeader']))
        elements.append(Paragraph(topic.summary, self.styles['DetailedText']))

        # 2. Background Context (detailed content beyond video)
        if topic.background_context:
            elements.append(Paragraph(
                "<b>Background & Context:</b>",
                self.styles['SectionHeader']
            ))
            elements.append(Paragraph(
                topic.background_context,
                self.styles['DetailedText']
            ))

        # 3. Detailed Analysis
        if topic.detailed_analysis:
            elements.append(Paragraph(
                "<b>Detailed Analysis:</b>",
                self.styles['SectionHeader']
            ))
            elements.append(Paragraph(
                topic.detailed_analysis,
                self.styles['DetailedText']
            ))

        # 4. Key Points
        if topic.key_points:
            elements.append(Paragraph(
                "<b>Key Points for Exam:</b>",
                self.styles['SectionHeader']
            ))
            elements.extend(self._create_key_points_list(topic.key_points))

        # 5. Implications & Significance
        if topic.implications:
            elements.append(Paragraph(
                "<b>Implications & Significance:</b>",
                self.styles['SectionHeader']
            ))
            elements.append(Paragraph(
                topic.implications,
                self.styles['DetailedText']
            ))

        # 6. Important Terms
        if topic.important_terms:
            elements.append(Paragraph(
                "<b>Important Terms & Definitions:</b>",
                self.styles['SectionHeader']
            ))
            elements.extend(self._create_terms_table(topic.important_terms))

        # 7. Topic-level Practice Questions (mini set)
        if include_questions and topic.practice_questions:
            elements.append(Paragraph(
                "<b>Practice Questions (This Topic):</b>",
                self.styles['SectionHeader']
            ))
            for q in topic.practice_questions[:3]:
                elements.append(Paragraph(
                    f"Q: {q}",
                    self.styles['Question']
                ))
                elements.append(Paragraph(
                    "_" * 80,
                    self.styles['AnswerSpace']
                ))

        # 8. Related Topics
        if topic.related_topics:
            elements.append(Paragraph(
                "<b>Related Topics for Further Study:</b>",
                self.styles['SectionHeader']
            ))
            related_text = " | ".join(topic.related_topics)
            elements.append(Paragraph(related_text, self.styles['BodyText']))

        elements.append(Spacer(1, 0.2*inch))
        elements.append(HRFlowable(
            width="100%",
            thickness=1.5,
            color=self.COLORS['academy_primary'],
            spaceBefore=8,
            spaceAfter=8
        ))
        elements.append(PageBreak())

        return elements

    def _create_relevance_tags(self, relevance: UPSCRelevance) -> List:
        """Create UPSC relevance tags."""
        elements = []

        tags_info = []
        tags_info.append(('Subject', relevance.subject.value, self.COLORS['academy_primary']))

        if relevance.exam_relevance.value == 'prelims':
            tags_info.append(('Exam', 'PRELIMS', self.COLORS['prelims']))
        elif relevance.exam_relevance.value == 'mains':
            tags_info.append(('Exam', 'MAINS', self.COLORS['mains']))
        else:
            tags_info.append(('Exam', 'PRELIMS + MAINS', self.COLORS['accent']))

        if relevance.mains_paper:
            tags_info.append(('Paper', relevance.mains_paper, self.COLORS['secondary']))

        tag_cells = [f"{label}: {value}" for label, value, _ in tags_info]
        tag_text = "  |  ".join(tag_cells)

        elements.append(Paragraph(
            f"<font color='#444444' size='9'><b>{tag_text}</b></font>",
            self.styles['BodyText']
        ))

        return elements

    def _create_key_points_list(self, key_points: List[KeyPoint]) -> List:
        """Create formatted list of key points."""
        elements = []

        for i, kp in enumerate(key_points, 1):
            point_text = f"<b>{i}.</b> {kp.text}"

            if kp.dates:
                point_text += f" <font color='#d69e2e'><b>[Date: {', '.join(kp.dates)}]</b></font>"

            if kp.figures:
                point_text += f" <font color='#38a169'><b>[Stats: {', '.join(kp.figures)}]</b></font>"

            elements.append(Paragraph(point_text, self.styles['KeyPoint']))

            if kp.related_facts:
                for fact in kp.related_facts:
                    elements.append(Paragraph(
                        f"    ▸ {fact}",
                        self.styles['BodyText']
                    ))

        return elements

    def _create_terms_table(self, terms: Dict[str, str]) -> List:
        """Create table of important terms."""
        elements = []

        term_data = [['Term / Concept', 'Definition / Explanation']]
        for term, definition in terms.items():
            term_data.append([term, definition])

        if len(term_data) > 1:
            term_table = Table(term_data, colWidths=[4.5*cm, 12.5*cm])
            term_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['academy_primary']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
                ('TOPPADDING', (0, 0), (-1, -1), 7),
                ('BACKGROUND', (0, 1), (0, -1), self.COLORS['section_bg']),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (0, 1), (0, -1), self.COLORS['academy_primary']),
                ('GRID', (0, 0), (-1, -1), 0.5, self.COLORS['secondary']),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ROWBACKGROUNDS', (1, 1), (-1, -1), [colors.white, self.COLORS['light']]),
            ]))
            elements.append(term_table)

        return elements

    def _create_summary_section(self, study_note: StudyNote) -> List:
        """Create overall summary section."""
        elements = []

        elements.extend(self._create_academy_logo_banner())

        elements.append(Paragraph(
            "SUMMARY - TODAY'S CURRENT AFFAIRS",
            self.styles['TopicTitle']
        ))
        elements.append(Spacer(1, 0.15*inch))

        for i, topic in enumerate(study_note.topics, 1):
            summary_text = f"<b>{i}. {topic.title}</b><br/>{topic.summary[:350]}..."
            summary_table = Table(
                [[Paragraph(summary_text, self.styles['BodyText'])]],
                colWidths=[17*cm]
            )
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), self.COLORS['light_blue'] if i % 2 == 0 else colors.white),
                ('BOX', (0, 0), (-1, -1), 0.5, self.COLORS['secondary']),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ]))
            elements.append(summary_table)
            elements.append(Spacer(1, 0.1*inch))

        elements.append(PageBreak())
        return elements

    def _create_quick_revision(self, study_note: StudyNote) -> List:
        """Create quick revision section with all key facts."""
        elements = []

        elements.extend(self._create_academy_logo_banner())

        elements.append(Paragraph(
            "QUICK REVISION - KEY FACTS",
            self.styles['TopicTitle']
        ))
        elements.append(Paragraph(
            "<i>Use this section for last-minute revision before exams</i>",
            self.styles['BodyText']
        ))
        elements.append(Spacer(1, 0.15*inch))

        fact_num = 1
        for topic in study_note.topics:
            # Topic label
            elements.append(Paragraph(
                f"<b>{topic.title}</b>",
                self.styles['SectionHeader']
            ))
            for kp in topic.key_points[:3]:  # Top 3 points per topic
                elements.append(Paragraph(
                    f"<b>{fact_num}.</b> {kp.text}",
                    self.styles['KeyPoint']
                ))
                fact_num += 1

        # Important numbers/statistics box
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph(
            "<b>Important Numbers & Statistics:</b>",
            self.styles['SectionHeader']
        ))

        figures = []
        for topic in study_note.topics:
            for kp in topic.key_points:
                figures.extend(kp.figures)

        if figures:
            figures_text = " | ".join(sorted(set(figures))[:20])
            elements.append(Paragraph(figures_text, self.styles['BodyText']))
        else:
            elements.append(Paragraph(
                "Refer to individual topic sections for statistics.",
                self.styles['BodyText']
            ))

        elements.append(PageBreak())
        return elements

    def _create_consolidated_questions_section(self, study_note: StudyNote) -> List:
        """
        Create a consolidated section with 20 practice questions
        covering all topics - MCQ and Descriptive formats.
        """
        elements = []

        elements.extend(self._create_academy_logo_banner())

        # Section header banner
        header_data = [['PRACTICE QUESTIONS SECTION']]
        header_table = Table(header_data, colWidths=[17*cm])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.COLORS['academy_secondary']),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 16),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(header_table)

        subtitle_data = [['20 Questions | MCQ + Descriptive | Self-Assessment']]
        subtitle_table = Table(subtitle_data, colWidths=[17*cm])
        subtitle_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.COLORS['academy_gold']),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.COLORS['dark']),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(subtitle_table)
        elements.append(Spacer(1, 0.2*inch))

        # Collect all questions from all topics
        all_questions = []
        for topic in study_note.topics:
            for q in topic.practice_questions:
                all_questions.append((q, topic.title))

        # Generate additional questions if we have fewer than 20
        generated_questions = self._generate_additional_questions(
            study_note, all_questions
        )
        all_questions.extend(generated_questions)

        # Ensure exactly 20 questions (or more if available)
        questions_to_show = all_questions[:20] if len(all_questions) >= 20 else all_questions

        # Part A: MCQ-style Questions (first 10)
        mcq_questions = questions_to_show[:10]
        desc_questions = questions_to_show[10:]

        # Part A Header
        part_a_data = [['PART A: Multiple Choice / Objective Questions (Q1 to Q10)']]
        part_a_table = Table(part_a_data, colWidths=[17*cm])
        part_a_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.COLORS['academy_primary']),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(part_a_table)
        elements.append(Spacer(1, 0.1*inch))

        for i, (question, topic_name) in enumerate(mcq_questions, 1):
            # Question number and topic tag
            q_header = f"Q{i}. <font color='#666666' size='8'>[{topic_name[:30]}]</font>"
            elements.append(Paragraph(q_header, self.styles['QuestionNumber']))
            elements.append(Paragraph(question, self.styles['Question']))
            elements.append(Paragraph(
                "Answer: ____________________________________________",
                self.styles['AnswerSpace']
            ))
            elements.append(Spacer(1, 0.05*inch))

        elements.append(Spacer(1, 0.2*inch))

        # Part B: Descriptive Questions (next 10)
        part_b_data = [['PART B: Descriptive / Analytical Questions (Q11 to Q20)']]
        part_b_table = Table(part_b_data, colWidths=[17*cm])
        part_b_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.COLORS['mains']),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(part_b_table)
        elements.append(Spacer(1, 0.1*inch))

        for i, (question, topic_name) in enumerate(desc_questions, 11):
            q_header = f"Q{i}. <font color='#666666' size='8'>[{topic_name[:30]}]</font>"
            elements.append(Paragraph(q_header, self.styles['QuestionNumber']))
            elements.append(Paragraph(question, self.styles['Question']))
            # Space for descriptive answer
            for _ in range(3):
                elements.append(Paragraph(
                    "_" * 95,
                    self.styles['AnswerSpace']
                ))
            elements.append(Spacer(1, 0.05*inch))

        # If we have more than 20 questions, show the extras as bonus
        bonus_questions = all_questions[20:]
        if bonus_questions:
            elements.append(Spacer(1, 0.2*inch))
            bonus_data = [[f'BONUS QUESTIONS (Q21 to Q{20 + len(bonus_questions)})']]
            bonus_table = Table(bonus_data, colWidths=[17*cm])
            bonus_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), self.COLORS['success']),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ]))
            elements.append(bonus_table)
            elements.append(Spacer(1, 0.1*inch))
            for i, (question, topic_name) in enumerate(bonus_questions, 21):
                q_header = f"Q{i}. <font color='#666666' size='8'>[{topic_name[:30]}]</font>"
                elements.append(Paragraph(q_header, self.styles['QuestionNumber']))
                elements.append(Paragraph(question, self.styles['Question']))
                elements.append(Paragraph(
                    "_" * 95,
                    self.styles['AnswerSpace']
                ))
                elements.append(Spacer(1, 0.05*inch))

        elements.append(PageBreak())
        return elements

    def _generate_additional_questions(
        self,
        study_note: StudyNote,
        existing_questions: List
    ) -> List:
        """
        Generate additional practice questions to reach 20 total.
        Creates standard UPSC-style questions based on topic titles.
        """
        needed = max(0, 20 - len(existing_questions))
        if needed == 0:
            return []

        additional = []
        date = study_note.date

        # Standard question templates for UPSC preparation
        question_templates = [
            ("Consider the following statements about {topic}:\n"
             "1. Statement A related to {topic}\n"
             "2. Statement B related to {topic}\n"
             "Which of the above statements is/are correct?\n"
             "(a) 1 only  (b) 2 only  (c) Both 1 and 2  (d) Neither 1 nor 2"),
            "Discuss the significance of {topic} in the context of India's development agenda.",
            "What are the key implications of {topic} for India's foreign policy?",
            "Examine the constitutional provisions related to {topic}.",
            "How does {topic} affect India's economic growth and development?",
            "Critically analyze the government's approach towards {topic}.",
            "What role does {topic} play in the context of sustainable development goals?",
            "Discuss the historical evolution and current status of {topic}.",
            "What are the challenges and opportunities associated with {topic}?",
            "With reference to {topic}, explain the relevant international frameworks.",
        ]

        topic_cycle = [t.title for t in study_note.topics] * (needed // len(study_note.topics) + 2)

        for i in range(needed):
            topic_name = topic_cycle[i % len(topic_cycle)]
            template = question_templates[i % len(question_templates)]
            question = template.format(topic=topic_name[:40])
            additional.append((question, topic_name))

        return additional[:needed]

    def _create_resources_section(self, study_note: StudyNote) -> List:
        """Create additional resources section."""
        elements = []

        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph(
            "Additional Resources",
            self.styles['SectionHeader']
        ))

        for resource in study_note.additional_resources:
            elements.append(Paragraph(f"• {resource}", self.styles['BodyText']))

        return elements

    def _create_footer_page(self, study_note: StudyNote) -> List:
        """Create final footer page with Academy branding."""
        elements = []

        elements.extend(self._create_academy_logo_banner())

        elements.append(Spacer(1, 0.5*inch))

        footer_content = f"""
<b>Thank you for studying with {ACADEMY_NAME}!</b><br/><br/>
This PDF covers all the current affairs from {study_note.date} in complete detail.<br/>
The video version covers key highlights — this PDF gives you the full picture.<br/><br/>
<b>Keep Learning. Keep Growing.</b><br/><br/>
{ACADEMY_TAGLINE}<br/><br/>
<font size="8" color="#888888">
Generated by Current Affairs Academy AI System | {datetime.now().strftime('%B %d, %Y')}
</font>
"""
        footer_table = Table(
            [[Paragraph(footer_content, self.styles['SubTitle'])]],
            colWidths=[17*cm]
        )
        footer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.COLORS['section_bg']),
            ('BOX', (0, 0), (-1, -1), 2, self.COLORS['academy_primary']),
            ('TOPPADDING', (0, 0), (-1, -1), 20),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
            ('LEFTPADDING', (0, 0), (-1, -1), 20),
            ('RIGHTPADDING', (0, 0), (-1, -1), 20),
        ]))
        elements.append(footer_table)

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

        topics = []
        for i, content in enumerate(extracted_contents):
            timestamp = (
                f"{(i * video_duration / len(extracted_contents) / 60):.0f}:00"
                if video_duration else ""
            )

            # Build detailed_analysis from available content
            detailed = getattr(content, 'detailed_analysis', '') or ''
            if not detailed and hasattr(content, 'article') and content.article:
                # Use article body as detailed content if available
                article_body = getattr(content.article, 'content', '') or ''
                detailed = article_body[:1500] if article_body else ''

            background = getattr(content, 'background_context', '') or ''
            implications = getattr(content, 'implications', '') or ''

            topic = TopicNote(
                title=content.article.title,
                summary=content.summary,
                key_points=content.key_points,
                upsc_relevance=content.upsc_relevance,
                important_terms=content.important_terms,
                practice_questions=content.practice_questions,
                related_topics=content.related_topics,
                detailed_analysis=detailed,
                background_context=background,
                implications=implications,
                timestamp=timestamp
            )
            topics.append(topic)

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
        print("\n=== Running Current Affairs Academy PDF Generator Test ===\n")

        from .content_extractor import KeyPoint, UPSCRelevance, SubjectCategory, ExamRelevance

        test_topic = TopicNote(
            title="India Launches New Space Mission to Study Sun",
            summary="ISRO successfully launched Aditya-L1, India's first solar observation mission. The spacecraft will study the Sun's corona and solar winds from the L1 Lagrange point, positioned 1.5 million km from Earth.",
            detailed_analysis="The Aditya-L1 mission represents a major milestone for India's space program. The spacecraft carries seven scientific payloads designed to observe the solar atmosphere, understand space weather events, and study the dynamics of the solar corona. This mission places India among the select group of nations with dedicated solar observation capabilities.",
            background_context="India's interest in solar science dates back decades. The mission was conceived by scientists at the Indian Institute of Astrophysics and developed jointly with multiple ISRO centers. The L1 Lagrange point was chosen because it allows uninterrupted observation of the Sun without eclipses or occultation.",
            implications="This mission will enhance India's capability to predict space weather events that can impact satellite communications, power grids, and GPS systems on Earth. The data from Aditya-L1 will contribute to global solar research and strengthen India's position in international space cooperation.",
            key_points=[
                KeyPoint(
                    text="Aditya-L1 is India's first dedicated solar observation mission",
                    importance=5,
                    dates=["September 2, 2023"],
                    figures=["1.5 million km from Earth", "7 scientific payloads"]
                ),
                KeyPoint(
                    text="Spacecraft placed at L1 Lagrange point for continuous Sun observation",
                    importance=4,
                    related_facts=["L1 is gravitationally stable", "No eclipse or occultation at L1"]
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
                "L1 Lagrange Point": "A gravitationally stable point between Earth and Sun, 1.5 million km from Earth",
                "Solar Corona": "The outermost layer of the Sun's atmosphere extending millions of km into space",
                "Solar Wind": "Continuous stream of charged particles (plasma) emanating from the Sun",
                "Space Weather": "Variations in the space environment between the Sun and Earth"
            },
            practice_questions=[
                "What is the primary scientific objective of the Aditya-L1 mission?",
                "Explain the significance of Lagrange points in space missions with examples.",
                "How does space weather affect modern technological systems? Discuss."
            ],
            related_topics=["ISRO Missions", "Chandrayaan-3", "Space Technology Policy", "Solar Physics"],
            timestamp="5:30"
        )

        test_note = StudyNote(
            title="Daily Current Affairs",
            date="September 2, 2023",
            topics=[test_topic],
            video_duration=1500.0
        )

        try:
            generator = PDFNotesGenerator()
            pdf_path = generator.generate_notes(test_note)
            print(f"\nSuccess! PDF generated: {pdf_path}")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
