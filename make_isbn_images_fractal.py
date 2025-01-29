"""Generate ISBN fractal images.

Usage:
    make_isbn_images_fractal.py [options]

Options:
    -i --input=<file>     Input filename [default: aa_isbn13_codes_20241204T185335Z.benc.zst]
    -x --suffix=<suffix>  Output filename suffix [default: _isbns]
    -o --output=<dir>     Output directory [default: images_tmp]
    -h --help            Show this help message
"""

import bencodepy
import PIL.Image
import PIL.ImageChops
import struct
import tqdm
import zstandard
from docopt import docopt
import os


WIDTH = 50000
HEIGHT = 40000
LEN_SHORT_ISBN = 10
VECTOR = [
    HEIGHT // 2,
    WIDTH // 10,
    HEIGHT // (2 * 10),
    WIDTH // 100,
    HEIGHT // (2 * 100),
    WIDTH // 1000,
    HEIGHT // (2 * 1000),
    WIDTH // 10000,
    HEIGHT // (2 * 10000),
]


def get_recursive_xy(position):
    coords = [0, 0]  # [x, y]
    isbn_str = str(position).zfill(LEN_SHORT_ISBN)
    # Process remaining digits
    for i in range(LEN_SHORT_ISBN - 1):
        digit = int(isbn_str[i])
        coords[(i + 1) % 2] += digit * VECTOR[i]

    digit = int(isbn_str[LEN_SHORT_ISBN - 1])
    last_y = digit // 5

    coords[0] += digit %5
    coords[1] += last_y
    return coords[0], coords[1]

def find_isbn_from_xy(x, y):
    # Initialize ISBN digits
    isbn_digits = [0] * LEN_SHORT_ISBN

    remaining_x = x
    remaining_y = y

    # Process all digits except the last one
    for i in range(LEN_SHORT_ISBN - 1):
        if (i + 1) % 2 == 0:  # x coordinate
            digit = remaining_x // VECTOR[i]
            remaining_x = remaining_x % VECTOR[i]
        else:  # y coordinate
            digit = remaining_y // VECTOR[i]
            remaining_y = remaining_y % VECTOR[i]

        if 0 <= digit <= 9:
            isbn_digits[i] = digit
        else:
            return None  # Invalid coordinates

    # Handle the last digit specially
    # The last digit needs to satisfy both:
    # digit % 5 = remaining_x
    # digit // 5 = remaining_y
    last_digit = (remaining_y * 5) + remaining_x

    if 0 <= last_digit <= 9:
        isbn_digits[LEN_SHORT_ISBN - 1] = last_digit
        isbn = int(''.join(map(str, isbn_digits)))
        return 978000000000 + isbn

    return None  # If no valid solution is found

def color_image(
    image, packed_isbns_binary, color=None, addcolor=None, unique_isbns=None
):
    """
    Go through our ISBN data (packed ISBN intervals) and color pixels
    according to get_recursive_xy(...) mapping.
    When called several times in a row, you can provide unique_isbns to avoid putting the same pixel.
    """
    packed_isbns_ints = struct.unpack(
        f"{len(packed_isbns_binary) // 4}I", packed_isbns_binary
    )
    isbn_streak = True
    position = 0  # offset from 978000000000

    for value in tqdm.tqdm(packed_isbns_ints):
        if isbn_streak:
            for _ in range(value):
                coords = get_recursive_xy(position)
                if coords is not None:
                    x, y = coords
                    if x < image.width and y < image.height:
                        if color is not None:
                            current_isbn = 978000000000 + position
                            if unique_isbns is None or current_isbn not in unique_isbns:
                                image.putpixel((x, y), color)
                            if unique_isbns is not None:
                                unique_isbns.add(current_isbn)
                        elif addcolor is not None:
                            current = image.getpixel((x, y))
                            if isinstance(current, tuple):
                                # For RGB images, add each component separately
                                new_color = tuple(
                                    min(c1 + c2, 255)
                                    for c1, c2 in zip(current, addcolor)
                                )
                                image.putpixel((x, y), new_color)
                            else:
                                # For grayscale images
                                image.putpixel((x, y), min(current + addcolor, 255))
                    else:
                        print(f"Pixel out of image {position} - {x} - {y}!!!")
                position += 1
        else:
            # gap_size, skip these positions
            position += value
        isbn_streak = not isbn_streak


def main():
    args = docopt(__doc__)
    input_filename = args["--input"]
    suffix = args["--suffix"]
    output_dir = args["--output"]

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    isbn_data = bencodepy.bread(
        zstandard.ZstdDecompressor().stream_reader(open(input_filename, "rb"))
    )

    # Generate individual prefix images
    print(f"### Generating *{suffix}.png...")
    for prefix, packed_isbns_binary in isbn_data.items():
        filename = f"{output_dir}/{prefix.decode()}{suffix}.png"
        print(f"Generating {filename}...")
        prefix_isbns_png = PIL.Image.new("1", (WIDTH, HEIGHT), 0)
        color_image(prefix_isbns_png, packed_isbns_binary, color=1)
        prefix_isbns_png.save(filename)

    # Generate one combined image
    print(f"### Generating {output_dir}/all{suffix}.png...")
    unique_isbns = set()
    all_isbns_png = PIL.Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    for prefix, packed_isbns_binary in isbn_data.items():
        if prefix == b"md5":
            continue
        print(f"Adding {prefix.decode()} to {output_dir}/all{suffix}.png")
        color_image(
            all_isbns_png,
            packed_isbns_binary,
            color=(255, 0, 0),
            unique_isbns=unique_isbns,
        )

    # Finally, add md5 in green, if present.
    if b"md5" in isbn_data:
        print(f"Adding md5 to {output_dir}/all{suffix}.png")
        color_image(all_isbns_png, isbn_data[b"md5"], addcolor=(0, 255, 0))

    all_isbns_png.save(f"{output_dir}/all{suffix}.png")
    print("Done.")


if __name__ == "__main__":
    main()
