"""ISBN Prefix Analyzer.

Usage:
    isbn_analyzer.py --prefix=<prefix>
    isbn_analyzer.py --unique-isbns
    isbn_analyzer.py (-h | --help)

Options:
    -h --help           Show this screen.
    --prefix=<prefix>   ISBN prefix to analyze (e.g., "978-0-00")
    --unique-isbns      Show all unique ISBN prefixes sorted by length
"""

import zstandard as zstd
import json
from collections import defaultdict
import io
from docopt import docopt

def get_unique_isbns(file_path):
    unique_prefixes = set()
    unique_countries = set()
    unique_agencies = set()
    unique_registrants = set()

    with open(file_path, 'rb') as fh:
        dctx = zstd.ZstdDecompressor()
        with dctx.stream_reader(fh) as reader:
            text_stream = io.TextIOWrapper(reader, encoding='utf-8')

            for line in text_stream:
                try:
                    record = json.loads(line)
                    metadata = record.get('metadata', {})
                    record_data = metadata.get('record', {})
                    unique_countries.add(record_data.get("country_name"))
                    unique_agencies.add(record_data.get("agency_name"))
                    registrant_name =  record_data.get("registrant_name", f'{record_data.get("country_name")} - {record_data.get("agency_name")} - None')
                    if not registrant_name:
                        registrant_name = f'{record_data.get("country_name")} - {record_data.get("agency_name")} - None'
                    unique_registrants.add(registrant_name)
                    isbns = record_data.get('isbns', [])

                    for isbn in isbns:
                        if isbn.get('isbn_type') == 'prefix':
                            unique_prefixes.add(isbn.get('isbn', ''))

                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"Error processing line: {e}")
                    continue

    # Sort prefixes first by length, then numerically
    sorted_prefixes = sorted(unique_prefixes, key=lambda x: (len(x.replace('-', '')), x))
    sorted_agencies = sorted(unique_agencies)
    sorted_countries = sorted(unique_countries)
    sorted_registrants = sorted(unique_registrants)
    return sorted_prefixes, sorted_agencies, sorted_countries, sorted_registrants


def calculate_possible_books(prefix):
    # Remove any hyphens
    clean_prefix = prefix.replace('-', '')
    # ISBN-13 is 13 digits long
    remaining_digits = 13 - len(clean_prefix)
    # Calculate possible combinations
    return 10 ** remaining_digits

def process_zst_file(file_path, target_prefix):
    registrant_data = defaultdict(lambda: {'count': 0, 'possible_books' : 0, 'isbns': set()})

    with open(file_path, 'rb') as fh:
        dctx = zstd.ZstdDecompressor()
        with dctx.stream_reader(fh) as reader:
            text_stream = io.TextIOWrapper(reader, encoding='utf-8')

            for line in text_stream:
                try:
                    record = json.loads(line)
                    metadata = record.get('metadata', {})
                    record_data = metadata.get('record', {})
                    isbns = record_data.get('isbns', [])

                    matching_isbns = [isbn.get('isbn') for isbn in isbns 
                                    if isbn.get('isbn_type') == 'prefix' 
                                    and isbn.get('isbn', '') == target_prefix]
                    
                    if matching_isbns:
                        registrant_name = record_data.get('registrant_name', 'Unknown')
                        possible_books = 0 
                        for isbn in isbns:
                            if isbn.get('isbn_type') == 'prefix':
                                possible_books += calculate_possible_books(isbn.get('isbn'))
                            elif isbn.get('isbn_type') == 'isbn13':
                                possible_books += 1
                            else:
                                print(isbn)
                                exit
                        registrant_data[registrant_name]['possible_books'] += possible_books
                        registrant_data[registrant_name]['count'] += len(isbns)
                        registrant_data[registrant_name]['isbns'].update([isbn.get('isbn') for isbn in isbns])

                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"Error processing line: {e}")
                    continue

    # Sort by count in descending order
    sorted_data = sorted(registrant_data.items(), 
                        key=lambda x: (x[1]['count'], x[1]['possible_books']), 
                        reverse=True)
    return sorted_data

def main():
    arguments = docopt(__doc__)
    file_path = "annas_archive_meta__aacid__isbngrp_records__20240920T194930Z--20240920T194930Z.jsonl.seekable.zst"

    if arguments.get('--unique-isbns', ''):
        print("\nListing all unique ISBN prefixes sorted by length:")
        print("-" * 50)
        
        prefixes, agencies, countries, registrants = get_unique_isbns(file_path)
        current_length = 0
        count = 0
        max_len = 6
        for prefix in prefixes:
            prefix_length = len(prefix.replace('-', ''))
            if prefix_length != current_length:
                current_length = prefix_length
                if current_length <= max_len:
                    print(f"\nLength {current_length}:")
            if current_length <= max_len:
                print(f"    {prefix}:")
                count += 1
                
        print(f"Prefixes of len <= {max_len} : {count}")
        
        print(f"\nTotal unique prefixes found: {len(prefixes)}")
        print(f"\nTotal unique countries found: {len(countries)}")
        print(f"\nTotal unique agencies found: {len(agencies)}")
        print(f"\nTotal unique registrants found: {len(registrants)}")
        return

    target_prefix = arguments['--prefix']

    print(f"\nAnalyzing ISBN prefix: {target_prefix}")
    print("-" * 70)

    results = process_zst_file(file_path, target_prefix)

    if results:
        print(results)
        print(f"{'Registrant Name':40} {'Number of books':15} {'Number of ISBNs':15}")
        print("-" * 55)
        
        # Print top 10 registrants with their ISBNs
        for registrant, data in results[:10]:
            print(f"\n{registrant:40} {data['possible_books']:15} {data['count']:15}")
            print("ISBNs:")
            for isbn in sorted(data['isbns'])[:20]:  # Show up to 20 ISBNs
                print(f"    {isbn}")
            if len(data['isbns']) > 20:
                print(f"    ... and {len(data['isbns']) - 20} more")
            print("-" * 55)  # Add separator between registrants
    else:
        print(f"No records found for prefix {target_prefix}")

    print(f"\nTotal unique registrants found: {len(results)}")


if __name__ == '__main__':
    main()