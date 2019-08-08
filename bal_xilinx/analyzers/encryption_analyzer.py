from bal_xilinx.analyzers.device_analyzer import XilinxDeviceAnalyzer
from bal_xilinx.context import XilinxContext


class XilinxEncryptionAnalyzer(XilinxDeviceAnalyzer):
    """
    An analyzer used to determine if a Xilinx bitstream it encrypted.

    :param XilinxContext context: The configured xilinx context
    """
    def __init__(self, context):
        super(XilinxDeviceAnalyzer, self).__init__(context)
        self.context = context

    def analyze(self):
        """
        Returns true if the bitstream is encrypted.

        :rtype: bool
        """
        config_packets = self.context.get_data().unpack()\
            .get_packets_by_register_name("Ctl")
        for config_packet in config_packets:
            decryption = config_packet.get_payload().unpack()\
                .get("dec").unpack()
            if decryption.get_value() == 1:
                return True
        return False
