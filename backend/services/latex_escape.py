import re

def escape_latex(text: str) -> str:
    """
    Escape LaTeX special characters in the given text.
    """
    if text is None:
        return ""
    
    # Dictionary of LaTeX special characters and their escapes
    replacements = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
        '\\': r'\textbackslash{}'
    }
    
    # Replace each special character
    for char, escape in replacements.items():
        text = text.replace(char, escape)
    
    return text