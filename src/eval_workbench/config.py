from pydantic import BaseModel


class AppConfig(BaseModel):
    model_panel: list[str] = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gpt-4o-mini",
        "gpt-4o",
        "claude-3-haiku-20240307",
        "claude-3-5-sonnet-20240620",
    ]

    default_judge_model: str = "gemini-2.5-flash"


config = AppConfig()


def get_config() -> AppConfig:
    return config
