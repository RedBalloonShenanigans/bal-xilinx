from setuptools import setup

setup(
    name="bal-xilinx",
    version="0.1",
    description="The xilinx implementation for the FPGA bitstream analysis framework",
    packages=[
        "bal_xilinx",
        "bal_xilinx.analyzers",
        "bal_xilinx.converters",
        "bal_xilinx.modifiers",
        "bal_xilinx.tools"
    ],
    install_requires=[
        "bal",
        "six",
        "typing"
    ],
    extras_requires={
      'docs': ["sphinx", "sphinx-rtd", "m2r"]
    }
)
