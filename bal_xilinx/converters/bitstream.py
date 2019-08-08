from bal.context_ioc import AbstractConverter
from bal.data_object import DataObject
from bal_xilinx.converters import WORD_SIZE
from bal_xilinx.data_model import XilinxBitstream, XilinxBitstreamHeaderInterface, \
    XilinxPackets, XilinxBitstreamSyncMarker


class XilinxBitstreamConverter(AbstractConverter):
    """
    Converter for a Xilinx FPGA bitstream

    :param XilinxContext context: A context used to create data objects/converters.
    """

    def __init__(self, context):
        super(XilinxBitstreamConverter, self).__init__(context)
        self.context = context

    def unpack(self, data_bytes):
        """
        :param bytes data_bytes:
        :rtype: XilinxBitstream
        """
        sync_marker = self.context.format.sync_word
        sync_marker_index = data_bytes.find(sync_marker)
        assert sync_marker_index >= 0, \
            "The sync marker is not present in the provided bitstream data"

        assert sync_marker_index + len(sync_marker) < len(data_bytes) - WORD_SIZE, \
            "The configuration data is expected to contain at least one word size worth of data"

        return XilinxBitstream(
            DataObject.create_packed(
                self.context,
                data_bytes[:sync_marker_index],
                XilinxBitstreamHeaderInterface
            ),
            DataObject.create_packed(
                self.context,
                data_bytes[sync_marker_index:sync_marker_index+len(sync_marker)],
                XilinxBitstreamSyncMarker,
            ),
            DataObject.create_packed(
                self.context,
                data_bytes[sync_marker_index + len(sync_marker):],
                XilinxPackets,
            )
        )

    def pack(self, data_model):
        """
        :param XilinxBitstream data_model:
        :rtype: bytes
        """
        assert isinstance(data_model, XilinxBitstream)
        return b"".join([
            data_model.get_header().pack(),
            self.context.format.sync_word,
            data_model.get_packets().pack()
        ])
