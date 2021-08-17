from setuptools import setup

setup(
    name='cryptocompare-py',
    version='0.0.9',
    description='Wrapper for CryptoCompare.com',
    url='https://github.com/Raytlty/cryptocompare-py',
    author='Raytlty',
    author_email='alexmao930918@gmail.com',
    keywords='crypto cryptocurrency wrapper cryptocompare',
    license='MIT',
    python_requires='>=3',
    packages=['cryptocompare'],
    classifiers=['Programming Language :: Python :: 3'],
    install_requires=['requests']
)
