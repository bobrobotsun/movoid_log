from setuptools import setup, find_packages

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()

setup(
    name='movoid_log',
    version='1.2.5',
    packages=find_packages(),
    url='',
    license='',
    author='movoid',
    author_email='bobrobotsun@163.com',
    description='create log',
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        'movoid_function',
        'movoid_timer',
    ],
)
