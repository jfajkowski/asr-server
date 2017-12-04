from setuptools import setup, find_packages


with open('README.md') as f:
    readme_content = f.read()

with open('LICENSE') as f:
    license_content = f.read()

setup(
    name='asr-server',
    version='0.1.0',
    description='Flask ASR server',
    long_description=readme_content,
    author='Jakub Fajkowski',
    author_email='jakub.fajkowski@gmail.com',
    url='https://github.com/jfajkowski/asr-server',
    license=license_content,
    packages=find_packages(exclude='tests')
)
