# BAL Xilinx Overview

The BAL Xilinx package is an implementation of the 
[Binary Abstraction Layer (BAL)](https://github.com/ballon-rouge/bal) framework for Xilinx FPGA.
It supports packing/unpacking of most of the bitstream, target device/encryption detection and 
pin modification (force the pin high/low).
It is supposed to be a dependency of a project, not a boilerplate project to be customized.
It was first introduced at Black Hat 2019, [here](https://www.usenix.org/conference/woot19/presentation/kataria) 
is a link to the presentation.

The full api documentation is available [here](https://RedBalloonShenanigans.github.io/bal-xilinx/).

## Contributors:


 - Jatin Kataria (Researcher)
 - Rick Housley (Researcher)
 - Alex Massonneau (Developer)
 - Andrew O'Brien (Developer)

## Installation

The  BAL Xilinx package requires the BAL package. 
See the [installation instructions](https://github.com/ballon-rouge/bal).
To install the BAL Xilinx package, run:

```
git clone https://github.com/RedBalloonShenanigans/bal-xilinx.git
cd bal-xilinx
pip install .
```

To generate the documentation, run:
```
pip install .[docs]
make html-docs
```

## Methodology

The Xilinx converters rely heavily on format definitions contained in [./configs](./configs). 
The methodology used to create these JSON files will be published shortly. 

## Guide

This guide assumes familiarity with the [BAL framework](https://github.com/ballon-rouge/bal).
As the name of the project implies, this is an implementation of it for Xilinx FPGA bitstreams.
Complete examples are available under [./example](./example).

### Analyzers

There are 3 analyzers available:

 - `bal_xilinx.analyzers.device_analyzer.XilinxDeviceAnalyzer` Determines the type of device 
 targeted by the bitstream.
 - `bal_xilinx.analyzers.encryption_analyzer.XilinxEncryptionAnalyzer` Determines if the FDRI 
 packets are encrypted.
 - `bal_xilinx.analyzers.visualizer_analyzer.XilinxVisualizerAnalyzer` Generate the configuration
  data for the [BAL visualizer](https://github.com/ballon-rouge/bal-visualizer/).
  
### Modifiers

There is currently a single analyzer:

- `bal_xilinx.modifiers.pin_modifier.XilinxPinModifer` Force a pin to be low/high regardless of 
the logic executed by the FPGA.

### Examples

Here is an example that puts together all the analyzers and modifiers available.

```python
# Configure the default converters
xilinx_context_factory = default_xilinx_context(XilinxContextFactory(
    # Register the formats for the LX9 and LX45T
    default_xilinx_formats(XilinxFormatBuilder()).build()
))

lx9_bin = wget.download('https://redballoonsecurity.com/files/JwfEU4veQSNFao8h/lx9.bin')
with open(lx9_bin, "rb") as f:
    data = f.read()
    
bitstream_context = xilinx_context_factory.create(data)

# Get the device type targeted by the bitstream
device_type = bitstream_context.create_analyzer(XilinxDeviceAnalyzer)\
    .analyze()
print("Device info: {}".format(device_type))

# Determine if the FDRI packets are encrypted.
is_encrypted = bitstream_context.create_analyzer(XilinxEncryptionAnalyzer)\
    .analyze()
print("Is encrypted: {}".format(is_encrypted))

# Unpack the entire bitstream to make sure the visualization includes everything
bitstream_context.get_data().unpack_all()

print("Writing the visualizer config to {}".format(os.path.abspath("data.json")))
with open("data.json", "w") as f:
    # Generate the visualization config file
    visualizer_config = bitstream_context.create_analyzer(VisualizerAnalyzer) \
        .analyze()
    json.dump(visualizer_config,  f)

print("Pulling the pins low")
pin_modifier = bitstream_context.create_modifier(XilinxPinModifer)
for pin in ["P134", "P133", "P132", "P131", "P127", "P126", "P124", "P123"]:
    pin_modifier.modify(pin, False)


print("Analysis and modifications done!")

```

That is it for the guide. Have fun!


