"""
This file shows an example of how to use the analyzers defined in the bal_xilinx package.
"""
import json
import os
import wget

from bal.analyzers.visualizer_analyzer import VisualizerAnalyzer
from bal_xilinx.analyzers.device_analyzer import XilinxDeviceAnalyzer
from bal_xilinx.analyzers.encryption_analyzer import XilinxEncryptionAnalyzer
from bal_xilinx.context import XilinxContextFactory
from bal_xilinx.defaults import default_xilinx_context, default_xilinx_formats
from bal_xilinx.format import XilinxFormatBuilder

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

with open("data.json", "w") as f:
    # Generate the visualization config file
    visualizer_config = bitstream_context.create_analyzer(VisualizerAnalyzer) \
        .analyze()
    json.dump(visualizer_config,  f)
    print("Wrote the config to {}".format(os.path.abspath("data.json")))


