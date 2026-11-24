from services.gemini_service import GeminiService

def test_build_system_prompt_levels_and_modes():
    gemini = GeminiService(api_key="dummy_key", model_name="gemini-2.5-flash")

    # Beginner A1 user, strict mode
    user_a1 = {
        "name": "Aziz",
        "level": "A1",
        "goal": "Travel",
        "correction_mode": "strict"
    }
    prompt_a1 = gemini.build_system_prompt(user_a1, trigger_exercise=True)
    assert "Aziz" in prompt_a1
    assert "A1" in prompt_a1
    assert "Travel" in prompt_a1
    assert "Strict Mode" in prompt_a1
    assert "Mini-challenge" in prompt_a1

    # Advanced C1 user, relax mode
    user_c1 = {
        "name": "Malika",
        "level": "C1",
        "goal": "Work & Career",
        "correction_mode": "relax"
    }
    prompt_c1 = gemini.build_system_prompt(user_c1, trigger_exercise=False)
    assert "Malika" in prompt_c1
    assert "C1" in prompt_c1
    assert "Work & Career" in prompt_c1
    assert "Relaxed Mode" in prompt_c1
    assert "Mini-challenge" not in prompt_c1

