from setuptools import setup, find_packages
from pathlib import Path

with (Path(__file__).parent / "whereisit" / "__version__.py").open() as version_file:
    exec(version_file.read())  # pylint: disable=W0122

install_requires = [
    "aiohttp",
    "uvloop",
    "toml",
    "pony",
]

setup(name="whereisit",
      classifiers=[
          "Programming Language :: Python :: 3.5",
      ],
      description="Track Israel Post packages",
      license="GPL3",
      author="Dror Levin",
      author_email="spatz@psybear.com",
      url="",
      version=__version__,  # pylint: disable=E0602
      packages=find_packages(exclude=["tests"]),
      install_requires=install_requires,
      entry_points=dict(
          console_scripts=[
              "whereisit = whereisit.main:main",
          ]
      ),
)
