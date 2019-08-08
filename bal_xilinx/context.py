from bal.data_object import DataObject
from bal.context import BALContextFactory, BALContext
from bal_xilinx.data_model import XilinxBitstream
from bal_xilinx.format import XilinxFormat


class XilinxContext(BALContext):
    """
    See the documentation of :py:class:`~bal.context.BALContext` for an overview of the
    purpose of the context class. In addition, the :py:class:`XilinxContext` stores a reference
    to a :py:class:`~bal_xilinx.format.XilinxFormat` instance that defines the format of a
    Xilinx bitstream.

    :param Dict[Type[ConverterInterface],Type[AbstractConverter]] converters_by_type: The converter
        interfaces mapped to their implementation.
    :param Dict[Type[AnalyzerInterface],Type[AbstractAnalyzer]] analyzers_by_type: The analyzer
        interfaces mapped to their implementation.
    :param Dict[Type[ModifierInterface],Type[AbstractModifier]] modifiers_by_type: The modifier
        interfaces mapped to their implementation.
    :param XilinxFormat bitstream_format: The Xilinx bitstream format configuration.
    :param bytes bytes: The bytes making up the bitstream.
    """
    def __init__(
            self,
            converters_by_type,
            analyzers_by_type,
            modifiers_by_type,
            bitstream_format,
            bytes
    ):
        super(XilinxContext, self).__init__(
            converters_by_type,
            analyzers_by_type,
            modifiers_by_type
        )
        self.id_code = None
        self.format = bitstream_format
        self._bitstream = DataObject.create_packed(self, bytes, XilinxBitstream)

    def get_data(self):
        """
        Get the data object wrapping the bitstream. The returned object starts out packed but may
        be modified by user call.

        :rtype: DataObject[XilinxBitstream]
        """
        return self._bitstream


class XilinxContextFactory(BALContextFactory):
    """
    See the documentation of :py:class:`~bal.context.BALContextFactory` for an overview of the
    purpose of the context factory class. In addition, the :py:class:`XilinxContextFactory` stores
    a reference to a :py:class:`~bal_xilinx.format.XilinxFormat` instance that defines the
    format of a Xilinx bitstream.

    :param XilinxFormat bitstream_format: The Xilinx bitstream format configuration.
    """
    def __init__(self, bitstream_format):
        super(XilinxContextFactory, self).__init__()
        self._format = bitstream_format

    def create(self, data):
        """
        Create an Xilinx FPGA context from the provided bytes.

        :param bytes bytes: The bytes for the Xilinx FPGA bitstream
        :rtype: XilinxContext
        """
        return XilinxContext(
            self._converters_by_type,
            self._analyzers_by_type,
            self._modifiers_by_type,
            self._format,
            data
        )

