from setuptools import setup, find_packages


setup(
    name='mkdocs-git-committers-plugin-2',
    version='1.0.2',
    description='An MkDocs plugin to create a list of contributors on the page',
    long_description='The git-committers plugin will seed the template context with a list of github committers and other useful GIT info such as last modified date',
    keywords='mkdocs pdf github',
    url='https://github.com/ojacques/mkdocs-git-committers-plugin-2/',
    author='Byrne Reese, Olivier Jacques',
    author_email='byrne@majordojo.com, ojacques2@gmail.com',
    license='MIT',
    python_requires='>=2.7',
    install_requires=[
        'mkdocs>=1.0.3',
        'gitpython',
        'requests',
        'beautifulsoup4'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ],
    packages=find_packages(),
    entry_points={
        'mkdocs.plugins': [
            'git-committers = mkdocs_git_committers_plugin_2.plugin:GitCommittersPlugin'
        ]
    }
)
