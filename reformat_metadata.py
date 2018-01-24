import argparse
import csv
import logging
from logging import config as logger_config
import os
import xml.etree.ElementTree as ET


def main():
    script_path = os.path.dirname(os.path.realpath(__file__))
    log_config = os.path.join(script_path, '../conf/logger.conf')

    if os.path.exists('/etc/goldfinch/logger.conf'):
        logger_config.fileConfig('/etc/goldfinch/logger.conf')
    elif os.path.exists(log_config) and os.path.isfile(log_config):
        logger_config.fileConfig(log_config)

    logger = logging.getLogger('genopheno')
    logger.debug('Parsing command-line arguments')

    input_dir, output_file = parse_args()

    samples = []
    keys = set()

    for root, subdirs, files in os.walk(input_dir):
        if root.endswith('/xmls/samples'):
            for f in files:
                tree = ET.parse(os.path.join(root, f))
                xml_root = tree.getroot()

                for child in xml_root:
                    new_sample = child.attrib
                    new_sample['files'] = []
                    for ident in child.findall('IDENTIFIERS'):
                        new_sample['Primary Identifier'] = ident.find('PRIMARY_ID').text
                        new_sample['Submitter ID'] = ident.find('SUBMITTER_ID').text

                    for sample_name in child.findall('SAMPLE_NAME'):
                        new_sample['Organism'] = sample_name.find('COMMON_NAME').text

                    for sample in child.findall('SAMPLE_ATTRIBUTES'):
                        for attr in sample.findall('SAMPLE_ATTRIBUTE'):
                            new_sample[attr.find('TAG').text] = attr.find('VALUE').text

                    keys |= set(new_sample.keys())
                    samples.append(new_sample)

    map_file = os.path.join(input_dir, 'delimited_maps', 'Sample_File.map')
    if os.path.exists(map_file):
        with open(map_file, 'r') as fh:
            for line in fh:
                parts = line.strip().split()
                new_dict = {
                    'Submitter ID': parts[0],
                    'sample_accession': parts[1],
                    'file_name': parts[2],
                    'file_accession': parts[3]
                }

                for item in samples:
                    if item['Submitter ID'] == new_dict['Submitter ID']:
                        item['files'].append(new_dict)
                        break

    keys = list(keys)
    keys.sort()

    with open(output_file, 'w') as oh:
        handle = csv.DictWriter(oh, keys)
        handle.writeheader()
        handle.writerows(samples)


def parse_args():
    """
    Parse the command-line arguments and extract the input directory and output file
    :return: tuple of input directory, output file
    """
    parser = argparse.ArgumentParser(description="Reformat XML metadata to a .csv file")
    parser.add_argument('-i', '--input_dir', help='The path to the metadata directory', type=str,
                        dest='input_dir', required=True)
    parser.add_argument('-u', '--outputfile', help='The path to write the reformatted output to', type=str,
                        dest='outputfile', default=None, required=True)

    args = parser.parse_args()

    # Confirm that each input file really exists
    if not os.path.isdir(args.input_dir) or not os.path.exists(args.input_dir):
        quit('Oops - I couldn\'t find the input directory you gave me: %s' % args.input_dir)

    # Check if the directory where the output file will live exists
    if not os.path.exists(os.path.dirname(args.outputfile)):
        os.makedirs(os.path.dirname(args.outputfile), 0o770)

    return args.input_dir, args.outputfile


if __name__ == "__main__":
    main()
