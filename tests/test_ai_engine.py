"""
Unit tests for ai_engine.py — multi-backend version.
Tests input validation, prompt building, error handling, and streaming
(without calling any real AI APIs).
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai_engine import (
    _validate_base_profile,
    _build_prompt,
    generate_tailored_profile,
    generate_tailored_profile_stream,
    GEMINI_MODELS,
    OPENAI_MODELS,
    ANTHROPIC_MODELS,
    MAX_RETRIES,
    SUPPORTED_BACKENDS,
)

VALID_RESPONSE = '''
{
    "skills": {"languages": ["Python"], "frameworks": ["FastAPI"], "tools": ["Docker"]},
    "experience": [{"company": "TestCo", "role": "Engineer", "location": "Remote",
                   "startDate": "2024", "endDate": "Present",
                   "bullets": ["Built something great."]}],
    "projects": [{"name": "Test Project", "technologies": ["Python"],
                 "bullets": ["Did something cool."]}]
}
'''

BASE_PROFILE = {
    'basics': {'name': 'Test User'},
    'skills': {'languages': ['Python', 'Java'], 'frameworks': [], 'tools': []},
    'experience': [],
    'projects': [],
}


class TestValidateBaseProfile(unittest.TestCase):
    def test_valid_profile(self):
        profile = {'basics': {'name': 'Test User', 'email': 'test@test.com'}}
        result = _validate_base_profile(profile)
        self.assertEqual(result, profile)

    def test_missing_basics(self):
        with self.assertRaises(ValueError) as ctx:
            _validate_base_profile({})
        self.assertIn("basics", str(ctx.exception))

    def test_basics_not_dict(self):
        with self.assertRaises(ValueError) as ctx:
            _validate_base_profile({'basics': 'not a dict'})
        self.assertIn("dictionary", str(ctx.exception))

    def test_missing_name(self):
        with self.assertRaises(ValueError) as ctx:
            _validate_base_profile({'basics': {'email': 'test@test.com'}})
        self.assertIn("name", str(ctx.exception))

    def test_empty_name(self):
        with self.assertRaises(ValueError) as ctx:
            _validate_base_profile({'basics': {'name': '', 'email': 'test@test.com'}})
        self.assertIn("name", str(ctx.exception))


class TestBuildPrompt(unittest.TestCase):
    def test_prompt_contains_company(self):
        profile = {'basics': {'name': 'Test'}}
        prompt = _build_prompt(profile, 'Some JD', 'Google')
        self.assertIn('Google', prompt)

    def test_prompt_contains_jd(self):
        profile = {'basics': {'name': 'Test'}}
        prompt = _build_prompt(profile, 'Build scalable systems', 'Google')
        self.assertIn('Build scalable systems', prompt)

    def test_prompt_contains_profile_json(self):
        profile = {'basics': {'name': 'Alice'}, 'skills': {'languages': ['Python']}}
        prompt = _build_prompt(profile, 'JD', 'Company')
        self.assertIn('Alice', prompt)
        self.assertIn('Python', prompt)


class TestGeminiBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._old_key = os.environ.get("GEMINI_API_KEY")
        os.environ["GEMINI_API_KEY"] = "mock-gemini-key"

    @classmethod
    def tearDownClass(cls):
        if cls._old_key:
            os.environ["GEMINI_API_KEY"] = cls._old_key
        else:
            os.environ.pop("GEMINI_API_KEY", None)

    @patch('app.ai_engine._generate_gemini')
    def test_successful_generation(self, mock_gen):
        mock_gen.return_value = VALID_RESPONSE
        result = generate_tailored_profile(BASE_PROFILE, 'Build APIs', 'TestCo', backend='gemini')
        self.assertIn('basics', result)
        self.assertEqual(result['skills']['languages'], ['Python'])
        self.assertEqual(len(result['experience']), 1)
        self.assertEqual(len(result['projects']), 1)

    @patch('app.ai_engine._generate_gemini')
    def test_retry_on_error(self, mock_gen):
        mock_gen.side_effect = Exception("API error")
        with self.assertRaises(RuntimeError):
            generate_tailored_profile(BASE_PROFILE, 'JD', 'Company', backend='gemini')
        self.assertEqual(mock_gen.call_count, MAX_RETRIES * len(GEMINI_MODELS))

    @patch('app.ai_engine._generate_gemini')
    def test_model_fallback(self, mock_gen):
        mock_gen.side_effect = Exception("fail")
        with self.assertRaises(RuntimeError):
            generate_tailored_profile(BASE_PROFILE, 'JD', 'Company', backend='gemini')
        # Should try each model MAX_RETRIES times
        self.assertEqual(mock_gen.call_count, MAX_RETRIES * len(GEMINI_MODELS))


class TestOpenAIBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._old_key = os.environ.get("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = "mock-openai-key"

    @classmethod
    def tearDownClass(cls):
        if cls._old_key:
            os.environ["OPENAI_API_KEY"] = cls._old_key
        else:
            os.environ.pop("OPENAI_API_KEY", None)

    @patch('app.ai_engine._generate_openai')
    def test_successful_generation(self, mock_gen):
        mock_gen.return_value = VALID_RESPONSE
        result = generate_tailored_profile(BASE_PROFILE, 'Build APIs', 'TestCo', backend='openai')
        self.assertIn('basics', result)
        self.assertEqual(result['skills']['languages'], ['Python'])

    @patch('app.ai_engine._generate_openai')
    def test_retry_on_error(self, mock_gen):
        mock_gen.side_effect = Exception("API error")
        with self.assertRaises(RuntimeError):
            generate_tailored_profile(BASE_PROFILE, 'JD', 'Company', backend='openai')
        self.assertEqual(mock_gen.call_count, MAX_RETRIES * len(OPENAI_MODELS))


class TestAnthropicBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._old_key = os.environ.get("ANTHROPIC_API_KEY")
        os.environ["ANTHROPIC_API_KEY"] = "mock-anthropic-key"

    @classmethod
    def tearDownClass(cls):
        if cls._old_key:
            os.environ["ANTHROPIC_API_KEY"] = cls._old_key
        else:
            os.environ.pop("ANTHROPIC_API_KEY", None)

    @patch('app.ai_engine._generate_anthropic')
    def test_successful_generation(self, mock_gen):
        mock_gen.return_value = VALID_RESPONSE
        result = generate_tailored_profile(BASE_PROFILE, 'Build APIs', 'TestCo', backend='anthropic')
        self.assertIn('basics', result)
        self.assertEqual(result['skills']['languages'], ['Python'])

    @patch('app.ai_engine._generate_anthropic')
    def test_retry_on_error(self, mock_gen):
        mock_gen.side_effect = Exception("API error")
        with self.assertRaises(RuntimeError):
            generate_tailored_profile(BASE_PROFILE, 'JD', 'Company', backend='anthropic')
        self.assertEqual(mock_gen.call_count, MAX_RETRIES * len(ANTHROPIC_MODELS))


class TestStreaming(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._old_gemini = os.environ.get("GEMINI_API_KEY")
        os.environ["GEMINI_API_KEY"] = "mock-gemini-key"

    @classmethod
    def tearDownClass(cls):
        if cls._old_gemini:
            os.environ["GEMINI_API_KEY"] = cls._old_gemini
        else:
            os.environ.pop("GEMINI_API_KEY", None)

    @patch('app.ai_engine._generate_gemini_stream')
    def test_stream_yields_chunks(self, mock_stream):
        full_json = '{"skills":{"languages":["Python"],"frameworks":[],"tools":[]},"experience":[{"company":"T","role":"E","location":"R","startDate":"2024","endDate":"P","bullets":["b"]}],"projects":[{"name":"P","technologies":["Py"],"bullets":["b"]}]}'
        chunk_size = 20
        chunks = [full_json[i:i+chunk_size] for i in range(0, len(full_json), chunk_size)]
        mock_stream.return_value = iter(chunks)
        result_chunks = list(generate_tailored_profile_stream(BASE_PROFILE, 'JD', 'Co', backend='gemini'))
        self.assertGreater(len(result_chunks), 0)
        self.assertEqual("".join(result_chunks), full_json)

    def test_stream_invalid_backend(self):
        with self.assertRaises(ValueError):
            list(generate_tailored_profile_stream(BASE_PROFILE, 'JD', 'Co', backend='invalid'))

    def test_generate_invalid_backend(self):
        with self.assertRaises(ValueError):
            generate_tailored_profile(BASE_PROFILE, 'JD', 'Co', backend='invalid')

    def test_missing_api_key(self):
        old_key = os.environ.pop("GEMINI_API_KEY", None)
        try:
            with self.assertRaises(ValueError) as ctx:
                generate_tailored_profile(BASE_PROFILE, 'JD', 'Co', backend='gemini')
            self.assertIn("API key", str(ctx.exception))
        finally:
            if old_key:
                os.environ["GEMINI_API_KEY"] = old_key


class TestConstants(unittest.TestCase):
    def test_gemini_models_not_empty(self):
        self.assertTrue(len(GEMINI_MODELS) > 0)

    def test_openai_models_not_empty(self):
        self.assertTrue(len(OPENAI_MODELS) > 0)

    def test_anthropic_models_not_empty(self):
        self.assertTrue(len(ANTHROPIC_MODELS) > 0)

    def test_supported_backends(self):
        self.assertEqual(SUPPORTED_BACKENDS, ("gemini", "openai", "anthropic"))

    def test_max_retries_positive(self):
        self.assertGreater(MAX_RETRIES, 0)


if __name__ == '__main__':
    unittest.main()
