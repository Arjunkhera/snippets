from setuptools import setup, find_packages

setup(
    name="akhera-ai-tools",
    version="0.1.0",
    description="AI tooling utilities",
    author="Arjun Khera",
    author_email="arjunkhera@gmail.com",
    packages=find_packages(),
    install_requires=[
        "pypdf>=4.0.0,<5.0.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
) 