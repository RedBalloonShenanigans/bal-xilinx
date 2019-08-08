from abc import ABCMeta
from typing import List

import six

from bal.data_object import DataObject
from bal.data_model import ClassModel, ValueModel, DictModel, ArrayModel, DataModel


class XilinxFdriLogicFrame(DataModel):
    """
    A single frame of the major of the logic block of an FDRI payload.
    """


class XilinxFdriLogicMajor(ArrayModel[DataObject[XilinxFdriLogicFrame]]):
    """
    A single major of the logic block of an FDRI payload.
    """


class XilinxFdriLogicRow(ArrayModel[DataObject[XilinxFdriLogicMajor]]):
    """
    A single row of the logic block of an FDRI payload.
    """


class XilinxFdriLogicBlock(ArrayModel[DataObject[XilinxFdriLogicRow]]):
    """
    The logic block of an FDRI payload.
    """


class XilinxFdriRAMBlockInterface(DataModel):
    """
    The RAM block of an FDRI payload.
    """


class XilinxFdriIOBlockInterface(DataModel):
    """
    The IO block of an FDRI payload.
    """


class XilinxFdriCRCInterface(DataModel):
    """
    The CRC tail of an FDRI payload.
    """


class XilinxType2PayloadInterface(DataModel):
    """
    The payload of a type 2 packet in the Xilinx bitstream.
    """


class XilinxFdriPayload(XilinxType2PayloadInterface, ClassModel[DataObject]):
    """
    The payload of a type 2 FDRI packet in the Xilinx bitstream. It contains configuration for
    logic blocks, ram blocks, and io blocks. It also contains a checksum of the blocks config in
    the tail.
    """

    def __init__(self, logic_block, bram_block, iob_block, crc):
        super(XilinxFdriPayload, self).__init__((
            ("logic_block", self.get_logic_block),
            ("ram_block", self.get_ram_block),
            ("io_block", self.get_io_block),
            ("tail", self.get_crc),
        ))
        self._logic_block = logic_block
        self._bram_block = bram_block
        self._iob_block = iob_block
        self._crc = crc

    def get_logic_block(self):
        """
        Get the data object for the logic block of the FDRI payload.

        :rtype: DataObject[XilinxFdriLogicBlock]
        """
        return self._logic_block

    def get_ram_block(self):
        """
        Get the data object for the RAM block of the FDRI payload.

        :rtype: XilinxFdriRAMBlockInterface
        """
        return self._bram_block

    def get_io_block(self):
        """
        Get the data object for the IO block of the FDRI payload.

        :rtype: XilinxFdriIOBlockInterface
        """
        return self._iob_block

    def get_crc(self):
        """
        Get the data object for the CRC tail of the FDRI payload.
        :rtype: XilinxFdriCRCInterface
        """
        return self._crc

    def set_logic_block(self, logic_block):
        self._synced = False
        self._logic_block = logic_block
        return self

    def set_ram_block(self, bram_block):
        self._synced = False
        self._bram_block = bram_block
        return self

    def set_io_block(self, iob_block):
        self._synced = False
        self._iob_block = iob_block
        return self

    def set_tail(self, tail):
        self._synced = False
        self._crc = tail
        return self


class XilinxType1PayloadAttribute(ValueModel):
    """
    An attibute of the payload of a type 1 packet in the Xilinx bitstream. It is parsed
    automatically using the Xilinx format configuration.
    """


class XilinxType1Payload(DictModel[DataObject[XilinxType1PayloadAttribute]]):
    """
    The payload of a type 1 packet in the Xilinx bitstream. It is parsed automatically from using
    the Xilinx format configuration. It's properties are not known until it is unpacked.
    """


class XilinxPacketHeader(ClassModel[DataObject]):
    """
    The header of a Xilinx register configuration packet. It contains the type of the packet (1
    or 2), the opcode (READ/WRITE/NOOP), the register address and the number of words in the
    payload.
    """

    def __init__(self, packet_type, opcode, register_address, word_count):
        super(XilinxPacketHeader, self).__init__((
            ("type", self.get_packet_type),
            ("opcode", self.get_opcode),
            ("register_address", self.get_register_address),
            ("word_count", self.get_word_count),
        ))
        self._type = packet_type
        self._opcode = opcode
        self._register_address = register_address
        self._word_count = word_count

    def get_packet_type(self):
        """
        :rtype: DataObject[ValueModel]
        """
        return self._type

    def get_opcode(self):
        """
        :rtype: DataObject[ValueModel]
        """
        return self._opcode

    def get_register_address(self):
        """
        :rtype: DataObject[ValueModel]
        """
        return self._register_address

    def get_word_count(self):
        """
        :rtype: DataObject[ValueModel]
        """
        return self._word_count

    def set_packet_type(self, packet_type):
        self._synced = False
        self._type = packet_type
        return self

    def set_opcode(self, opcode):
        self._synced = False
        self._opcode = opcode
        return self

    def set_register_address(self, register_address):
        self._synced = False
        self._register_address = register_address
        return self

    def set_word_count(self, word_count):
        self._synced = False
        self._word_count = word_count
        return self


class XilinxPacket(ClassModel[DataObject]):
    """
    A packet within a Xilinx bitstream. It contains a header and a payload.
    """

    def __init__(
            self,
            header,
            payload_size,
            payload,
    ):
        self._header = header
        self._payload_size = payload_size
        self._payload = payload
        super(XilinxPacket, self).__init__((
            ("header", self.get_header),
            ("payload_size", self.get_payload_size),
            ("payload", self.get_payload)
        ))

    def get_header(self):
        """
        :rtype: DataObject[XilinxPacketHeader]
        """
        return self._header

    def get_payload_size(self):
        """
        :rtype: DataObject[ValueModel]
        """
        return self._payload_size

    def get_payload(self):
        """
        :rtype: DataObject
        """
        return self._payload

    def set_header(self, header):
        self._synced = False
        self._header = header
        return self

    def set_payload(self, payload):
        self._synced = False
        self._payload = payload
        return self


class XilinxPacketsTail(DataModel):
    """
    The tail data for the packets. It cannot be detected by the XilinxBitstreamConverter so it
    must be handled as any other packet.
    """
    pass


class XilinxPackets(ArrayModel[DataObject[XilinxPacket]]):
    """
    An array of Xilinx register configuration packet.
    """

    def __init__(self, items):
        super(XilinxPackets, self).__init__(items)


class XilinxBitstreamHeaderInterface(DataModel):
    """
    The Xilinx bitstream header contains unknown information.
    """


class  XilinxBitstreamSyncMarker(DataModel):
    """
    The Xilinx bitstream sync marker
    """


class XilinxBitstream(ClassModel[DataObject]):
    """
    The root model for a Xilinx bitstream. It contains a header and packets data objects.
    """

    def __init__(
            self,
            header,
            sync_marker,
            packets
    ):
        """
        :param DataObject[XilinxBitstreamHeaderInterface] header:
        :param DataObject[XilinxBitstreamSyncMarker] sync_marker:
        :param DataObject[XilinxPackets] packets:
        """
        super(XilinxBitstream, self).__init__((
            ("header", self.get_header),
            ("sync_marker", self.get_sync_marker),
            ("packets", self.get_packets),
        ))
        self._header = header
        self._sync_marker = sync_marker
        self._packets = packets
        self._packets_by_register = {}
        for packet_object in self._packets.unpack():
            if not packet_object.is_unpacked() and not packet_object.is_convertible():
                continue
            packet = packet_object.unpack()
            register_name = packet.get_header().unpack()\
                .get_register_address().unpack()\
                .value_name
            register_packets = self._packets_by_register.get(register_name)
            if register_packets is None:
                register_packets = []
                self._packets_by_register[register_name] = register_packets
            register_packets.append(packet)

    def get_header(self):
        """
        :rtype: DataObject[XilinxBitstreamHeaderInterface]
        """
        return self._header

    def get_sync_marker(self):
        """
        :rtype: DataObject[XilinxBitstreamSyncMarker]
        """
        return self._sync_marker

    def get_packets(self):
        """
        :rtype: DataObject[XilinxPackets]
        """
        return self._packets

    def get_packets_by_register_name(self, register):
        """
        :param str register:
        :rtype: List[XilinxPacket]
        """
        return self._packets_by_register.get(register) or tuple()

    def set_header(self, header):
        """
        :param DataObject header:
        """
        self._synced = False
        self._header = header
        return self

    def set_packets(self, packets):
        self._synced = False
        self._packets = packets
        return self
