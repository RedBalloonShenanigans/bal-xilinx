import ctypes
import io
import struct

import six
from typing import Tuple

from bal.context_ioc import AbstractConverter
from bal.data_model import ValueModel
from bal.data_object import DataObject
from bal_xilinx.converters import WORD_SIZE
from bal_xilinx.data_model import XilinxPacket, XilinxPackets, \
    XilinxPacketHeader, XilinxType1Payload, XilinxType2PayloadInterface, \
    XilinxFdriPayload, XilinxPacketsTail
from bal_xilinx.format import XilinxRegisterFormat


class XilinxCtypePacketBigEndianHeaderBase(ctypes.BigEndianStructure):
    word_count = 0
    register_address = 0
    opcode = 0
    type = 0

    _pack_ = 1
    _fields_ = [
        # In a type 2 packet word_count is unused
        ("type", ctypes.c_uint32, 3),
        ("opcode", ctypes.c_uint32, 2),
        ("register_address", ctypes.c_uint32, 6),
        ("word_count", ctypes.c_uint32, 5),
    ]


class XilinxCtypeLittleEndianPacketHeaderBits(ctypes.LittleEndianStructure):
    word_count = 0
    register_address = 0
    opcode = 0
    type = 0

    _pack_ = 1
    _fields_ = [
        # In a type 2 packet word_count is unused
        ("word_count", ctypes.c_uint32, 5),
        ("register_address", ctypes.c_uint32, 6),
        ("opcode", ctypes.c_uint32, 2),
        ("type", ctypes.c_uint32, 3),
    ]


class XilinxCtypeLittleEndianPacketHeader(ctypes.Union):
    _fields_ = [
        ("bits", XilinxCtypeLittleEndianPacketHeaderBits),
        ("binary_data", ctypes.c_uint16)
    ]

    def __init__(self, val):
        self.binary_data = struct.unpack(">H", val)[0]


class XilinxCtypePacketHeader(object):
    def __init__(self, type=0, opcode=0, register_address=0, word_count=0):
        self.type = type
        self.opcode = opcode
        self.register_address = register_address
        self.word_count = word_count

    def get_bytes(self):
        # type: () -> bytes
        if six.PY3:
            return \
                bytes(
                    bytearray(
                        XilinxCtypePacketBigEndianHeaderBase(
                            self.type,
                            self.opcode,
                            self.register_address,
                            self.word_count
                        )
                    )
                )
        elif six.PY2:
            header = XilinxCtypeLittleEndianPacketHeaderBits(
                self.word_count,
                self.register_address,
                self.opcode,
                self.type
            )
            out_of_order_bytes = bytes(bytearray(header))
            return b"".join([out_of_order_bytes[1], out_of_order_bytes[0], out_of_order_bytes[2:]])
        else:
            raise NotImplementedError

    @staticmethod
    def from_buffer_copy(raw_bytes):
        # type: (bytes) -> XilinxCtypePacketHeader
        if six.PY3:
            header = XilinxCtypePacketBigEndianHeaderBase.from_buffer_copy(raw_bytes)
            return XilinxCtypePacketHeader(
                header.type,
                header.opcode,
                header.register_address,
                header.word_count
            )
        elif six.PY2:
            header = XilinxCtypeLittleEndianPacketHeader(raw_bytes[:2])
            return XilinxCtypePacketHeader(
                header.bits.type,
                header.bits.opcode,
                header.bits.register_address,
                header.bits.word_count
            )
        else:
            raise NotImplementedError


class TypeValue(ValueModel):
    pass


class OpCodeValue(ValueModel):
    pass


class RegisterAddressValue(ValueModel):
    pass


class WordCountValue(ValueModel):
    pass


class XilinxPacketsConverter(AbstractConverter):
    """
    Unpacker for a Xilinx FPGA bitstream

    :param XilinxContext context: A factory used to create data objects/converters.
    :ivar XilinxContext context: A factory used to create data objects/converters.
    """
    def __init__(self, context):
        super(XilinxPacketsConverter, self).__init__(context)
        self.context = context

    def _get_register_format(self, header):
        """
        :param XilinxCtypePacketHeader header:
        :rtype: XilinxRegisterFormat
        """
        register_format = self.context.format.get_register_format(header.register_address)
        # Corner case for a the FAR_MAJ register
        if register_format is not None and register_format.name == "FarMaj" and \
                header.word_count > 1:
            register_format = self.context.format.get_register_format_by_name("FarMajExtended")
        # Verify that we know how to parse the config for the register
        if register_format is None:
            raise ValueError(
                "No register format found for address {}".format(hex(header.register_address))
            )
        return register_format

    def _create_type1_payload(self, data_stream, header, register_format):
        """
        Unpack the payload for a type 1 packet

        :param io.BytesIO data_stream:
        :param XilinxCtypePacketHeader header:
        :param XilinxRegisterFormat register_format:
        :rtype: Tuple[DataObject, bool]
        """
        if header.word_count == 0:
            return None, False
        payload_data = data_stream.read(header.word_count * WORD_SIZE)
        if header.opcode == 0:
            raise ValueError("NOOP Xilinx packets are expected to have a 0 length payload")

        payload = DataObject.create_packed(
            self.context,
            payload_data,
            XilinxType1Payload,
            converter_args=(register_format, ),
        )
        if register_format.name == "Cmd":
            return payload, payload.unpack().get("command").get_model().value_name == "DESYNC"

        return payload, False

    def _create_type2_payload(self, data_stream, header):
        """
        Unpack the payload for a type 2 packet
        :param io.BytesIO data_stream:
        :param XilinxCtypePacketHeader header:
        :rtype: Tuple[DataObject,DataObject]
        """
        register_format = self._get_register_format(header)
        word_count_data = data_stream.read(4)
        word_count, = struct.unpack(">I", word_count_data)
        payload_size_object = DataObject.create_unpacked(
            self.context,
            WordCountValue(word_count),
            bytes=word_count_data
        )
        payload_data = data_stream.read((word_count + 2) * WORD_SIZE)
        # TODO: Remove this hack for the LX45T, it's got 2 FDRI packets, one is waaaaay too small.
        if register_format.name != "Fdri" or len(payload_data) < 500:
            return payload_size_object, DataObject.create_packed(
                self.context,
                payload_data,
                XilinxType2PayloadInterface,
                converter_args=(register_format,)
            )

        return payload_size_object, DataObject.create_packed(
            self.context,
            payload_data,
            XilinxFdriPayload
        )

    def _get_type_name(self, type):
        """
        Get the name for the type value
        :param int type:
        :rtype: str
        """
        if type == 0:
            return "NOOP"
        elif type == 1:
            return "Type1"
        elif type == 2:
            return "Type2"
        else:
            raise ValueError(
                "Unexpected header type {} while parsing the Xilinx config packets".format(type)
            )

    def _get_opcode_name(self, opcode):
        """
        Get the name for the opcode value
        :param int opcode:
        :rtype: str
        """
        if opcode == 0:
            return "NOOP"
        elif opcode == 1:
            return "READ"
        elif opcode == 2:
            return "WRITE"
        else:
            raise ValueError(
                "Unexpected header opcode {} while parsing the Xilinx config packets".format(opcode)
            )

    def unpack(self, data_bytes):
        """
        :param bytes data_bytes:
        :rtype: XilinxPackets
        """
        packets = []
        data_stream = io.BytesIO(data_bytes)
        previous_packet_type = 0
        while data_stream.tell() < len(data_bytes):
            header_raw_data = data_stream.read(2)
            header = XilinxCtypePacketHeader.from_buffer_copy(
                bytearray([
                    header_raw_data[0],
                    header_raw_data[1],
                    0,
                    0
                ])
            )
            is_done = False
            register_format = self._get_register_format(header)
            if header.type == 0:
                payload_object = None
                payload_size_object = None
            elif header.type == 1:
                payload_object, is_done = self._create_type1_payload(
                    data_stream,
                    header,
                    register_format
                )
                payload_size_object = None
            elif header.type == 2:
                if previous_packet_type != 1:
                    raise ValueError(
                        "Unexpected packet type 2 after a packet type {}".format(
                            previous_packet_type
                        )
                    )
                payload_size_object, payload_object = self._create_type2_payload(
                    data_stream,
                    header
                )
            else:
                raise ValueError(
                    "Unexpected packet type {} while parsing the Xilinx bitstream".format(
                        header.type
                    )
                )
            previous_packet_type = header.type
            raw_packet_data = header_raw_data
            if payload_size_object is not None:
                raw_packet_data += payload_size_object.get_bytes()
            if payload_object is not None:
                raw_packet_data += payload_object.get_bytes()

            header_object = DataObject.create_unpacked(
                self.context,
                model=XilinxPacketHeader(
                    DataObject.create_unpacked(
                        self.context,
                        TypeValue(int(header.type), self._get_type_name(header.type)),
                        3,
                    ),
                    DataObject.create_unpacked(
                        self.context,
                        OpCodeValue(int(header.opcode), self._get_opcode_name(header.opcode)),
                        2,
                    ),
                    DataObject.create_unpacked(
                        self.context,
                        RegisterAddressValue(int(header.register_address), register_format.name),
                        6,
                    ),
                    DataObject.create_unpacked(
                        self.context,
                        WordCountValue(int(header.word_count)),
                        5,
                    ),
                ),
                bytes=header_raw_data,
            )
            packets.append(DataObject.create_unpacked(
                self.context,
                model=XilinxPacket(
                    header_object,
                    payload_size_object,
                    payload_object,
                ),
                bytes=raw_packet_data,
            ))
            if is_done is True:
                packets.append(DataObject.create_packed(
                    self.context,
                    data_stream.read(),
                    XilinxPacketsTail,
                ))
                break
        return XilinxPackets(packets)

    def pack(self, packets):
        """
        :param XilinxPackets packets:
        :rtype: bytes
        """
        assert isinstance(packets, XilinxPackets)
        parts = []
        for packet_object in packets:
            if not packet_object.is_unpacked():
                parts.append(packet_object.get_bytes())
                continue
            packet = packet_object.get_model()
            header = packet.get_header().get_model()
            packet_type = header.get_packet_type().get_model().get_value()
            register_address = header.get_register_address().get_model().get_value()
            opcode = header.get_opcode().get_model().get_value()

            payload = packet.get_payload()
            payload_raw = payload.pack() if payload is not None else b""
            if packet_type == 0 or packet_type == 1:
                header = XilinxCtypePacketHeader(
                    packet_type,
                    opcode,
                    register_address,
                    int(len(payload_raw) / WORD_SIZE),
                )
                header_raw = header.get_bytes()
                parts.append(header_raw[:2])
                if opcode != 0:
                    register_format = self._get_register_format(header)
                    assert register_format.size == len(payload_raw), \
                        "The payload size ({}) does not match the expected payload size ({}) for " \
                        "register {}".format(
                            len(payload_raw),
                            register_format.size,
                            register_format.name
                        )
                    parts.append(payload_raw)
            elif packet_type == 2:
                header = XilinxCtypePacketHeader(
                    packet_type,
                    opcode,
                    register_address,
                    0,
                )
                header_raw = header.get_bytes()
                parts.append(header_raw[:2])
                parts.append(struct.pack(">I", int(len(payload_raw) / WORD_SIZE) - 2))
                parts.append(payload_raw)
        return b"".join(parts)


