from setuptools import setup, find_packages

try:
    with open('README.md', 'r', encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = 'A tool to analyze CSS class usage in HTML, PHP and JS files'

setup(
    name='css-analyzer',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[],
    entry_points={
        'console_scripts': [
            'css-analyzer=css_analyzer.cli:main',
        ],
    },
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "coverage>=7.0.0",
        ],
    },
    author='Chase Parks',
    author_email='chase.parks94@gmail.com',
    description='A tool to analyze CSS class usage in HTML, PHP and JS files',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/chasepants/css-analyzer',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)