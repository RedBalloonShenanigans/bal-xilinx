import ctypes
import json
import struct
from collections import OrderedDict

from typing import List

import six


def hex_to_bytes(hex):
    """
    Convert a hex value to the bytes representation used by the interpreter.

    :param str hex:
    :rtype: bytes
    """
    if six.PY2:
        return hex.decode("hex")
    else:
        return bytes.fromhex(hex)


class XilinxAttributeValueDocumentation:
    """
    Defines the documentation for a specific value of a register attribute.

    :param int value: The attribute's value.
    :param Optional[str] name: The  name for the value of the attribute.
    :param Optional[None] description: The description for the value of the attribute.

    :ivar int value: The attribute's value.
    :ivar Optional[str] name: The  name for the value of the attribute.
    :ivar Optional[None] description: The description for the value of the attribute.
    """
    def __init__(
            self,
            value,
            name,
            description
    ):
        self.value = value
        self.name = name
        self.description = description


class XilinxRegisterAttributeFormat:
    """
    Defines the format/documentation of a register payload attribute.

    :param str name: The name of the attribute.
    :param int bit_size: The size of the attribute value in bits.
    :param str description: A description of the attribute.
    :param List[XilinxAttributeValueDocumentation] values: The documentation for values
        of the attribute.

    :ivar str name: The name of the attribute.
    :ivar int bit_size: The size of the attribute value in bits.
    :ivar str description: A description of the attribute.
    """
    def __init__(
        self,
        name,
        bit_size,
        description,
        values,
    ):
        self.name = name
        self.bit_size = bit_size
        self.description = description
        self._value_config_by_value = {c.value: c for c in values}

    def get_value_documentation(self, value):
        """
        Get the documentation for the provided value of the attribute

        :param int value: The value of the register attribute
        :rtype: Optional[XilinxAttributeValueDocumentation]
        """
        return self._value_config_by_value.get(value)


class XilinxRegisterFormatCtypeLE(ctypes.Union):
    _fields_ = []

    def __init__(self, raw_bytes):
        if len(raw_bytes) == 2:
            struct_flag = ">H"
        elif len(raw_bytes) == 4:
            struct_flag = ">I"
        else:
            raise RuntimeError(
                "XilinxRegisterFormatCtypeLE currently only supports 2 and 4 byte structures"
            )
        self.binary_data = struct.unpack(struct_flag, raw_bytes)[0]


class XilinxRegisterFormatCtype(object):
    def __init__(self, class_name, fields, values=None):
        self.class_name = class_name
        self.fields = fields
        self.values = values
        if six.PY2:
            bit_size = sum([bit_size for _, _, bit_size in fields])
            if bit_size <= 16:
                binary_data_type = ctypes.c_uint16
            elif bit_size == 32:
                binary_data_type = ctypes.c_uint32
            else:
                raise RuntimeError("XilinxRegisterFormatCtype bit size not supported")
            self.bits = type("{}Bits".format(str(class_name)), (ctypes.LittleEndianStructure, ), {
                "_pack_": 1,
                "_fields_": fields[::-1]
            })

            self.ctype = type(str(class_name), (XilinxRegisterFormatCtypeLE, ), {
                "_fields_": [
                    ("bits", self.bits),
                    ("binary_data", binary_data_type)
                ]
            })
        if six.PY3:
            self.ctype = type(str(class_name), (ctypes.BigEndianStructure, ), {
                "_pack_": 1,
                "_fields_": fields
            })

    def get_bytes(self, *values):
        # type: (*int) -> bytes

        if six.PY3:
            ctype_instance = self.ctype(*values)
            return bytearray(bytes(ctype_instance))
        elif six.PY2:
            reversed_values = values[::-1]
            ctype_instance = self.bits(*reversed_values)
            num_packed_bytes = sum([bit_size for _, _, bit_size in self.fields]) / 8
            out_of_order_bytes = bytes(bytearray(ctype_instance))
            bytes_to_reverse = out_of_order_bytes[:num_packed_bytes]
            reversed_bytes = b"".join(
                [byte_to_reverse for byte_to_reverse in bytes_to_reverse][::-1]
            )
            return b"".join([reversed_bytes, out_of_order_bytes[num_packed_bytes:]])
        else:
            raise RuntimeError

    def from_buffer_copy(self, raw_bytes):
        # type: (bytes) -> XilinxRegisterFormatCtype
        if six.PY3:
            ctype_instance = self.ctype.from_buffer_copy(raw_bytes)
            values = []
            for field_name, _, _ in self.fields:
                values.append(ctype_instance.__getattribute__(field_name))
        elif six.PY2:
            num_packed_bytes = sum([bit_size for _, _, bit_size in self.fields]) / 8
            ctype_instance = self.ctype(raw_bytes[:num_packed_bytes])
            values = []
            for field_name, _, _ in self.fields:
                values.append(ctype_instance.bits.__getattribute__(field_name))
        else:
            raise RuntimeError
        return XilinxRegisterFormatCtype(self.class_name, self.fields, values)


class XilinxRegisterFormat:
    """
    Defines the format/documentation for a register packet.

    :param int address: The address of the register.
    :param str name: The name of the register targeted by a packet.
    :param str description: A description of the register.
    :param List[XilinxRegisterAttributeFormat] attributes: The attributes to parse in
        a packet's data.

    :ivar int address: The address of the register.
    :ivar str name: The name of the register targeted by a packet.
    :ivar str description: A description of the register.
    :ivar List[XilinxRegisterAttributeFormat] attributes: The attributes to parse in
        a packet's data.
    :ivar int size: Ths aggregate bit size of the register payload attributes.
    :ivar ctype ctype: A ctype class definition configured to match the register payload
        attributes.
    """
    def __init__(
        self,
        address,
        name,
        description,
        attributes,
    ):
        self.address = address
        self.name = name
        self.description = description
        self.attributes = attributes

        bit_size = sum([attr.bit_size for attr in self.attributes])
        if bit_size % 8 != 0:
            raise ValueError("The bit size of the register config should be a multiple of 8")
        self.size = int(bit_size / 8)

        class_name = "".join([p.title() for p in self.name.split("_")])
        fields = [
            (attr.name.lower(), ctypes.c_uint32, attr.bit_size)
            for attr in self.attributes
        ]
        self.ctype = XilinxRegisterFormatCtype(str(class_name), fields)


class XilinxFdriMajorFormat:
    """
    Defines the format for a specif major type.

    :param str name: The name of the major.
    :param int frame_size: The size of a frame within the major.
    :param int frame_count: The number of frames making up the major.
    :param List[str] frame_descriptions: A description of each frame. The length of the list is
        expected to match the `frame_count` property.

    :ivar str name: The name of the major.
    :ivar int frame_size: The size of a frame within the major.
    :ivar int frame_count: The number of frames making up the major.
    :ivar List[str] frame_descriptions: A description of each frame. The length of the list is
        expected to match the `frame_count` property.
    """
    def __init__(
            self,
            name,
            frame_size,
            frame_count,
            frame_descriptions
    ):
        self.name = name
        self.frame_size = frame_size
        self.frame_count = frame_count
        self.frame_descriptions = frame_descriptions


class XilinxFdriPinFormat:
    """
    Defines the format for a specif io pin.

    :param str name: The name of the pin.
    :param int offset: The offset of the pin.
    :param str on_value: The hex representation of the value to turn the pin on.
    :param str off_value: The hex representation of the value to turn the pin off.

    :ivar str name: The name of the pin.
    :ivar int offset: The offset of the pin.
    :ivar bytes on_value: The hex representation of the value to turn the pin on.
    :ivar bytes off_value: The hex representation of the value to turn the pin off
    """
    def __init__(
            self,
            name,
            offset,
            on_value,
            off_value
    ):
        self.name = name
        self.offset = offset
        self.on_value = hex_to_bytes(on_value)
        self.off_value = hex_to_bytes(off_value)


class XilinxFdriFormat:
    """
    Defines the format of an FDRI register payload for a specific type of FPGA.

    :param str device_name: The name of the FPGA.
    :param int logic_block_size: The size of the logic block in bytes.
    :param int ram_block_size: The size of the ram block in bytes.
    :param int io_block_size: The size of the io block in bytes.
    :param int crc_size: The size of the CRC checksum in bytes.
    :param Optional[List[List[XilinxFdriMajorFormat]]Optional[ logic_block_format: A matrix of Major
        formats that are contained in the logic block..
    :param Optional[List[XilinxFdriPinFormat]] io_block_format: A list of pin formats that are
        contained in the io block.

    :ivar str device_name: The name of the FPGA.
    :ivar int logic_block_size: The size of the logic block in bytes.
    :ivar int ram_block_size: The size of the ram block in bytes.
    :ivar int io_block_size: The size of the io block in bytes.
    :ivar int crc_size: The size of the CRC checksum in bytes.
    :ivar Optional[List[List[XilinxFdriMajorFormat]]Optional[ logic_block_format: A matrix of Major
        formats.
    """
    def __init__(
            self,
            device_name,
            logic_block_size,
            ram_block_size,
            io_block_size,
            crc_size,
            logic_block_format,
            io_block_format,
    ):
        self.device_name = device_name
        self.logic_block_size = logic_block_size
        self.bram_block_size = ram_block_size
        self.io_block_size = io_block_size
        self.crc_size = crc_size
        self.logic_block_format = logic_block_format
        if io_block_format is None:
            self._io_pin_by_name = {}
        else:
            self._io_pin_by_name = {pin.name: pin for pin in io_block_format}

    def get_io_pin_by_name(self, name):
        """
        Retrieve the IO pin format for the provided IO pin name.

        :param str name: The name of the IO pin
        :rtype: XilinxFdriPinFormat|None
        """
        return self._io_pin_by_name.get(name)


class XilinxFormat:
    """
    Defines the format of the registers in a Xilinx bitstream. It contains indexes to look up
    register formats by name or address.

    :param List[XilinxRegisterFormat] registers: The list of register formats.
    :param List[XilinxFdriFormat] fdri_formats: The list of FDRI packets formats targeting
        different types of FPGA.
    :param Any visualizer_style: The style config for the visualizer frontend.
    :param str sync_word: The sync word that marks the beginning of the configuration data in hex
        format.

    :ivar bytes sync_word: The sync word that marks the beginning of the configuration data.
    """
    def __init__(self, registers, fdri_formats, visualizer_style, sync_word="AA995566"):
        self._register_format_by_address = {c.address: c for c in registers}
        self._register_format_by_name = {c.name: c for c in registers}
        self._fdri_format_by_device = {c.device_name: c for c in fdri_formats}
        self.visualizer_style = visualizer_style
        self.sync_word = hex_to_bytes(sync_word)

    def get_fdri_format(self, device_name):
        """
        Lookup the FDRI format for the provided device name
        :param str device_name: The name of the device
        :rtype: XilinxFdriFormat | None
        """
        return self._fdri_format_by_device.get(device_name)

    def get_register_format(self, address):
        """
        Lookup a register format by its address
        :param int address: The register's address
        :rtype: XilinxRegisterFormat | None
        """
        return self._register_format_by_address.get(address)

    def get_register_format_by_name(self, name):
        """
        Lookup a register format by its name
        :param str name: The register's name
        :rtype: XilinxRegisterFormat | None
        """
        return self._register_format_by_name.get(name)


class XilinxFormatBuilder:
    def __init__(self):
        self._visualizer_config = None # type: Any
        self._register_formats = []  # type: List[Any]
        self._fdri_io_block_formats = []  # type: List[Any]
        self._fdri_logic_block_formats = []  # type: List[Any]
        self._fdri_major_formats = []  # type: List[Any]
        self._fdri_formats = []  # type: List[Any]

    def set_visualizer_config(self, visualizer_config):
        self._visualizer_config = visualizer_config

    def add_fdri_logic_block_formats(self, logic_block_formats):
        if not isinstance(logic_block_formats, list):
            raise ValueError("The FDRI logic blocks formats are expected to be a list")
        self._fdri_logic_block_formats.extend(logic_block_formats)

    def add_fdri_io_block_formats(self, io_block_formats):
        if not isinstance(io_block_formats, list):
            raise ValueError("The FDRI IO blocks formats are expected to be a list")
        self._fdri_io_block_formats.extend(io_block_formats)

    def add_register_formats(self, register_formats):
        if not isinstance(register_formats, list):
            raise ValueError("The register formats are expected to be a list")
        self._register_formats.extend(register_formats)

    def add_fdri_formats(self, fdri_formats):
        if not isinstance(fdri_formats, list):
            raise ValueError("The fdri formats are expected to be a list")
        self._fdri_formats.extend(fdri_formats)

    def add_fdri_major_formats(self, major_formats):
        if not isinstance(major_formats, list):
            raise ValueError("The fdri formats are expected to be a list")
        self._fdri_major_formats.extend(major_formats)

    def set_visualizer_config_json(self, path):
        with open(path, "r") as f:
            return self.set_visualizer_config(json.load(f))

    def add_fdri_logic_block_formats_json(self, path):
        with open(path, "r") as f:
            return self.add_fdri_logic_block_formats(json.load(f))

    def add_fdri_io_block_formats_json(self, path):
        with open(path, "r") as f:
            return self.add_fdri_io_block_formats(json.load(f))

    def add_register_formats_json(self, path):
        with open(path, "r") as f:
            return self.add_register_formats(json.load(f))

    def add_fdri_formats_json(self, path):
        with open(path, "r") as f:
            return self.add_fdri_formats(json.load(f))

    def add_fdri_major_formats_json(self, path):
        with open(path, "r") as f:
            return self.add_fdri_major_formats(json.load(f))

    def _create_register_attribute_value_format(self, value_format):
        if not isinstance(value_format, dict):
            raise ValueError("The register attribute value format is expected to be a dict")
        return XilinxAttributeValueDocumentation(
            value_format["value"],
            value_format["name"],
            value_format["description"],
        )

    def _create_register_attribute_format(self, attribute_format):
        if not isinstance(attribute_format, dict):
            raise ValueError("The register attribute format is expected to be a dict")

        return XilinxRegisterAttributeFormat(
            attribute_format["name"],
            attribute_format["bit_size"],
            attribute_format["description"],
            [
                self._create_register_attribute_value_format(value_format)
                for value_format in attribute_format["values"]
            ]
        )

    def _create_register_format(self, register_format):
        if not isinstance(register_format, dict):
            raise ValueError("The register format is expected to be a dict")
        if not isinstance(register_format["attributes"], list):
            raise ValueError("The register format attributes is expected to be a list")
        return XilinxRegisterFormat(
            register_format["address"],
            register_format["name"],
            register_format["description"],
            [
                self._create_register_attribute_format(attribute_format)
                for attribute_format in register_format["attributes"]
            ]
        )

    def _create_fdri_major_format(self, major_format):
        if not isinstance(major_format, dict):
            raise ValueError("The major format is expected to be a dict")
        return XilinxFdriMajorFormat(
            major_format["name"],
            major_format["frame_size"],
            major_format["frame_count"],
            major_format["frame_descriptions"],
        )

    def _create_fdri_logic_block_format(self, logic_block_format, fdri_major_formats_by_name):
        if not isinstance(logic_block_format, list):
            raise ValueError("The logic block format is expected to be a list")
        logic_block_format_obj = []
        for row_format in logic_block_format:
            if not isinstance(row_format, list):
                raise ValueError("The column format is expected to be a list")
            row_format_obj = []
            for major_name in row_format:
                if six.PY2:
                    expected_type = unicode
                elif six.PY3:
                    expected_type = str
                else:
                    raise RuntimeError
                if not isinstance(major_name, expected_type):
                    raise ValueError("The major name should be a string")
                if major_name not in fdri_major_formats_by_name:
                    raise ValueError("No major format named {}".format(major_name))
                row_format_obj.append(fdri_major_formats_by_name[major_name])
            logic_block_format_obj.append(row_format_obj)
        return logic_block_format_obj

    def _create_fdri_io_block_format(
            self,
            fdri_io_block_format,
    ):
        if fdri_io_block_format is None:
            return None
        if not isinstance(fdri_io_block_format, list):
            raise ValueError("The FDRI io block format is expected to be a dict")
        items = []
        for fdri_io_pin_format in fdri_io_block_format:
            items.append(XilinxFdriPinFormat(
                fdri_io_pin_format["pin_name"],
                fdri_io_pin_format["offset"],
                fdri_io_pin_format.get("on_value"),
                fdri_io_pin_format.get("off_value"),
            ))
        return items

    def _create_fdri_format(
            self,
            fdri_format,
            fdri_logic_block_format,
            fdri_io_block_format,
            fdri_major_formats_by_name,
    ):
        if not isinstance(fdri_format, dict):
            raise ValueError("The fdri format is expected to be a dict")

        return XilinxFdriFormat(
            fdri_format["device_name"],
            fdri_format["logic_block_size"],
            fdri_format["bram_block_size"],
            fdri_format["io_block_size"],
            fdri_format["crc_size"],
            self._create_fdri_logic_block_format(
                fdri_logic_block_format,
                fdri_major_formats_by_name
            ),
            self._create_fdri_io_block_format(
                fdri_io_block_format
            ),
        )

    def build(self):
        register_formats = [
            self._create_register_format(register_format)
            for register_format in self._register_formats
        ]
        fdri_major_formats = [
            self._create_fdri_major_format(fdri_format)
            for fdri_format in self._fdri_major_formats
        ]
        fdri_major_formats_by_name = {m.name: m for m in fdri_major_formats}

        fdri_io_block_by_name = {
            m["device_name"]: m["io_block_format"]
            for m in self._fdri_io_block_formats
        }
        fdri_logic_block_by_name = {
            m["device_name"]: m["logic_block_format"]
            for m in self._fdri_logic_block_formats
        }
        fdri_formats = [
            self._create_fdri_format(
                fdri_format,
                fdri_logic_block_by_name.get(fdri_format["device_name"]),
                fdri_io_block_by_name.get(fdri_format["device_name"]),
                fdri_major_formats_by_name,
            )
            for fdri_format in self._fdri_formats
        ]
        return XilinxFormat(
            register_formats,
            fdri_formats,
            self._visualizer_config
        )