# coding: utf-8

import os

from setuptools import setup, find_packages

version = '0.0.1'

with open(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'requirements.txt')) as f:
    requirements = [i.strip() for i in f.readlines() if i]

entry_points = {
    "console_scripts": [
        'pic_web_http = src.http_server:run',
    ]
}

setup(name='pic_web',
      version=version,
      description="pic_web",
      long_description_content_type='text/markdown',
      classifiers=[
          'Programming Language :: Python',
      ],
      package_data={
          "": ['*']
      },
      include_package_data=True,
      packages=find_packages(exclude=['tests', ]),
      zip_safe=False,
      entry_points=entry_points,
      install_requires=requirements,
      )
