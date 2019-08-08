import io

from typing import List

from bal.context_ioc import AbstractConverter
from bal.data_model import ArrayModel
from bal.data_object import DataObject
from bal_xilinx.context import XilinxContext
from bal_xilinx.data_model import XilinxFdriPayload, XilinxFdriLogicBlock, \
    XilinxFdriRAMBlockInterface, XilinxFdriIOBlockInterface, XilinxFdriCRCInterface, \
    XilinxFdriLogicRow, XilinxFdriLogicMajor, XilinxFdriLogicFrame
from bal_xilinx.format import XilinxFdriMajorFormat


class XilinxFdriLogicMajorConverter(AbstractConverter):
    def __init__(self, context, major_format):
        """
        :param XilinxContext context:
        :param XilinxFdriMajorFormat major_format: The format of the register being parsed.
        """
        super(XilinxFdriLogicMajorConverter, self).__init__(context)
        self.context = context
        self._major_format = major_format

    def unpack(self, data_bytes):
        """
        :param bytes data_bytes:
        :rtype: ArrayModel
        """
        frames = []
        data_stream = io.BytesIO(data_bytes)
        expected_size = 0
        for frame_index in range(self._major_format.frame_count):
            frame_data = data_stream.read(self._major_format.frame_size)
            expected_size += self._major_format.frame_size
            frame_description = None
            if len(self._major_format.frame_descriptions) > frame_index:
                frame_description = self._major_format.frame_descriptions[frame_index]
            FrameInterface = type(
                "XilinxFdriLogicFrame",
                (XilinxFdriLogicFrame,),
                {}
            )
            FrameInterface.__doc__ = frame_description
            frames.append(
                DataObject.create_packed(
                    self.context,
                    frame_data,
                    FrameInterface
                )
            )

        assert expected_size == len(data_bytes), \
            "The number of bytes provided {} does not match the expected number of bytes {}".format(
                len(data_bytes),
                expected_size

        )
        major_name = "".join([p.title() for p in self._major_format.name.split("_")])
        class_name = "{}".format(major_name)
        MajorModel = type(class_name, (XilinxFdriLogicMajor,), {})
        MajorModel.__doc__ = "The config data for a {} major".format(self._major_format.name)
        return MajorModel(frames)

    def pack(self, data_model):
        """
        :param ArrayModel data_model:
        :rtype: bytes
        """
        return b"".join([c.pack() for c in data_model])


class XilinxFdriLogicBlockRowConverter(AbstractConverter):
    """
    :param XilinxContext context:
    :param List[XilinxFdriMajorFormat] row_format: The format of the register being parsed.
    """
    def __init__(self, context, row_format):
        super(XilinxFdriLogicBlockRowConverter, self).__init__(context)
        self.context = context
        self._row_format = row_format

    def unpack(self, data_bytes):
        """
        :param bytes data_bytes:
        :rtype: ArrayModel
        """
        majors = []
        data_stream = io.BytesIO(data_bytes)
        expected_size = 0
        for major_format in self._row_format:
            major_size = major_format.frame_count * major_format.frame_size
            expected_size += major_size
            majors.append(DataObject.create_packed(
                self.context,
                data_stream.read(major_size),
                XilinxFdriLogicMajor,
                converter_args=(major_format, )
            ))

        assert expected_size == len(data_bytes), \
            "The number of bytes provided {} does not match the expected number of bytes {}".format(
                len(data_bytes),
                expected_size
            )
        return XilinxFdriLogicRow(majors)

    def pack(self, data_model):
        """
        :param ArrayModel data_model:
        :rtype: bytes
        """
        return b"".join([c.pack() for c in data_model])


class XilinxFdriLogicConverter(AbstractConverter):
    """
    :param XilinxContext context: A factory used to create data objects/converters.
    """
    def __init__(self, context):
        super(XilinxFdriLogicConverter, self).__init__(context)
        self.context = context

    def unpack(self, data_bytes):
        """
        :param bytes data_bytes:
        :rtype: ArrayModel
        """
        if self.context.id_code is None:
            raise ValueError(
                "The ID code for the targeted device has not been set on the bitstream context."
            )

        rows = []
        expected_size = 0
        data_stream = io.BytesIO(data_bytes)
        fdri_format = self.context.format.get_fdri_format(self.context.id_code)
        for row_format in fdri_format.logic_block_format:
            row_size = sum([
                major_format.frame_size * major_format.frame_count
                for major_format in row_format
            ])
            expected_size += row_size
            rows.append(DataObject.create_packed(
                self.context,
                data_stream.read(row_size),
                XilinxFdriLogicRow,
                converter_args=(row_format, ),
            ))

        assert expected_size == len(data_bytes), \
            "The number of bytes provided {} does not match the expected number of bytes {}".format(
                len(data_bytes),
                expected_size
            )
        return XilinxFdriLogicBlock(rows)

    def pack(self, data_object):
        """
        :param ArrayModel data_object:
        :rtype: bytes
        """
        return b"".join([c.pack() for c in data_object])


class XilinxFdriRAMBlockConverter(AbstractConverter):
    pass


class XilinxFdriIOBlockConverter(AbstractConverter):
    pass


class XilinxFdriTailConverter(AbstractConverter):
    pass


class XilinxFdriPayloadConverter(AbstractConverter):
    """
    :param XilinxContext context: A factory used to create data objects/converters.
    """
    def __init__(self, context):
        super(XilinxFdriPayloadConverter, self).__init__(context)
        self.context = context

    def unpack(self, data_bytes):
        """
        :param bytes data_bytes:
        :rtype: XilinxFdriPayload
        """
        if self.context.id_code is None:
            raise ValueError(
                "The ID code for the targeted device has not been set on the bitstream context."
            )
        fdri_format = self.context.format.get_fdri_format(self.context.id_code)
        expected_size = fdri_format.logic_block_size + fdri_format.bram_block_size + \
                fdri_format.io_block_size + fdri_format.crc_size
        assert len(data_bytes) == expected_size, \
            "The size of the config data ({}) does not match the expected size ({})".format(
                len(data_bytes),
                expected_size
            )
        data_stream = io.BytesIO(data_bytes)
        return XilinxFdriPayload(
            DataObject.create_packed(
                self.context,
                data_stream.read(fdri_format.logic_block_size),
                XilinxFdriLogicBlock,
            ),
            DataObject.create_packed(
                self.context,
                data_stream.read(fdri_format.bram_block_size),
                XilinxFdriRAMBlockInterface,
            ),
            DataObject.create_packed(
                self.context,
                data_stream.read(fdri_format.io_block_size),
                XilinxFdriIOBlockInterface
            ),
            DataObject.create_packed(
                self.context,
                data_stream.read(fdri_format.crc_size),
                XilinxFdriCRCInterface,
            ),
        )

    def pack(self, data_object):
        """
        :param XilinxFdriPayload data_object:
        :rtype: bytes
        """
        assert isinstance(data_object, XilinxFdriPayload)
        return b"".join([
            data_object.get_logic_block().pack(),
            data_object.get_ram_block().pack(),
            data_object.get_io_block().pack(),
            data_object.get_crc().pack()
        ])