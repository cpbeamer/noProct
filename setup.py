from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="QuestionAssistant",
    version="1.0.0",
    description="Automated Question Answering Assistant",
    author="QuestionAssistant Team",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "question-assistant=main:main",
        ],
    },
)