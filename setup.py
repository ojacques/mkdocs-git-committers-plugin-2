from pathlib import Path
from typing import Union

from setuptools import setup, find_packages

# The directory containing this file
HERE = Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

def load_requirements(requirements_files: Union[Path, list[Path]]) -> list:
    """Helper to load requirements list from a path or a list of paths.

    Args:
        requirements_files (Path | list[Path]): path or list to paths of requirements
            file(s)

    Returns:
        list: list of requirements loaded from file(s)
    """
    out_requirements = []

    if isinstance(requirements_files, Path):
        requirements_files = [
            requirements_files,
        ]

    for requirements_file in requirements_files:
        with requirements_file.open(encoding="UTF-8") as f:
            out_requirements += [
                line
                for line in f.read().splitlines()
                if not line.startswith(("#", "-")) and len(line)
            ]

    return out_requirements

setup(
    name='mkdocs-git-committers-plugin-2',
    version='1.2.0',
    description='An MkDocs plugin to create a list of contributors on the page. The git-committers plugin will seed the template context with a list of github committers and other useful GIT info such as last modified date',
    long_description=README,
    long_description_content_type="text/markdown",
    keywords='mkdocs pdf github',
    url='https://github.com/ojacques/mkdocs-git-committers-plugin-2/',
    author='Byrne Reese, Olivier Jacques',
    author_email='byrne@majordojo.com, ojacques2@gmail.com',
    license='MIT',
    python_requires='>=3.8,<4',
    install_requires=load_requirements(HERE / "requirements.txt"),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11'
    ],
    packages=find_packages(),
    entry_points={
        'mkdocs.plugins': [
            'git-committers = mkdocs_git_committers_plugin_2.plugin:GitCommittersPlugin'
        ]
    }
)
