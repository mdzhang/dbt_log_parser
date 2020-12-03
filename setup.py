import sys
from pathlib import Path  # noqa E402

from setuptools import setup

CURRENT_DIR = Path(__file__).parent
sys.path.insert(0, str(CURRENT_DIR))  # for setuptools.build_meta


def get_long_description() -> str:
    return (
        (CURRENT_DIR / "README.md").read_text(encoding="utf8")
        + "\n\n"
        + (CURRENT_DIR / "CHANGELOG.md").read_text(encoding="utf8")
    )


setup(
    name="dbt_log_parser",
    use_scm_version={
        "write_to": "src/_dbt_log_parser_version.py",
        "write_to_template": 'version = "{version}"\n',
    },
    description="Parse structured metadata from dbt logs",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    keywords="dbt",
    author="Michelle Zhang",
    author_email="zhang.michelle.d@gmail.com",
    url="https://github.com/mdzhang/dbt_log_parser",
    project_urls={
        "Changelog": (
            "https://github.com/mdzhang/dbt_log_parser/blob/master/CHANGELOG.md"
        )
    },
    license="MIT",
    py_modules=["_dbt_log_parser_version"],
    packages=["dbt_log_parser"],
    package_dir={"": "src"},
    python_requires=">=3.6",
    zip_safe=True,
    install_requires=[
        "transitions>=0.8.5",
    ],
    extras_require={},
    test_suite="tests",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3 :: Only",
    ],
    entry_points={
        "console_scripts": [
            "dbtlp=dbt_log_parser:main",
        ]
    },
)
