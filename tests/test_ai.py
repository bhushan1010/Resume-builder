import os
import sys
import yaml
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.ai_engine import generate_tailored_profile

def test():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               'config', 'base_profile.yaml')
    with open(config_path, "r", encoding="utf-8") as f:
        base_profile_dict = yaml.safe_load(f)
        
    print("Testing generate_tailored_profile...")
    try:
        res = generate_tailored_profile(base_profile_dict, "Software Engineer", "Google")
        print("Success!")
        print(res['skills'])
    except Exception as e:
        print("Error!")
        print(e)
        
if __name__ == "__main__":
    test()
