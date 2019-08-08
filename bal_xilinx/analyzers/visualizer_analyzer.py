import base64

from bal.analyzers.visualizer_analyzer import VisualizerAnalyzer
from bal_xilinx.context import XilinxContext


class XilinxVisualizerAnalyzer(VisualizerAnalyzer):
    """
    Generate nested native objects (ie can be fed to serialization libraries) that are used by
    the visualizer to display the data within the provided data object.

    :param XilinxContext context: The configured xilinx context
    """
    def __init__(self, context):
        super(XilinxVisualizerAnalyzer, self).__init__(context)
        self.context = context

    def analyze(self):
        """
        Build a visualizer config object for the bitstream.
        :rtype: Dict[str, Any]
        """
        bitstream = self.context.get_data()
        bitstream.synchronize()
        bitstream_data = bitstream.pack()
        return {
            "style": self.context.format.visualizer_style,
            "data": self._traverse(bitstream),
            "bytes": base64.b64encode(bitstream_data).decode('ascii')
        }


