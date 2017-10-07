#!/usr/bin/env python3

from setuptools import setup

setup(name='levelorm',
		version='0.2',
		description='python3.6+ ORM for leveldb using plyvel',
		url='http://github.com/raylu/levelorm',
		author='raylu',
		author_email='raylu@users.noreply.github.com',
		packages=['levelorm'],
		python_requires='>=3.6', # https://docs.python.org/3/reference/datamodel.html#object.__init_subclass__
		install_requires=[
			'plyvel',
		],
		test_suite='tests',
		zip_safe=True)
