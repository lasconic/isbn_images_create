"""Generate ISBN images from encoded data.

Usage:
    make_isbn_json.py [options]

Options:
    -p --publisher-file=<file>    Input filename [default: annas_archive_meta__aacid__isbngrp_records__20240920T194930Z--20240920T194930Z.jsonl.seekable.zst]
    -o --output=<file>    Generate GeoJSON output to specified file
    --label-point    Output labels as points [default: True]
    --max-prefix-len=<len>    Maximum prefix length for publishers [default: 6]
    --scale=<scale>    GeoJSON scale factor [default: 32]
    --hd    Use high definition recursive XY function
    -h --help    Show this help message
"""

from make_isbn_images_fractal_cluster import get_recursive_xy as get_recursive_xy_ld
from make_isbn_images_fractal import get_recursive_xy as get_recursive_xy_hd
from docopt import docopt
import io
import tqdm
from collections import defaultdict
import zstandard as zstd
import json

get_recursive_xy = None

countries={'978-0':'English language','978-1':'English language','978-2':'French language','978-3':'German language','978-4':'Japan','978-5':'former U.S.S.R','978-600':'Iran','978-601':'Kazakhstan','978-602':'Indonesia','978-603':'Saudi Arabia','978-604':'Vietnam','978-605':'Turkey','978-606':'Romania','978-607':'Mexico','978-608':'North Macedonia','978-609':'Lithuania','978-611':'Thailand','978-612':'Peru','978-613':'Mauritius','978-614':'Lebanon','978-615':'Hungary','978-616':'Thailand','978-617':'Ukraine','978-618':'Greece','978-619':'Bulgaria','978-620':'Mauritius','978-621':'Philippines','978-622':'Iran','978-623':'Indonesia','978-624':'Sri Lanka','978-625':'Turkey','978-626':'Taiwan','978-627':'Pakistan','978-628':'Colombia','978-629':'Malaysia','978-630':'Romania','978-631':'Argentina','978-65':'Brazil','978-7': "China, People's Republic", '978-80':'former Czechoslovakia','978-81':'India','978-82':'Norway','978-83':'Poland','978-84':'Spain','978-85':'Brazil','978-86':'former Yugoslavia','978-87':'Denmark','978-88':'Italy','978-89':'Korea, Republic','978-90':'Netherlands','978-91':'Sweden','978-92':'International NGO Publishers and EU Organizations','978-93':'India','978-94':'Netherlands','978-950':'Argentina','978-951':'Finland','978-952':'Finland','978-953':'Croatia','978-954':'Bulgaria','978-955':'Sri Lanka','978-956':'Chile','978-957':'Taiwan','978-958':'Colombia','978-959':'Cuba','978-960':'Greece','978-961':'Slovenia','978-962':'Hong Kong, China','978-963':'Hungary','978-964':'Iran','978-965':'Israel','978-966':'Ukraine','978-967':'Malaysia','978-968':'Mexico','978-969':'Pakistan','978-970':'Mexico','978-971':'Philippines','978-972':'Portugal','978-973':'Romania','978-974':'Thailand','978-975':'Turkey','978-976':'Caribbean Community','978-977':'Egypt','978-978':'Nigeria','978-979':'Indonesia','978-980':'Venezuela','978-981':'Singapore','978-982':'South Pacific','978-983':'Malaysia','978-984':'Bangladesh','978-985':'Belarus','978-986':'Taiwan','978-987':'Argentina','978-988':'Hong Kong, China','978-989':'Portugal','978-9910':'Uzbekistan','978-9911':'Montenegro','978-9912':'Tanzania','978-9913':'Uganda','978-9914':'Kenya','978-9915':'Uruguay','978-9916':'Estonia','978-9917':'Bolivia','978-9918':'Malta','978-9919':'Mongolia','978-9920':'Morocco','978-9921':'Kuwait','978-9922':'Iraq','978-9923':'Jordan','978-9924':'Cambodia','978-9925':'Cyprus','978-9926':'Bosnia and Herzegovina','978-9927':'Qatar','978-9928':'Albania','978-9929':'Guatemala','978-9930':'Costa Rica','978-9931':'Algeria','978-9932': "Lao People's Democratic Republic", '978-9933':'Syria','978-9934':'Latvia','978-9935':'Iceland','978-9936':'Afghanistan','978-9937':'Nepal','978-9938':'Tunisia','978-9939':'Armenia','978-9940':'Montenegro','978-9941':'Georgia','978-9942':'Ecuador','978-9943':'Uzbekistan','978-9944':'Turkey','978-9945':'Dominican Republic','978-9946':'Korea, P.D.R.','978-9947':'Algeria','978-9948':'United Arab Emirates','978-9949':'Estonia','978-9950':'Palestine','978-9951':'Kosova','978-9952':'Azerbaijan','978-9953':'Lebanon','978-9954':'Morocco','978-9955':'Lithuania','978-9956':'Cameroon','978-9957':'Jordan','978-9958':'Bosnia and Herzegovina','978-9959':'Libya','978-9960':'Saudi Arabia','978-9961':'Algeria','978-9962':'Panama','978-9963':'Cyprus','978-9964':'Ghana','978-9965':'Kazakhstan','978-9966':'Kenya','978-9967':'Kyrgyz Republic','978-9968':'Costa Rica','978-9969':'Algeria','978-9970':'Uganda','978-9971':'Singapore','978-9972':'Peru','978-9973':'Tunisia','978-9974':'Uruguay','978-9975':'Moldova','978-9976':'Tanzania','978-9977':'Costa Rica','978-9978':'Ecuador','978-9979':'Iceland','978-9980':'Papua New Guinea','978-9981':'Morocco','978-9982':'Zambia','978-9983':'Gambia','978-9984':'Latvia','978-9985':'Estonia','978-9986':'Lithuania','978-9987':'Tanzania','978-9988':'Ghana','978-9989':'North Macedonia','978-99901':'Bahrain','978-99902':'Reserved Agency','978-99903':'Mauritius','978-99904':'Curaçao','978-99905':'Bolivia','978-99906':'Kuwait','978-99908':'Malawi','978-99909':'Malta','978-99910':'Sierra Leone','978-99911':'Lesotho','978-99912':'Botswana','978-99913':'Andorra','978-99914':'International NGO Publishers','978-99915':'Maldives','978-99916':'Namibia','978-99917':'Brunei Darussalam','978-99918':'Faroe Islands','978-99919':'Benin','978-99920':'Andorra','978-99921':'Qatar','978-99922':'Guatemala','978-99923':'El Salvador','978-99924':'Nicaragua','978-99925':'Paraguay','978-99926':'Honduras','978-99927':'Albania','978-99928':'Georgia','978-99929':'Mongolia','978-99930':'Armenia','978-99931':'Seychelles','978-99932':'Malta','978-99933':'Nepal','978-99934':'Dominican Republic','978-99935':'Haiti','978-99936':'Bhutan','978-99937':'Macau','978-99938':'Srpska, Republic of','978-99939':'Guatemala','978-99940':'Georgia','978-99941':'Armenia','978-99942':'Sudan','978-99943':'Albania','978-99944':'Ethiopia','978-99945':'Namibia','978-99946':'Nepal','978-99947':'Tajikistan','978-99948':'Eritrea','978-99949':'Mauritius','978-99950':'Cambodia','978-99951':'Reserved Agency','978-99952':'Mali','978-99953':'Paraguay','978-99954':'Bolivia','978-99955':'Srpska, Republic of','978-99956':'Albania','978-99957':'Malta','978-99958':'Bahrain','978-99959':'Luxembourg','978-99960':'Malawi','978-99961':'El Salvador','978-99962':'Mongolia','978-99963':'Cambodia','978-99964':'Nicaragua','978-99965':'Macau','978-99966':'Kuwait','978-99967':'Paraguay','978-99968':'Botswana','978-99969':'Oman','978-99970':'Haiti','978-99971':'Myanmar','978-99972':'Faroe Islands','978-99973':'Mongolia','978-99974':'Bolivia','978-99975':'Tajikistan','978-99976':'Srpska, Republic of','978-99977':'Rwanda','978-99978':'Mongolia','978-99979':'Honduras','978-99980':'Bhutan','978-99981':'Macau','978-99982':'Benin','978-99983':'El Salvador','978-99984':'Brunei Darussalam','978-99985':'Tajikistan','978-99986':'Myanmar','978-99987':'Luxembourg','978-99988':'Sudan','978-99989':'Paraguay','978-99990':'Ethiopia','978-99992':'Oman','978-99993':'Mauritius','979-10':'France','979-11':'Korea, Republic','979-12':'Italy','979-8':'United States'}

def calculate_possible_books(prefix):
    # Remove any hyphens
    clean_prefix = prefix.replace('-', '')
    # ISBN-13 is 13 digits long = 12 + 1 control
    remaining_digits = 12 - len(clean_prefix)
    # Calculate possible combinations
    return 10 ** remaining_digits

def get_coordinates_from_prefix(isbn_prefix, geojson_scale):
    clean_prefix = isbn_prefix.replace("-", "").strip()
    # Get start and end of range
    start_isbn = int(clean_prefix.ljust(12, "0")) - 978000000000
    # Calculate end of range (next prefix - 1)
    end_isbn = int(clean_prefix.ljust(12,"9")) - 978000000000

    # Get coordinates for start and end
    start_x, start_y = get_recursive_xy(start_isbn)
    end_x, end_y = get_recursive_xy(end_isbn)
    start_x *= geojson_scale
    start_y *= geojson_scale
    end_x += 1
    end_y += 1
    end_x *= geojson_scale
    end_y *= geojson_scale
        
    # Create polygon coordinates (rectangle)
    return [
            [start_x, start_y],
            [end_x, start_y],
            [end_x, end_y ],
            [start_x, end_y],
            [start_x, start_y]  # Close the polygon
        ]

def get_features_for_publishers(file_path, index, geojson_scale, label_point = True, max_prefix=6):
    prefixes_data = defaultdict(lambda: {'registrants': set()})
    registrant_data = defaultdict(lambda: {'prefix_count': 0, 'possible_books' : 0, 'isbns': set()})


    with open(file_path, 'rb') as fh:
        dctx = zstd.ZstdDecompressor()
        with dctx.stream_reader(fh) as reader:
            text_stream = io.TextIOWrapper(reader, encoding='utf-8')
            print(f"Generate features for publishers with prefix length <= {max_prefix}")
            for line in tqdm.tqdm(text_stream):
                try:
                    record = json.loads(line)
                    metadata = record.get('metadata', {})
                    record_data = metadata.get('record', {})
                    isbns = record_data.get('isbns', [])
                    registrant_name = record_data.get('registrant_name', 'Unknown')
                    possible_books = 0 
                    for isbn in isbns:
                        if isbn.get('isbn_type') == 'prefix':
                            possible_books += calculate_possible_books(isbn.get('isbn'))
                            registrant_data[registrant_name]['prefix_count'] += 1
                        elif isbn.get('isbn_type') == 'isbn13':
                            possible_books += 1
                        else:
                            print(f"UNKNOWN ISBN TYPE !!! {isbn.get('isbn_type')}")
                        registrant_data[registrant_name]['possible_books'] += possible_books
                        registrant_data[registrant_name]['isbns'].update([isbn.get('isbn') for isbn in isbns])

                    # find prefixes <= max_prefix
                    matching_isbns = [isbn.get('isbn') for isbn in isbns 
                                    if isbn.get('isbn_type') == 'prefix' 
                                     and len(isbn.get('isbn').replace('-', '')) <= max_prefix]
                    for isbn in matching_isbns:
                        prefixes_data[isbn.replace('-', '')]["registrants"].add(registrant_name)
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"Error processing line: {e}")
                    continue
        
    # Print all prefix data
    features = []
    for prefix, data in prefixes_data.items():
        print(f"\nPrefix: {prefix}")
        print(f"Registrant count: {len(data['registrants'])}")
        print(f"Registrants: {', '.join(data['registrants'])}")
        # Filter and print prefixes with multiple registrants
        max_books_registrant = ""
        if len(data['registrants']) > 1:
            # Find registrant with most possible books, TODO better heuristic to choose a single publisher to display...
            max_books_registrant = max(data['registrants'], key=lambda x: registrant_data[x]['possible_books'])
        else:
            max_books_registrant = data["registrants"].pop()
        
        print(f"Selected registrant: {max_books_registrant}")
        print(f"Number of possible books: {registrant_data[max_books_registrant]['possible_books']}")        

        # Create GeoJSON features for prefixes
        # Get coordinates for the prefix
        
        # Create polygon feature
        coordinates = get_coordinates_from_prefix(prefix, geojson_scale)
        start_x = coordinates[0][0]
        end_x = coordinates[1][0]
        start_y = coordinates[0][1]
        end_y = coordinates[2][1]
        polygon_feature = {
            "type": "Feature",
            "id": index,
            "geometry": {
                "type": "Polygon",
                "coordinates": [coordinates]
            },
            "properties": {
                "type": "publisher",
                "prefix": prefix,
                "label": max_books_registrant
            }
        }
        features.append(polygon_feature)
        index += 1
        
        # Create point feature for label if requested
        if label_point:
            center_x = (start_x + end_x) / 2
            center_y = (start_y + end_y) / 2
            point_feature = {
                "type": "Feature",
                "id": index,
                "geometry": {
                    "type": "Point",
                    "coordinates": [center_x, center_y]
                },
                "properties": {
                    "type": "publisher",
                    "prefix": prefix,
                    "label": max_books_registrant,
                    "width": end_x - start_x,
                    "height": end_y - start_y,
                }
            }
            features.append(point_feature)
            index+=1

    return features




def generate_geojson(output_file, geojson_scale, label_point=True, publisher_file = None, max_prefix=6):
    """Generate GeoJSON file containing country ISBN ranges as polygons."""
    features = []
    i = 1
    print("Generate features for countries")
    for isbn_prefix, country_name in tqdm.tqdm(countries.items()):
        # Create polygon coordinates (rectangle)
        coordinates = get_coordinates_from_prefix(isbn_prefix, geojson_scale)
        start_x = coordinates[0][0]
        end_x = coordinates[1][0]
        start_y = coordinates[0][1]
        end_y = coordinates[2][1]
        feature = {
            "type": "Feature",
            "id": i,
            "geometry": {
                "type": "Polygon",
                "coordinates": [coordinates]
            },
            "properties": {
                "type": "country",
                "prefix": isbn_prefix,
                "label": country_name
            }
        }
        features.append(feature)
        i += 1

        # Add label point feature if requested
        if label_point:
            center_x = (start_x + end_x) / 2
            center_y = (start_y + end_y) / 2
            point_feature = {
                "type": "Feature",
                "id": i,
                "geometry": {
                    "type": "Point",
                    "coordinates": [center_x, center_y]
                },
                "properties": {
                    "type": "country",
                    "prefix": isbn_prefix,
                    "label": country_name,
                    "width": end_x - start_x,
                    "height": end_y - start_y,
                }
            }
            features.append(point_feature)
            i +=1
        
    if publisher_file is not None:
        pub_features = get_features_for_publishers(publisher_file, i, geojson_scale, label_point= label_point, max_prefix=max_prefix)
        features.extend(pub_features)

    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    # Save GeoJSON file
    with open(output_file, 'w') as f:
        json.dump(geojson, f, indent=2)
    
    print(f"GeoJSON file generated: {output_file}")


def main():
    args = docopt(__doc__)
    publisher_file = args['--publisher-file']
    geojson_file = args['--output']
    label_point = args['--label-point']
    max_prefix = int(args['--max-prefix-len'])
    geojson_scale = int(args['--scale'])


    global get_recursive_xy
    get_recursive_xy = get_recursive_xy_hd if args['--hd'] else get_recursive_xy_ld

    if geojson_file:
        generate_geojson(
            geojson_file, 
            geojson_scale, 
            label_point=label_point, 
            publisher_file=publisher_file, 
            max_prefix=max_prefix
        )

    print("Done.")


if __name__ == "__main__":
    main()
