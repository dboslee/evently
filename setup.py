from setuptools import setup, find_packages

setup(
    name='evently',
    version=__import__('evently').__version__,
    description='evently, a lightweight event bus.',
    author='David Boslee',
    author_email='dboslee@gmail.com',
    url='http://github.com/dboslee/evently/',
    packages=find_packages(),
    package_data={
        'evently': [
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)
