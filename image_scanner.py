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

DATA_PATH = Path(__file__).parent / "sample_data"
DATA_FILE = "sample_40_bits_01.png"  # 92630 samples
DATA_FILE = "sample_40_bits_02.png"  # 92630 samples
DATA_FILE = "sample_40_bits_03.png"  # 92630 samples


def scan_and_gate_image(image_filename, show_plot=False):
    """Scans the image to generate stream of bits along noise upper axis"""

    # creating a image object
    im = Image.open(image_filename)
    px = im.load()
    print(px[4, 4])
    px[4, 4] = (0, 0, 0)
    print(px[4, 4])
    coordinate = x, y = 150, 59

    # using getpixel method
    print(im.getpixel(coordinate))


def run_demod():
    """Run main algorithm"""

    source_file_name = Path(DATA_PATH) / DATA_FILE
    gated_data = scan_and_gate_image(source_file_name, show_plot=False)

    count_high = gated_data.count(True)
    count_total = len(gated_data)
    duty_cycle = int(count_high / count_total * 100)

    print(f"Data has {count_high} highs in {count_total} samples (~ {duty_cycle} %)")

    # opt_divisor = try_bit_streams(gated_data, print_verbose=False)
    # bit_stream, timing_list = extract_bit_stream(
    #    gated_data, opt_divisor, print_verbose=False
    # )
    # bit_values, bit_text = calc_bit_values(timing_list, print_verbose=False)

    # print(f"Bit values ({len(bit_values)}):\n{bit_text}")


if __name__ == "__main__":
    run_demod()
