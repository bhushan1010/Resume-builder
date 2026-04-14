"""
Unit tests for ats_analytics.py
"""

import os
import sys
import unittest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ats_analytics import analyze_ats_score, _extract_keywords, _extract_tech_keywords


class TestExtractKeywords(unittest.TestCase):
    def test_basic_extraction(self):
        text = "Python developer with AWS experience"
        keywords = _extract_keywords(text)
        self.assertIn('python', keywords)
        self.assertIn('developer', keywords)
        self.assertIn('aws', keywords)

    def test_filters_stop_words(self):
        text = "the and is are have been will would could"
        keywords = _extract_keywords(text)
        self.assertEqual(len(keywords), 0)

    def test_filters_short_words(self):
        text = "an it is in on at to"
        keywords = _extract_keywords(text)
        self.assertEqual(len(keywords), 0)

    def test_case_insensitive(self):
        text = "Python PYTHON python"
        keywords = _extract_keywords(text)
        self.assertEqual(keywords, {'python'})


class TestExtractTechKeywords(unittest.TestCase):
    def test_detects_aws(self):
        self.assertIn('AWS', _extract_tech_keywords("Experience with AWS required"))

    def test_detects_api(self):
        self.assertIn('API', _extract_tech_keywords("REST API development"))

    def test_detects_cicd(self):
        self.assertIn('CI/CD', _extract_tech_keywords("CI/CD pipeline management"))

    def test_detects_capitalized_terms(self):
        result = _extract_tech_keywords("Kubernetes Docker TensorFlow")
        self.assertIn('Kubernetes', result)
        self.assertIn('Docker', result)
        self.assertIn('TensorFlow', result)


class TestAnalyzeAtsScore(unittest.TestCase):
    def _make_profile(self, **overrides):
        base = {
            'basics': {'name': 'Test User', 'email': 'test@test.com'},
            'education': [{'institution': 'Test Uni', 'degree': 'B.S. CS', 'location': 'City', 'startDate': '2020', 'endDate': '2024'}],
            'experience': [{'company': 'TechCo', 'role': 'Engineer', 'location': 'Remote', 'startDate': '2024', 'endDate': 'Present', 'bullets': ['Built Python APIs with AWS and Docker']}],
            'projects': [{'name': 'ML Pipeline', 'technologies': ['Python', 'TensorFlow', 'AWS'], 'bullets': ['Built ML pipeline']}],
            'skills': {'languages': ['Python', 'SQL'], 'frameworks': ['TensorFlow'], 'tools': ['AWS', 'Docker']},
        }
        base.update(overrides)
        return base

    def test_returns_correct_structure(self):
        profile = self._make_profile()
        jd = "Python, AWS, Docker, SQL, TensorFlow"
        result = analyze_ats_score(profile, jd)
        self.assertIn('overall_score', result)
        self.assertIn('keyword_match', result)
        self.assertIn('section_scores', result)
        self.assertIn('suggestions', result)
        self.assertIn('strengths', result)

    def test_score_range(self):
        profile = self._make_profile()
        jd = "Python, AWS, Docker, SQL, TensorFlow"
        result = analyze_ats_score(profile, jd)
        self.assertGreaterEqual(result['overall_score'], 0)
        self.assertLessEqual(result['overall_score'], 100)

    def test_high_match_profile(self):
        profile = self._make_profile(
            experience=[{'company': 'TechCo', 'role': 'ML Engineer', 'location': 'Remote',
                         'startDate': '2024', 'endDate': 'Present',
                         'bullets': ['Built Python ML pipelines with TensorFlow on AWS using Docker and SQL']}],
            skills={'languages': ['Python', 'SQL'], 'frameworks': ['TensorFlow', 'PyTorch'], 'tools': ['AWS', 'Docker', 'Kubernetes']},
        )
        jd = "Python TensorFlow AWS Docker SQL ML pipelines Kubernetes"
        result = analyze_ats_score(profile, jd)
        self.assertGreater(result['overall_score'], 40)

    def test_low_match_profile(self):
        profile = {
            'basics': {'name': 'Test User'},
            'education': [],
            'experience': [],
            'projects': [],
            'skills': {'languages': ['Java'], 'frameworks': [], 'tools': []},
        }
        jd = "Python TensorFlow AWS Docker Kubernetes MLOps"
        result = analyze_ats_score(profile, jd)
        self.assertLess(result['overall_score'], 30)

    def test_keyword_match_tracking(self):
        profile = self._make_profile()
        jd = "Python AWS Docker"
        result = analyze_ats_score(profile, jd)
        self.assertIn('matched', result['keyword_match'])
        self.assertIn('missing', result['keyword_match'])
        self.assertIn('percentage', result['keyword_match'])
        self.assertGreater(result['keyword_match']['matched_count'], 0)

    def test_section_scores_exist(self):
        profile = self._make_profile()
        jd = "Python AWS Docker"
        result = analyze_ats_score(profile, jd)
        self.assertIn('experience', result['section_scores'])
        self.assertIn('skills', result['section_scores'])
        self.assertIn('projects', result['section_scores'])

    def test_suggestions_generated(self):
        profile = self._make_profile()
        jd = "Python AWS Docker Kubernetes Terraform Jenkins Grafana Prometheus"
        result = analyze_ats_score(profile, jd)
        self.assertIsInstance(result['suggestions'], list)
        self.assertGreater(len(result['suggestions']), 0)

    def test_strengths_generated(self):
        profile = self._make_profile()
        jd = "Python AWS Docker"
        result = analyze_ats_score(profile, jd)
        self.assertIsInstance(result['strengths'], list)
        self.assertGreater(len(result['strengths']), 0)

    def test_empty_jd(self):
        profile = self._make_profile()
        result = analyze_ats_score(profile, '')
        self.assertEqual(result['overall_score'], 100)
        self.assertEqual(result['keyword_match']['percentage'], 100)


class TestAwardsPublicationsInPDF(unittest.TestCase):
    def setUp(self):
        self.output = tempfile.mktemp(suffix='.pdf')

    def tearDown(self):
        if os.path.exists(self.output):
            os.unlink(self.output)

    def test_awards_rendered(self):
        from app.resume_builder import build_resume_pdf
        profile = {
            'basics': {'name': 'Test User', 'email': 'test@test.com'},
            'awards': [
                {'title': 'Employee of the Year', 'organization': 'TechCo', 'date': '2024', 'description': 'Outstanding performance.'},
            ],
        }
        result = build_resume_pdf(profile, self.output)
        self.assertTrue(os.path.exists(result))

    def test_publications_rendered(self):
        from app.resume_builder import build_resume_pdf
        profile = {
            'basics': {'name': 'Test User', 'email': 'test@test.com'},
            'publications': [
                {'title': 'Deep Learning Advances', 'venue': 'NeurIPS', 'date': '2024'},
            ],
        }
        result = build_resume_pdf(profile, self.output)
        self.assertTrue(os.path.exists(result))

    def test_awards_and_publications_together(self):
        from app.resume_builder import build_resume_pdf
        profile = {
            'basics': {'name': 'Test User', 'email': 'test@test.com'},
            'awards': [
                {'title': 'Best Paper Award', 'organization': 'ICML', 'date': '2024'},
            ],
            'publications': [
                {'title': 'Efficient Transformers', 'venue': 'ICML', 'date': '2024'},
                {'title': 'RAG Systems', 'venue': 'NeurIPS', 'date': '2024'},
            ],
        }
        result = build_resume_pdf(profile, self.output)
        self.assertTrue(os.path.exists(result))


if __name__ == '__main__':
    unittest.main()
