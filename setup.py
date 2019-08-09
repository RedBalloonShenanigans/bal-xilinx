from setuptools import setup

setup(
    name='bal-xilinx',
    version='0.1',
    description='An implementation of the BAL framework for Xilinx FPGAs',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Red Balloon Security',
    author_email='quack-tech@redballoonsecurity.com',
    packages=[
        'bal_xilinx',
        'bal_xilinx.analyzers',
        'bal_xilinx.converters',
        'bal_xilinx.modifiers',
        'bal_xilinx.tools'
    ],
    include_package_data=True,
    install_requires=[
        'bal',
        'six',
        'typing;python_version<"3.5"'
    ],
    extras_requires={
        'docs': ['sphinx', 'sphinx-rtd', 'm2r'],
        'examples': ['wget'],
        'tests': ['pytest']
    },
)
