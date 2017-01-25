"""Setup script for VWS Python, a wrapper for Vuforia's Web Services APIs."""

from setuptools import find_packages, setup

# We use requirements.txt instead of just declaring the requirements here
# because this helps with Docker package caching.
with open("requirements.txt") as requirements:
    install_requires = requirements.readlines()

# We use dev-requirements.txt instead of just declaring the requirements here
# because Read The Docs needs a requirements file.
with open("dev-requirements.txt") as dev_requirements:
    dev_requires = dev_requirements.readlines()

with open('README.md') as f:
    long_description = f.read()

setup(
    name="VWS Python",
    version="0.1",
    author="Adam Dangoor",
    author_email='adamdangoor@gmail.com',
    description="Interact with the Vuforia Web Services (VWS) API.",
    long_description=long_description,
    license='MIT',
    packages=find_packages(
        where='src', exclude='common'
    ),
    zip_safe=False,
    url='http://vws-python.readthedocs.io',
    keywords='vuforia mock fake client',
    package_dir={'': 'src'},
    install_requires=install_requires,
    extras_require={"dev": dev_requires, },
    classifiers=[
        'Operating System :: POSIX',
        'Environment :: Web Environment',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
    ],
)
