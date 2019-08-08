import pytest
import six

from bal_xilinx.converters.bitstream_packets import XilinxCtypePacketHeader


class XilinxCtypePacketHeaderTestCase:
    def __init__(self, raw_bytes, type_arg, opcode, register_address, word_count):
        # type: (bytes, int, int, int int) -> None
        self.raw_bytes = raw_bytes
        self.type = type_arg
        self.opcode = opcode
        self.register_address = register_address
        self.word_count = word_count


XILINX_CTYPE_PACKET_HEADER_TEST_CASES = [
    XilinxCtypePacketHeaderTestCase(
        six.b("\x30\xa1\x00\x00"),
        1,
        2,
        5,
        1
    )
]


@pytest.mark.parametrize("test_case", XILINX_CTYPE_PACKET_HEADER_TEST_CASES)
def test_xilinx_ctype_packet_header_from_buffer_copy(test_case):
    # type: (XilinxCtypePacketHeaderTestCase) -> None
    header = XilinxCtypePacketHeader.from_buffer_copy(test_case.raw_bytes)
    # assert header.get_bytes() == test_case.raw_bytes
    assert header.type == test_case.type
    assert header.opcode == test_case.opcode
    assert header.register_address == test_case.register_address
    assert header.word_count == test_case.word_count


@pytest.mark.parametrize("test_case", XILINX_CTYPE_PACKET_HEADER_TEST_CASES)
def test_xilinx_ctype_packet_header_(test_case):
    # type: (XilinxCtypePacketHeaderTestCase) -> None
    header = XilinxCtypePacketHeader(
        test_case.type,
        test_case.opcode,
        test_case.register_address,
        test_case.word_count
    )
    assert header.get_bytes() == test_case.raw_bytes
    assert header.type == test_case.type
    assert header.opcode == test_case.opcode
    assert header.register_address == test_case.register_address
    assert header.word_count == test_case.word_count
