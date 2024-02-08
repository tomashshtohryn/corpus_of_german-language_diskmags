from typing import Tuple
import cbmcodecs2
from collections import Counter
import os
import re
from scipy.stats import entropy
import numpy as np


def decode_text(binary_text: bytes, threshold: float) -> Tuple[str, str]:
    if not isinstance(binary_text, bytes):
        raise TypeError('Input must be a bytes object')
    if check_entropy(binary_text) > 7:
        return 'Compressed file', 'Unknown encoding'
    encoding_mapping = {0: 'ascii', 1: 'petscii_c64en_lc', 2: 'screencode_c64_lc'}
    texts = []
    sum_chars = []
    for encoding in encoding_mapping.values():
        decoded = binary_text.decode(encoding=encoding, errors='replace')
        texts.append(decoded)
        chars = [character for character in decoded if character.isalpha()]
        sum_chars.append(len(chars) / len(decoded))
    best_encoding = np.argmax(np.array(sum_chars))
    if max(sum_chars) < threshold:
        return 'Code', encoding_mapping[best_encoding]
    else:
        return texts[best_encoding], encoding_mapping[best_encoding]


def check_entropy(binary_text: bytes) -> int:
    """
    The functions checks shannon's entropy of the binary file
    :param binary_text: Binary version of some diskmag program
    :return: Returns the entropy value
    """
    binary_text_size = len(binary_text)
    character_counts = Counter(binary_text)
    dist = [char / binary_text_size for char in character_counts.values()]
    entropy_value = entropy(np.array(dist), base=2)
    return entropy_value


def replace_alt_umlauts(string: str) -> str:
    """
    The function takes a string and returns new string
    where alternative umlaut representations are replaced
    with german umlaut representations
    :param string: The string which should be processed by function
    :return: string with fixed umlauts
    """
    alternative_umlauts = {'ae': 'ä', 'Ae': 'Ä', 'oe': 'ö', 'Oe': 'Ö', 'ue': 'ü', 'Ue': 'ü', 'ss': 'ß'}
    pattern = re.compile('|'.join(alternative_umlauts.keys()))
    fixed_string = pattern.sub(lambda match: alternative_umlauts[match.group(0)], string)
    return fixed_string


def create_title_path(file_path: str) -> str:
    """
    The function returns the full path to the converted file
    :param file_path: Full path to the disk image
    :return: Returns full path to the converted file
    """
    folder_path, filename = os.path.split(file_path)
    folder_name_sanitized = os.path.basename(folder_path).lower().replace(' ', '_')
    file_index = os.listdir(folder_path).index(filename) + 1
    new_filename = f'{folder_name_sanitized}_{file_index}.txt'
    return os.path.join(folder_path, new_filename)

# def convert_diskmag(path:str, base_file_name:str, full_file_name:str):
#     with DiskImage(path) as image:
#         content_table = image.directory()
#         with open(f'{base_file_name}.txt', 'w', encoding='utf-16') as text_file:
#             # Write title and table of contents
#             text_file.write(f'Datei: {full_file_name}\n\nInhaltsverzeichnis:\n')
#             for program_file in content_table: text_file.write(f'{program_file}\n')
#             text_file.write('\n')
#
#             # Write contents
#             directory = image.directory()
#             next(directory)
#             for filename, program in zip(directory, image.glob(b'*')):
#                 text_file.write(f'{filename}\n')
#                 if 'DEL' in filename: text_file.write(f'Gelöschte Datei\n\n')
#                 else:
#                     try:
#                         pass
#                     except (AttributeError, FileNotFoundError, ValueError) as e:
#                         text_file.write(f'Korrupte Datei. Fehler: {e}\n\n')