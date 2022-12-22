""" First look at quick and dirty pulse demodulation from data capture with URH

    If you want the plots, you'll need to install matplotlib:
    python -m pip install -U matplotlib

    Run this program to do analysis on the data file

    John Tocher
    20/12/2022

"""

import matplotlib.pyplot as plt
from pathlib import Path

DATA_PATH = Path(__file__).parent / "sample_data"

DATA_SAMPLE_1 = "sample_40_bits_01.complex16u"  # 92630 samples
DATA_SAMPLE_2 = "sample_40_bits_02.complex16u"  # 92630 samples
DATA_SAMPLE_3 = "sample_40_bits_03.complex16u"  # 92630 samples


def raw_read(raw_file_name, print_verbose=False):
    """Reads the supplied file and spits out data for exploration"""

    chunk_count = 0
    chunk_size = False

    raw_data = list()

    TEST_RANGE = 0

    if raw_file_name.suffix.endswith(".complex16u"):
        chunk_size = 2
        byte_order = "big"
        is_signed = False

    assert chunk_size, f"Unexpected chunk size for file: {raw_file_name}"

    with open(raw_file_name, "rb") as input_file:
        this_chunk = input_file.read(chunk_size)
        while this_chunk:
            chunk_count += 1
            this_chunk = input_file.read(chunk_size)
            if this_chunk:
                # this_val = struct.unpack("@h", this_chunk)
                this_val = int.from_bytes(
                    this_chunk, byteorder=byte_order, signed=is_signed
                )
                raw_data.append(this_val)
                if chunk_count < TEST_RANGE:
                    print(f"Chunk: {chunk_count:04} value: {this_val}")
            else:
                chunk_count -= 1

    if print_verbose:
        print(
            f"Read {chunk_count} chunks of size {chunk_size} from file {raw_file_name}"
        )

    return raw_data


def auto_scale_and_gate(raw_data, show_plot=False):
    """Attempts to autoscale the waveform provided"""

    val_min = min(raw_data)
    val_max = max(raw_data)
    val_range = val_max - val_min
    val_mid = int(val_range / 2)

    threshhold = int(val_range / 4)

    val_high = val_mid + threshhold
    val_low = val_mid

    scaled_data = [(this_point - val_min) for this_point in raw_data]

    gated_data = list()
    binary_data = list()

    for each_point in scaled_data:
        if abs(each_point - val_mid) > threshhold:
            gated_data.append(val_high)
            binary_data.append(True)
        else:
            gated_data.append(val_low)
            binary_data.append(False)

    if show_plot:
        plt.plot(scaled_data)
        plt.plot(gated_data)
        plt.show()

    return binary_data


def extract_bit_stream(gated_data, sample_divisor=500, print_verbose=False):
    """Attempts to calculate the number of bits and a stream of ones and zeroes"""

    raw_count = len(gated_data)
    min_width = int(raw_count / sample_divisor)
    # print(f"Trying min width: {min_width}")

    running_high = 0
    running_low = 0

    rise_count = 0
    fall_count = 0

    state_high = False
    state_low = True

    sample_count = 0

    peak_list = list()
    peak_start = 0

    for each_bit in gated_data:
        sample_count += 1
        if each_bit:
            running_high += 1
            if state_high:  # Already on a peak - keep going
                pass
            elif running_high > min_width:
                peak_start = sample_count
                rise_count += 1
                running_low = 0
                state_high = True
                state_low = False
                peak_list.append(["L-H", sample_count])
                if print_verbose:
                    print(f"L-H at {sample_count}")
        else:
            running_low += 1
            if state_low:  # Already in trough - keep going
                pass
            elif running_low > min_width:
                fall_count += 1
                peak_width = sample_count - peak_start
                peak_start = sample_count
                running_high = 0
                state_high = False
                state_low = True
                peak_list.append(["H-L", sample_count])
                if print_verbose:
                    print(f"H-L at {sample_count} width {peak_width}")

    if print_verbose:
        print(f"Rise count:{rise_count} Fall count:{fall_count}")

    if fall_count == rise_count:
        return peak_list
    else:
        edge_diff = int(rise_count - fall_count)
        if edge_diff > 1:
            print(gated_data)
            assert False, f"Unexpected edge mismatch: {fall_count} != {rise_count}"
        else:
            if rise_count:
                return peak_list
            else:
                assert False, f"No edges detected: {fall_count} != {rise_count}"
    return 0


def count_bitstream_transistions(bitstream_list, what_to_count):
    """Returns the instanaces of an event such as "L-H from the supplied bitstream list

    the list items are lists themselves, [being event, sample_position] so a single positive
    pulse might look like:
    [ ["L-H", 125], ["L-H", 150] ]

    for a H-L transition at sample 125 , then the transition down at sample 150, 25 samples later
    """

    event_count = 0
    for each_transition in bitstream_list:
        if what_to_count in each_transition[0]:
            event_count += 1

    return event_count


def try_bit_streams(gated_data, print_verbose=False):
    """Run a bunch of extractions with different pulse width thresholds"""

    # Assuming
    # 1o pulses in 12 pulse range, 10 % duty cycle, peak width = samples / 120
    # 100 pulses in 120 pulse range 10 % duty cycle, peak width = samples / 1200

    trial_result = dict()
    summary_dict = dict()
    result_list = list()

    size_of_data = len(gated_data)

    for pulse_width_min in range(100, 1250, 50):
        timing_list = extract_bit_stream(gated_data, pulse_width_min, False)
        this_attempt = count_bitstream_transistions(timing_list, "H-L")
        result_list.append(this_attempt)
        new_value = summary_dict.get(this_attempt, 0) + 1
        summary_dict[this_attempt] = new_value
        trial_result[pulse_width_min] = this_attempt

    descending_results = list(summary_dict.values())
    descending_results.sort(reverse=True)

    highest_frequency = descending_results[0]

    assert highest_frequency > 3, "Not enough consistency in pulse width"

    summary_val = False

    for summary_val, summary_score in summary_dict.items():
        if summary_score == highest_frequency:
            sample_mode = summary_val

    assert summary_val, "Couldn't find the mode in the frequency distrubution"
    # print(f"Mode is: {sample_mode}")

    sample_sum = 0
    for each_key in trial_result.keys():
        if trial_result[each_key] == sample_mode:
            sample_sum += each_key

    avg_divisor = int(sample_sum / highest_frequency)
    if print_verbose:
        print(
            f"Will use a sample divisor of {avg_divisor} ({highest_frequency} of 12 match)"
        )

    return avg_divisor


def calc_bit_values(timing_list, print_verbose=False):
    """Analyses the pulse widths looking for sensible values"""

    low_started = False
    low_widths = list()

    time_down = False
    time_up = False

    bits_list = list()
    bits_text = ""

    for time_data in timing_list:
        if time_data[0] == "L-H":
            if low_started:  # Not the first pulse up
                time_up = time_data[1]
                low_width = time_up - time_down
                low_widths.append(low_width)
                if print_verbose:
                    print(f"Low pulse width: {low_width}")
                low_started = False
            else:
                if print_verbose:
                    print("First L-H (start pulse)")
        elif time_data[0] == "H-L":
            assert not low_started, "Shouldn't get two H-L transistions!"
            low_started = True
            time_down = time_data[1]
        else:
            assert False, f"Unexpected event: {time_data[0]}"

    width_total = 0
    num_lows = len(low_widths)

    for each_pulse in low_widths:
        width_total += each_pulse

    avg_width = int(width_total / num_lows)

    if print_verbose:
        print(f"Average width: {avg_width}")

    pulse_count = 0
    for each_pulse in low_widths:
        deviation = (each_pulse - avg_width) / avg_width
        delta_t = int(deviation * 100)
        if delta_t > 10:
            bit_value = True
            bit_show = "1"

        elif delta_t < -10:
            bit_value = False
            bit_show = "0"
        else:
            assert pulse_count == 0, "Uncertain pulse width"
            bit_show = "s"
        if print_verbose:
            print(
                f"Count: {pulse_count:02}  Value: {bit_show}   Width {each_pulse}  Delta: {delta_t}"
            )

        if pulse_count > 0:
            bits_list.append(bit_value)
            bits_text += bit_show
        pulse_count += 1

    return bits_list, bits_text


def get_bits_for_data_file(data_file_name, return_as_text=False, print_verbose=False):
    """Returns the demodulated bitstream for the supplied data file

    Returns a list of booleans: [True, False, False.....True]
    or a text representation : "11000.....1"
    depending on the value of return_as_text
    """

    raw_data = raw_read(data_file_name)
    gated_data = auto_scale_and_gate(raw_data, show_plot=False)

    count_high = gated_data.count(True)
    count_total = len(gated_data)
    duty_cycle = int(count_high / count_total * 100)

    if print_verbose:
        print(
            f"Data has {count_high} highs in {count_total} samples (~ {duty_cycle} %)"
        )

    opt_divisor = try_bit_streams(gated_data, print_verbose=False)
    timing_list = extract_bit_stream(gated_data, opt_divisor, print_verbose=False)
    bit_values, bit_text = calc_bit_values(timing_list, print_verbose=False)

    if print_verbose:
        print(f"Bit values ({len(bit_values)}):\n{bit_text}")

    if return_as_text:
        return bit_text
    else:
        return bit_values


def compare_multiple_files(data_file_list):
    """Do a simple comparison for multiple data_files"""

    result_list = list()
    result_set = set()

    for each_file in data_file_list:
        bit_text = get_bits_for_data_file(
            each_file, return_as_text=True, print_verbose=False
        )
        result_list.append(bit_text)
        print(f"{each_file.name} : {bit_text}")

    for result in result_list:
        result_set.add(result)

    print(f"Found {len(result_set)} unique streams from {len(result_list)} data files")

    return result_list


def run_demod():
    """Run main algorithm"""

    # Example for a single file
    source_file_name = Path(DATA_PATH) / DATA_SAMPLE_1
    bit_text = get_bits_for_data_file(source_file_name, True, False)
    print(f"Bit values ({len(bit_text)}):\n{bit_text}")

    # Example to compare multiple files
    data_file_list = list()
    data_file_list.append(Path(DATA_PATH) / DATA_SAMPLE_1)
    data_file_list.append(Path(DATA_PATH) / DATA_SAMPLE_2)
    data_file_list.append(Path(DATA_PATH) / DATA_SAMPLE_3)
    result_list = compare_multiple_files(data_file_list)


if __name__ == "__main__":
    run_demod()
