from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
import markdown
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib import colors
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import os
import tempfile
import asyncio
from datetime import datetime, timedelta
import uuid
from typing import Optional

router = APIRouter(prefix="/api/feedback", tags=["feedback"])

# Request model
class FeedbackPDFRequest(BaseModel):
    validation_content: str
    user_id: str
    filename: Optional[str] = None

# Store for tracking temporary files
temp_files = {}

# CSS styles for TalentElevate theme
TALENT_ELEVATE_CSS = """
@page {
    margin: 2cm;
    @top-center {
        content: "TalentElevate - Validation Feedback";
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 10pt;
        color: #1E40AF;
    }
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    margin: 0;
    padding: 20px;
}

h1, h2, h3, h4, h5, h6 {
    color: #1E40AF;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    font-weight: 600;
}

h1 {
    font-size: 24pt;
    border-bottom: 3px solid #1E40AF;
    padding-bottom: 10px;
}

h2 {
    font-size: 20pt;
    border-bottom: 2px solid #1E40AF;
    padding-bottom: 8px;
}

h3 {
    font-size: 16pt;
    border-bottom: 1px solid #1E40AF;
    padding-bottom: 5px;
}

h4 {
    font-size: 14pt;
}

h5, h6 {
    font-size: 12pt;
}

strong, b {
    font-weight: 600;
    color: #1E40AF;
}

code {
    background-color: #f5f5f5;
    padding: 2px 4px;
    border-radius: 3px;
    font-family: 'Courier New', Consolas, monospace;
    font-size: 0.9em;
    color: #d63384;
}

pre {
    background-color: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 16px;
    margin: 16px 0;
    overflow-x: auto;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

pre code {
    background-color: transparent;
    padding: 0;
    border-radius: 0;
    color: #333;
    font-size: 0.85em;
    line-height: 1.4;
}

ul, ol {
    margin: 12px 0;
    padding-left: 24px;
}

li {
    margin: 6px 0;
    line-height: 1.5;
}

ul ul, ol ol, ul ol, ol ul {
    margin: 6px 0;
    padding-left: 20px;
}

hr {
    border: none;
    height: 3px;
    background: linear-gradient(to right, #1E40AF, #3B82F6, #1E40AF);
    margin: 24px 0;
    border-radius: 2px;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

th, td {
    border: 1px solid #dee2e6;
    padding: 12px;
    text-align: left;
}

th {
    background-color: #1E40AF;
    color: white;
    font-weight: 600;
}

tr:nth-child(even) {
    background-color: #f8f9fa;
}

.success-icon {
    color: #28a745;
    font-weight: bold;
}

.error-icon {
    color: #dc3545;
    font-weight: bold;
}

p {
    margin: 12px 0;
    text-align: justify;
}

blockquote {
    border-left: 4px solid #1E40AF;
    margin: 16px 0;
    padding: 12px 16px;
    background-color: #f8f9fa;
    font-style: italic;
}

.header {
    text-align: center;
    margin-bottom: 30px;
    padding: 20px;
    background: linear-gradient(135deg, #1E40AF, #3B82F6);
    color: white;
    border-radius: 8px;
}

.footer {
    text-align: center;
    margin-top: 30px;
    padding: 15px;
    font-size: 10pt;
    color: #666;
    border-top: 1px solid #dee2e6;
}
"""

def process_markdown_content(content: str) -> str:
    """Convert markdown to HTML with custom processing for icons and styling"""
    # Convert markdown to HTML
    html = markdown.markdown(content, extensions=['tables', 'fenced_code', 'nl2br'])
    
    # Parse with BeautifulSoup for additional processing
    soup = BeautifulSoup(html, 'html.parser')
    
    # Replace checkmark and cross symbols with styled spans
    for text_node in soup.find_all(text=True):
        if '✅' in text_node:
            new_text = text_node.replace('✅', '<span class="success-icon">✅</span>')
            text_node.replace_with(BeautifulSoup(new_text, 'html.parser'))
        if '❌' in text_node:
            new_text = text_node.replace('❌', '<span class="error-icon">❌</span>')
            text_node.replace_with(BeautifulSoup(new_text, 'html.parser'))
    
    return str(soup)

def create_pdf_html(content: str, user_id: str) -> str:
    """Create simplified HTML content for ReportLab processing"""
    processed_content = process_markdown_content(content)
    current_time = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    exercise_title = f"Exercise Validation Report - User {user_id}"
    
    html_template = f"""
    <html>
    <head>
        <title>TalentElevate - Detailed Feedback</title>
    </head>
    <body>
        <div class="header">
            <h1>TalentElevate</h1>
            <h2>Detailed Validation Feedback</h2>
            <h3>{exercise_title}</h3>
            <p>Generated on {current_time}</p>
        </div>
        
        <div class="content">
            {processed_content}
        </div>
        
        <div class="footer">
            <p>This report was generated by TalentElevate for User ID: {user_id}</p>
            <p>© 2024 TalentElevate. All rights reserved.</p>
        </div>
    </body>
    </html>
    """
    
    return html_template

def create_pdf_styles():
    """Create custom PDF styles for TalentElevate branding"""
    styles = getSampleStyleSheet()
    
    # TalentElevate blue color
    talent_blue = HexColor('#2563eb')
    
    # Custom styles - check if they exist before adding
    if 'TitleStyle' not in styles:
        styles.add(ParagraphStyle(
            name='TitleStyle',
            parent=styles['Title'],
            fontSize=24,
            textColor=talent_blue,
            spaceAfter=20,
            alignment=TA_CENTER
        ))
    
    if 'SubtitleStyle' not in styles:
        styles.add(ParagraphStyle(
            name='SubtitleStyle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=talent_blue,
            spaceAfter=15,
            alignment=TA_CENTER
        ))
    
    if 'SectionHeading' not in styles:
        styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=talent_blue,
            spaceBefore=15,
            spaceAfter=10,
            leftIndent=0
        ))
    
    # Use a different name to avoid conflict with existing BodyText
    if 'CustomBodyText' not in styles:
        styles.add(ParagraphStyle(
            name='CustomBodyText',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            alignment=TA_JUSTIFY
        ))
    
    if 'CodeStyle' not in styles:
        styles.add(ParagraphStyle(
            name='CodeStyle',
            parent=styles['Code'],
            fontSize=10,
            leftIndent=20,
            backgroundColor=HexColor('#f8f9fa'),
            borderColor=HexColor('#e9ecef'),
            borderWidth=1
        ))
    
    return styles

def convert_html_to_reportlab(html_content: str, styles) -> list:
    """Convert HTML content to ReportLab story elements"""
    soup = BeautifulSoup(html_content, 'html.parser')
    story = []
    
    # Add header
    story.append(Paragraph("TalentElevate", styles['TitleStyle']))
    story.append(Paragraph("Detailed Validation Feedback", styles['SubtitleStyle']))
    story.append(Spacer(1, 20))
    
    # Process content
    content_div = soup.find('div', class_='content')
    if content_div:
        story.extend(process_html_elements(content_div, styles))
    
    # Add footer
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        name='Footer',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", footer_style))
    story.append(Paragraph("© 2024 TalentElevate - Confidential Assessment Report", footer_style))
    
    return story

def process_html_elements(element, styles) -> list:
    """Process HTML elements and convert to ReportLab elements"""
    story = []
    
    for child in element.children:
        if hasattr(child, 'name'):
            if child.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                story.append(Spacer(1, 10))
                story.append(Paragraph(child.get_text().strip(), styles['SectionHeading']))
            elif child.name == 'p':
                text = child.get_text().strip()
                if text:
                    story.append(Paragraph(text, styles['CustomBodyText']))
            elif child.name in ['ul', 'ol']:
                for li in child.find_all('li'):
                    text = li.get_text().strip()
                    if text:
                        story.append(Paragraph(f"• {text}", styles['CustomBodyText']))
            elif child.name == 'pre':
                code_text = child.get_text().strip()
                if code_text:
                    story.append(Paragraph(code_text, styles['CodeStyle']))
            elif child.name == 'blockquote':
                quote_text = child.get_text().strip()
                if quote_text:
                    quote_style = ParagraphStyle(
                        name='Quote',
                        parent=styles['CustomBodyText'],
                        leftIndent=30,
                        fontStyle='italic',
                        borderColor=HexColor('#2563eb'),
                        borderWidth=2
                    )
                    story.append(Paragraph(quote_text, quote_style))
            elif child.name == 'div' and child.get('class') and 'score-section' in child.get('class'):
                # Handle score sections with special styling
                score_text = child.get_text().strip()
                if score_text:
                    score_style = ParagraphStyle(
                        name='ScoreSection',
                        parent=styles['CustomBodyText'],
                        backgroundColor=HexColor('#f0f9ff'),
                        borderColor=HexColor('#2563eb'),
                        borderWidth=2,
                        leftIndent=10,
                        rightIndent=10,
                        spaceBefore=10,
                        spaceAfter=10
                    )
                    story.append(Paragraph(score_text, score_style))
            else:
                # Process nested elements
                story.extend(process_html_elements(child, styles))
        else:
            # Text node
            text = str(child).strip()
            if text and text not in ['\n', '\r\n', '\t']:
                story.append(Paragraph(text, styles['CustomBodyText']))
    
    return story

async def cleanup_temp_file(file_path: str, delay_minutes: int = 5):
    """Delete temporary file after specified delay"""
    await asyncio.sleep(delay_minutes * 60)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            if file_path in temp_files:
                del temp_files[file_path]
    except Exception as e:
        print(f"Error cleaning up temp file {file_path}: {e}")

@router.post("/generate-pdf")
async def generate_feedback_pdf(
    request: FeedbackPDFRequest,
    background_tasks: BackgroundTasks
):
    """Generate PDF from markdown validation content"""
    try:
        # Create temp directory if it doesn't exist
        temp_dir = os.path.join(tempfile.gettempdir(), "feedback")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = request.filename or f"feedback_{request.user_id}_{file_id}.pdf"
        if not filename.endswith('.pdf'):
            filename += '.pdf'
        
        file_path = os.path.join(temp_dir, filename)
        
        # Create HTML content
        html_content = create_pdf_html(request.validation_content, request.user_id)
        
        # Generate PDF using ReportLab
        doc = SimpleDocTemplate(file_path, pagesize=letter)
        styles = create_pdf_styles()
        
        # Convert HTML content to ReportLab elements
        story = convert_html_to_reportlab(html_content, styles)
        
        # Build PDF
        doc.build(story)
        
        # Store file info for tracking
        temp_files[file_path] = {
            'created_at': datetime.now(),
            'user_id': request.user_id,
            'filename': filename
        }
        
        # Schedule cleanup
        background_tasks.add_task(cleanup_temp_file, file_path, 5)
        
        return {
            "success": True,
            "message": "PDF generated successfully",
            "file_id": file_id,
            "filename": filename,
            "download_url": f"/api/feedback/download/{file_id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")

@router.get("/download/{file_id}")
async def download_feedback_pdf(file_id: str, background_tasks: BackgroundTasks):
    """Download generated PDF file"""
    try:
        # Find file by ID
        temp_dir = os.path.join(tempfile.gettempdir(), "feedback")
        target_file = None
        
        for file_path, file_info in temp_files.items():
            if file_id in file_path:
                target_file = file_path
                break
        
        if not target_file or not os.path.exists(target_file):
            raise HTTPException(status_code=404, detail="File not found or has expired")
        
        filename = temp_files[target_file]['filename']
        
        # Schedule immediate cleanup after download
        background_tasks.add_task(cleanup_temp_file, target_file, 0)
        
        return FileResponse(
            path=target_file,
            filename=filename,
            media_type='application/pdf',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading PDF: {str(e)}")

@router.get("/cleanup")
async def manual_cleanup():
    """Manual cleanup endpoint for maintenance"""
    try:
        temp_dir = os.path.join(tempfile.gettempdir(), "feedback")
        cleaned_count = 0
        
        if os.path.exists(temp_dir):
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                try:
                    os.remove(file_path)
                    cleaned_count += 1
                except Exception:
                    pass
        
        # Clear tracking dict
        temp_files.clear()
        
        return {
            "success": True,
            "message": f"Cleaned up {cleaned_count} temporary files"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during cleanup: {str(e)}")