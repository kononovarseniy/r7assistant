import setuptools

with open('README.md', 'r') as f:
    long_description = f.read()

setuptools.setup(
    name='r7assistant',
    version='0.0.1',
    author='Arseniy Kononov',
    author_email='a.kononov1@g.nsu.ru',
    description='A set of utilities for creating simple voice assistants',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/kononovarseniy/r7assistant",
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    install_requires=[
        'sounddevice',
        'pocketsphinx',
        'pyjsgf'
    ],
    python_requires='>=3.7',
)
