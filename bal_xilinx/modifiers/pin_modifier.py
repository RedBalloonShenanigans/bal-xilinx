from bal.context_ioc import AbstractModifier
from bal_xilinx.context import XilinxContext
from bal_xilinx.data_model import XilinxFdriPayload


class XilinxPinModifer(AbstractModifier):
    """
    An analyzer used to modify an FDRI IOB pin config.

    :param XilinxContext context: The configured xilinx context
    """

    def __init__(self, context):
        super(XilinxPinModifer, self).__init__(context)
        self.context = context

    def modify(self, pin_name, on, **kwargs):
        """
        Modify an FDRI IOB pin config.

        :param str pin_name: The name of the pin to modify.
        :param bool on: If True, the pin will be pulled high. Otherwise it will be pulled low.
        :param Any kwargs:
        """
        if self.context.id_code is None:
            raise ValueError(
                "The ID code for the targeted device has not been set on the bitstream context."
            )
        io_pin_format = self.context.format.get_fdri_format(self.context.id_code)\
            .get_io_pin_by_name(pin_name)

        if io_pin_format is None:
            raise ValueError("No format information for the IO pin {}".format(pin_name))

        if on is True:
            io_pin_value = io_pin_format.on_value
        else:
            io_pin_value = io_pin_format.off_value

        if io_pin_value is None:
            raise ValueError("No value configured for pin {}, on={}".format(pin_name, on))

        fdri_packets = self.context.get_data().unpack()\
            .get_packets_by_register_name("Fdri")
        if len(fdri_packets) != 1:
            raise ValueError("A single Fdri register packet is expected in the bitstream")
        fdri_packet = fdri_packets[0]
        fdri_packet_payload = fdri_packet.get_payload().unpack()
        assert isinstance(fdri_packet_payload, XilinxFdriPayload)
        io_block_object = fdri_packet_payload.get_io_block()
        io_block_bytes = io_block_object.get_bytes()
        if io_pin_format.offset + len(io_pin_value) > len(io_block_bytes):
            raise ValueError(
                "Invalid format definition for IO pin {}. The last byte would "
                "be written at offset {} but the IO block data size is only {}".format(
                    pin_name,
                    hex(io_pin_format.offset + len(io_pin_value) - 1),
                    len(io_block_bytes)
                )
            )
        io_block_object.set_bytes(
            io_block_bytes[:io_pin_format.offset] + \
                io_pin_value + \
                io_block_bytes[io_pin_format.offset + len(io_pin_value):]
        )
