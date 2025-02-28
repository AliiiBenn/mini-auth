from setuptools import setup, find_packages

setup(
    name="mini-auth",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "sqlalchemy>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.3.0",
            "isort>=5.10.1",
            "flake8>=4.0.1",
        ],
    },
    python_requires=">=3.7",
    author="David",
    author_email="",
    description="A minimalist authentication library for Python applications",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    keywords="authentication, security, jwt, auth",
    url="https://github.com/david/mini-auth",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
) 