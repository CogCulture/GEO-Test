import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Store in the backend root directory for visibility
USAGE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tool_usage_db.json")

def load_usage() -> Dict[str, Any]:
    if os.path.exists(USAGE_FILE):
        try:
            with open(USAGE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading usage file: {e}")
            return {}
    return {}

def save_usage(data: Dict[str, Any]):
    try:
        with open(USAGE_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving usage file: {e}")

def check_llms_txt_limit(user_id: str) -> bool:
    usage = load_usage()
    user_usage = usage.get(str(user_id), {})
    llms_count = user_usage.get("llms_txt", 0)
    return llms_count < 2

def increment_llms_txt_usage(user_id: str):
    usage = load_usage()
    uid = str(user_id)
    if uid not in usage:
        usage[uid] = {}
    usage[uid]["llms_txt"] = usage[uid].get("llms_txt", 0) + 1
    save_usage(usage)

def check_seo_skill_limit(user_id: str, skill: str) -> bool:
    usage = load_usage()
    user_usage = usage.get(str(user_id), {})
    skills_usage = user_usage.get("seo_skills", {})
    return skills_usage.get(skill, 0) < 1

def increment_seo_skill_usage(user_id: str, skill: str):
    usage = load_usage()
    uid = str(user_id)
    if uid not in usage:
        usage[uid] = {}
    if "seo_skills" not in usage[uid]:
        usage[uid]["seo_skills"] = {}
    
    usage[uid]["seo_skills"][skill] = usage[uid]["seo_skills"].get(skill, 0) + 1
    save_usage(usage)

def get_user_tool_usage(user_id: str) -> Dict[str, Any]:
    usage = load_usage()
    user_usage = usage.get(str(user_id), {})
    return {
        "llms_txt": user_usage.get("llms_txt", 0),
        "seo_skills": user_usage.get("seo_skills", {}),
        "limits": {
            "llms_txt": 2,
            "seo_skill_per_skill": 1
        }
    }
