from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.enums import TA_LEFT

styles = {
    'bullet': ParagraphStyle('bullet', fontName='Helvetica', fontSize=8, textColor=(0,0,0), leading=11, alignment=TA_LEFT, leftIndent=0, spaceBefore=0, spaceAfter=0),
}

story = []
story.append(Paragraph('<bullet bulletFontName="ZapfDingbats" bulletFontSize="7">&#110;</bullet> Test bullet point 1', styles['bullet']))
story.append(Paragraph('<bullet bulletFontName="ZapfDingbats" bulletFontSize="7">&#110;</bullet> Test bullet point 2', styles['bullet']))
story.append(Paragraph('<bullet bulletFontName="ZapfDingbats" bulletFontSize="7">&#110;</bullet> Test bullet point 3', styles['bullet']))

doc = SimpleDocTemplate('output/test_bullets.pdf', pagesize=A4, leftMargin=72, rightMargin=72, topMargin=72, bottomMargin=72)
doc.build(story)
print('Test PDF generated')
