"""
Unit tests for database.py
"""

import os
import sys
import unittest
import tempfile
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import (
    init_db, create_user, authenticate_user, create_session, validate_session,
    delete_session, save_profile, get_profiles, get_profile, delete_profile,
    save_resume, get_resumes, get_resume, _hash_password
)


def _unique_email():
    return f"test-{uuid.uuid4().hex[:8]}@example.com"


class TestDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = tempfile.mktemp(suffix='.db')
        from app import database
        database.DB_PATH = cls.db_path
        init_db()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.db_path):
            os.unlink(cls.db_path)

    def _create_user(self):
        return create_user(_unique_email(), 'password123', 'Test User')

    def test_create_user(self):
        user = self._create_user()
        self.assertEqual(user['name'], 'Test User')
        self.assertIn('@example.com', user['email'])

    def test_duplicate_user(self):
        email = _unique_email()
        create_user(email, 'password123', 'User1')
        with self.assertRaises(ValueError):
            create_user(email, 'password123', 'User2')

    def test_authenticate_user_success(self):
        email = _unique_email()
        create_user(email, 'password123', 'Test User')
        user = authenticate_user(email, 'password123')
        self.assertIsNotNone(user)
        self.assertEqual(user['email'], email)

    def test_authenticate_user_wrong_password(self):
        email = _unique_email()
        create_user(email, 'password123', 'Test User')
        user = authenticate_user(email, 'wrongpassword')
        self.assertIsNone(user)

    def test_authenticate_nonexistent_user(self):
        user = authenticate_user('nobody@example.com', 'password')
        self.assertIsNone(user)

    def test_session_lifecycle(self):
        user = self._create_user()
        token = create_session(user['id'])
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 20)

        session_user = validate_session(token)
        self.assertIsNotNone(session_user)
        self.assertEqual(session_user['id'], user['id'])

        delete_session(token)
        self.assertIsNone(validate_session(token))

    def test_save_and_get_profiles(self):
        user = self._create_user()
        profile_data = {'basics': {'name': 'Test'}, 'skills': {'languages': ['Python']}}
        profile_id = save_profile(user['id'], 'My Profile', profile_data, is_default=True)
        self.assertIsInstance(profile_id, int)

        profiles = get_profiles(user['id'])
        self.assertEqual(len(profiles), 1)
        self.assertEqual(profiles[0]['name'], 'My Profile')

        profile = get_profile(user['id'], profile_id)
        self.assertEqual(profile['profile_data']['basics']['name'], 'Test')

    def test_delete_profile(self):
        user = self._create_user()
        profile_data = {'basics': {'name': 'Temp'}}
        profile_id = save_profile(user['id'], 'Temp Profile', profile_data)
        self.assertTrue(delete_profile(user['id'], profile_id))
        self.assertFalse(delete_profile(user['id'], profile_id))

    def test_save_and_get_resumes(self):
        user = self._create_user()
        resume_id = save_resume(user['id'], 'Google', 'JD text', 'jakes', 1, ats_score=75)
        self.assertIsInstance(resume_id, int)

        resumes = get_resumes(user['id'])
        self.assertEqual(len(resumes), 1)
        self.assertEqual(resumes[0]['company'], 'Google')
        self.assertEqual(resumes[0]['ats_score'], 75)

    def test_get_resume_with_profile(self):
        user = self._create_user()
        profile_data = {'basics': {'name': 'Test'}, 'skills': {'languages': ['Python']}}
        profile_id = save_profile(user['id'], 'Linked Profile', profile_data)
        resume_id = save_resume(user['id'], 'Meta', 'JD', 'classic', 1, profile_id=profile_id)

        resume = get_resume(user['id'], resume_id)
        self.assertIsNotNone(resume)
        self.assertEqual(resume['company'], 'Meta')
        self.assertEqual(resume['profile_data']['basics']['name'], 'Test')


class TestHashPassword(unittest.TestCase):
    def test_hash_is_deterministic_with_salt(self):
        pw_hash1, salt = _hash_password('secret')
        pw_hash2, _ = _hash_password('secret', salt)
        self.assertEqual(pw_hash1, pw_hash2)

    def test_different_passwords_different_hash(self):
        h1, _ = _hash_password('pass1')
        h2, _ = _hash_password('pass2')
        self.assertNotEqual(h1, h2)

    def test_different_salts_different_hash(self):
        h1, _ = _hash_password('same')
        h2, _ = _hash_password('same')
        self.assertNotEqual(h1, h2)


if __name__ == '__main__':
    unittest.main()
