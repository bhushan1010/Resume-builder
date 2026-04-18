import os
import tempfile
import subprocess
import json
from jinja2 import Environment, FileSystemLoader
from .latex_escape import escape_latex
from fastapi import HTTPException

def generate(resume_json: dict) -> bytes:
    """
    Generate PDF from resume JSON using LaTeX template and Tectonic.
    """
    try:
        # Set up Jinja2 environment
        template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('resume.tex.j2')
        
        # Escape all string values in resume_json
        escaped_json = escape_resume_json(resume_json)
        
        # Render template
        rendered_tex = template.render(**escaped_json)
        
        # Create temporary directory for LaTeX compilation
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write .tex file
            tex_file_path = os.path.join(temp_dir, "resume.tex")
            with open(tex_file_path, 'w', encoding='utf-8') as f:
                f.write(rendered_tex)
            
            # Run Tectonic to compile PDF
            result = subprocess.run(
                ["tectonic", "-X", "compile", tex_file_path, "--outdir", temp_dir],
                capture_output=True,
                timeout=30,
                text=True
            )
            
            # Check if compilation succeeded
            if result.returncode != 0:
                raise HTTPException(
                    status_code=500,
                    detail=f"LaTeX compilation failed: {result.stderr}"
                )
            
            # Read generated PDF
            pdf_file_path = os.path.join(temp_dir, "resume.pdf")
            if not os.path.exists(pdf_file_path):
                raise HTTPException(
                    status_code=500,
                    detail="PDF file was not generated"
                )
            
            with open(pdf_file_path, 'rb') as f:
                pdf_bytes = f.read()
            
            return pdf_bytes
            
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=500,
            detail="LaTeX compilation timed out"
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed: {str(e)}"
        )

def escape_resume_json(resume_json: dict) -> dict:
    """
    Recursively escape all string values in resume JSON using LaTeX escaping.
    """
    if isinstance(resume_json, dict):
        escaped = {}
        for key, value in resume_json.items():
            escaped[key] = escape_resume_json(value)
        return escaped
    elif isinstance(resume_json, list):
        return [escape_resume_json(item) for item in resume_json]
    elif isinstance(resume_json, str):
        return escape_latex(resume_json)
    else:
        return resume_json