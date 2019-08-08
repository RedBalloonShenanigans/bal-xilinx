from collections import OrderedDict

from bal.context_ioc import AbstractConverter
from bal.data_object import DataObject
from bal_xilinx.data_model import XilinxType1Payload, XilinxType1PayloadAttribute
from bal_xilinx.format import XilinxRegisterFormat


def pad_bytes(data, alignment=4):
    if len(data) % alignment == 0:
        return data
    data = bytearray(data)
    while len(data) % alignment != 0:
        data.append(0)
    return bytes(data)


class XilinxType1PayloadConverter(AbstractConverter):
    def __init__(self, context, register_format):
        """
        :param XilinxContext context: A factory used to create data objects/converters.
        :param XilinxRegisterFormat register_format: The format of the register being parsed.
        """
        super(XilinxType1PayloadConverter, self).__init__(context)
        self.context = context
        self.register_format = register_format

    def unpack(self, data_bytes):
        """
        :param bytes data_bytes:
        :rtype: XilinxType1Payload
        """
        if len(data_bytes) != self.register_format.size:
            raise ValueError(
                "Error while parsing the config for register {}. "
                "The expected size of the register config data ({}) "
                "does not match the size of the data to parse ({})".format(
                    self.register_format.name,
                    self.register_format.size,
                    len(data_bytes)
                )
            )
        data_bytes = pad_bytes(data_bytes)
        # Parse the register config attributes using the ctype defined by the
        attributes_values = self.register_format.ctype.from_buffer_copy(data_bytes)
        attributes = OrderedDict()
        for i, attribute_format in enumerate(self.register_format.attributes):
            value = attributes_values.values[i]
            value_documentation = attribute_format.get_value_documentation(value)
            if value_documentation is not None:
                value_name = value_documentation.name
                value_description = value_documentation.description
            else:
                value_name = None
                value_description = None
            attribute_name = attribute_format.name.lower()
            class_name = "".join([p.title() for p in attribute_name.split("_")]) + "Value"
            attributes[attribute_name] = self._create_attribute_object(
                attribute_format,
                class_name,
                value,
                value_name,
                value_description,
            )
        class_name = "Xilinx{}Payload".format(self.register_format.name)
        PayloadModel = type(class_name, (XilinxType1Payload,), {})
        PayloadModel.__doc__ = self.register_format.description
        return PayloadModel(attributes)

    def _create_attribute_object(
            self,
            attribute_format,
            class_name,
            value,
            value_name,
            value_description,
    ):
        AttributeModel = type(str(class_name), (XilinxType1PayloadAttribute, ), {})
        AttributeModel.__doc__ = attribute_format.description
        model = AttributeModel(int(value), value_name, value_description)
        return DataObject.create_unpacked(self.context, model, bit_size=attribute_format.bit_size)

    def pack(self, data_model):
        """
        :param XilinxType1Payload data_model:
        :rtype: bytes
        """
        assert isinstance(data_model, XilinxType1Payload)
        attributes = []
        for attribute_format in self.register_format.attributes:
            attributes.append(data_model.get(attribute_format.name.lower()).get_model().get_value())
        raw_attributes = self.register_format.ctype.get_bytes(*attributes)
        raw_attributes = raw_attributes[:self.register_format.size]
        return raw_attributes
