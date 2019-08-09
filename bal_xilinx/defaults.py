import os

from bal.analyzers.visualizer_analyzer import VisualizerAnalyzer
from bal_xilinx.analyzers.device_analyzer import XilinxDeviceAnalyzer
from bal_xilinx.analyzers.encryption_analyzer import XilinxEncryptionAnalyzer
from bal_xilinx.analyzers.visualizer_analyzer import XilinxVisualizerAnalyzer
from bal_xilinx.converters.bitstream import XilinxBitstreamConverter
from bal_xilinx.converters.bitstream_packets import XilinxPacketsConverter
from bal_xilinx.converters.bitstream_packets_1 import XilinxType1PayloadConverter
from bal_xilinx.converters.bitstream_packets_fdri import XilinxFdriPayloadConverter, \
    XilinxFdriLogicConverter, XilinxFdriLogicBlockRowConverter, XilinxFdriLogicMajorConverter
from bal_xilinx.data_model import XilinxBitstream, XilinxPackets, \
    XilinxType1Payload, XilinxFdriPayload, XilinxFdriLogicBlock, \
    XilinxFdriLogicRow, XilinxFdriLogicMajor
from bal_xilinx.format import XilinxFormatBuilder
from bal_xilinx.modifiers.pin_modifier import XilinxPinModifer


def register_defaults_context_converters(context):
    context.register_converter(XilinxBitstream, XilinxBitstreamConverter)
    context.register_converter(XilinxPackets, XilinxPacketsConverter)
    context.register_converter(XilinxType1Payload, XilinxType1PayloadConverter)
    context.register_converter(XilinxFdriPayload, XilinxFdriPayloadConverter)
    context.register_converter(XilinxFdriLogicBlock, XilinxFdriLogicConverter)
    context.register_converter(XilinxFdriLogicRow, XilinxFdriLogicBlockRowConverter)
    context.register_converter(XilinxFdriLogicMajor, XilinxFdriLogicMajorConverter)
    return context


def register_defaults_context_analyzers(context):
    context.register_analyzer(VisualizerAnalyzer, XilinxVisualizerAnalyzer)
    context.register_analyzer(XilinxDeviceAnalyzer, XilinxDeviceAnalyzer)
    context.register_analyzer(XilinxEncryptionAnalyzer, XilinxEncryptionAnalyzer)
    return context


def register_defaults_context_modifiers(context):
    context.register_modifier(XilinxPinModifer, XilinxPinModifer)
    return context


def default_xilinx_context(context):
    register_defaults_context_converters(context)
    register_defaults_context_analyzers(context)
    register_defaults_context_modifiers(context)

    return context


def default_xilinx_formats(format_builder):
    """
    Load the default JSON config files for Xilinx fpgas.

    :rtype: XilinxFormatBuilder
    """
    root_path = os.path.join(os.path.dirname(__file__), "configs")
    # Configure the register formats
    format_builder.add_register_formats_json(os.path.join(root_path, "xilinx_registers.json"))
    # Configure the FDRI major formats
    format_builder.add_fdri_major_formats_json(os.path.join(root_path, "xilinx_fdri_majors.json"))
    # Configure the style
    format_builder.set_visualizer_config_json(os.path.join(root_path, "xilinx_visualization.json"))
    # Configure the FDRI formats
    # LX9
    format_builder.add_fdri_formats_json(os.path.join(root_path, "lx9_fdri.json"))
    format_builder.add_fdri_logic_block_formats_json(
        os.path.join(root_path, "lx9_fdri_logic_block.json")
    )
    format_builder.add_fdri_io_block_formats_json(
        os.path.join(root_path, "lx9_fdri_io_block.json")
    )
    # LX45t
    format_builder.add_fdri_formats_json(os.path.join(root_path, "lx45t_fdri.json"))
    format_builder.add_fdri_logic_block_formats_json(
        os.path.join(root_path, "lx45t_fdri_logic_block.json")
    )
    return format_builder
