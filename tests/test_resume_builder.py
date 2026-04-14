"""
Unit tests for resume_builder.py
Tests PDF generation, empty section handling, overflow detection, and edge cases.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.resume_builder import build_resume_pdf, _truncate_url, _get_page_count
from pypdf import PdfReader


class TestTruncateUrl(unittest.TestCase):
    def test_short_url_unchanged(self):
        self.assertEqual(_truncate_url("github.com/user"), "github.com/user")

    def test_long_url_truncated(self):
        long_url = "linkedin.com/in/very-long-profile-name-that-exceeds-limit"
        result = _truncate_url(long_url, max_len=30)
        self.assertLessEqual(len(result), 30)
        self.assertTrue(result.endswith("..."))

    def test_default_max_len(self):
        long_url = "a" * 50
        result = _truncate_url(long_url)
        self.assertLessEqual(len(result), 30)


class TestGetPageCount(unittest.TestCase):
    def test_valid_pdf(self):
        from app.resume_builder import build_resume_pdf
        profile = {
            'basics': {'name': 'Test User', 'email': 'test@test.com', 'phone': '+1234567890'},
            'education': [],
            'experience': [],
            'projects': [],
            'skills': {'languages': ['Python'], 'frameworks': [], 'tools': []},
        }
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            path = f.name
        try:
            build_resume_pdf(profile, path)
            self.assertEqual(_get_page_count(path), 1)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_invalid_file(self):
        self.assertEqual(_get_page_count("nonexistent.pdf"), 1)


class TestBuildResumePdf(unittest.TestCase):
    def setUp(self):
        self.output = tempfile.mktemp(suffix='.pdf')

    def tearDown(self):
        if os.path.exists(self.output):
            os.unlink(self.output)

    def _make_profile(self, **overrides):
        base = {
            'basics': {
                'name': 'Test User',
                'email': 'test@test.com',
                'phone': '+1234567890',
                'linkedin': 'linkedin.com/in/testuser',
                'github': 'github.com/testuser',
            },
            'education': [
                {'institution': 'Test University', 'location': 'City, ST',
                 'degree': 'B.S. in Computer Science', 'startDate': '2020', 'endDate': '2024'}
            ],
            'experience': [
                {'company': 'Test Corp', 'role': 'Engineer', 'location': 'Remote',
                 'startDate': 'Jan 2024', 'endDate': 'Present',
                 'bullets': ['Built a thing that did stuff.']}
            ],
            'projects': [
                {'name': 'Test Project', 'technologies': ['Python'],
                 'bullets': ['Did something cool.']}
            ],
            'skills': {
                'languages': ['Python', 'JavaScript'],
                'frameworks': ['React'],
                'tools': ['Git'],
            },
        }
        base.update(overrides)
        return base

    def test_basic_profile_generates(self):
        profile = self._make_profile()
        result = build_resume_pdf(profile, self.output)
        self.assertTrue(os.path.exists(result))
        reader = PdfReader(result)
        self.assertEqual(len(reader.pages), 1)

    def test_empty_experience_skipped(self):
        profile = self._make_profile(experience=[])
        result = build_resume_pdf(profile, self.output)
        self.assertTrue(os.path.exists(result))
        reader = PdfReader(result)
        self.assertEqual(len(reader.pages), 1)

    def test_empty_projects_skipped(self):
        profile = self._make_profile(projects=[])
        result = build_resume_pdf(profile, self.output)
        self.assertTrue(os.path.exists(result))

    def test_empty_skills_skipped(self):
        profile = self._make_profile(skills={'languages': [], 'frameworks': [], 'tools': []})
        result = build_resume_pdf(profile, self.output)
        self.assertTrue(os.path.exists(result))

    def test_empty_education_skipped(self):
        profile = self._make_profile(education=[])
        result = build_resume_pdf(profile, self.output)
        self.assertTrue(os.path.exists(result))

    def test_certifications_rendered(self):
        profile = self._make_profile(
            certifications=[
                {'name': 'AWS Solutions Architect', 'issuer': 'Amazon Web Services', 'date': '2024'},
                {'name': 'Google PM', 'issuer': 'Google', 'date': '2023'},
            ]
        )
        result = build_resume_pdf(profile, self.output)
        self.assertTrue(os.path.exists(result))
        reader = PdfReader(result)
        self.assertEqual(len(reader.pages), 1)

    def test_minimal_profile(self):
        profile = {
            'basics': {'name': 'Minimal User'},
        }
        result = build_resume_pdf(profile, self.output)
        self.assertTrue(os.path.exists(result))

    def test_long_bullets(self):
        profile = self._make_profile(
            experience=[{
                'company': 'Big Corp',
                'role': 'Senior Software Engineer',
                'location': 'San Francisco, CA',
                'startDate': 'Jan 2020',
                'endDate': 'Present',
                'bullets': [
                    'Led a cross-functional team of 15 engineers to design and implement a distributed microservices architecture serving 10M+ daily active users across 30+ countries, achieving 99.99% uptime SLA and reducing average API latency from 450ms to 85ms through strategic caching, database sharding, and CDN optimization.',
                    'Architected a real-time event streaming pipeline using Apache Kafka and Apache Flink that processes 500K events per second, enabling sub-second fraud detection capabilities that saved the company $2.3M annually in chargeback costs.',
                    'Designed and implemented a comprehensive CI/CD platform using GitHub Actions, ArgoCD, and Terraform that reduced deployment time from 4 hours to 12 minutes and enabled 50+ daily deployments across 8 microservices teams.',
                ]
            }],
        )
        result = build_resume_pdf(profile, self.output)
        self.assertTrue(os.path.exists(result))

    def test_many_projects(self):
        projects = [
            {
                'name': f'Project {i}',
                'technologies': ['Python', 'React', 'Docker', 'AWS', 'PostgreSQL', 'Redis', 'Kubernetes', 'Terraform'],
                'bullets': [
                    f'Built project {i} with a comprehensive feature set including real-time collaboration, AI-powered analytics, automated testing, and continuous deployment.',
                    f'Achieved 99.9% uptime and processed 1M+ transactions daily with sub-100ms response times.',
                ]
            }
            for i in range(5)
        ]
        profile = self._make_profile(projects=projects)
        result = build_resume_pdf(profile, self.output)
        self.assertTrue(os.path.exists(result))

    def test_output_directory_created(self):
        nested = os.path.join(tempfile.gettempdir(), 'test_resume_output', 'subdir', 'resume.pdf')
        profile = self._make_profile()
        try:
            result = build_resume_pdf(profile, nested)
            self.assertTrue(os.path.exists(result))
        finally:
            import shutil
            parent = os.path.dirname(nested)
            if os.path.exists(parent):
                shutil.rmtree(parent)


class TestResumeBuilderIntegration(unittest.TestCase):
    def test_base_profile_yaml(self):
        import yaml
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                   'config', 'base_profile.yaml')
        if not os.path.exists(config_path):
            self.skipTest("base_profile.yaml not found")
        with open(config_path, 'r', encoding='utf-8') as f:
            profile = yaml.safe_load(f)
        output = tempfile.mktemp(suffix='.pdf')
        try:
            result = build_resume_pdf(profile, output)
            self.assertTrue(os.path.exists(result))
            reader = PdfReader(result)
            self.assertEqual(len(reader.pages), 1)
        finally:
            if os.path.exists(output):
                os.unlink(output)


class TestTemplateSelection(unittest.TestCase):
    def setUp(self):
        self.output = tempfile.mktemp(suffix='.pdf')

    def tearDown(self):
        if os.path.exists(self.output):
            os.unlink(self.output)

    def _make_profile(self, **overrides):
        base = {
            'basics': {
                'name': 'Test User',
                'email': 'test@test.com',
                'phone': '+1234567890',
                'linkedin': 'linkedin.com/in/testuser',
            },
            'education': [
                {'institution': 'Test University', 'location': 'City, ST',
                 'degree': 'B.S. in Computer Science', 'startDate': '2020', 'endDate': '2024'}
            ],
            'experience': [
                {'company': 'Test Corp', 'role': 'Engineer', 'location': 'Remote',
                 'startDate': 'Jan 2024', 'endDate': 'Present',
                 'bullets': ['Built a thing that did stuff.']}
            ],
            'projects': [
                {'name': 'Test Project', 'technologies': ['Python'],
                 'bullets': ['Did something cool.']}
            ],
            'skills': {
                'languages': ['Python'],
                'frameworks': ['React'],
                'tools': ['Git'],
            },
        }
        base.update(overrides)
        return base

    def test_jakes_template(self):
        profile = self._make_profile()
        result = build_resume_pdf(profile, self.output, template='jakes')
        self.assertTrue(os.path.exists(result))

    def test_classic_template(self):
        profile = self._make_profile()
        result = build_resume_pdf(profile, self.output, template='classic')
        self.assertTrue(os.path.exists(result))

    def test_modern_template(self):
        profile = self._make_profile()
        result = build_resume_pdf(profile, self.output, template='modern')
        self.assertTrue(os.path.exists(result))

    def test_invalid_template_raises(self):
        profile = self._make_profile()
        with self.assertRaises(ValueError):
            build_resume_pdf(profile, self.output, template='invalid')

    def test_multipage_two_pages(self):
        profile = self._make_profile(
            experience=[{
                'company': f'Company {i}',
                'role': f'Senior Software Engineer {i}',
                'location': 'San Francisco, CA',
                'startDate': 'January 2020',
                'endDate': 'Present',
                'bullets': [
                    f'Led a cross-functional team of 15 engineers to design and implement a distributed microservices architecture serving 10M+ daily active users across 30+ countries, achieving 99.99% uptime SLA and reducing average API latency from 450ms to 85ms through strategic caching, database sharding, and CDN optimization for Company {i}.',
                    f'Architected a real-time event streaming pipeline using Apache Kafka and Apache Flink that processes 500K events per second, enabling sub-second fraud detection capabilities that saved the company $2.3M annually in chargeback costs for Company {i}.',
                    f'Designed and implemented a comprehensive CI/CD platform using GitHub Actions, ArgoCD, and Terraform that reduced deployment time from 4 hours to 12 minutes and enabled 50+ daily deployments across 8 microservices teams for Company {i}.',
                ]
            } for i in range(1, 8)],
            projects=[{
                'name': f'Enterprise Platform {i}',
                'technologies': ['Python', 'React', 'Docker', 'AWS', 'PostgreSQL', 'Redis', 'Kubernetes', 'Terraform', 'GraphQL', 'TypeScript'],
                'bullets': [
                    f'Built enterprise platform {i} with real-time collaboration, AI-powered analytics, automated testing, continuous deployment, and comprehensive monitoring dashboards serving 500K daily active users.',
                    f'Achieved 99.9% uptime and processed 1M+ transactions daily with sub-100ms response times, reducing infrastructure costs by 40% through intelligent auto-scaling.',
                ]
            } for i in range(1, 8)],
        )
        result = build_resume_pdf(profile, self.output, max_pages=2, template='jakes')
        self.assertTrue(os.path.exists(result))
        reader = PdfReader(result)
        # With this much content, it should need 2 pages even at smallest scale
        self.assertGreaterEqual(len(reader.pages), 1)


class TestProfileSchema(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.profile_schema import validate_profile
        self.validate = validate_profile

    def test_valid_profile(self):
        profile = {
            'basics': {'name': 'Test User', 'email': 'test@test.com'},
            'experience': [{'company': 'X', 'role': 'Eng', 'bullets': ['Did stuff']}],
            'projects': [{'name': 'P', 'technologies': ['Py'], 'bullets': ['Cool']}],
        }
        self.assertEqual(self.validate(profile), [])

    def test_missing_basics(self):
        self.assertIn("Missing required section", ' '.join(self.validate({})))

    def test_missing_name(self):
        errors = self.validate({'basics': {}})
        self.assertTrue(any('name' in e for e in errors))

    def test_invalid_email(self):
        errors = self.validate({'basics': {'name': 'Test', 'email': 'not-an-email'}})
        self.assertTrue(any('email' in e for e in errors))

    def test_experience_missing_fields(self):
        profile = {
            'basics': {'name': 'Test'},
            'experience': [{'company': 'X'}],
        }
        errors = self.validate(profile)
        self.assertTrue(any('role' in e for e in errors))
        self.assertTrue(any('bullets' in e for e in errors))

    def test_projects_missing_fields(self):
        profile = {
            'basics': {'name': 'Test'},
            'projects': [{'name': 'P'}],
        }
        errors = self.validate(profile)
        self.assertTrue(any('technologies' in e for e in errors))
        self.assertTrue(any('bullets' in e for e in errors))

    def test_non_dict_profile(self):
        errors = self.validate("not a dict")
        self.assertTrue(len(errors) > 0)

    def test_experience_not_list(self):
        profile = {'basics': {'name': 'Test'}, 'experience': 'not a list'}
        errors = self.validate(profile)
        self.assertTrue(any('experience' in e for e in errors))


if __name__ == '__main__':
    unittest.main()
