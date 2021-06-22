from setuptools import setup

setup(
        name='gpufan',
        version="0.0.1",
        py_modules=['gpufan'],
        entry_points={
            'console_scripts': ['gpufan = gpufan:main']
            },
        )
