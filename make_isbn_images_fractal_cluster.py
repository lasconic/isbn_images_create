"""Generate ISBN images from encoded data.

Usage:
    make_isbn_images_fixed.py [options]

Options:
    -i --input=<file>      Input filename [default: aa_isbn13_codes_20241204T185335Z.benc.zst]
    -x --suffix=<suffix>   Output filename suffix [default: _isbns_cluster]
    -o --output=<dir>      Output directory [default: images_tmp]
    -h --help             Show this help message
"""

import bencodepy
from docopt import docopt
from PIL import Image, ImageChops
import os
import struct
import tqdm
import zstandard

WIDTH = 1000
HEIGHT = 800
LEN_SHORT_ISBN = 10
SCALE = 50
SCALE_SQUARED = 50*50

countries={'978-0':'English language','978-1':'English language','978-2':'French language','978-3':'German language','978-4':'Japan','978-5':'former U.S.S.R','978-600':'Iran','978-601':'Kazakhstan','978-602':'Indonesia','978-603':'Saudi Arabia','978-604':'Vietnam','978-605':'Turkey','978-606':'Romania','978-607':'Mexico','978-608':'North Macedonia','978-609':'Lithuania','978-611':'Thailand','978-612':'Peru','978-613':'Mauritius','978-614':'Lebanon','978-615':'Hungary','978-616':'Thailand','978-617':'Ukraine','978-618':'Greece','978-619':'Bulgaria','978-620':'Mauritius','978-621':'Philippines','978-622':'Iran','978-623':'Indonesia','978-624':'Sri Lanka','978-625':'Turkey','978-626':'Taiwan','978-627':'Pakistan','978-628':'Colombia','978-629':'Malaysia','978-630':'Romania','978-631':'Argentina','978-65':'Brazil','978-7': "China, People's Republic", '978-80':'former Czechoslovakia','978-81':'India','978-82':'Norway','978-83':'Poland','978-84':'Spain','978-85':'Brazil','978-86':'former Yugoslavia','978-87':'Denmark','978-88':'Italy','978-89':'Korea, Republic','978-90':'Netherlands','978-91':'Sweden','978-92':'International NGO Publishers and EU Organizations','978-93':'India','978-94':'Netherlands','978-950':'Argentina','978-951':'Finland','978-952':'Finland','978-953':'Croatia','978-954':'Bulgaria','978-955':'Sri Lanka','978-956':'Chile','978-957':'Taiwan','978-958':'Colombia','978-959':'Cuba','978-960':'Greece','978-961':'Slovenia','978-962':'Hong Kong, China','978-963':'Hungary','978-964':'Iran','978-965':'Israel','978-966':'Ukraine','978-967':'Malaysia','978-968':'Mexico','978-969':'Pakistan','978-970':'Mexico','978-971':'Philippines','978-972':'Portugal','978-973':'Romania','978-974':'Thailand','978-975':'Turkey','978-976':'Caribbean Community','978-977':'Egypt','978-978':'Nigeria','978-979':'Indonesia','978-980':'Venezuela','978-981':'Singapore','978-982':'South Pacific','978-983':'Malaysia','978-984':'Bangladesh','978-985':'Belarus','978-986':'Taiwan','978-987':'Argentina','978-988':'Hong Kong, China','978-989':'Portugal','978-9910':'Uzbekistan','978-9911':'Montenegro','978-9912':'Tanzania','978-9913':'Uganda','978-9914':'Kenya','978-9915':'Uruguay','978-9916':'Estonia','978-9917':'Bolivia','978-9918':'Malta','978-9919':'Mongolia','978-9920':'Morocco','978-9921':'Kuwait','978-9922':'Iraq','978-9923':'Jordan','978-9924':'Cambodia','978-9925':'Cyprus','978-9926':'Bosnia and Herzegovina','978-9927':'Qatar','978-9928':'Albania','978-9929':'Guatemala','978-9930':'Costa Rica','978-9931':'Algeria','978-9932': "Lao People's Democratic Republic", '978-9933':'Syria','978-9934':'Latvia','978-9935':'Iceland','978-9936':'Afghanistan','978-9937':'Nepal','978-9938':'Tunisia','978-9939':'Armenia','978-9940':'Montenegro','978-9941':'Georgia','978-9942':'Ecuador','978-9943':'Uzbekistan','978-9944':'Turkey','978-9945':'Dominican Republic','978-9946':'Korea, P.D.R.','978-9947':'Algeria','978-9948':'United Arab Emirates','978-9949':'Estonia','978-9950':'Palestine','978-9951':'Kosova','978-9952':'Azerbaijan','978-9953':'Lebanon','978-9954':'Morocco','978-9955':'Lithuania','978-9956':'Cameroon','978-9957':'Jordan','978-9958':'Bosnia and Herzegovina','978-9959':'Libya','978-9960':'Saudi Arabia','978-9961':'Algeria','978-9962':'Panama','978-9963':'Cyprus','978-9964':'Ghana','978-9965':'Kazakhstan','978-9966':'Kenya','978-9967':'Kyrgyz Republic','978-9968':'Costa Rica','978-9969':'Algeria','978-9970':'Uganda','978-9971':'Singapore','978-9972':'Peru','978-9973':'Tunisia','978-9974':'Uruguay','978-9975':'Moldova','978-9976':'Tanzania','978-9977':'Costa Rica','978-9978':'Ecuador','978-9979':'Iceland','978-9980':'Papua New Guinea','978-9981':'Morocco','978-9982':'Zambia','978-9983':'Gambia','978-9984':'Latvia','978-9985':'Estonia','978-9986':'Lithuania','978-9987':'Tanzania','978-9988':'Ghana','978-9989':'North Macedonia','978-99901':'Bahrain','978-99902':'Reserved Agency','978-99903':'Mauritius','978-99904':'Curaçao','978-99905':'Bolivia','978-99906':'Kuwait','978-99908':'Malawi','978-99909':'Malta','978-99910':'Sierra Leone','978-99911':'Lesotho','978-99912':'Botswana','978-99913':'Andorra','978-99914':'International NGO Publishers','978-99915':'Maldives','978-99916':'Namibia','978-99917':'Brunei Darussalam','978-99918':'Faroe Islands','978-99919':'Benin','978-99920':'Andorra','978-99921':'Qatar','978-99922':'Guatemala','978-99923':'El Salvador','978-99924':'Nicaragua','978-99925':'Paraguay','978-99926':'Honduras','978-99927':'Albania','978-99928':'Georgia','978-99929':'Mongolia','978-99930':'Armenia','978-99931':'Seychelles','978-99932':'Malta','978-99933':'Nepal','978-99934':'Dominican Republic','978-99935':'Haiti','978-99936':'Bhutan','978-99937':'Macau','978-99938':'Srpska, Republic of','978-99939':'Guatemala','978-99940':'Georgia','978-99941':'Armenia','978-99942':'Sudan','978-99943':'Albania','978-99944':'Ethiopia','978-99945':'Namibia','978-99946':'Nepal','978-99947':'Tajikistan','978-99948':'Eritrea','978-99949':'Mauritius','978-99950':'Cambodia','978-99951':'Reserved Agency','978-99952':'Mali','978-99953':'Paraguay','978-99954':'Bolivia','978-99955':'Srpska, Republic of','978-99956':'Albania','978-99957':'Malta','978-99958':'Bahrain','978-99959':'Luxembourg','978-99960':'Malawi','978-99961':'El Salvador','978-99962':'Mongolia','978-99963':'Cambodia','978-99964':'Nicaragua','978-99965':'Macau','978-99966':'Kuwait','978-99967':'Paraguay','978-99968':'Botswana','978-99969':'Oman','978-99970':'Haiti','978-99971':'Myanmar','978-99972':'Faroe Islands','978-99973':'Mongolia','978-99974':'Bolivia','978-99975':'Tajikistan','978-99976':'Srpska, Republic of','978-99977':'Rwanda','978-99978':'Mongolia','978-99979':'Honduras','978-99980':'Bhutan','978-99981':'Macau','978-99982':'Benin','978-99983':'El Salvador','978-99984':'Brunei Darussalam','978-99985':'Tajikistan','978-99986':'Myanmar','978-99987':'Luxembourg','978-99988':'Sudan','978-99989':'Paraguay','978-99990':'Ethiopia','978-99992':'Oman','978-99993':'Mauritius','979-10':'France','979-11':'Korea, Republic','979-12':'Italy','979-8':'United States'}


VECTOR = [
    HEIGHT//2, 
    WIDTH//10, 
    HEIGHT//(2*10), 
    WIDTH//100, 
    HEIGHT//(2*100),
    WIDTH//1000 
]

def get_recursive_xy(position):
    coords = [0, 0]  # [x, y]
    isbn_str = str(position).zfill(LEN_SHORT_ISBN)
    # Process remaining digits
    for i in range(len(VECTOR)):
        digit = int(isbn_str[i])
        coords[(i+1) % 2] += digit * VECTOR[i]

    last_four = int(isbn_str[len(VECTOR):])
    coords[1] += last_four // SCALE_SQUARED
    #print(f"{isbn_str} {coords}")
    return coords[0], coords[1]

def find_isbn_from_xy(x, y):
    # Try all possible combinations for the last 4 digits
    for last_four in [0, 2500, 5000, 7500]:
        # Start with empty isbn
        isbn_digits = [0] * LEN_SHORT_ISBN
        
        # Set the last digits from last_four
        isbn_digits[len(VECTOR):] = [int(d) for d in str(last_four).zfill(4)]
        
        remaining_x = x
        remaining_y = y - (last_four // SCALE_SQUARED)
        
        for i in range(len(VECTOR)):
            if (i+1) % 2 == 0:  # x coordinate
                digit = remaining_x // VECTOR[i]
                remaining_x = remaining_x % VECTOR[i]
            else:  # y coordinate
                digit = remaining_y // VECTOR[i]
                remaining_y = remaining_y % VECTOR[i]
            if 0 <= digit <= 9:
                isbn_digits[i] = digit
            else:
                break
                
        if remaining_x == 0 and remaining_y == 0:
            isbn = int(''.join(map(str, isbn_digits)))
            return 978000000000 + isbn



def color_image(image, packed_isbns_binary, addcolor=None):
    packed_isbns_ints = struct.unpack(f"{len(packed_isbns_binary) // 4}I", packed_isbns_binary)
    isbn_streak = True  # Alternate between reading `isbn_streak` and `gap_size`.
    position = 0  # ISBN (without check digit) is `978000000000 + position`.
    for value in tqdm.tqdm(packed_isbns_ints):
        if isbn_streak:
            remaining = value
            #optimisation : count up to "SCALE_SQUARED" and then putpixel
            while remaining > 0:
                count = min(remaining, SCALE_SQUARED - (position % SCALE_SQUARED))
                remaining -= count
                if remaining <= 0:
                    x,y = get_recursive_xy(position)
                    if x < image.width and y < image.height:
                        current_value = image.getpixel((x, y))
                        image.putpixel((x, y), current_value + (count * addcolor))
                    else:
                        print(f"Pixel out of image {position} - {x} - {y}!!!")
                position += count
        else:  # Reading `gap_size`.
            position += value
        isbn_streak = not isbn_streak


def color_image_unique(image, packed_isbns_binary, processed_isbns, addcolor=None, ):
    """
    Count isbn only once per square by keeping track of added one in processed_isbns
    """
    packed_isbns_ints = struct.unpack(f"{len(packed_isbns_binary) // 4}I", packed_isbns_binary)
    isbn_streak = True
    position = 0
    for value in tqdm.tqdm(packed_isbns_ints):
        if isbn_streak:
            for _ in range(0, value):
                current_isbn = 978000000000 + position
                if current_isbn not in processed_isbns:
                    x,y = get_recursive_xy(position)
                    if x < image.width and y < image.height:
                        image.putpixel((x, y), addcolor + image.getpixel((x, y)))
                        processed_isbns.add(current_isbn)
                    else:
                        print(f"Pixel out of image {position} - {x} - {y}!!!")
                position += 1
        else:
            position += value
        isbn_streak = not isbn_streak


def main():
    args = docopt(__doc__)
    # Get the latest from the `codes_benc` directory in `aa_derived_mirror_metadata`:
    # https://annas-archive.org/torrents#aa_derived_mirror_metadata
    args = docopt(__doc__)
    input_filename = args['--input']
    suffix = args['--suffix']
    output_dir = args['--output']

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    isbn_data = bencodepy.bread(zstandard.ZstdDecompressor().stream_reader(open(input_filename, "rb")))
    
    print(f"### Generating {output_dir}/*{suffix}.png...")
    for prefix, packed_isbns_binary in isbn_data.items():
        filename = f"{output_dir}/{prefix.decode()}{suffix}.png"
        print(f"Generating {filename}...")
        prefix_isbns_png_smaller = Image.new("F", (1000, 800), 0.0)
        color_image(
            prefix_isbns_png_smaller,
            packed_isbns_binary,
            addcolor=1.0 / float(SCALE_SQUARED),
        )
        prefix_isbns_png_smaller.point(lambda x: x * 255).convert("L").save(filename)

    print(f"### Generating {output_dir}/all{suffix}.png...")
    all_isbns_png_smaller_red = Image.new("F", ((1000, 800)), 0.0)
    all_isbns_png_smaller_green = Image.new("F", ((1000, 800)), 0.0)
    # Create a set to track processed ISBNs
    processed_isbns = set()
    for prefix, packed_isbns_binary in isbn_data.items():
        if prefix == b"md5":
            continue
        print(f"Adding {prefix.decode()} to {output_dir}/all{suffix}.png")
        color_image_unique(
            all_isbns_png_smaller_red,
            packed_isbns_binary,
            processed_isbns,
            addcolor=1.0 / float(SCALE_SQUARED),
        )
    print(f"Adding md5 to {output_dir}/all{suffix}.png")
    color_image(
        all_isbns_png_smaller_green,
        isbn_data[b"md5"],
        addcolor=1.0 / float(SCALE_SQUARED),
    )
    Image.merge(
        "RGB",
        (
            ImageChops.subtract(all_isbns_png_smaller_red.point(lambda x: x * 255).convert("L"), all_isbns_png_smaller_green.point(lambda x: x * 255).convert("L")),
            all_isbns_png_smaller_green.point(lambda x: x * 255).convert("L"),
            Image.new("L", all_isbns_png_smaller_red.size, 0),
        ),
    ).save(f"{output_dir}/all{suffix}.png")

    print("Done.")


if __name__ == "__main__":
    main()
