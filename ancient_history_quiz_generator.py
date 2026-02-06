# Ancient History Quiz Generator - 500 Unique Questions
# Generates a PDF with multiple choice questions on Ancient History

from fpdf import FPDF
import os

class QuizPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Ancient History Mock Test - 500 Questions', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def add_question(self, q_num, question, options, answer):
        self.set_font('Arial', 'B', 10)
        # Handle encoding issues
        question = question.encode('latin-1', 'replace').decode('latin-1')
        self.multi_cell(0, 6, f"Q{q_num}. {question}")

        self.set_font('Arial', '', 9)
        for i, opt in enumerate(options):
            opt = opt.encode('latin-1', 'replace').decode('latin-1')
            self.cell(0, 5, f"    {chr(65+i)}) {opt}", 0, 1)

        self.ln(3)


# 500 Ancient History Questions
QUESTIONS = [
    # INDUS VALLEY CIVILIZATION (1-50)
    {
        "question": "The Indus Valley Civilization belonged to which age?",
        "options": ["Neolithic Age", "Paleolithic Age", "Chalcolithic Age", "Iron Age"],
        "answer": "C"
    },
    {
        "question": "Harappa is located in which present-day country?",
        "options": ["India", "Pakistan", "Afghanistan", "Bangladesh"],
        "answer": "B"
    },
    {
        "question": "Who discovered the Harappan civilization in 1921?",
        "options": ["John Marshall", "Daya Ram Sahni", "R.D. Banerjee", "Mortimer Wheeler"],
        "answer": "B"
    },
    {
        "question": "Mohenjo-daro is located on the banks of which river?",
        "options": ["Ravi", "Indus", "Chenab", "Sutlej"],
        "answer": "B"
    },
    {
        "question": "The Great Bath was discovered at which site?",
        "options": ["Harappa", "Mohenjo-daro", "Lothal", "Kalibangan"],
        "answer": "B"
    },
    {
        "question": "Which Indus Valley site is known for its dockyard?",
        "options": ["Harappa", "Mohenjo-daro", "Lothal", "Dholavira"],
        "answer": "C"
    },
    {
        "question": "The script of Indus Valley Civilization was:",
        "options": ["Deciphered", "Pictographic", "Boustrophedon", "All of these"],
        "answer": "D"
    },
    {
        "question": "Which animal was not known to Indus Valley people?",
        "options": ["Bull", "Horse", "Elephant", "Giraffe"],
        "answer": "D"
    },
    {
        "question": "The main occupation of Indus Valley people was:",
        "options": ["Agriculture", "Trade", "Hunting", "Both A and B"],
        "answer": "D"
    },
    {
        "question": "Which metal was not known to Indus Valley Civilization?",
        "options": ["Copper", "Bronze", "Iron", "Gold"],
        "answer": "C"
    },
    {
        "question": "The Indus Valley Civilization flourished during:",
        "options": ["5000-3500 BCE", "3500-2500 BCE", "2500-1750 BCE", "1500-500 BCE"],
        "answer": "C"
    },
    {
        "question": "Which site has the evidence of fire altars?",
        "options": ["Lothal", "Kalibangan", "Mohenjo-daro", "Harappa"],
        "answer": "B"
    },
    {
        "question": "The dancing girl statue was found at:",
        "options": ["Harappa", "Mohenjo-daro", "Chanhudaro", "Lothal"],
        "answer": "B"
    },
    {
        "question": "Dholavira is located in which Indian state?",
        "options": ["Rajasthan", "Gujarat", "Punjab", "Haryana"],
        "answer": "B"
    },
    {
        "question": "The Indus Valley people worshipped:",
        "options": ["Vishnu", "Mother Goddess", "Brahma", "Shiva only"],
        "answer": "B"
    },
    {
        "question": "Which Indus site shows evidence of horse remains?",
        "options": ["Harappa", "Surkotada", "Lothal", "Mohenjo-daro"],
        "answer": "B"
    },
    {
        "question": "The weight and measures of Indus Valley were:",
        "options": ["Decimal", "Binary", "Hexadecimal", "Irregular"],
        "answer": "B"
    },
    {
        "question": "The main crops of Indus Valley Civilization were:",
        "options": ["Wheat and Barley", "Rice and Maize", "Cotton and Sugarcane", "Tea and Coffee"],
        "answer": "A"
    },
    {
        "question": "Evidence of rice cultivation in Indus Valley was found at:",
        "options": ["Harappa", "Lothal", "Rangpur", "Kalibangan"],
        "answer": "C"
    },
    {
        "question": "The Priest King statue was found at:",
        "options": ["Harappa", "Mohenjo-daro", "Lothal", "Dholavira"],
        "answer": "B"
    },
    {
        "question": "Which site is known as the 'Manchester of Indus Valley'?",
        "options": ["Harappa", "Mohenjo-daro", "Lothal", "Surkotada"],
        "answer": "C"
    },
    {
        "question": "The granary of Harappa was discovered by:",
        "options": ["John Marshall", "Mortimer Wheeler", "R.D. Banerjee", "Daya Ram Sahni"],
        "answer": "B"
    },
    {
        "question": "Mohenjo-daro means:",
        "options": ["Mound of Living", "Mound of Dead", "Mound of Treasure", "Mound of Kings"],
        "answer": "B"
    },
    {
        "question": "Which Indus site shows evidence of ploughed field?",
        "options": ["Harappa", "Kalibangan", "Lothal", "Banawali"],
        "answer": "B"
    },
    {
        "question": "The seals of Indus Valley were made of:",
        "options": ["Terracotta", "Steatite", "Bronze", "Copper"],
        "answer": "B"
    },
    {
        "question": "The most common motif on Indus seals was:",
        "options": ["Elephant", "Unicorn Bull", "Tiger", "Rhino"],
        "answer": "B"
    },
    {
        "question": "Which site has evidence of earthquake destruction?",
        "options": ["Harappa", "Mohenjo-daro", "Kalibangan", "Lothal"],
        "answer": "C"
    },
    {
        "question": "The Indus Valley drainage system was:",
        "options": ["Open", "Covered", "Mixed", "Non-existent"],
        "answer": "B"
    },
    {
        "question": "Chanhudaro is famous for:",
        "options": ["Great Bath", "Dockyard", "Bead-making factory", "Fire altars"],
        "answer": "C"
    },
    {
        "question": "The only Indus site with an artificial brick dockyard:",
        "options": ["Harappa", "Mohenjo-daro", "Lothal", "Dholavira"],
        "answer": "C"
    },
    {
        "question": "Which Indus site is in Rajasthan?",
        "options": ["Lothal", "Kalibangan", "Dholavira", "Surkotada"],
        "answer": "B"
    },
    {
        "question": "The cemetery H culture belongs to:",
        "options": ["Early Harappan", "Mature Harappan", "Late Harappan", "Pre-Harappan"],
        "answer": "C"
    },
    {
        "question": "Which site shows evidence of cotton cultivation?",
        "options": ["Harappa", "Mohenjo-daro", "Mehrgarh", "Lothal"],
        "answer": "C"
    },
    {
        "question": "The town planning of Indus Valley was based on:",
        "options": ["Circular pattern", "Grid pattern", "Random pattern", "Radial pattern"],
        "answer": "B"
    },
    {
        "question": "Banawali is located in which state?",
        "options": ["Punjab", "Haryana", "Rajasthan", "Gujarat"],
        "answer": "B"
    },
    {
        "question": "The decline of Indus Valley Civilization was due to:",
        "options": ["Aryan invasion", "Floods", "Climate change", "All theories proposed"],
        "answer": "D"
    },
    {
        "question": "Which site has the largest geographical area?",
        "options": ["Harappa", "Mohenjo-daro", "Rakhigarhi", "Dholavira"],
        "answer": "C"
    },
    {
        "question": "Evidence of surgery in Indus Valley was found at:",
        "options": ["Harappa", "Kalibangan", "Lothal", "Mohenjo-daro"],
        "answer": "B"
    },
    {
        "question": "The standard Harappan brick ratio was:",
        "options": ["1:2:3", "1:2:4", "1:3:5", "1:4:6"],
        "answer": "B"
    },
    {
        "question": "Which site shows evidence of a stadium?",
        "options": ["Harappa", "Mohenjo-daro", "Dholavira", "Lothal"],
        "answer": "C"
    },
    {
        "question": "The Indus script has approximately how many signs?",
        "options": ["200", "300", "400", "500"],
        "answer": "C"
    },
    {
        "question": "Mehrgarh is considered:",
        "options": ["Contemporary of IVC", "Predecessor of IVC", "Successor of IVC", "Unrelated to IVC"],
        "answer": "B"
    },
    {
        "question": "Which burial practice was common in Indus Valley?",
        "options": ["Cremation only", "Extended burial", "Pot burial only", "All types"],
        "answer": "D"
    },
    {
        "question": "The toy cart was found at:",
        "options": ["Harappa", "Mohenjo-daro", "Banawali", "Lothal"],
        "answer": "C"
    },
    {
        "question": "Evidence of ivory scale was found at:",
        "options": ["Harappa", "Lothal", "Mohenjo-daro", "Kalibangan"],
        "answer": "B"
    },
    {
        "question": "Which site is known for its water reservoir system?",
        "options": ["Harappa", "Mohenjo-daro", "Dholavira", "Lothal"],
        "answer": "C"
    },
    {
        "question": "The Pashupati seal was found at:",
        "options": ["Harappa", "Mohenjo-daro", "Lothal", "Kalibangan"],
        "answer": "B"
    },
    {
        "question": "Sutkagendor was a trading post with:",
        "options": ["Egypt", "Mesopotamia", "China", "Greece"],
        "answer": "B"
    },
    {
        "question": "The worship of fire in IVC is evidenced at:",
        "options": ["Harappa and Mohenjo-daro", "Kalibangan and Lothal", "Dholavira and Surkotada", "Banawali and Rakhigarhi"],
        "answer": "B"
    },
    {
        "question": "Which IVC site shows three phases of town planning?",
        "options": ["Harappa", "Mohenjo-daro", "Dholavira", "Lothal"],
        "answer": "C"
    },

    # VEDIC AGE (51-100)
    {
        "question": "The Rig Veda contains how many hymns?",
        "options": ["1000", "1028", "1050", "1100"],
        "answer": "B"
    },
    {
        "question": "The term 'Arya' means:",
        "options": ["Superior race", "Noble", "Warrior", "Farmer"],
        "answer": "B"
    },
    {
        "question": "The battle of Ten Kings was fought on which river?",
        "options": ["Ganga", "Yamuna", "Ravi", "Indus"],
        "answer": "C"
    },
    {
        "question": "Which river is most mentioned in Rig Veda?",
        "options": ["Ganga", "Saraswati", "Indus", "Yamuna"],
        "answer": "C"
    },
    {
        "question": "The Gayatri Mantra is found in which Veda?",
        "options": ["Rig Veda", "Sama Veda", "Yajur Veda", "Atharva Veda"],
        "answer": "A"
    },
    {
        "question": "Sabha and Samiti were:",
        "options": ["Rivers", "Mountains", "Assemblies", "Tribes"],
        "answer": "C"
    },
    {
        "question": "The term 'Gotra' originated in which period?",
        "options": ["Pre-Vedic", "Early Vedic", "Later Vedic", "Post-Vedic"],
        "answer": "C"
    },
    {
        "question": "Which Veda is known as 'Book of Melodies'?",
        "options": ["Rig Veda", "Sama Veda", "Yajur Veda", "Atharva Veda"],
        "answer": "B"
    },
    {
        "question": "The concept of Varna first appeared in:",
        "options": ["Rig Veda", "Sama Veda", "Yajur Veda", "Atharva Veda"],
        "answer": "A"
    },
    {
        "question": "Purusha Sukta is found in:",
        "options": ["Mandala IX of Rig Veda", "Mandala X of Rig Veda", "Sama Veda", "Yajur Veda"],
        "answer": "B"
    },
    {
        "question": "The early Vedic society was:",
        "options": ["Matriarchal", "Patriarchal", "Egalitarian", "Feudal"],
        "answer": "B"
    },
    {
        "question": "Which was the most important deity in Rig Vedic period?",
        "options": ["Vishnu", "Shiva", "Indra", "Brahma"],
        "answer": "C"
    },
    {
        "question": "The term 'Aghanya' in Rig Veda refers to:",
        "options": ["Horse", "Cow", "Elephant", "Goat"],
        "answer": "B"
    },
    {
        "question": "The Upanishads deal mainly with:",
        "options": ["Rituals", "Philosophy", "Grammar", "Astronomy"],
        "answer": "B"
    },
    {
        "question": "How many Upanishads are considered principal?",
        "options": ["8", "10", "12", "108"],
        "answer": "D"
    },
    {
        "question": "The word 'Upanishad' means:",
        "options": ["To sit near", "Sacred text", "Divine knowledge", "Hidden truth"],
        "answer": "A"
    },
    {
        "question": "Brahmanas are texts related to:",
        "options": ["Philosophy", "Rituals", "Grammar", "Medicine"],
        "answer": "B"
    },
    {
        "question": "The Aranyakas are also known as:",
        "options": ["Village texts", "Forest texts", "Urban texts", "Mountain texts"],
        "answer": "B"
    },
    {
        "question": "The Later Vedic period saw the rise of:",
        "options": ["Tribal republics", "Mahajanapadas", "Kingdoms", "Empires"],
        "answer": "C"
    },
    {
        "question": "Iron was known as:",
        "options": ["Ayas", "Shyama Ayas", "Tamra", "Loha"],
        "answer": "B"
    },
    {
        "question": "The Ashvamedha was a:",
        "options": ["Marriage ceremony", "Horse sacrifice", "Coronation", "Death ritual"],
        "answer": "B"
    },
    {
        "question": "The Rajasuya was performed for:",
        "options": ["Conquering territories", "Coronation", "Birth of son", "Death of king"],
        "answer": "B"
    },
    {
        "question": "The Vajapeya sacrifice was for:",
        "options": ["Strength and power", "Long life", "Sons", "Wealth"],
        "answer": "A"
    },
    {
        "question": "Which animal was domesticated first by Aryans?",
        "options": ["Cow", "Horse", "Dog", "Sheep"],
        "answer": "B"
    },
    {
        "question": "The main occupation of Later Vedic people was:",
        "options": ["Pastoralism", "Agriculture", "Trade", "Warfare"],
        "answer": "B"
    },
    {
        "question": "The term 'Jana' in Vedic texts refers to:",
        "options": ["King", "Priest", "People/Tribe", "Warrior"],
        "answer": "C"
    },
    {
        "question": "Panchajana in Vedic literature refers to:",
        "options": ["Five elements", "Five tribes", "Five rivers", "Five gods"],
        "answer": "B"
    },
    {
        "question": "The Bharata tribe was associated with:",
        "options": ["Saraswati region", "Ganga valley", "Deccan", "Northwest"],
        "answer": "A"
    },
    {
        "question": "The Vedic god Varuna was associated with:",
        "options": ["War", "Rain", "Cosmic order (Rita)", "Fire"],
        "answer": "C"
    },
    {
        "question": "Agni in Vedic religion was the god of:",
        "options": ["Water", "Wind", "Fire", "Earth"],
        "answer": "C"
    },
    {
        "question": "The concept of 'Rita' represents:",
        "options": ["Truth", "Cosmic order", "Sacrifice", "Both A and B"],
        "answer": "D"
    },
    {
        "question": "The Vedic term 'Vis' denotes:",
        "options": ["King", "Priest", "Common people", "Warriors"],
        "answer": "C"
    },
    {
        "question": "Soma was:",
        "options": ["A god", "A ritual drink", "A sacrifice", "Both A and B"],
        "answer": "D"
    },
    {
        "question": "The Dasharajna (Battle of Ten Kings) is mentioned in:",
        "options": ["Mandala III", "Mandala VII", "Mandala X", "Sama Veda"],
        "answer": "B"
    },
    {
        "question": "The Later Vedic period saw decline of which god?",
        "options": ["Vishnu", "Brahma", "Indra", "Shiva"],
        "answer": "C"
    },
    {
        "question": "Prajapati rose to prominence in:",
        "options": ["Rig Vedic period", "Later Vedic period", "Epic period", "Gupta period"],
        "answer": "B"
    },
    {
        "question": "The term 'Rashtra' for territory appears in:",
        "options": ["Rig Veda", "Later Vedic texts", "Epics", "Puranas"],
        "answer": "B"
    },
    {
        "question": "Women in Early Vedic society could:",
        "options": ["Attend assemblies", "Receive education", "Choose husbands", "All of these"],
        "answer": "D"
    },
    {
        "question": "The status of women declined in:",
        "options": ["Early Vedic period", "Later Vedic period", "Mauryan period", "Gupta period"],
        "answer": "B"
    },
    {
        "question": "The concept of four Ashramas appeared in:",
        "options": ["Rig Veda", "Later Vedic literature", "Epics", "Smritis"],
        "answer": "B"
    },
    {
        "question": "Grihastha Ashrama refers to:",
        "options": ["Student life", "Householder life", "Forest dweller", "Renunciate"],
        "answer": "B"
    },
    {
        "question": "Vanaprastha means:",
        "options": ["Student", "Householder", "Forest dweller", "Ascetic"],
        "answer": "C"
    },
    {
        "question": "The Vedangas are:",
        "options": ["4", "5", "6", "8"],
        "answer": "C"
    },
    {
        "question": "Nirukta deals with:",
        "options": ["Grammar", "Etymology", "Phonetics", "Metrics"],
        "answer": "B"
    },
    {
        "question": "Shiksha deals with:",
        "options": ["Grammar", "Etymology", "Phonetics", "Metrics"],
        "answer": "C"
    },
    {
        "question": "Chandas deals with:",
        "options": ["Grammar", "Etymology", "Phonetics", "Metrics"],
        "answer": "D"
    },
    {
        "question": "Kalpa deals with:",
        "options": ["Rituals", "Grammar", "Astronomy", "Phonetics"],
        "answer": "A"
    },
    {
        "question": "Jyotisha in Vedangas deals with:",
        "options": ["Grammar", "Astronomy", "Rituals", "Etymology"],
        "answer": "B"
    },
    {
        "question": "Vyakarana deals with:",
        "options": ["Grammar", "Etymology", "Phonetics", "Rituals"],
        "answer": "A"
    },
    {
        "question": "The Rig Veda has how many Mandalas?",
        "options": ["8", "9", "10", "12"],
        "answer": "C"
    },

    # MAHAJANAPADAS AND RISE OF BUDDHISM/JAINISM (101-175)
    {
        "question": "How many Mahajanapadas are mentioned in Buddhist texts?",
        "options": ["12", "14", "16", "18"],
        "answer": "C"
    },
    {
        "question": "Which was the most powerful Mahajanapada?",
        "options": ["Kashi", "Kosala", "Magadha", "Vajji"],
        "answer": "C"
    },
    {
        "question": "The capital of Magadha was initially at:",
        "options": ["Pataliputra", "Rajgir", "Vaishali", "Champa"],
        "answer": "B"
    },
    {
        "question": "Vajji was a:",
        "options": ["Monarchy", "Oligarchy", "Republic", "Theocracy"],
        "answer": "C"
    },
    {
        "question": "The capital of Vajji was:",
        "options": ["Rajgir", "Vaishali", "Champa", "Kaushambi"],
        "answer": "B"
    },
    {
        "question": "Avanti had its capital at:",
        "options": ["Ujjain", "Mathura", "Taxila", "Rajgir"],
        "answer": "A"
    },
    {
        "question": "Gandhara had its capital at:",
        "options": ["Mathura", "Taxila", "Ujjain", "Indraprastha"],
        "answer": "B"
    },
    {
        "question": "Buddha was born in:",
        "options": ["563 BCE", "540 BCE", "527 BCE", "487 BCE"],
        "answer": "A"
    },
    {
        "question": "Buddha's birthplace was:",
        "options": ["Bodh Gaya", "Lumbini", "Sarnath", "Kushinagar"],
        "answer": "B"
    },
    {
        "question": "Buddha belonged to which clan?",
        "options": ["Maurya", "Shakya", "Licchavi", "Nanda"],
        "answer": "B"
    },
    {
        "question": "Buddha attained enlightenment at:",
        "options": ["Lumbini", "Bodh Gaya", "Sarnath", "Kushinagar"],
        "answer": "B"
    },
    {
        "question": "Buddha's first sermon was at:",
        "options": ["Lumbini", "Bodh Gaya", "Sarnath", "Rajgir"],
        "answer": "C"
    },
    {
        "question": "Buddha's first sermon is called:",
        "options": ["Mahaparinirvana", "Dhammachakka Pravartana", "Triratna", "Sangha"],
        "answer": "B"
    },
    {
        "question": "Buddha passed away at:",
        "options": ["Bodh Gaya", "Sarnath", "Kushinagar", "Vaishali"],
        "answer": "C"
    },
    {
        "question": "The Four Noble Truths deal with:",
        "options": ["Suffering", "Salvation", "Both A and B", "Neither"],
        "answer": "C"
    },
    {
        "question": "The Eightfold Path is also called:",
        "options": ["Madhyama Marga", "Dharma Marga", "Moksha Marga", "Bhakti Marga"],
        "answer": "A"
    },
    {
        "question": "Triratna in Buddhism includes:",
        "options": ["Buddha, Dharma, Sangha", "Karma, Moksha, Nirvana", "Satya, Ahimsa, Asteya", "Jnana, Karma, Bhakti"],
        "answer": "A"
    },
    {
        "question": "The first Buddhist council was held at:",
        "options": ["Vaishali", "Rajgir", "Pataliputra", "Kashmir"],
        "answer": "B"
    },
    {
        "question": "The first Buddhist council was held during reign of:",
        "options": ["Bimbisara", "Ajatashatru", "Ashoka", "Kanishka"],
        "answer": "B"
    },
    {
        "question": "The second Buddhist council was at:",
        "options": ["Rajgir", "Vaishali", "Pataliputra", "Kashmir"],
        "answer": "B"
    },
    {
        "question": "Buddhism split into Hinayana and Mahayana at:",
        "options": ["First council", "Second council", "Third council", "Fourth council"],
        "answer": "D"
    },
    {
        "question": "The third Buddhist council was held by:",
        "options": ["Ajatashatru", "Ashoka", "Kanishka", "Harsha"],
        "answer": "B"
    },
    {
        "question": "The fourth Buddhist council was held at:",
        "options": ["Rajgir", "Vaishali", "Pataliputra", "Kashmir"],
        "answer": "D"
    },
    {
        "question": "The fourth Buddhist council was patronized by:",
        "options": ["Ashoka", "Kanishka", "Harsha", "Menander"],
        "answer": "B"
    },
    {
        "question": "Mahavira was the founder of:",
        "options": ["Buddhism", "Jainism", "Ajivika sect", "Hinduism"],
        "answer": "B"
    },
    {
        "question": "Mahavira was born at:",
        "options": ["Lumbini", "Kundagrama", "Vaishali", "Pataliputra"],
        "answer": "B"
    },
    {
        "question": "Mahavira was the Tirthankara number:",
        "options": ["22nd", "23rd", "24th", "25th"],
        "answer": "C"
    },
    {
        "question": "The first Tirthankara was:",
        "options": ["Parsvanath", "Rishabhadeva", "Mahavira", "Neminatha"],
        "answer": "B"
    },
    {
        "question": "The 23rd Tirthankara was:",
        "options": ["Rishabhadeva", "Parsvanath", "Mahavira", "Neminatha"],
        "answer": "B"
    },
    {
        "question": "The symbol of Mahavira is:",
        "options": ["Bull", "Elephant", "Lion", "Horse"],
        "answer": "C"
    },
    {
        "question": "Jainism split into two sects during reign of:",
        "options": ["Bimbisara", "Chandragupta Maurya", "Ashoka", "Kanishka"],
        "answer": "B"
    },
    {
        "question": "Digambara means:",
        "options": ["White clad", "Sky clad", "Red clad", "No cloth"],
        "answer": "B"
    },
    {
        "question": "Svetambara means:",
        "options": ["White clad", "Sky clad", "Red clad", "Yellow clad"],
        "answer": "A"
    },
    {
        "question": "The Triratna of Jainism includes:",
        "options": ["Right faith, knowledge, conduct", "Buddha, Dharma, Sangha", "Satya, Ahimsa, Brahmacharya", "Jnana, Karma, Bhakti"],
        "answer": "A"
    },
    {
        "question": "Anekantavada is a Jain philosophy of:",
        "options": ["Non-violence", "Many-sidedness", "Non-attachment", "Asceticism"],
        "answer": "B"
    },
    {
        "question": "Syadvada is related to:",
        "options": ["Anekantavada", "Ahimsa", "Aparigraha", "Satya"],
        "answer": "A"
    },
    {
        "question": "The sacred texts of Jainism are called:",
        "options": ["Vedas", "Tripitakas", "Agamas", "Puranas"],
        "answer": "C"
    },
    {
        "question": "Bhadrabahu led Jain migration to:",
        "options": ["Kashmir", "South India", "Central India", "East India"],
        "answer": "B"
    },
    {
        "question": "Sthulabhadra stayed back in:",
        "options": ["North India", "South India", "East India", "West India"],
        "answer": "A"
    },
    {
        "question": "The Ajivika sect was founded by:",
        "options": ["Mahavira", "Buddha", "Makkhali Gosala", "Ajita Kesakambali"],
        "answer": "C"
    },
    {
        "question": "Ajivikas believed in:",
        "options": ["Free will", "Strict determinism", "Karma", "Rebirth"],
        "answer": "B"
    },
    {
        "question": "Charvaka philosophy is also known as:",
        "options": ["Lokayata", "Ajivika", "Sankhya", "Yoga"],
        "answer": "A"
    },
    {
        "question": "Charvaka was a:",
        "options": ["Theistic philosophy", "Materialistic philosophy", "Idealistic philosophy", "Dualistic philosophy"],
        "answer": "B"
    },
    {
        "question": "Haryanka dynasty was founded by:",
        "options": ["Bimbisara", "Ajatashatru", "Udayin", "Shishunaga"],
        "answer": "A"
    },
    {
        "question": "Bimbisara was a contemporary of:",
        "options": ["Only Buddha", "Only Mahavira", "Both Buddha and Mahavira", "Neither"],
        "answer": "C"
    },
    {
        "question": "Ajatashatru killed his father:",
        "options": ["Udayin", "Bimbisara", "Shishunaga", "Mahapadma Nanda"],
        "answer": "B"
    },
    {
        "question": "The Shishunaga dynasty was founded by:",
        "options": ["Bimbisara", "Shishunaga", "Kalashoka", "Mahapadma Nanda"],
        "answer": "B"
    },
    {
        "question": "Kalashoka is associated with:",
        "options": ["First Buddhist council", "Second Buddhist council", "Third Buddhist council", "Fourth Buddhist council"],
        "answer": "B"
    },
    {
        "question": "The Nanda dynasty was founded by:",
        "options": ["Dhana Nanda", "Mahapadma Nanda", "Ugrasena", "Panduka"],
        "answer": "B"
    },
    {
        "question": "Mahapadma Nanda is described as:",
        "options": ["Kshatriya", "Ekarat", "Brahmin", "Vaishya"],
        "answer": "B"
    },
    {
        "question": "The last Nanda ruler was:",
        "options": ["Mahapadma Nanda", "Dhana Nanda", "Panduka", "Ugrasena"],
        "answer": "B"
    },
    {
        "question": "Alexander invaded India in:",
        "options": ["326 BCE", "323 BCE", "320 BCE", "317 BCE"],
        "answer": "A"
    },
    {
        "question": "Alexander defeated which Indian king at Hydaspes?",
        "options": ["Ambhi", "Porus", "Dhana Nanda", "Chandragupta"],
        "answer": "B"
    },
    {
        "question": "Battle of Hydaspes was fought on which river?",
        "options": ["Indus", "Jhelum", "Chenab", "Ravi"],
        "answer": "B"
    },
    {
        "question": "Alexander's teacher was:",
        "options": ["Plato", "Socrates", "Aristotle", "Pythagoras"],
        "answer": "C"
    },
    {
        "question": "Alexander died in:",
        "options": ["326 BCE", "323 BCE", "320 BCE", "317 BCE"],
        "answer": "B"
    },
    {
        "question": "Ambhi was the ruler of:",
        "options": ["Punjab", "Taxila", "Gandhara", "Kashmir"],
        "answer": "B"
    },
    {
        "question": "Which Mahajanapada had republican form of government?",
        "options": ["Magadha", "Kosala", "Vajji", "Avanti"],
        "answer": "C"
    },
    {
        "question": "Kashi was later absorbed by:",
        "options": ["Magadha", "Kosala", "Vajji", "Avanti"],
        "answer": "B"
    },
    {
        "question": "The capital of Kosala was:",
        "options": ["Varanasi", "Shravasti", "Kaushambi", "Mathura"],
        "answer": "B"
    },
    {
        "question": "The capital of Vatsa was:",
        "options": ["Shravasti", "Kaushambi", "Mathura", "Ujjain"],
        "answer": "B"
    },
    {
        "question": "Champa was the capital of:",
        "options": ["Magadha", "Anga", "Kosala", "Vajji"],
        "answer": "B"
    },
    {
        "question": "The Mallas had their capital at:",
        "options": ["Kushinagar", "Vaishali", "Champa", "Rajgir"],
        "answer": "A"
    },
    {
        "question": "Buddha's clan, the Shakyas, were located in:",
        "options": ["Magadha", "Kosala", "Kapilavastu", "Vaishali"],
        "answer": "C"
    },
    {
        "question": "Prasenjit was the king of:",
        "options": ["Magadha", "Kosala", "Vatsa", "Avanti"],
        "answer": "B"
    },
    {
        "question": "Udayana was the king of:",
        "options": ["Magadha", "Kosala", "Vatsa", "Avanti"],
        "answer": "C"
    },
    {
        "question": "Pradyota was the king of:",
        "options": ["Magadha", "Kosala", "Vatsa", "Avanti"],
        "answer": "D"
    },
    {
        "question": "The Buddhist text Mahavagga mentions how many great cities?",
        "options": ["4", "6", "8", "10"],
        "answer": "B"
    },
    {
        "question": "Which metal helped in clearing forests in Ganga plains?",
        "options": ["Copper", "Bronze", "Iron", "Steel"],
        "answer": "C"
    },
    {
        "question": "The earliest coins in India were:",
        "options": ["Gold coins", "Silver punch-marked coins", "Copper coins", "Bronze coins"],
        "answer": "B"
    },
    {
        "question": "The Gana-Sanghas were:",
        "options": ["Monarchies", "Republics", "Theocracies", "Oligarchies"],
        "answer": "B"
    },
    {
        "question": "Mahavira attained Kaivalya at:",
        "options": ["Pavapuri", "Kundagrama", "Vaishali", "Pataliputra"],
        "answer": "A"
    },

    # MAURYAN EMPIRE (176-250)
    {
        "question": "Chandragupta Maurya founded the Mauryan Empire in:",
        "options": ["326 BCE", "324 BCE", "321 BCE", "317 BCE"],
        "answer": "C"
    },
    {
        "question": "Chandragupta Maurya was guided by:",
        "options": ["Megasthenes", "Chanakya", "Bindusara", "Ashoka"],
        "answer": "B"
    },
    {
        "question": "Chanakya is also known as:",
        "options": ["Vishnugupta", "Kautilya", "Both A and B", "Neither"],
        "answer": "C"
    },
    {
        "question": "Arthashastra was written by:",
        "options": ["Chandragupta", "Chanakya", "Ashoka", "Megasthenes"],
        "answer": "B"
    },
    {
        "question": "Arthashastra deals with:",
        "options": ["Philosophy", "Statecraft", "Religion", "Medicine"],
        "answer": "B"
    },
    {
        "question": "Megasthenes was ambassador of:",
        "options": ["Alexander", "Seleucus Nicator", "Antigonus", "Ptolemy"],
        "answer": "B"
    },
    {
        "question": "Megasthenes wrote:",
        "options": ["Arthashastra", "Indica", "Mudrarakshasa", "Rajatarangini"],
        "answer": "B"
    },
    {
        "question": "Chandragupta defeated Seleucus Nicator in:",
        "options": ["326 BCE", "323 BCE", "305 BCE", "298 BCE"],
        "answer": "C"
    },
    {
        "question": "The treaty with Seleucus gave Chandragupta:",
        "options": ["Punjab only", "Afghanistan regions", "Central Asia", "None"],
        "answer": "B"
    },
    {
        "question": "Chandragupta embraced which religion later?",
        "options": ["Buddhism", "Jainism", "Hinduism", "Ajivika"],
        "answer": "B"
    },
    {
        "question": "Chandragupta died at:",
        "options": ["Pataliputra", "Shravanabelagola", "Ujjain", "Taxila"],
        "answer": "B"
    },
    {
        "question": "Bindusara was known as:",
        "options": ["Amitraghata", "Priyadarshi", "Devanampriya", "Piyadasi"],
        "answer": "A"
    },
    {
        "question": "Amitraghata means:",
        "options": ["Beloved of Gods", "Slayer of enemies", "Righteous king", "Wise ruler"],
        "answer": "B"
    },
    {
        "question": "Ashoka ascended throne in:",
        "options": ["273 BCE", "268 BCE", "265 BCE", "261 BCE"],
        "answer": "A"
    },
    {
        "question": "The Kalinga War was fought in:",
        "options": ["268 BCE", "265 BCE", "261 BCE", "258 BCE"],
        "answer": "C"
    },
    {
        "question": "Kalinga corresponds to modern:",
        "options": ["Bihar", "Bengal", "Odisha", "Andhra Pradesh"],
        "answer": "C"
    },
    {
        "question": "After Kalinga War, Ashoka embraced:",
        "options": ["Jainism", "Buddhism", "Hinduism", "Ajivika"],
        "answer": "B"
    },
    {
        "question": "Ashoka's Buddhist teacher was:",
        "options": ["Mahendra", "Upagupta", "Moggaliputta Tissa", "Ananda"],
        "answer": "B"
    },
    {
        "question": "Ashoka convened which Buddhist council?",
        "options": ["First", "Second", "Third", "Fourth"],
        "answer": "C"
    },
    {
        "question": "The third Buddhist council was held at:",
        "options": ["Rajgir", "Vaishali", "Pataliputra", "Kashmir"],
        "answer": "C"
    },
    {
        "question": "Ashoka sent missionaries to:",
        "options": ["Sri Lanka", "Central Asia", "Greece", "All of these"],
        "answer": "D"
    },
    {
        "question": "Who did Ashoka send to Sri Lanka?",
        "options": ["Upagupta", "Mahendra and Sanghamitra", "Moggaliputta", "Ananda"],
        "answer": "B"
    },
    {
        "question": "The Ashoka Pillar at Sarnath has:",
        "options": ["One lion", "Two lions", "Three lions", "Four lions"],
        "answer": "D"
    },
    {
        "question": "India's national emblem is from:",
        "options": ["Sanchi Stupa", "Sarnath Pillar", "Bodh Gaya", "Amaravati"],
        "answer": "B"
    },
    {
        "question": "Ashoka's edicts were written in:",
        "options": ["Sanskrit", "Prakrit", "Pali", "Greek"],
        "answer": "B"
    },
    {
        "question": "The script of most Ashokan edicts was:",
        "options": ["Kharoshthi", "Brahmi", "Greek", "Aramaic"],
        "answer": "B"
    },
    {
        "question": "Kharoshthi script was used in:",
        "options": ["Eastern India", "Northwestern India", "Southern India", "Central India"],
        "answer": "B"
    },
    {
        "question": "Ashokan edicts were deciphered by:",
        "options": ["William Jones", "James Prinsep", "Alexander Cunningham", "John Marshall"],
        "answer": "B"
    },
    {
        "question": "The year of decipherment of Brahmi was:",
        "options": ["1815", "1823", "1837", "1847"],
        "answer": "C"
    },
    {
        "question": "Ashoka's Dhamma was:",
        "options": ["Buddhism", "Jainism", "Moral code", "Hinduism"],
        "answer": "C"
    },
    {
        "question": "Dhamma Mahamattas were:",
        "options": ["Tax collectors", "Dharma officers", "Military generals", "Provincial governors"],
        "answer": "B"
    },
    {
        "question": "How many Rock Edicts of Ashoka are there?",
        "options": ["12", "14", "16", "18"],
        "answer": "B"
    },
    {
        "question": "How many Pillar Edicts of Ashoka are there?",
        "options": ["5", "7", "9", "11"],
        "answer": "B"
    },
    {
        "question": "The Kalinga Edict mentions:",
        "options": ["Ashoka's victories", "Ashoka's remorse", "Buddhist principles", "Trade relations"],
        "answer": "B"
    },
    {
        "question": "Ashoka's name appears in which edict?",
        "options": ["Rock Edict XIII", "Maski Edict", "Pillar Edict VII", "Separate Kalinga Edict"],
        "answer": "B"
    },
    {
        "question": "In most edicts Ashoka calls himself:",
        "options": ["Ashoka", "Devanampriya Priyadarshi", "Chakravartin", "Samrat"],
        "answer": "B"
    },
    {
        "question": "Devanampriya means:",
        "options": ["Beloved of Gods", "Friend of People", "Great King", "Righteous Ruler"],
        "answer": "A"
    },
    {
        "question": "Priyadarshi means:",
        "options": ["Beloved of Gods", "Of pleasing appearance", "Great conqueror", "Wise king"],
        "answer": "B"
    },
    {
        "question": "The Mauryan capital was:",
        "options": ["Rajgir", "Pataliputra", "Ujjain", "Taxila"],
        "answer": "B"
    },
    {
        "question": "The Mauryan administration was:",
        "options": ["Decentralized", "Highly centralized", "Federal", "Confederal"],
        "answer": "B"
    },
    {
        "question": "The spy system in Mauryan Empire was called:",
        "options": ["Gudhapurusha", "Mantri", "Senapati", "Amatya"],
        "answer": "A"
    },
    {
        "question": "The provincial governor was called:",
        "options": ["Amatya", "Kumara", "Mahamatra", "Rajuka"],
        "answer": "B"
    },
    {
        "question": "The district officer was called:",
        "options": ["Pradeshika", "Rajuka", "Gramani", "Sthanikadhyaksha"],
        "answer": "A"
    },
    {
        "question": "The village headman was called:",
        "options": ["Pradeshika", "Gramani", "Rajuka", "Yukta"],
        "answer": "B"
    },
    {
        "question": "Mauryan state revenue was called:",
        "options": ["Bhaga", "Bali", "Shulka", "All of these"],
        "answer": "D"
    },
    {
        "question": "Bhaga was:",
        "options": ["Land tax", "Trade tax", "Emergency tax", "Religious tax"],
        "answer": "A"
    },
    {
        "question": "The standard land tax was:",
        "options": ["1/4th", "1/6th", "1/8th", "1/10th"],
        "answer": "B"
    },
    {
        "question": "Shulka was:",
        "options": ["Land tax", "Customs duty", "Emergency tax", "Water tax"],
        "answer": "B"
    },
    {
        "question": "The Mauryan standing army was maintained by:",
        "options": ["Feudal lords", "State", "Mercenaries", "Tribal chiefs"],
        "answer": "B"
    },
    {
        "question": "Megasthenes mentions how many army boards?",
        "options": ["4", "5", "6", "7"],
        "answer": "C"
    },
    {
        "question": "The superintendent of mines was called:",
        "options": ["Sitadhyaksha", "Akaradhyaksha", "Panyadhyaksha", "Sunadhyaksha"],
        "answer": "B"
    },
    {
        "question": "Sita land was:",
        "options": ["Crown land", "Private land", "Forest land", "Temple land"],
        "answer": "A"
    },
    {
        "question": "The last Mauryan ruler was:",
        "options": ["Ashoka", "Dasharatha", "Salisuka", "Brihadratha"],
        "answer": "D"
    },
    {
        "question": "Brihadratha was killed by:",
        "options": ["Chandragupta", "Pushyamitra Shunga", "Kanishka", "Menander"],
        "answer": "B"
    },
    {
        "question": "The Mauryan Empire ended in:",
        "options": ["232 BCE", "200 BCE", "185 BCE", "150 BCE"],
        "answer": "C"
    },
    {
        "question": "Chandragupta Maurya's queen was from:",
        "options": ["Nanda family", "Seleucid family", "Licchavi clan", "Shakya clan"],
        "answer": "B"
    },
    {
        "question": "The Mudrarakshasa was written by:",
        "options": ["Kautilya", "Vishakhadatta", "Kalidasa", "Banabhatta"],
        "answer": "B"
    },
    {
        "question": "Mudrarakshasa is about:",
        "options": ["Ashoka", "Chandragupta Maurya", "Bindusara", "Samudragupta"],
        "answer": "B"
    },
    {
        "question": "The Mauryan art style shows influence of:",
        "options": ["Greek art", "Persian art", "Chinese art", "Roman art"],
        "answer": "B"
    },
    {
        "question": "The Sanchi Stupa was originally built by:",
        "options": ["Chandragupta", "Ashoka", "Kanishka", "Harsha"],
        "answer": "B"
    },
    {
        "question": "The Barabar caves were excavated by:",
        "options": ["Chandragupta", "Ashoka", "Dasharatha", "Both B and C"],
        "answer": "D"
    },
    {
        "question": "The Barabar caves were for:",
        "options": ["Buddhists", "Jains", "Ajivikas", "Hindus"],
        "answer": "C"
    },
    {
        "question": "Megasthenes described Indian society as having how many classes?",
        "options": ["4", "5", "7", "9"],
        "answer": "C"
    },
    {
        "question": "According to Megasthenes, slavery in India was:",
        "options": ["Widespread", "Non-existent", "Limited", "Unknown"],
        "answer": "B"
    },
    {
        "question": "Pataliputra was described by Megasthenes as shaped like a:",
        "options": ["Circle", "Square", "Parallelogram", "Triangle"],
        "answer": "C"
    },
    {
        "question": "The Girnar Rock Edict is in:",
        "options": ["Madhya Pradesh", "Gujarat", "Maharashtra", "Rajasthan"],
        "answer": "B"
    },
    {
        "question": "The Junagarh Rock inscription was later added to by:",
        "options": ["Kanishka", "Rudradaman", "Samudragupta", "Skandagupta"],
        "answer": "B"
    },
    {
        "question": "Ashoka adopted Buddhism after meeting:",
        "options": ["Upagupta", "Nigrodha", "Moggaliputta", "Both A and B"],
        "answer": "B"
    },
    {
        "question": "Rock Edict XIII describes:",
        "options": ["Ashoka's Dhamma", "Kalinga War", "Buddhist councils", "Foreign missions"],
        "answer": "B"
    },
    {
        "question": "The casualties in Kalinga War were:",
        "options": ["50,000", "100,000", "150,000", "200,000"],
        "answer": "C"
    },

    # POST-MAURYAN PERIOD (251-325)
    {
        "question": "The Shunga dynasty was founded by:",
        "options": ["Agnimitra", "Pushyamitra", "Vasumitra", "Devabhuti"],
        "answer": "B"
    },
    {
        "question": "Pushyamitra Shunga was a:",
        "options": ["Kshatriya", "Brahmin", "Vaishya", "Shudra"],
        "answer": "B"
    },
    {
        "question": "The Shungas patronized:",
        "options": ["Buddhism", "Jainism", "Hinduism", "Ajivika"],
        "answer": "C"
    },
    {
        "question": "Pushyamitra performed the Ashvamedha sacrifice:",
        "options": ["Once", "Twice", "Thrice", "Four times"],
        "answer": "B"
    },
    {
        "question": "The Sanchi Stupa was enlarged by:",
        "options": ["Mauryas", "Shungas", "Satavahanas", "Kushans"],
        "answer": "B"
    },
    {
        "question": "The last Shunga ruler was:",
        "options": ["Pushyamitra", "Agnimitra", "Vasumitra", "Devabhuti"],
        "answer": "D"
    },
    {
        "question": "The Kanva dynasty was founded by:",
        "options": ["Vasudeva", "Bhumimitra", "Narayana", "Susharman"],
        "answer": "A"
    },
    {
        "question": "The Satavahanas ruled in:",
        "options": ["Northern India", "Deccan", "South India", "Northwest India"],
        "answer": "B"
    },
    {
        "question": "The founder of Satavahana dynasty was:",
        "options": ["Simuka", "Satakarni I", "Gautamiputra Satakarni", "Vasishthiputra"],
        "answer": "A"
    },
    {
        "question": "The greatest Satavahana ruler was:",
        "options": ["Simuka", "Satakarni I", "Gautamiputra Satakarni", "Hala"],
        "answer": "C"
    },
    {
        "question": "Gautamiputra Satakarni defeated:",
        "options": ["Kushans", "Shakas", "Greeks", "All of these"],
        "answer": "D"
    },
    {
        "question": "The Satavahanas were also called:",
        "options": ["Andhras", "Pallavas", "Cholas", "Pandyas"],
        "answer": "A"
    },
    {
        "question": "The capital of Satavahanas was:",
        "options": ["Amaravati", "Pratishthana", "Ujjain", "Nasik"],
        "answer": "B"
    },
    {
        "question": "The official language of Satavahanas was:",
        "options": ["Sanskrit", "Prakrit", "Tamil", "Telugu"],
        "answer": "B"
    },
    {
        "question": "The Satavahanas issued coins predominantly in:",
        "options": ["Gold", "Silver", "Lead", "Copper"],
        "answer": "C"
    },
    {
        "question": "The Gathasaptashati was compiled by:",
        "options": ["Simuka", "Satakarni I", "Hala", "Gautamiputra"],
        "answer": "C"
    },
    {
        "question": "The Gathasaptashati is in which language?",
        "options": ["Sanskrit", "Prakrit", "Tamil", "Pali"],
        "answer": "B"
    },
    {
        "question": "The Nasik Prasasti mentions:",
        "options": ["Simuka", "Gautamiputra Satakarni", "Hala", "Vasishthiputra"],
        "answer": "B"
    },
    {
        "question": "The Indo-Greeks ruled in:",
        "options": ["South India", "Northwest India", "East India", "Central India"],
        "answer": "B"
    },
    {
        "question": "The most famous Indo-Greek king was:",
        "options": ["Demetrius", "Menander", "Eucratides", "Antimachus"],
        "answer": "B"
    },
    {
        "question": "Menander is known in Indian literature as:",
        "options": ["Milinda", "Minandra", "Melanthios", "Menaikos"],
        "answer": "A"
    },
    {
        "question": "The Milindapanha records conversations between Menander and:",
        "options": ["Upagupta", "Nagasena", "Ashvaghosha", "Vasumitra"],
        "answer": "B"
    },
    {
        "question": "Menander embraced:",
        "options": ["Hinduism", "Buddhism", "Jainism", "Zoroastrianism"],
        "answer": "B"
    },
    {
        "question": "The Indo-Greeks introduced:",
        "options": ["Die-struck coins", "Punch-marked coins", "Cast coins", "Paper currency"],
        "answer": "A"
    },
    {
        "question": "The Shakas originally came from:",
        "options": ["Persia", "Central Asia", "Greece", "China"],
        "answer": "B"
    },
    {
        "question": "The Shakas are also known as:",
        "options": ["Parthians", "Scythians", "Huns", "Kushans"],
        "answer": "B"
    },
    {
        "question": "The most famous Shaka ruler was:",
        "options": ["Maues", "Azes", "Rudradaman", "Nahapana"],
        "answer": "C"
    },
    {
        "question": "Rudradaman is known for:",
        "options": ["Conquests", "Junagarh inscription", "Buddhist patronage", "All of these"],
        "answer": "B"
    },
    {
        "question": "The Junagarh inscription is the first:",
        "options": ["Sanskrit inscription", "Prakrit inscription", "Brahmi inscription", "Kharoshthi inscription"],
        "answer": "A"
    },
    {
        "question": "Rudradaman repaired the:",
        "options": ["Sanchi Stupa", "Sudarshana Lake", "Great Bath", "Nalanda University"],
        "answer": "B"
    },
    {
        "question": "The Sudarshana Lake was originally built by:",
        "options": ["Chandragupta Maurya", "Ashoka", "Pushyamitra", "Menander"],
        "answer": "A"
    },
    {
        "question": "The Parthians are also called:",
        "options": ["Shakas", "Pahlavas", "Kushans", "Huns"],
        "answer": "B"
    },
    {
        "question": "The most famous Parthian ruler was:",
        "options": ["Gondophernes", "Maues", "Azes", "Spalirises"],
        "answer": "A"
    },
    {
        "question": "According to tradition, which apostle visited Gondophernes?",
        "options": ["St. Peter", "St. Paul", "St. Thomas", "St. John"],
        "answer": "C"
    },
    {
        "question": "The Kushans originally belonged to:",
        "options": ["Shakas", "Yuezhi tribe", "Huns", "Parthians"],
        "answer": "B"
    },
    {
        "question": "The founder of Kushan dynasty was:",
        "options": ["Kanishka", "Kujula Kadphises", "Vima Kadphises", "Huvishka"],
        "answer": "B"
    },
    {
        "question": "Kujula Kadphises was succeeded by:",
        "options": ["Kanishka", "Vima Kadphises", "Huvishka", "Vasudeva"],
        "answer": "B"
    },
    {
        "question": "Vima Kadphises issued coins in:",
        "options": ["Gold only", "Silver only", "Gold and Copper", "Lead"],
        "answer": "C"
    },
    {
        "question": "The greatest Kushan ruler was:",
        "options": ["Kujula", "Vima", "Kanishka", "Huvishka"],
        "answer": "C"
    },
    {
        "question": "Kanishka's capital was at:",
        "options": ["Pataliputra", "Purushapura", "Mathura", "Taxila"],
        "answer": "B"
    },
    {
        "question": "Purushapura is modern:",
        "options": ["Lahore", "Peshawar", "Kabul", "Kandahar"],
        "answer": "B"
    },
    {
        "question": "Kanishka started an era in:",
        "options": ["58 BCE", "78 CE", "320 CE", "606 CE"],
        "answer": "B"
    },
    {
        "question": "This era is known as:",
        "options": ["Vikram Era", "Shaka Era", "Gupta Era", "Harsha Era"],
        "answer": "B"
    },
    {
        "question": "Kanishka patronized:",
        "options": ["Hinayana Buddhism", "Mahayana Buddhism", "Jainism", "Hinduism"],
        "answer": "B"
    },
    {
        "question": "The fourth Buddhist council was convened by:",
        "options": ["Ashoka", "Kanishka", "Harsha", "Menander"],
        "answer": "B"
    },
    {
        "question": "The fourth Buddhist council was held at:",
        "options": ["Rajgir", "Vaishali", "Pataliputra", "Kundalvana, Kashmir"],
        "answer": "D"
    },
    {
        "question": "The fourth council was presided by:",
        "options": ["Upagupta", "Nagasena", "Vasumitra", "Ashvaghosha"],
        "answer": "C"
    },
    {
        "question": "The vice-president of fourth council was:",
        "options": ["Vasumitra", "Ashvaghosha", "Nagarjuna", "Charaka"],
        "answer": "B"
    },
    {
        "question": "Ashvaghosha wrote:",
        "options": ["Milindapanha", "Buddhacharita", "Natyashastra", "Arthashastra"],
        "answer": "B"
    },
    {
        "question": "Nagarjuna was associated with:",
        "options": ["Mahayana Buddhism", "Hinayana Buddhism", "Jainism", "Hinduism"],
        "answer": "A"
    },
    {
        "question": "Nagarjuna founded the:",
        "options": ["Yogachara school", "Madhyamika school", "Sautrantika school", "Vaibhashika school"],
        "answer": "B"
    },
    {
        "question": "Charaka was a famous:",
        "options": ["Philosopher", "Physician", "Astronomer", "Mathematician"],
        "answer": "B"
    },
    {
        "question": "Charaka Samhita is about:",
        "options": ["Surgery", "Medicine", "Astronomy", "Mathematics"],
        "answer": "B"
    },
    {
        "question": "Sushruta Samhita is about:",
        "options": ["Medicine", "Surgery", "Astronomy", "Philosophy"],
        "answer": "B"
    },
    {
        "question": "The Gandhara school of art flourished under:",
        "options": ["Mauryas", "Shungas", "Kushans", "Guptas"],
        "answer": "C"
    },
    {
        "question": "The Gandhara school shows influence of:",
        "options": ["Persian art", "Greek art", "Indian art", "Both B and C"],
        "answer": "D"
    },
    {
        "question": "The Mathura school of art used:",
        "options": ["Blue schist", "Red sandstone", "White marble", "Black basalt"],
        "answer": "B"
    },
    {
        "question": "The Amaravati school was patronized by:",
        "options": ["Kushans", "Satavahanas", "Guptas", "Pallavas"],
        "answer": "B"
    },
    {
        "question": "The Silk Route connected India with:",
        "options": ["Rome", "China", "Both A and B", "Neither"],
        "answer": "C"
    },
    {
        "question": "The Kushans promoted trade through:",
        "options": ["Land routes", "Sea routes", "Both", "Neither"],
        "answer": "C"
    },
    {
        "question": "The last Kushan ruler was:",
        "options": ["Kanishka II", "Huvishka", "Vasudeva I", "Vasudeva II"],
        "answer": "C"
    },
    {
        "question": "The Western Kshatrapas were feudatories of:",
        "options": ["Kushans", "Satavahanas", "Independent rulers", "Guptas"],
        "answer": "A"
    },
    {
        "question": "Nahapana was a ruler of:",
        "options": ["Kushans", "Western Kshatrapas", "Satavahanas", "Shakas"],
        "answer": "B"
    },
    {
        "question": "The Periplus of the Erythraean Sea describes:",
        "options": ["Land trade routes", "Sea trade", "Philosophical concepts", "Religious practices"],
        "answer": "B"
    },
    {
        "question": "The author of Periplus was:",
        "options": ["Indian", "Greek", "Roman", "Persian"],
        "answer": "B"
    },
    {
        "question": "Barygaza mentioned in Periplus is modern:",
        "options": ["Mumbai", "Bharuch", "Surat", "Daman"],
        "answer": "B"
    },

    # GUPTA EMPIRE (326-400)
    {
        "question": "The Gupta Empire was founded by:",
        "options": ["Chandragupta I", "Samudragupta", "Sri Gupta", "Ghatotkacha"],
        "answer": "C"
    },
    {
        "question": "Chandragupta I founded the Gupta Era in:",
        "options": ["319-320 CE", "335 CE", "375 CE", "415 CE"],
        "answer": "A"
    },
    {
        "question": "Chandragupta I married into which clan?",
        "options": ["Shakya", "Licchavi", "Maurya", "Nanda"],
        "answer": "B"
    },
    {
        "question": "Kumaradevi was a princess of:",
        "options": ["Vaishali", "Pataliputra", "Ujjain", "Mathura"],
        "answer": "A"
    },
    {
        "question": "Samudragupta is known as the:",
        "options": ["Indian Alexander", "Indian Napoleon", "Lord of the Earth", "Great Conqueror"],
        "answer": "B"
    },
    {
        "question": "The Allahabad Pillar inscription was composed by:",
        "options": ["Kalidasa", "Harishena", "Varahamihira", "Aryabhata"],
        "answer": "B"
    },
    {
        "question": "The Allahabad inscription is also called:",
        "options": ["Prayag Prashasti", "Gupta Prashasti", "Victory inscription", "Both A and B"],
        "answer": "A"
    },
    {
        "question": "Samudragupta performed the:",
        "options": ["Rajasuya", "Ashvamedha", "Vajapeya", "All of these"],
        "answer": "B"
    },
    {
        "question": "Samudragupta's policy towards South Indian kings was:",
        "options": ["Annexation", "Dharma vijaya", "Tribute and release", "Alliance"],
        "answer": "C"
    },
    {
        "question": "Samudragupta was also known as:",
        "options": ["Kaviraja", "Vikramaditya", "Shakari", "All of these"],
        "answer": "A"
    },
    {
        "question": "The Gupta coins show Samudragupta playing:",
        "options": ["Flute", "Veena", "Drums", "Sitar"],
        "answer": "B"
    },
    {
        "question": "Chandragupta II was also known as:",
        "options": ["Vikramaditya", "Kaviraja", "Shakari", "Both A and C"],
        "answer": "D"
    },
    {
        "question": "Chandragupta II defeated which rulers?",
        "options": ["Shakas", "Hunas", "Kushans", "Pallavas"],
        "answer": "A"
    },
    {
        "question": "After defeating Shakas, Chandragupta II got the title:",
        "options": ["Vikramaditya", "Shakari", "Simhavikrama", "Both A and B"],
        "answer": "B"
    },
    {
        "question": "The Navratnas were in the court of:",
        "options": ["Samudragupta", "Chandragupta II", "Kumaragupta", "Skandagupta"],
        "answer": "B"
    },
    {
        "question": "Kalidasa was a court poet of:",
        "options": ["Samudragupta", "Chandragupta II", "Kumaragupta", "Harsha"],
        "answer": "B"
    },
    {
        "question": "Kalidasa wrote:",
        "options": ["Shakuntala", "Meghaduta", "Raghuvamsha", "All of these"],
        "answer": "D"
    },
    {
        "question": "Fa-Hien visited India during reign of:",
        "options": ["Samudragupta", "Chandragupta II", "Kumaragupta", "Skandagupta"],
        "answer": "B"
    },
    {
        "question": "Fa-Hien was from:",
        "options": ["Japan", "China", "Korea", "Tibet"],
        "answer": "B"
    },
    {
        "question": "Fa-Hien came to India in search of:",
        "options": ["Trade", "Buddhist texts", "Hindu scriptures", "Adventure"],
        "answer": "B"
    },
    {
        "question": "The Iron Pillar at Mehrauli was erected by:",
        "options": ["Samudragupta", "Chandragupta II", "Kumaragupta", "Skandagupta"],
        "answer": "B"
    },
    {
        "question": "The Iron Pillar is famous for being:",
        "options": ["Tallest", "Rust-resistant", "Oldest", "Most decorated"],
        "answer": "B"
    },
    {
        "question": "Kumaragupta I founded:",
        "options": ["Taxila University", "Nalanda University", "Vikramashila", "Odantapuri"],
        "answer": "B"
    },
    {
        "question": "Kumaragupta I performed the:",
        "options": ["Rajasuya", "Ashvamedha", "Vajapeya", "None"],
        "answer": "B"
    },
    {
        "question": "The Huna invasion began during reign of:",
        "options": ["Chandragupta II", "Kumaragupta I", "Skandagupta", "Budhagupta"],
        "answer": "B"
    },
    {
        "question": "Skandagupta successfully repelled:",
        "options": ["Shakas", "Hunas", "Kushans", "Parthians"],
        "answer": "B"
    },
    {
        "question": "The Junagarh inscription of Skandagupta mentions:",
        "options": ["Huna defeat", "Sudarshana Lake repair", "Both A and B", "Neither"],
        "answer": "C"
    },
    {
        "question": "After Skandagupta, the Gupta Empire:",
        "options": ["Expanded", "Declined", "Remained stable", "Split"],
        "answer": "B"
    },
    {
        "question": "The Gupta period is called the:",
        "options": ["Iron Age", "Golden Age", "Silver Age", "Bronze Age"],
        "answer": "B"
    },
    {
        "question": "Aryabhata was a famous:",
        "options": ["Poet", "Mathematician", "Doctor", "Philosopher"],
        "answer": "B"
    },
    {
        "question": "Aryabhata wrote:",
        "options": ["Aryabhatiya", "Surya Siddhanta", "Pancha Siddhantika", "Brihat Samhita"],
        "answer": "A"
    },
    {
        "question": "Varahamihira wrote:",
        "options": ["Aryabhatiya", "Brihat Samhita", "Charaka Samhita", "Sushruta Samhita"],
        "answer": "B"
    },
    {
        "question": "The concept of zero was developed during:",
        "options": ["Mauryan period", "Gupta period", "Mughal period", "British period"],
        "answer": "B"
    },
    {
        "question": "The decimal system was developed during:",
        "options": ["Vedic period", "Mauryan period", "Gupta period", "Medieval period"],
        "answer": "C"
    },
    {
        "question": "The Ajanta caves were mainly created during:",
        "options": ["Mauryan period", "Shunga period", "Gupta period", "Chalukya period"],
        "answer": "C"
    },
    {
        "question": "The Ajanta paintings depict:",
        "options": ["Jataka stories", "Ramayana", "Mahabharata", "Puranas"],
        "answer": "A"
    },
    {
        "question": "The Ellora caves have temples of:",
        "options": ["Buddhism only", "Hinduism only", "Jainism only", "All three"],
        "answer": "D"
    },
    {
        "question": "The Dashavatara temple at Deogarh was built during:",
        "options": ["Mauryan period", "Gupta period", "Pallava period", "Chola period"],
        "answer": "B"
    },
    {
        "question": "The Gupta temples followed which style?",
        "options": ["Dravidian", "Nagara", "Vesara", "Indo-Islamic"],
        "answer": "B"
    },
    {
        "question": "The Bhitari Pillar inscription mentions:",
        "options": ["Samudragupta", "Chandragupta II", "Skandagupta", "Kumaragupta"],
        "answer": "C"
    },
    {
        "question": "The Gupta administration had provinces called:",
        "options": ["Bhukti", "Vishaya", "Rashtra", "Pradesh"],
        "answer": "A"
    },
    {
        "question": "The district was called:",
        "options": ["Bhukti", "Vishaya", "Rashtra", "Pradesh"],
        "answer": "B"
    },
    {
        "question": "The Gupta land grants were called:",
        "options": ["Agraharas", "Jagirs", "Zamindari", "Ryotwari"],
        "answer": "A"
    },
    {
        "question": "The land revenue during Gupta period was:",
        "options": ["1/4th", "1/6th", "1/8th", "Variable"],
        "answer": "B"
    },
    {
        "question": "The Gupta coinage was mainly in:",
        "options": ["Gold", "Silver", "Copper", "All of these"],
        "answer": "D"
    },
    {
        "question": "The Gupta gold coins were called:",
        "options": ["Dinara", "Rupaka", "Karshapana", "Nishka"],
        "answer": "A"
    },
    {
        "question": "The Gupta period saw development of:",
        "options": ["Sanskrit literature", "Temple architecture", "Science", "All of these"],
        "answer": "D"
    },
    {
        "question": "Vishnu Sharma wrote:",
        "options": ["Panchatantra", "Hitopadesha", "Jataka tales", "Kathasaritsagara"],
        "answer": "A"
    },
    {
        "question": "The Amarakosha was written by:",
        "options": ["Kalidasa", "Amarasimha", "Dhanvantari", "Varahamihira"],
        "answer": "B"
    },
    {
        "question": "Amarakosha is a work on:",
        "options": ["Grammar", "Lexicography", "Medicine", "Astronomy"],
        "answer": "B"
    },
    {
        "question": "The last great Gupta ruler was:",
        "options": ["Kumaragupta I", "Skandagupta", "Budhagupta", "Vishnugupta"],
        "answer": "B"
    },
    {
        "question": "The Later Guptas were:",
        "options": ["Descendants of Imperial Guptas", "Unrelated dynasty", "Feudatories", "Both B and C"],
        "answer": "B"
    },
    {
        "question": "The Hunas who invaded India were:",
        "options": ["Ephthalites", "Xiongnu", "Rouran", "Avars"],
        "answer": "A"
    },
    {
        "question": "Toramana was a:",
        "options": ["Gupta ruler", "Huna chief", "Vardhana ruler", "Pushyabhuti king"],
        "answer": "B"
    },
    {
        "question": "Mihirakula was the son of:",
        "options": ["Skandagupta", "Toramana", "Yashodharman", "Harsha"],
        "answer": "B"
    },
    {
        "question": "Mihirakula was defeated by:",
        "options": ["Skandagupta", "Narasimhagupta", "Yashodharman", "Both B and C"],
        "answer": "D"
    },
    {
        "question": "Yashodharman belonged to:",
        "options": ["Gupta dynasty", "Aulikara dynasty", "Vardhana dynasty", "Huna dynasty"],
        "answer": "B"
    },
    {
        "question": "The Gupta Empire completely ended around:",
        "options": ["467 CE", "500 CE", "550 CE", "600 CE"],
        "answer": "C"
    },

    # POST-GUPTA AND HARSHA (401-450)
    {
        "question": "Harsha belonged to which dynasty?",
        "options": ["Gupta", "Pushyabhuti", "Vardhana", "Both B and C"],
        "answer": "D"
    },
    {
        "question": "Harsha's capital was at:",
        "options": ["Pataliputra", "Kanauj", "Thanesar", "Both B and C"],
        "answer": "D"
    },
    {
        "question": "Harsha ascended the throne in:",
        "options": ["590 CE", "606 CE", "620 CE", "647 CE"],
        "answer": "B"
    },
    {
        "question": "Harsha united North India in:",
        "options": ["5 years", "6 years", "10 years", "15 years"],
        "answer": "B"
    },
    {
        "question": "Harsha was stopped in the south by:",
        "options": ["Pallavas", "Chalukyas", "Cholas", "Pandyas"],
        "answer": "B"
    },
    {
        "question": "The Chalukya king who defeated Harsha was:",
        "options": ["Pulakeshin I", "Pulakeshin II", "Vikramaditya I", "Vikramaditya II"],
        "answer": "B"
    },
    {
        "question": "The battle between Harsha and Pulakeshin II was on river:",
        "options": ["Ganga", "Yamuna", "Narmada", "Godavari"],
        "answer": "C"
    },
    {
        "question": "Harsha wrote plays in:",
        "options": ["Prakrit", "Sanskrit", "Pali", "Tamil"],
        "answer": "B"
    },
    {
        "question": "Harsha wrote:",
        "options": ["Nagananda", "Ratnavali", "Priyadarshika", "All of these"],
        "answer": "D"
    },
    {
        "question": "Hieun Tsang visited India during reign of:",
        "options": ["Chandragupta II", "Skandagupta", "Harsha", "Narasimhagupta"],
        "answer": "C"
    },
    {
        "question": "Hieun Tsang was from:",
        "options": ["Japan", "China", "Korea", "Tibet"],
        "answer": "B"
    },
    {
        "question": "Hieun Tsang stayed in India for:",
        "options": ["5 years", "10 years", "14 years", "20 years"],
        "answer": "C"
    },
    {
        "question": "Hieun Tsang studied at:",
        "options": ["Taxila", "Nalanda", "Vikramashila", "Odantapuri"],
        "answer": "B"
    },
    {
        "question": "Hieun Tsang's account is called:",
        "options": ["Indica", "Si-Yu-Ki", "Fa-Hien-Ki", "Records of India"],
        "answer": "B"
    },
    {
        "question": "Banabhatta was the court poet of:",
        "options": ["Chandragupta II", "Samudragupta", "Harsha", "Pulakeshin II"],
        "answer": "C"
    },
    {
        "question": "Banabhatta wrote:",
        "options": ["Harshacharita", "Kadambari", "Both A and B", "Neither"],
        "answer": "C"
    },
    {
        "question": "The Harshacharita is a:",
        "options": ["Play", "Biography", "Poetry", "Philosophical text"],
        "answer": "B"
    },
    {
        "question": "Harsha held religious assemblies at:",
        "options": ["Kanauj", "Prayag", "Thanesar", "Nalanda"],
        "answer": "B"
    },
    {
        "question": "The Prayag assembly was held every:",
        "options": ["3 years", "5 years", "6 years", "12 years"],
        "answer": "B"
    },
    {
        "question": "Harsha personally followed:",
        "options": ["Hinduism initially, then Buddhism", "Buddhism only", "Hinduism only", "Jainism"],
        "answer": "A"
    },
    {
        "question": "Harsha died in:",
        "options": ["630 CE", "640 CE", "647 CE", "650 CE"],
        "answer": "C"
    },
    {
        "question": "After Harsha's death, his empire:",
        "options": ["Continued", "Disintegrated", "Was conquered", "Expanded"],
        "answer": "B"
    },
    {
        "question": "The Maukharis ruled from:",
        "options": ["Kanauj", "Thanesar", "Pataliputra", "Ujjain"],
        "answer": "A"
    },
    {
        "question": "The Vakatakas ruled in:",
        "options": ["North India", "Deccan", "South India", "Northwest"],
        "answer": "B"
    },
    {
        "question": "The Vakatakas were contemporaries of:",
        "options": ["Mauryas", "Shungas", "Guptas", "Palas"],
        "answer": "C"
    },
    {
        "question": "The Maitrakas ruled in:",
        "options": ["Bengal", "Gujarat", "Rajasthan", "Maharashtra"],
        "answer": "B"
    },
    {
        "question": "The capital of Maitrakas was:",
        "options": ["Ujjain", "Valabhi", "Bharuch", "Anhilwara"],
        "answer": "B"
    },
    {
        "question": "Valabhi was famous for its:",
        "options": ["Temple", "University", "Port", "Fort"],
        "answer": "B"
    },
    {
        "question": "The Gauda kingdom was in:",
        "options": ["Gujarat", "Bengal", "Bihar", "Odisha"],
        "answer": "B"
    },
    {
        "question": "Shashanka was the ruler of:",
        "options": ["Kanauj", "Gauda", "Valabhi", "Thanesar"],
        "answer": "B"
    },
    {
        "question": "Shashanka was an enemy of:",
        "options": ["Pulakeshin II", "Harsha", "Narasimhagupta", "Toramana"],
        "answer": "B"
    },
    {
        "question": "Shashanka killed:",
        "options": ["Harsha", "Rajyavardhana", "Grahavarman", "Both B and C"],
        "answer": "D"
    },
    {
        "question": "Rajyavardhana was Harsha's:",
        "options": ["Father", "Brother", "Son", "Uncle"],
        "answer": "B"
    },
    {
        "question": "Rajyashri was Harsha's:",
        "options": ["Mother", "Sister", "Wife", "Daughter"],
        "answer": "B"
    },
    {
        "question": "Harsha's title was:",
        "options": ["Shiladitya", "Vikramaditya", "Samudragupta", "Chakravartin"],
        "answer": "A"
    },
    {
        "question": "The Chinese mission to Harsha's court was led by:",
        "options": ["Fa-Hien", "Hieun Tsang", "Wang Hiuen Tse", "I-Tsing"],
        "answer": "C"
    },
    {
        "question": "I-Tsing visited India:",
        "options": ["During Harsha's reign", "After Harsha's death", "During Gupta period", "During Mauryan period"],
        "answer": "B"
    },
    {
        "question": "I-Tsing studied at:",
        "options": ["Taxila", "Nalanda", "Vikramashila", "Valabhi"],
        "answer": "B"
    },
    {
        "question": "The Pallava kingdom was in:",
        "options": ["Karnataka", "Andhra Pradesh", "Tamil Nadu", "Kerala"],
        "answer": "C"
    },
    {
        "question": "The capital of Pallavas was:",
        "options": ["Madurai", "Kanchipuram", "Thanjavur", "Mahabalipuram"],
        "answer": "B"
    },
    {
        "question": "Mahabalipuram temples were built by:",
        "options": ["Mahendravarman I", "Narasimhavarman I", "Nandivarman II", "Aparajita"],
        "answer": "B"
    },
    {
        "question": "The Kailasanatha temple at Kanchipuram was built by:",
        "options": ["Pallavas", "Cholas", "Pandyas", "Chalukyas"],
        "answer": "A"
    },
    {
        "question": "The Shore Temple at Mahabalipuram was built by:",
        "options": ["Mahendravarman I", "Narasimhavarman I", "Narasimhavarman II", "Nandivarman"],
        "answer": "C"
    },
    {
        "question": "Narasimhavarman I had the title:",
        "options": ["Mahamalla", "Vatapikonda", "Both A and B", "Neither"],
        "answer": "C"
    },
    {
        "question": "Vatapikonda means:",
        "options": ["Conqueror of Vatapi", "Lord of Vatapi", "Destroyer of enemies", "Great warrior"],
        "answer": "A"
    },
    {
        "question": "Vatapi was the capital of:",
        "options": ["Pallavas", "Chalukyas", "Cholas", "Rashtrakutas"],
        "answer": "B"
    },

    # SOUTH INDIAN DYNASTIES (451-500)
    {
        "question": "The Chalukyas of Badami were founded by:",
        "options": ["Pulakeshin I", "Pulakeshin II", "Vikramaditya I", "Jayasimha"],
        "answer": "A"
    },
    {
        "question": "Badami is in modern:",
        "options": ["Tamil Nadu", "Karnataka", "Andhra Pradesh", "Maharashtra"],
        "answer": "B"
    },
    {
        "question": "Aihole is famous for:",
        "options": ["Temples", "University", "Port", "Fort"],
        "answer": "A"
    },
    {
        "question": "Aihole is called the:",
        "options": ["Cradle of Indian architecture", "City of temples", "Southern capital", "Religious center"],
        "answer": "A"
    },
    {
        "question": "The Aihole inscription was composed by:",
        "options": ["Kalidasa", "Ravikirti", "Banabhatta", "Harishena"],
        "answer": "B"
    },
    {
        "question": "The Chalukyas of Badami ended due to:",
        "options": ["Pallava invasion", "Rashtrakuta conquest", "Chola invasion", "Internal revolt"],
        "answer": "B"
    },
    {
        "question": "The Rashtrakutas were founded by:",
        "options": ["Krishna I", "Dantidurga", "Govinda III", "Amoghavarsha"],
        "answer": "B"
    },
    {
        "question": "The capital of Rashtrakutas was:",
        "options": ["Badami", "Manyakheta", "Ellora", "Aihole"],
        "answer": "B"
    },
    {
        "question": "The Kailasa temple at Ellora was built by:",
        "options": ["Dantidurga", "Krishna I", "Govinda III", "Amoghavarsha"],
        "answer": "B"
    },
    {
        "question": "The Kailasa temple is dedicated to:",
        "options": ["Vishnu", "Shiva", "Brahma", "Buddha"],
        "answer": "B"
    },
    {
        "question": "Amoghavarsha wrote:",
        "options": ["Kavirajamarga", "Pampa Bharata", "Vikramankadeva Charita", "Prithviraj Raso"],
        "answer": "A"
    },
    {
        "question": "Kavirajamarga is in which language?",
        "options": ["Sanskrit", "Kannada", "Tamil", "Telugu"],
        "answer": "B"
    },
    {
        "question": "The Rashtrakutas were succeeded by:",
        "options": ["Chalukyas of Kalyani", "Hoysalas", "Yadavas", "Kakatiyas"],
        "answer": "A"
    },
    {
        "question": "The Chola dynasty was revived by:",
        "options": ["Vijayalaya", "Aditya I", "Parantaka I", "Rajaraja I"],
        "answer": "A"
    },
    {
        "question": "The greatest Chola ruler was:",
        "options": ["Vijayalaya", "Rajaraja I", "Rajendra I", "Kulottunga I"],
        "answer": "B"
    },
    {
        "question": "Rajaraja I built the:",
        "options": ["Shore Temple", "Kailasa Temple", "Brihadeshwara Temple", "Meenakshi Temple"],
        "answer": "C"
    },
    {
        "question": "The Brihadeshwara Temple is at:",
        "options": ["Kanchipuram", "Thanjavur", "Madurai", "Mahabalipuram"],
        "answer": "B"
    },
    {
        "question": "Rajendra I conquered up to:",
        "options": ["Ganga river", "Deccan", "Sri Lanka", "All of these"],
        "answer": "D"
    },
    {
        "question": "Rajendra I assumed the title:",
        "options": ["Gangaikonda", "Chola Martanda", "Rajakesari", "All of these"],
        "answer": "A"
    },
    {
        "question": "Gangaikondacholapuram was built by:",
        "options": ["Rajaraja I", "Rajendra I", "Kulottunga I", "Vikrama Chola"],
        "answer": "B"
    },
    {
        "question": "The Chola naval expedition to Southeast Asia was led by:",
        "options": ["Rajaraja I", "Rajendra I", "Kulottunga I", "Rajadhiraja"],
        "answer": "B"
    },
    {
        "question": "The Chola local self-government was:",
        "options": ["Centralized", "Village assemblies", "Feudal", "Military"],
        "answer": "B"
    },
    {
        "question": "The Chola village assembly was called:",
        "options": ["Sabha", "Ur", "Nagaram", "All of these"],
        "answer": "D"
    },
    {
        "question": "The Uttaramerur inscriptions describe:",
        "options": ["Temple administration", "Village administration", "Military organization", "Trade guilds"],
        "answer": "B"
    },
    {
        "question": "The Chola bronze sculptures are famous for:",
        "options": ["Nataraja", "Buddha images", "Jain Tirthankaras", "Vishnu statues"],
        "answer": "A"
    },
    {
        "question": "The Pandya capital was at:",
        "options": ["Kanchipuram", "Thanjavur", "Madurai", "Uraiyur"],
        "answer": "C"
    },
    {
        "question": "The Pandyas were famous for:",
        "options": ["Temples", "Pearls", "Spices", "All of these"],
        "answer": "D"
    },
    {
        "question": "Marco Polo visited the:",
        "options": ["Chola kingdom", "Pandya kingdom", "Pallava kingdom", "Chalukya kingdom"],
        "answer": "B"
    },
    {
        "question": "The Sangam literature belongs to:",
        "options": ["Tamil", "Telugu", "Kannada", "Malayalam"],
        "answer": "A"
    },
    {
        "question": "The Sangam Age is dated to:",
        "options": ["300 BCE - 300 CE", "500 BCE - 500 CE", "100 BCE - 100 CE", "400 CE - 600 CE"],
        "answer": "A"
    },
    {
        "question": "The three Sangam academies were held at:",
        "options": ["Madurai", "Kapatapuram", "Madurai again", "All of these"],
        "answer": "D"
    },
    {
        "question": "Silappadikaram was written by:",
        "options": ["Ilango Adigal", "Tiruvalluvar", "Sattanar", "Tholkappiyar"],
        "answer": "A"
    },
    {
        "question": "Manimekalai was written by:",
        "options": ["Ilango Adigal", "Sattanar", "Tiruvalluvar", "Kamban"],
        "answer": "B"
    },
    {
        "question": "Tirukkural was written by:",
        "options": ["Ilango", "Sattanar", "Tiruvalluvar", "Kamban"],
        "answer": "C"
    },
    {
        "question": "Tolkappiyam is a work on:",
        "options": ["Grammar", "Poetry", "Philosophy", "History"],
        "answer": "A"
    },
    {
        "question": "The Chera kingdom was in modern:",
        "options": ["Tamil Nadu", "Karnataka", "Kerala", "Andhra Pradesh"],
        "answer": "C"
    },
    {
        "question": "The port of Muziris was in:",
        "options": ["Chola kingdom", "Pandya kingdom", "Chera kingdom", "Pallava kingdom"],
        "answer": "C"
    },
    {
        "question": "Muziris had trade relations with:",
        "options": ["China", "Rome", "Arabia", "Both B and C"],
        "answer": "D"
    },
    {
        "question": "The Hoysalas ruled from:",
        "options": ["Halebid", "Badami", "Manyakheta", "Warangal"],
        "answer": "A"
    },
    {
        "question": "The Hoysala temples are famous for:",
        "options": ["Size", "Intricate carvings", "Height", "Paintings"],
        "answer": "B"
    },
    {
        "question": "The Chennakesava temple is at:",
        "options": ["Halebid", "Belur", "Somnathpur", "All of these"],
        "answer": "B"
    },
    {
        "question": "The Kakatiyas ruled from:",
        "options": ["Halebid", "Warangal", "Devagiri", "Dwarasamudra"],
        "answer": "B"
    },
    {
        "question": "The Kakatiya ruler Rudramadevi was a:",
        "options": ["King", "Queen", "Princess", "Minister"],
        "answer": "B"
    },
    {
        "question": "The Yadavas ruled from:",
        "options": ["Halebid", "Warangal", "Devagiri", "Dwarasamudra"],
        "answer": "C"
    },
    {
        "question": "Devagiri is modern:",
        "options": ["Aurangabad", "Daulatabad", "Both A and B", "Neither"],
        "answer": "C"
    },
    {
        "question": "The Eastern Chalukyas ruled in:",
        "options": ["Karnataka", "Andhra Pradesh", "Tamil Nadu", "Maharashtra"],
        "answer": "B"
    },
    {
        "question": "The capital of Eastern Chalukyas was:",
        "options": ["Badami", "Vengi", "Warangal", "Amaravati"],
        "answer": "B"
    },
    # Additional questions to complete 500
    {
        "question": "The Pala dynasty was founded by:",
        "options": ["Dharmapala", "Gopala", "Devapala", "Mahipala"],
        "answer": "B"
    },
    {
        "question": "The Palas ruled in:",
        "options": ["Bengal and Bihar", "Gujarat", "Rajasthan", "Maharashtra"],
        "answer": "A"
    },
    {
        "question": "The Palas were patrons of:",
        "options": ["Hinduism", "Buddhism", "Jainism", "Shaivism"],
        "answer": "B"
    },
    {
        "question": "Vikramashila University was founded by:",
        "options": ["Gopala", "Dharmapala", "Devapala", "Mahipala"],
        "answer": "B"
    },
    {
        "question": "Odantapuri University was in:",
        "options": ["Bengal", "Bihar", "Odisha", "Assam"],
        "answer": "B"
    },
    {
        "question": "The Sena dynasty succeeded the:",
        "options": ["Palas", "Pratiharas", "Rashtrakutas", "Chalukyas"],
        "answer": "A"
    },
    {
        "question": "The Senas were originally from:",
        "options": ["Bengal", "Karnataka", "Tamil Nadu", "Gujarat"],
        "answer": "B"
    },
    {
        "question": "Ballala Sena wrote:",
        "options": ["Danasagara", "Adbhutasagara", "Both A and B", "Neither"],
        "answer": "C"
    },
    {
        "question": "The Pratiharas are also called:",
        "options": ["Gurjara-Pratiharas", "Rashtrakutas", "Palas", "Chalukyas"],
        "answer": "A"
    },
    {
        "question": "The Pratiharas ruled from:",
        "options": ["Kanauj", "Pataliputra", "Thanesar", "Ujjain"],
        "answer": "A"
    },
    {
        "question": "The greatest Pratihara ruler was:",
        "options": ["Nagabhata I", "Mihira Bhoja", "Mahendrapala", "Rajyapala"],
        "answer": "B"
    },
    {
        "question": "The tripartite struggle was for control of:",
        "options": ["Pataliputra", "Kanauj", "Ujjain", "Thanesar"],
        "answer": "B"
    },
    {
        "question": "The tripartite struggle involved:",
        "options": ["Palas, Pratiharas, Rashtrakutas", "Cholas, Chalukyas, Pandyas", "Pallavas, Cheras, Cholas", "Guptas, Vakatakas, Kadambas"],
        "answer": "A"
    },
    {
        "question": "The Paramaras ruled in:",
        "options": ["Malwa", "Bengal", "Gujarat", "Rajasthan"],
        "answer": "A"
    },
    {
        "question": "Bhoja Paramara was famous for:",
        "options": ["Military conquests", "Learning and literature", "Religious reforms", "Temple building"],
        "answer": "B"
    },
    {
        "question": "The Chahamanas (Chauhans) ruled from:",
        "options": ["Ajmer", "Kanauj", "Delhi", "Lahore"],
        "answer": "A"
    },
    {
        "question": "Prithviraj III fought against:",
        "options": ["Mahmud of Ghazni", "Muhammad Ghori", "Qutbuddin Aibak", "Iltutmish"],
        "answer": "B"
    },
    {
        "question": "The first battle of Tarain was fought in:",
        "options": ["1191 CE", "1192 CE", "1194 CE", "1206 CE"],
        "answer": "A"
    },
    {
        "question": "The second battle of Tarain was in:",
        "options": ["1191 CE", "1192 CE", "1194 CE", "1206 CE"],
        "answer": "B"
    },
    {
        "question": "The Gahadavalas ruled from:",
        "options": ["Kanauj", "Varanasi", "Both A and B", "Neither"],
        "answer": "C"
    },
    {
        "question": "Jaichand Gahadavala was defeated by:",
        "options": ["Mahmud of Ghazni", "Muhammad Ghori", "Prithviraj III", "Qutbuddin Aibak"],
        "answer": "B"
    },
    {
        "question": "The battle of Chandawar was fought in:",
        "options": ["1191 CE", "1192 CE", "1194 CE", "1206 CE"],
        "answer": "C"
    },
    {
        "question": "The Solankis ruled in:",
        "options": ["Bengal", "Gujarat", "Rajasthan", "Malwa"],
        "answer": "B"
    },
    {
        "question": "The capital of Solankis was:",
        "options": ["Anhilwara", "Ujjain", "Ajmer", "Dhar"],
        "answer": "A"
    },
    {
        "question": "The Sun Temple at Modhera was built by:",
        "options": ["Paramaras", "Solankis", "Chauhans", "Pratiharas"],
        "answer": "B"
    },
    {
        "question": "Hemachandra was a scholar in the court of:",
        "options": ["Paramaras", "Solankis", "Chauhans", "Rashtrakutas"],
        "answer": "B"
    },
    {
        "question": "The Chandelas built temples at:",
        "options": ["Khajuraho", "Konark", "Bhubaneswar", "Puri"],
        "answer": "A"
    },
    {
        "question": "The Khajuraho temples were built between:",
        "options": ["7th-8th century", "9th-11th century", "12th-13th century", "14th-15th century"],
        "answer": "B"
    },
    {
        "question": "The Kalacuris ruled in:",
        "options": ["Central India", "South India", "North India", "East India"],
        "answer": "A"
    },
    {
        "question": "The Eastern Gangas ruled in:",
        "options": ["Bengal", "Odisha", "Andhra", "Karnataka"],
        "answer": "B"
    },
    {
        "question": "The Sun Temple at Konark was built by:",
        "options": ["Palas", "Eastern Gangas", "Chandelas", "Chalukyas"],
        "answer": "B"
    },
    {
        "question": "Narasimhadeva I built the:",
        "options": ["Lingaraja Temple", "Konark Temple", "Jagannath Temple", "Mukteshwar Temple"],
        "answer": "B"
    },
    {
        "question": "The Jagannath Temple at Puri was built by:",
        "options": ["Chodaganga", "Narasimhadeva", "Anantavarman", "Bhanudeva"],
        "answer": "C"
    },
    {
        "question": "The Lingaraja Temple is at:",
        "options": ["Puri", "Konark", "Bhubaneswar", "Cuttack"],
        "answer": "C"
    },
    {
        "question": "The Kadambas were the first dynasty to use:",
        "options": ["Sanskrit", "Kannada", "Tamil", "Telugu"],
        "answer": "B"
    },
    {
        "question": "The capital of Kadambas was:",
        "options": ["Vanavasi", "Badami", "Aihole", "Pattadakal"],
        "answer": "A"
    },
    {
        "question": "Mayurasharma founded the:",
        "options": ["Chalukya dynasty", "Kadamba dynasty", "Ganga dynasty", "Pallava dynasty"],
        "answer": "B"
    },
    {
        "question": "The Western Gangas ruled in:",
        "options": ["Odisha", "Karnataka", "Tamil Nadu", "Andhra"],
        "answer": "B"
    },
    {
        "question": "The Gomateshwara statue at Shravanabelagola was built by:",
        "options": ["Chalukyas", "Gangas", "Rashtrakutas", "Hoysalas"],
        "answer": "B"
    },
    {
        "question": "Chamundaraya built the Gomateshwara statue during reign of:",
        "options": ["Rashtrakutas", "Western Gangas", "Chalukyas", "Hoysalas"],
        "answer": "B"
    },
    {
        "question": "The height of Gomateshwara statue is approximately:",
        "options": ["37 feet", "47 feet", "57 feet", "67 feet"],
        "answer": "C"
    },
]

def generate_quiz_pdf():
    pdf = QuizPDF()
    pdf.add_page()

    # Title page content
    pdf.set_font('Arial', 'B', 20)
    pdf.cell(0, 20, '', 0, 1)  # Spacing
    pdf.cell(0, 15, 'ANCIENT HISTORY', 0, 1, 'C')
    pdf.cell(0, 15, 'MOCK TEST', 0, 1, 'C')
    pdf.set_font('Arial', '', 14)
    pdf.cell(0, 10, '500 Multiple Choice Questions', 0, 1, 'C')
    pdf.cell(0, 10, '', 0, 1)

    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'Topics Covered:', 0, 1, 'C')
    pdf.set_font('Arial', '', 11)
    topics = [
        '1. Indus Valley Civilization (Q1-50)',
        '2. Vedic Age (Q51-100)',
        '3. Mahajanapadas, Buddhism & Jainism (Q101-175)',
        '4. Mauryan Empire (Q176-250)',
        '5. Post-Mauryan Period (Q251-325)',
        '6. Gupta Empire (Q326-400)',
        '7. Post-Gupta & Harsha (Q401-450)',
        '8. South Indian Dynasties (Q451-500)'
    ]
    for topic in topics:
        pdf.cell(0, 7, topic, 0, 1, 'C')

    pdf.add_page()

    # Add questions
    for i, q in enumerate(QUESTIONS, 1):
        pdf.add_question(i, q["question"], q["options"], q["answer"])

        # Add page break if near bottom
        if pdf.get_y() > 250:
            pdf.add_page()

    # Save PDF
    output_path = "Ancient_History_500_Questions_No_Answers.pdf"
    pdf.output(output_path)
    print(f"PDF generated successfully: {output_path}")
    print(f"Total questions: {len(QUESTIONS)}")
    return output_path

if __name__ == "__main__":
    generate_quiz_pdf()
