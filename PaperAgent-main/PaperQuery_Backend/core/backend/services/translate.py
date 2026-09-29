
"""Offline English-to-Chinese translation for selected PDF passages."""

from functools import lru_cache


@lru_cache(maxsize=1)
def _english_to_chinese():
    import argostranslate.translate

    languages = {lang.code: lang for lang in argostranslate.translate.get_installed_languages()}
    if "en" not in languages or "zh" not in languages:
        raise RuntimeError("离线英中翻译模型未安装，请运行 scripts/install_offline_translation.py")
    translation = languages["en"].get_translation(languages["zh"])
    if translation is None:
        raise RuntimeError("离线英中翻译模型未安装，请运行 scripts/install_offline_translation.py")
    return translation


class Translator:
    def __init__(self, from_lang="en", to_lang="zh"):
        if (from_lang, to_lang) != ("en", "zh"):
            raise ValueError("目前仅支持离线英文翻译为简体中文")

    def translate(self, text: str) -> str:
        source = " ".join(text.split())
        return _english_to_chinese().translate(source) if source else ""
