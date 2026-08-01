def empty_profile() -> dict:
    return {
        "registered": True,
        "personal": {
            "photo": "", "name": "", "name_en": "", "name_cn": "", "address": "",
            "phone": "", "email": "", "emergency_phone": "", "emergency_relation": "",
        },
        "links": [], "educations": [], "languages": [], "awards": [], "certificates": [],
        "careers": [], "projects": [], "activities": [],
    }
