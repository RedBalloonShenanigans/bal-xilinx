from bal.context_ioc import AbstractAnalyzer
from bal_xilinx.context import XilinxContext


class XilinxDeviceAnalyzer(AbstractAnalyzer):
    """
    An analyzer used to retrieve the device type from a Xilinx bitstream.

    :param XilinxContext context: The configured xilinx context
    """
    def __init__(self, context):
        super(XilinxDeviceAnalyzer, self).__init__(context)
        self.context = context

    def analyze(self, **kwargs):
        """
        Returns the device name and it's int representation in the bitstream
        :rtype: str
        """
        if self.context.id_code is not None:
            return self.context.id_code
        config_packets = self.context.get_data().unpack()\
            .get_packets_by_register_name("Idcode")
        if len(config_packets) != 1:
            raise ValueError("A single Idcode register packet is expected in the bitstream")
        config_packet = config_packets[0]
        config_payload_object = config_packet.get_payload()
        config_payload = config_payload_object.unpack()
        id_code_value = config_payload.get("idcode").unpack()
        self.context.id_code = id_code_value.value_name
        return self.context.id_code


