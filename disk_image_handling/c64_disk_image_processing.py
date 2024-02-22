import json
from d64 import DiskImage
import glob
from disk_image_handling.c64_disk_image_processing_utils import *
import os
from tqdm import tqdm
from zipfile import ZipFile, BadZipfile
import textwrap
import numpy as np


class Corpus:
    def __init__(self, corpus_name, corpus_path):
        if not os.path.exists(corpus_path):
            raise ValueError('The path to the corpus seems to be invalid')
        self.corpus_name = corpus_name
        self.corpus_path = corpus_path
        self.files = self.get_files()

    def unpack(self, remove_zip=False):
        """
        Users are allowed to unpack available .zip archives
        and save them in the same folders
        """
        paths = glob.glob(os.path.join(self.corpus_path, '**', '*.zip'), recursive=True)
        paths.extend(glob.glob(os.path.join(self.corpus_path, '**', '*.ZIP'), recursive=True))
        paths = set(paths)
        if not paths:
            print(f'There are no .zip files in the directory')
        else:
            for path in tqdm(paths, desc='Unpacking .zip files', unit='file'):
                target_dir = os.path.dirname(path)
                try:
                    with ZipFile(path, 'r') as zip_ref:
                        zip_ref.extractall(path=target_dir)
                except (BadZipfile, NotImplementedError) as e:
                    print(f'Unable to open the archive "{os.path.basename(path)}": {e}')
                if remove_zip:
                    os.remove(path)

    def get_files(self):
        """
        Get a list of all files in the corpus and save it to a text file
        """
        for root, _, files in os.walk(self.corpus_path):
            for file in files:
                yield os.path.relpath(os.path.join(root, file), start=self.corpus_path)

    def save_file_list(self):
        """
        Save the list of all files in the corpus to a text
        """
        with open(f'{self.corpus_path}/{self.corpus_name}_filelist.txt', 'w', encoding='utf-8') as txt_file:
            txt_file.write(f'List of all files in the corpus {self.corpus_name}\n\n')
            for file in self.get_files():
                txt_file.write(f'{file}\n')


class DiskmagC64:
    def __init__(self, diskmag_path: str, char_threshold: float, line_length: int):
        self.image = DiskImage(diskmag_path)
        self.path = diskmag_path
        self.char_threshold = char_threshold
        self.line_length = line_length
        self.filename = os.path.basename(diskmag_path)
        self.diskmag = os.path.basename(os.path.dirname(os.path.dirname(diskmag_path)))
        self.issue = os.path.split(os.path.dirname(diskmag_path))[-1]

    def show_directory(self):
        with self.image as disk_image:
            #directory = [program.name.decode('petscii_c64en_lc') for program in disk_image.glob(b'*')]
            directory = list(disk_image.directory())[1:-1]
            #directory = [elem.decode('petscii_c64en_lc', errors='replace') for elem in directory]
            return '\n'.join(directory)

    def convert_to_text(self):
        with self.image as disk_image:
            for program_file in disk_image.glob(b'*'):
                program = ProgramFileC64(disk_image.path(program_file.name))
                content = program.content
                print (decode_text(binary_text=content, threshold=0.5))

    def convert_to_txt(self):
        with open(f'{os.path.dirname(self.path)}/{self.filename}.txt', 'w', encoding='utf-8') as txt_file:
            with self.image as disk_image:
                directory = list(disk_image.directory())[1:-1]
                txt_file.write('\t\tVerzeichnis:\n\n')
                txt_file.write('\n'.join(directory))
                txt_file.write('\n\n\t\tInhalte:\n')
                dir = disk_image.directory()
                for filename, program_file in zip(directory, disk_image.glob(b'*')):
                    program = ProgramFileC64(disk_image.path(program_file.name))
                    content = program.content
                    text = decode_text(binary_text=content, threshold=self.char_threshold)
                    wrapper = textwrap.TextWrapper(width=self.line_length)
                    text = wrapper.fill(text)
                    txt_file.write(f'\n\t{program_file.name.decode("petscii_c64en_lc", errors="replace")}\n')
                    if 'DEL' in filename:
                        txt_file.write(f'\nDeleted file\n')
                    else:
                        txt_file.write(f'\n{text}\n')

    def save_metadata(self):
        file_name = '../raw_code/metadata.json'
        size = os.path.getsize(self.path) / 1024
        amount_of_files = len(self.show_directory())
        extensions = {ext[-3:] for ext in self.show_directory()}
        metadata = {
            'file': self.filename,
            'diskmag': self.diskmag,
            'issue': self.issue,
            'location of converted diskmag': create_title_path(self.path),
            'location': self.path,
            'size in kb': size,
            'amount of files': amount_of_files,
            'available extensions': ', '.join(extensions)
        }
        if os.path.exists(file_name) and os.path.getsize(file_name) > 0:
            with open(file_name, 'r+', encoding='utf-8') as metadata_file:
                try:
                    file_data = json.load(metadata_file)
                except json.JSONDecodeError:
                    file_data = []
                file_data.append(metadata)
                metadata_file.seek(0)
                json.dump(file_data, metadata_file, indent=4)
                metadata_file.truncate()
        else:
            with open(file_name, 'w', encoding='utf-8') as metadata_file:
                json.dump([metadata], metadata_file, indent=4)


class ProgramFileC64:
    def __init__(self, file):
        self.file = file.open()
        try:
            self.content = self.file.read()
        except (AttributeError, ValueError) as e:
            self.content = None