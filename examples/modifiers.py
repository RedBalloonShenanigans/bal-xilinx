"""
This file shows an example of how to use the modifiers defined in the bal_xilinx package.
"""
import wget
from bal_xilinx.analyzers.device_analyzer import XilinxDeviceAnalyzer
from bal_xilinx.context import XilinxContextFactory
from bal_xilinx.defaults import default_xilinx_context, default_xilinx_formats
from bal_xilinx.format import XilinxFormatBuilder
from bal_xilinx.modifiers.pin_modifier import XilinxPinModifer

# Configure the default converters
xilinx_context_factory = default_xilinx_context(XilinxContextFactory(
    # Register the formats for the LX9 and LX45T
    default_xilinx_formats(XilinxFormatBuilder()).build()
))

lx9_bin = wget.download('https://redballoonsecurity.com/files/JwfEU4veQSNFao8h/lx9.bin')
with open(lx9_bin, "rb") as f:
    data = f.read()

bitstream_context = xilinx_context_factory.create(data)

# The pin modifier requires that the device analyzer has been run.
device_type = bitstream_context.create_analyzer(XilinxDeviceAnalyzer)\
    .analyze()

print("Pulling the pins low")
pin_modifier = bitstream_context.create_modifier(XilinxPinModifer)
for pin in ["P134", "P133", "P132", "P131", "P127", "P126", "P124", "P123"]:
    pin_modifier.modify(pin, False)

print("Packing the bitstream")
# Update the tree so that the modification state of all nodes match that of its descendant.
bitstream_context.get_data().synchronize()
# Repack the parts of the bitstream that have changed.
packed_data = bitstream_context.get_data().pack()
assert packed_data != data, "The packed data should have changed."

print("Done!")
