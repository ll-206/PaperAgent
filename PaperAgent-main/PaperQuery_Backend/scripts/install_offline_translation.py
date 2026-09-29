"""One-time setup for the offline English -> Chinese Argos language package.

Run with the backend virtual environment while online. The translation endpoint
uses only the installed local package and never fetches data on a request.
"""

import argostranslate.package
import argostranslate.translate


def main():
    languages = {lang.code: lang for lang in argostranslate.translate.get_installed_languages()}
    if "en" in languages and "zh" in languages and languages["en"].get_translation(languages["zh"]):
        print("Offline en->zh package is already installed")
        return
    argostranslate.package.update_package_index()
    package = next(
        (item for item in argostranslate.package.get_available_packages()
         if item.from_code == "en" and item.to_code == "zh"),
        None,
    )
    if package is None:
        raise RuntimeError("Argos package index has no en->zh model")
    argostranslate.package.install_from_path(package.download())
    print("Offline en->zh package installed")


if __name__ == "__main__":
    main()
