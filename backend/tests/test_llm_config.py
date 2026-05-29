from app.core.config import LlmProvider, Settings


def test_default_models_gemini_planner_groq_judge() -> None:
    s = Settings(
        gemini_api_key="",
        groq_api_key="",
        planner_model="",
        judge_model="",
    )
    assert s.resolved_planner_llm_provider() == LlmProvider.gemini
    assert s.resolved_judge_llm_provider() == LlmProvider.groq
    assert s.resolved_planner_model() == "gemini-2.5-flash"
    assert s.resolved_judge_model() == "llama-3.3-70b-versatile"


def test_custom_model_overrides() -> None:
    s = Settings(
        planner_model="gemini-2.0-flash",
        judge_model="llama-3.1-8b-instant",
    )
    assert s.resolved_planner_model() == "gemini-2.0-flash"
    assert s.resolved_judge_model() == "llama-3.1-8b-instant"
