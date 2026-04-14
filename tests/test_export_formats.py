"""
Unit tests for export_formats.py
"""

import os
import sys
import unittest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.export_formats import export_to_docx, export_to_text, export_to_markdown


PROFILE = {
    'basics': {'name': 'Test User', 'email': 'test@test.com', 'phone': '+1234'},
    'education': [{'institution': 'Test Uni', 'degree': 'B.S. CS', 'location': 'City', 'startDate': '2020', 'endDate': '2024'}],
    'experience': [{'company': 'TechCo', 'role': 'Engineer', 'location': 'Remote', 'startDate': '2024', 'endDate': 'Present', 'bullets': ['Built stuff']}],
    'projects': [{'name': 'Test Project', 'technologies': ['Python', 'AWS'], 'bullets': ['Did cool thing']}],
    'skills': {'languages': ['Python', 'SQL'], 'frameworks': ['FastAPI'], 'tools': ['Docker']},
    'certifications': [{'name': 'AWS SA', 'issuer': 'Amazon', 'date': '2024'}],
    'awards': [{'title': 'Employee of Month', 'organization': 'TechCo', 'date': '2024'}],
    'publications': [{'title': 'Test Paper', 'venue': 'IEEE', 'date': '2024'}],
}


class TestExportDocx(unittest.TestCase):
    def test_creates_file(self):
        path = tempfile.mktemp(suffix='.docx')
        try:
            result = export_to_docx(PROFILE, path)
            self.assertTrue(os.path.exists(result))
            self.assertGreater(os.path.getsize(result), 0)
        finally:
            if os.path.exists(path):
                os.unlink(path)


class TestExportText(unittest.TestCase):
    def test_creates_file(self):
        path = tempfile.mktemp(suffix='.txt')
        try:
            result = export_to_text(PROFILE, path)
            self.assertTrue(os.path.exists(result))
            with open(result, 'r') as f:
                content = f.read()
            self.assertIn('TEST USER', content)
            self.assertIn('TechCo', content)
            self.assertIn('Test Project', content)
            self.assertIn('AWS SA', content)
            self.assertIn('Employee of Month', content)
            self.assertIn('Test Paper', content)
        finally:
            if os.path.exists(path):
                os.unlink(path)


class TestExportMarkdown(unittest.TestCase):
    def test_creates_file(self):
        path = tempfile.mktemp(suffix='.md')
        try:
            result = export_to_markdown(PROFILE, path)
            self.assertTrue(os.path.exists(result))
            with open(result, 'r') as f:
                content = f.read()
            self.assertIn('# Test User', content)
            self.assertIn('## Professional Experience', content)
            self.assertIn('## Projects', content)
            self.assertIn('## Technical Skills', content)
            self.assertIn('*TechCo*', content)
            self.assertIn('[test@test.com](mailto:test@test.com)', content)
        finally:
            if os.path.exists(path):
                os.unlink(path)


if __name__ == '__main__':
    unittest.main()
