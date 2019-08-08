"""
This file showcase how an external developer can add a new converter. The same logic
can be applied to modifiers and analyzers.
"""
import wget
from bal.context_ioc import AbstractConverter
from bal.data_model import ClassModel, DataModel
from bal.data_object import DataObject
from bal_xilinx.context import XilinxContextFactory
from bal_xilinx.converters.bitstream_packets import XilinxPacketsConverter
from bal_xilinx.data_model import XilinxBitstreamHeaderInterface, XilinxPackets
from bal_xilinx.defaults import default_xilinx_context, default_xilinx_formats
from bal_xilinx.format import XilinxFormatBuilder


class CustomXilinxHeaderPart1Interface(DataModel):
    """
    We're not sure what goes into part1
    """


class CustomXilinxHeaderPart2Interface(DataModel):
    """
    We're not sure what goes into part2
    """


class CustomXilinxHeaderModel(ClassModel[DataObject], XilinxBitstreamHeaderInterface):
    """
    A custom model for the xilinx header.
    """
    def __init__(self, part1, part2):
        super(CustomXilinxHeaderModel, self).__init__({
            "part1": self.get_part1,
            "part2": self.get_part2
        })
        self.parts1 = part1
        self.parts2 = part2

    def get_part1(self):
        return self.parts1

    def get_part2(self):
        return self.parts2


class CustomXilinxHeaderConverter(AbstractConverter):
    def __init__(self, context):
        super(CustomXilinxHeaderConverter, self).__init__(context)
        self.context = context

    def unpack(self, data_bytes):
        """
        :param bytes data_bytes:
        :rtype: CustomXilinxHeaderModel
        """
        assert len(data_bytes) == 16, \
            "The header data is expected to contain 16 bytes"

        return CustomXilinxHeaderModel(
            DataObject.create_packed(
                self.context,
                data_bytes[:4],
                CustomXilinxHeaderPart1Interface
            ),
            DataObject.create_packed(
                self.context,
                data_bytes[4:16],
                CustomXilinxHeaderPart2Interface,
            ),
        )

    def pack(self, data_model):
        """
        :param CustomXilinxHeaderModel data_model:
        :rtype: bytes
        """
        assert isinstance(data_model, CustomXilinxHeaderModel)
        return b"".join([
            data_model.get_part1().pack(),
            data_model.get_part2().pack()
        ])


class CustomXilinxPacketsConverter(XilinxPacketsConverter):
    def _create_type2_payload(self, data_stream, header):
        print("Creating type2 payload!")
        return super(CustomXilinxPacketsConverter, self)._create_type2_payload(
            data_stream,
            header,
        )


# Configure the default converters
xilinx_context_factory = default_xilinx_context(XilinxContextFactory(
    # Register the formats for the LX9 and LX45T
    default_xilinx_formats(XilinxFormatBuilder()).build()
))
# Register our new converter
xilinx_context_factory.register_converter(
    XilinxBitstreamHeaderInterface,
    CustomXilinxHeaderConverter
)
# Override the existing converter
xilinx_context_factory.register_converter(
    XilinxPackets,
    CustomXilinxPacketsConverter
)

lx9_bin = wget.download('https://redballoonsecurity.com/files/JwfEU4veQSNFao8h/lx9.bin')
with open(lx9_bin, "rb") as f:
    data = f.read()

bitstream_context = xilinx_context_factory.create(data)
bitstream_object = bitstream_context.get_data()

# In order to index the packets, the bitstream model unpacks them.
# Therefore our custom converter is called and you should see a bunch of "Creating type2
# payload!" messages in the console.
header_object = bitstream_object.unpack().get_header()

# At this point our custom unpacker for the header hasn't been hit yet. We'll get all the info
# that the base interface provided.
print("Header type: {}".format(header_object.get_model_type()))
print("Header implementation: {}".format(header_object.get_model_implementation()))
print("Header description: {}".format(header_object.get_model_description()))

print("\nUnpacking the header\n")
header_model = header_object.unpack()

# Now our custom unpacker has been hit and the header model should be an instance of
# CustomXilinxHeaderModel
assert isinstance(header_model, CustomXilinxHeaderModel), \
    "Expected the header_model to be an instance of CustomXilinxHeaderModel"

# Now we should get all the info provided by the custom header model.
print("Header type: {}".format(header_object.get_model_type()))
print("Header implementation: {}".format(header_object.get_model_implementation()))
print("Header description: {}".format(header_object.get_model_description()))

# The part1 and part2 data objects should be available but packed
print("Header part 1: {}".format(header_model.get_part1()))
print("Header part 2: {}".format(header_model.get_part2()))

