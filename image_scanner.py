""" First look at quick and dirty pulse demodulation from a screenshot captured with URH

    If you want the plots, you'll need to install matplotlib:
    python -m pip install -U matplotlib

    Run this program to do analysis on the screen capture from URH
    
    John Tocher
    20/12/2022
"""

# Importing Image from PIL package
import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path

from signal_demod import try_bit_streams
from signal_demod import extract_bit_stream
from signal_demod import calc_bit_values

DATA_PATH = Path(__file__).parent / "sample_data"
IMAGE_SAMPLE_1 = "sample_40_bits_01.png"  # 92630 samples
IMAGE_SAMPLE_2 = "sample_40_bits_02.png"  # 92630 samples
IMAGE_SAMPLE_3 = "sample_40_bits_03.png"  # 92630 samples


def scan_and_gate_image(image_filename, show_plot=False, print_verbose=False):
    """Scans the image to generate stream of bits along noise upper axis

    Analog of function:auto_scale_and_gate in signal_demod.py"""

    binary_data = list()

    noise_colour_values = list()  # Bit of a hack getting colours from sample image
    noise_colour_values.append((244, 172, 172))
    noise_colour_values.append((245, 161, 161))

    # creating a image object
    im = Image.open(image_filename)
    image_pixels = im.load()

    size_x = im.width
    size_y = im.height

    if print_verbose:
        print(f"Image {image_filename} {size_x} x {size_y}")

    line_y_to_scan = False

    # Locate top_most ogrange nose edge
    last_pixel = False
    for y_val in range(0, size_y):
        test_point = (1, y_val)
        test_pixel = im.getpixel(test_point)
        if test_pixel == last_pixel:
            pass
            # print(f"    pixel at y={y_val:04} value:{test_pixel}")
        else:
            # print(f"New pixel at y={y_val:04} value:{test_pixel}")
            last_pixel = test_pixel
            if test_pixel in noise_colour_values:
                line_y_to_scan = y_val
                break

    assert line_y_to_scan, f"Didn't find orange band in file {image_filename}"
    if print_verbose:
        print(f"Scanning row y = {line_y_to_scan}")

    for x_val in range(0, size_x):
        test_point = (x_val, line_y_to_scan)
        test_pixel = im.getpixel(test_point)
        sum_of_colours = sum(test_pixel)
        if sum_of_colours < 30:  # Sum of RGB coloours is low
            binary_data.append(True)
        else:
            binary_data.append(False)

    return binary_data


def get_bits_for_image_file(image_file_name, return_as_text=False, print_verbose=False):
    """Returns the demodulated bitstream for the supplied image file

    Returns a list of booleans: [True, False, False.....True]
    or a text representation : "11000.....1"
    depending on the value of return_as_text
    """
    gated_data = scan_and_gate_image(
        image_file_name, show_plot=False, print_verbose=False
    )

    count_high = gated_data.count(True)
    count_total = len(gated_data)
    duty_cycle = int(count_high / count_total * 100)

    print(f"Data has {count_high} highs in {count_total} samples (~ {duty_cycle} %)")

    opt_divisor = try_bit_streams(gated_data, print_verbose=False)
    timing_list = extract_bit_stream(gated_data, opt_divisor, print_verbose=False)
    bit_values, bit_text = calc_bit_values(timing_list, print_verbose=False)
    if print_verbose:
        print(f"Bit values ({len(bit_values)}):\n{bit_text}")

    if return_as_text:
        return bit_text
    else:
        return bit_values


def run_demod():
    """Run main algorithm"""

    # Example for a single image file
    source_file_name = Path(DATA_PATH) / IMAGE_SAMPLE_2
    bit_text = get_bits_for_image_file(
        source_file_name, return_as_text=True, print_verbose=False
    )
    print(f"Bit values for {source_file_name.name} ({len(bit_text)}):\n{bit_text}")


if __name__ == "__main__":
    run_demod()
