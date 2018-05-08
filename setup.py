#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='melange',
      version='3.1.3',
      description='A messaging library for an easy inter-communication in distributed and microservices architectures',
      url='https://github.com/Rydra/melange',
      author='David Jiménez (Rydra)',
      author_email='davigetto@gmail.com',
      license='MIT',
      keywords='microservices bus aws rabbitmq distributed architecture messaging',
      packages=find_packages(),
      classifiers=[
            'Development Status :: 3 - Alpha',
            'Programming Language :: Python'
      ],
      install_requires=[
        "boto3",
        "pika",
        "marshmallow",
        "pyopenssl",
      ],
      setup_requires=['pytest-runner'],
      tests_require=['pytest'],
      include_package_data=True,
      dependency_links=[
          'https://github.com/Rydra/redis-simple-cache/archive/master.tar.gz#egg=redis-simple-cache-0'],
      zip_safe=False)
