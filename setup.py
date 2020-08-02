import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="greenletio",
    version="0.0.4",
    author="Miguel Grinberg",
    author_email="miguel.grinberg@gmail.com",
    description="Asyncio integration with sync code using greenlets.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/miguelgrinberg/greenletio",
    packages=setuptools.find_packages(),
    install_requires=[
        'greenlet'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
