from setuptools import setup, Command

import os
import glob
import shutil


class CleanCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        for folder in ['build', 'dist']:
            if os.path.exists(folder):
                shutil.rmtree(folder)
        for egg_file in glob.glob('*egg-info'):
            shutil.rmtree(egg_file)


setup(
    name='py-awe',
    version='1.0.0',
    author='Stefan Maetschke',
    author_email='stefan.maetschke@gmail.com',
    description='A simple workflow engine',
    install_requires=['dpath'],
    packages=['pyawe'],
    cmdclass={
        'clean': CleanCommand,
    },
)
