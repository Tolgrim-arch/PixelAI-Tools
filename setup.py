"""Include the single-source procedural library in built distributions."""

from pathlib import Path
import shutil

from setuptools import setup
from setuptools.command.build_py import build_py


class BuildWithLibrary(build_py):
    def run(self):
        super().run()
        source = Path(__file__).parent / "library"
        target = Path(self.build_lib) / "pixelai" / "library"
        shutil.copytree(source, target, dirs_exist_ok=True)


setup(cmdclass={"build_py": BuildWithLibrary})
