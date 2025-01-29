"""Generate ISBN images with tiled layout.

Usage:
    make_isbn_images_2_tiling.py [options]

Options:
    -i --input=<dir>        Input directory [default: images_tmp]
    -s --suffix=<suffix>    Input file suffix [default: isbns_cluster]
    -t --tile-size=<n>      Size of tile square [default: 256]
    -m --overlap=<n>        Overlap size around tiles [default: 0]
    -d --depth=<depth>      Pyramid depth : onetile, onepixel, one [default: onetile]
    -o --output=<dir>       Output directory [default: images]
    -r --resize=<n>         Resize factor (power of 2) [default: 1]
    -v --move-dir=<dir>     Move directory for depth=one [default: none]
    -p --move-suffix=<move> Move to directory with suffix
    -h --help            Show this help message

Example:
    python make_isbn_images_2_tiling.py
    python make_isbn_images_2_tiling.py -i myimages -s png -t 40 -m 5 -d onepixel -o output
"""

import sys
import os
import pyvips
from docopt import docopt
from pathlib import Path
import shutil

def get_next_directory_number(move_dir):
    """Get the next available number for the directory"""
    if not os.path.exists(move_dir):
        return 0
    existing_dirs = [int(d) for d in os.listdir(move_dir) if d.isdigit()]
    return max(existing_dirs + [-1]) + 1


def create_pyramid(input_dir, input_suffix, tile_size, overlap, depth, resize, output_dir, move_dir, move_suffix):
    """
    Create pyramids for all images with given suffix in the input directory.
    The pyramids will be created in the same directory.

    Args:
        input_dir (str): Directory containing the input images
        input_suffix (str): Suffix of input files (e.g., '_isbns_cluster')
        output_dir (str): Directory where pyramids will be created
    """
    
    # Convert input_dir to Path object
    input_path = Path(input_dir)

    # Check if directory exists
    if not input_path.exists():
        print(f"Error: Directory {input_dir} does not exist!")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Find all files with the given suffix
    input_files = list(input_path.glob(f'*_{input_suffix}.png'))

    if not input_files:
        print(f"No files with suffix {input_suffix} found in {input_dir}")
        return

    print(f"Found {len(input_files)} files to process")

    # Process each file
    for input_file in input_files:
        try:
            # Create output name (same as input but with _t suffix)
            output_base = input_file.stem + '_t'
            output_path = Path(output_dir) / output_base

            print(f"\nProcessing: {input_file.name}")

            # Load image
            image = pyvips.Image.new_from_file(str(input_file))
            
            # Resize image if needed
            
            if resize > 1:
                # doing it with vips, I can't find the right way to double each pixel
                #image = image.resize(resize, kernel=pyvips.enums.Kernel.NEAREST)
                image = image.affine([resize, 0, 0, resize], interpolate=pyvips.Interpolate.new('nearest'))

            # Get image dimensions
            width = image.width
            height = image.height
            print(f"Image dimensions: {width}x{height}")

            # Create pyramid with default settings
            # Using DeepZoom format, tile size 256, and onetile depth
            image.dzsave(str(output_path),
                        tile_size=tile_size,
                        depth=depth,
                        overlap=overlap,
                        region_shrink= pyvips.enums.RegionShrink.NEAREST,
                        suffix='.png')

            print(f"Created pyramid at: {output_path}_files/")
            print(f"Metadata file at: {output_path}.dzi")
            os.remove(f"{output_path}.dzi")
            os.remove(f"{output_path}_files/vips-properties.xml")

            if depth == "one" and move_dir != "none":
                source_dir = f"{output_path}_files/0"
                out_move_dir = f"{move_dir}/{input_file.stem}{move_suffix}_t_files"
                os.makedirs(out_move_dir, exist_ok=True)
                if os.path.exists(source_dir) and os.path.exists(out_move_dir):
                    next_num = get_next_directory_number(out_move_dir)
                    target_dir = os.path.join(out_move_dir, str(next_num))
                    shutil.move(source_dir, target_dir)
                    print(f"Moved {source_dir} to {target_dir}")
                    # Clean up empty directory
                    shutil.rmtree(f"{output_path}_files")
                else:
                    print(f"Cannot move {source_dir} to {out_move_dir} as one of them does not exist")

        except Exception as e:
            print(f"Error processing {input_file.name}: {str(e)}")

def main():
    args = docopt(__doc__)
    input_dir = args['--input']
    input_suffix = args['--suffix']
    tile_size = int(args['--tile-size'])
    overlap = int(args['--overlap'])
    depth = args['--depth']
    resize = int(args['--resize'])
    output_dir = args['--output']
    move_dir = args['--move-dir']
    move_suffix = args['--move-suffix']

    # Validate resize is a power of 2
    if resize & (resize - 1) != 0:
        print("Error: resize factor must be a power of 2")
        sys.exit(1)

    create_pyramid(input_dir, input_suffix, tile_size, overlap, depth, resize, output_dir, move_dir, move_suffix)

if __name__ == "__main__":
    main()