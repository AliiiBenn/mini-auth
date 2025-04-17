from setuptools import setup, find_packages

setup(
    name="mini-auth",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn>=0.24.0",
        "sqlalchemy>=2.0.23",
        "aiosqlite>=0.19.0",
        "alembic>=1.12.1",
        "python-jose>=3.3.0",
        "python-multipart>=0.0.6",
        "pydantic>=2.5.2",
        "pydantic-settings>=2.1.0",
        "python-dotenv>=1.0.0",
        "email_validator>=2.2.0",
        "passlib>=1.7.4",
        "bcrypt>=4.0.1"
    ],
    python_requires=">=3.8",
) 