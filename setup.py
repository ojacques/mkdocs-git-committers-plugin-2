from setuptools import setup, find_packages
import pathlib

# The directory containing this file
here = pathlib.Path(__file__).parent.resolve()

# The text of the README file
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="mkdocs-git-committers-plugin-2",
    version="2.4.1",
    description="An MkDocs plugin to create a list of contributors on the page. The git-committers plugin will seed the template context with a list of GitHub or GitLab committers and other useful GIT info such as last modified date",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="mkdocs, plugin, github, committers",
    url="https://github.com/ojacques/mkdocs-git-committers-plugin-2/",
    author="Byrne Reese, Olivier Jacques",
    author_email="byrne@majordojo.com, ojacques2@gmail.com",
    license="MIT",
    python_requires=">=3.8,<4",
    install_requires=[
        "mkdocs>=1.0.3",
        "requests",
        "gitpython"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11"
    ],
    packages=find_packages(),
    entry_points={
        "mkdocs.plugins": [
            "git-committers = mkdocs_git_committers_plugin_2.plugin:GitCommittersPlugin"
        ]
    }
)
