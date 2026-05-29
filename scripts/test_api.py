import requests
import time

BASE_URL = 'http://localhost:8000'

print('Testing Login...')
login_data = {'username': 'testuser', 'password': 'TestPassword123!'}
r = requests.post(f'{BASE_URL}/auth/login', data=login_data)
token = r.json().get('access_token')

headers = {'Authorization': f'Bearer {token}'}
payload = {
    'resume_text': 'Software Engineer with 3 years of React experience.',
    'job_description': 'Frontend Developer with React.',
    'industry': 'Software'
}
r = requests.post(f'{BASE_URL}/resume/rewrite', json=payload, headers=headers)
data = r.json()
print(f'Rewrite successful! Session ID: {data.get("session_id")}')

session_id = data.get("session_id")

print(f'Testing PDF Export for session {session_id}...')
r_pdf = requests.post(f'{BASE_URL}/resume/export/{session_id}', headers=headers)
if r_pdf.status_code == 200:
    print('PDF Export successful! Saving to test_output.pdf')
    with open('test_output.pdf', 'wb') as f:
        f.write(r_pdf.content)
else:
    print(f'PDF Export failed: {r_pdf.status_code} - {r_pdf.text}')
