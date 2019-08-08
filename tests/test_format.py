import ctypes

import pytest
import six

from bal_xilinx.format import XilinxRegisterFormatCtype


class XilinxRegisterFormatCtypeTestCase:
    def __init__(self, name, raw_bytes, fields, values):
        self.name = name
        self.raw_bytes = raw_bytes
        self.fields = fields
        self.values = values


XILINX_REGISTER_FORMAT_CTYPE_TEST_CASES = [
    XilinxRegisterFormatCtypeTestCase(
        u'Cor1',
        six.b("\x3d\x18\x00\x00"),
        [
            (u'drive_awake', ctypes.c_uint32, 1),
            (u'reserved', ctypes.c_uint32, 10),
            (u'crc_bypass', ctypes.c_uint32, 1),
            (u'done_pipe', ctypes.c_uint32, 1),
            (u'drive_done', ctypes.c_uint32, 1),
            (u'ssclksrc', ctypes.c_uint32, 2)
        ],
        [0, 488, 1, 1, 0, 0]
    ),
    XilinxRegisterFormatCtypeTestCase(
        u'Cclkfreq',
        six.b("\x3c\xc8\x00\x00"),
        [
            (u'reserved1', ctypes.c_uint32, 1),
            (u'ext_0mclk', ctypes.c_uint32, 1),
            (u'reserved', ctypes.c_uint32, 4),
            (u'mclk_freq', ctypes.c_uint32, 10),
        ],
        [0, 0, 15, 200]
    ),
    XilinxRegisterFormatCtypeTestCase(
        u'Idcode',
        six.b("\x04\x00\x10\x93"),
        [
            (u'idcode', ctypes.c_uint32, 32)
        ],
        [67113107]
    ),
]


def construct_ctype_class(name, fields):
    return type(str(name), (ctypes.BigEndianStructure,), {
        "_pack_": 1,
        "_fields_": fields
    })


@pytest.mark.parametrize("test_case", XILINX_REGISTER_FORMAT_CTYPE_TEST_CASES)
def test_xilinx_register_format_ctype_class(test_case):
    """
    Test the the XilinxRegisterFormat.ctype class that is created performs as expected.

    This test is needed because of discrepencies between the python2 and python3 versions of
    ~ctypes.BigEngianStructure.
    """
    ctype_class = XilinxRegisterFormatCtype(test_case.name, test_case.fields)
    attributes_values = ctype_class.get_bytes(*test_case.values)
    assert attributes_values == test_case.raw_bytes

    # for value, field in zip(values, fields):
    #     attribute, _, _ = field
    #     assert cor_1.__getattribute__(attribute) == value


@pytest.mark.parametrize("test_case", XILINX_REGISTER_FORMAT_CTYPE_TEST_CASES)
def test_xilinx_register_format_ctype_class_from_buffer_copy(test_case):
    class_definition = XilinxRegisterFormatCtype(test_case.name, test_case.fields)
    xilinx_register_format_ctype = class_definition.from_buffer_copy(test_case.raw_bytes)
    import ipdb; ipdb.set_trace()
    assert xilinx_register_format_ctype.values == test_case.values
