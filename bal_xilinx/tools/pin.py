import argparse
import os

from bal_xilinx.analyzers.device_analyzer import XilinxDeviceAnalyzer
from bal_xilinx.context import XilinxContextFactory
from bal_xilinx.defaults import default_xilinx_context, default_xilinx_formats
from bal_xilinx.format import XilinxFormatBuilder
from bal_xilinx.modifiers.pin_modifier import XilinxPinModifer


def update_xilinx_pin(bitstream_path, output_bitstream_path, is_on, pins):
    xilinx_context_factory = default_xilinx_context(XilinxContextFactory(
        default_xilinx_formats(XilinxFormatBuilder()).build()
    ))
    with open(bitstream_path, "rb") as f:
        data = f.read()

    bitstream_context = xilinx_context_factory.create(data)
    bitstream_object = bitstream_context.get_data()

    device_type = bitstream_context.create_analyzer(XilinxDeviceAnalyzer) \
        .analyze()
    if device_type != "LX9":
        print("The script only supports bitstreams targetting the LX9.")

    print("Modifying the bitstream")
    pin_modifier = bitstream_context.create_modifier(XilinxPinModifer)
    for pin in pins:
        pin_modifier.modify(pin, is_on)

    bitstream_object.synchronize(True)
    packed_data = bitstream_object.pack()
    assert packed_data != data, "The bitstream did not change."
    print("Writing modified bitstream to {}".format(output_bitstream_path))
    with open(output_bitstream_path, "wb") as f:
        f.write(packed_data)
    print("Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="bal_xilinx.tools.pin",
        description='Modify a Xilinx FPGA bitstream to turn a specific pin on or off. It currently'
                    'supports bitstream targeting the LX9.'
    )
    parser.add_argument(
        'path',
        metavar='PATH',
        help='The path to the bitstream'
    )
    parser.add_argument(
        'state',
        metavar='STATE',
        choices=['on', 'off'],
        help='Determine if the pin should pull low (on) or high (off)'
    )
    parser.add_argument(
        'pins',
        metavar='PIN',
        nargs="+",
        help='The name of the pin to modify (ie P134)'
    )

    args = parser.parse_args()
    bitstream_output_path = os.path.splitext(args.path)[0] + "_repacked.bin"
    update_xilinx_pin(args.path, bitstream_output_path, args.state == 'on', args.pins)