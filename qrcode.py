from polynomials import generate_message_polynomial, perform_long_division
import re
from math import ceil
from mode import Mode
from typing import Optional
from pprint import pprint
import sys
from PIL import Image, ImageDraw
from color import *
from anchor_position import AnchorPosition 
from mask_pattern import MaskPattern
from error_correction import ErrorCorrection
from constants import alignment_patterns_locations
from utils import golay, to_color, bose_chaudhuri_hocquenghem
from encoding import to_alphanumeric
from square import Square

class QRCode():

    version: int # 1 <= V <= 40
    size: int
    matrix: list[list[Optional[bool]]]
    error_correction_level: ErrorCorrection
    mask_pattern: Optional[int]
    data: list[tuple[Mode, str]] = []

    def __init__(self,
                 version: int = 7,
                 error_correction_level: ErrorCorrection = ErrorCorrection.LOW,
                 mask_pattern: int = None
             ):
        self.version = version
        self.size = (4 * self.version) + 17
        self.error_correction_level = error_correction_level
        self.mask_pattern = mask_pattern

    def add_data(self, data: str, mode: Mode=Mode.ALPHANUMERIC):
        # TODO: Some sort of length validation for all modes
        # TODO: Some sort of whole data validation maybe? I probably want an Encoding class with abstract methods which are imlemented?
        if(mode == Mode.ALPHANUMERIC and len(data) > 511):
            raise ValueError("Alphanumeric data is over 511 characters long and needs to be broken into multiple segments")
        self.data.append((mode, data))

    def generate(self):
        self._generate_matrix()
        self._add_finder_patterns()
        self._add_separators()
        self._add_alignment_patterns()
        self._add_timing_patterns()
        self._add_dark_module()
        self._reserve_format_information_area()
        self._add_version_information_area()
        self._add_data()
        self._add_data_mask()
        self._add_format_information_area()

    def _generate_matrix(self):
        self.matrix = [[Square() for _ in range(self.size)] for _ in range(self.size)]
        #pprint(self.matrix)

    def _place_artifact(self, artifact: list[list[tuple[int, int, int]]], anchorPosition: AnchorPosition, padding_row: int=0, padding_column: int=0):
        match anchorPosition:
            case AnchorPosition.TOP_LEFT:
                row_offset = padding_row
                column_offset = padding_column
            case AnchorPosition.TOP_RIGHT:
                row_offset = padding_row
                column_offset = self.size - len(artifact[0]) - padding_column
            case AnchorPosition.BOTTOM_LEFT:
                row_offset = self.size - len(artifact) - padding_row
                column_offset = padding_column
            case AnchorPosition.BOTTOM_RIGHT:
                row_offset = self.size - len(artifact) - padding_row
                column_offset = self.size - len(artifact[0]) - padding_column
            case _:
                raise ValueError("Invalid AnchorPosition")

        # Make artifact a clone, so we don't impact the original
        artifact = [row[:] for row in artifact]

        # Flip horizontally if position to the right
        if anchorPosition in [AnchorPosition.TOP_RIGHT, AnchorPosition.BOTTOM_RIGHT]:
            for row in range(len(artifact)):
                artifact[row] = list(reversed(artifact[row]))

        # Flip vertically if position to the bottom
        if anchorPosition in [AnchorPosition.BOTTOM_LEFT, AnchorPosition.BOTTOM_RIGHT]:
            artifact = list(reversed(artifact))

        for row in range(len(artifact)):
            for col in range(len(artifact[row])):

                if artifact[row][col] == None: continue
                self.matrix[row + row_offset][col + column_offset].set_color(artifact[row][col]).lock()

    def _add_finder_patterns(self):
        finder_pattern = [
            [BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK],
            [BLACK, WHITE, WHITE, WHITE, WHITE, WHITE, BLACK],
            [BLACK, WHITE, BLACK, BLACK, BLACK, WHITE, BLACK],
            [BLACK, WHITE, BLACK, BLACK, BLACK, WHITE, BLACK],
            [BLACK, WHITE, BLACK, BLACK, BLACK, WHITE, BLACK],
            [BLACK, WHITE, WHITE, WHITE, WHITE, WHITE, BLACK],
            [BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK],
        ]

        self._place_artifact(finder_pattern, AnchorPosition.TOP_LEFT)
        self._place_artifact(finder_pattern, AnchorPosition.TOP_RIGHT)
        self._place_artifact(finder_pattern, AnchorPosition.BOTTOM_LEFT)

    def _add_separators(self):
        separator_pattern = [
            [None, None, None, None, None, None, None, WHITE],
            [None, None, None, None, None, None, None, WHITE],
            [None, None, None, None, None, None, None, WHITE],
            [None, None, None, None, None, None, None, WHITE],
            [None, None, None, None, None, None, None, WHITE],
            [None, None, None, None, None, None, None, WHITE],
            [None, None, None, None, None, None, None, WHITE],
            [WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE],
        ]

        self._place_artifact(separator_pattern, AnchorPosition.TOP_LEFT)
        self._place_artifact(separator_pattern, AnchorPosition.TOP_RIGHT)
        self._place_artifact(separator_pattern, AnchorPosition.BOTTOM_LEFT)

    def _add_alignment_patterns(self):
        # From https://www.arscreatio.com/repositorio/images/n_23/SC031-N-1915-18004Text.pdf#page=87
        locations = alignment_patterns_locations[self.version]

        alignment_pattern = [
            [BLACK, BLACK, BLACK, BLACK, BLACK],
            [BLACK, WHITE, WHITE, WHITE, BLACK],
            [BLACK, WHITE, BLACK, WHITE, BLACK],
            [BLACK, WHITE, WHITE, WHITE, BLACK],
            [BLACK, BLACK, BLACK, BLACK, BLACK],
        ]

        for row in locations:
            for col in locations:
                if self._check_overlap_exists(row, col, len(alignment_pattern)//2): continue
                self._place_artifact(alignment_pattern, AnchorPosition.TOP_LEFT, padding_row=row-2, padding_column=col-2)
                
    def _check_overlap_exists(self, row: int, col: int, radius: int) -> bool:
        return self.matrix[row + radius][col - radius].is_locked() or \
        self.matrix[row + radius][col + radius].is_locked() or \
        self.matrix[row - radius][col - radius].is_locked() or \
        self.matrix[row - radius][col + radius].is_locked()


    def _add_timing_patterns(self):
        for i in range(8, self.size - 8):
            self.matrix[6][i].set_color(BLACK if i % 2 == 0 else WHITE).lock()
            self.matrix[i][6].set_color(BLACK if i % 2 == 0 else WHITE).lock()

    def _add_dark_module(self):
        self.matrix[(4 * self.version) + 9][8].set_color(BLACK).lock()

    def _reserve_format_information_area(self):
        for i in range(self.size - 8, self.size):
            self.matrix[8][i].set_color(GREEN).reserve()
            # Do not overwrite the dark module
            # Technically not needed since that square is locked
            if i == self.size - 8: continue
            self.matrix[i][8].set_color(GREEN).reserve()

        for i in range(6):
            self.matrix[i][8].set_color(GREEN).reserve()
            self.matrix[8][i].set_color(GREEN).reserve()

        self.matrix[7][8].set_color(GREEN).reserve()
        self.matrix[8][7].set_color(GREEN).reserve()
        self.matrix[8][8].set_color(GREEN).reserve()

    def _add_version_information_area(self):
        # According to https://upload.wikimedia.org/wikipedia/commons/4/45/QRCode-2-Structure.png version info is only required when version >= 7
        if self.version < 7: return

        code = list(reversed(golay(self.version)))
        version_artifact = [
            [ to_color(c) for c in code[ 0: 3] ],
            [ to_color(c) for c in code[ 3: 6] ],
            [ to_color(c) for c in code[ 6: 9] ],
            [ to_color(c) for c in code[ 9:12] ],
            [ to_color(c) for c in code[12:15] ],
            [ to_color(c) for c in code[15:18] ],
        ]

        self._place_artifact(version_artifact, AnchorPosition.TOP_LEFT, padding_column=self.size - 11)


        # Rotate the array (modified from https://stackoverflow.com/a/8421412)
        version_artifact = list(zip(*version_artifact))

        self._place_artifact(version_artifact, AnchorPosition.TOP_LEFT, padding_row=self.size - 11)

    def _push_byte(self,
                   byte_data: str,
                   row: int,
                   col: int,
                   is_going_up: bool,
                   is_right: bool) -> tuple[bool, bool]:
        bit_arr = list(byte_data)

        while len(bit_arr) > 0:

            if not self.matrix[row][col].is_locked() and \
                not self.matrix[row][col].is_reserved():
                self.matrix[row][col].set_color(to_color(bit_arr.pop(0)))
                #print("setting color", self.matrix[row][col].get_color())

            if is_right:
                col -= 1
            else:
                col += 1
                if is_going_up:
                    row -= 1
                else:
                    row += 1

            is_right = not is_right


            if row < 0:
                row = 0
                col -= 2
                is_going_up = not is_going_up
            elif row >= self.size:
                row = self.size - 1
                col -= 2
                is_going_up = not is_going_up

            # Column 6 is a special case with no usable space, so skip it
            # https://www.thonky.com/qr-code-tutorial/module-placement-matrix > "Exception: Vertical Timing Pattern"
            if col == 6: col -= 1


            # TODO: Some check for if you hit the vertical timing, probably hardcode a column num

            if col < 0:
                raise Exception("Trying to write off of the map")

        return (row, col, is_going_up, is_right)

    def _add_data(self):
        row: int = self.size - 1
        col: int = self.size - 1
        is_going_up: bool = True
        is_right: bool = True
        inserted_bits = ""

        for mode, data in self.data:
            #print(f"Adding data of type {mode.name.lower()}: \"{data}\"")
            #print(f"First byte of data to add is {bin(mode)} with length 4")
            alphanumeric_bit_string = to_alphanumeric(data)
            #print(alphanumeric_bit_string)
            #row, col, is_going_up, is_right = self._push_byte(alphanumeric_bit_string, row, col, is_going_up, is_right)
            inserted_bits += alphanumeric_bit_string

        # TODO: Make this a lookup from a table
        data_codewords = 13

        bits_required = data_codewords * 8

        maximum_terminator_length = 4

        terminator_required = min(bits_required, len(inserted_bits) + maximum_terminator_length)

        inserted_bits = inserted_bits.ljust(terminator_required, '0')

        if(len(inserted_bits) % 8 != 0):
            next_multiple_of_8 = ceil(len(inserted_bits) / 8)*8
            inserted_bits = inserted_bits.ljust(next_multiple_of_8, '0')

        padding_bytes = ("11101100", "00010001")
        i = 0
        while(len(inserted_bits) < bits_required):
            inserted_bits += padding_bytes[i % 2]
            i += 1

        #print(inserted_bits)

        row, col, is_going_up, is_right = self._push_byte(inserted_bits, row, col, is_going_up, is_right)

        self._add_error_correction_code(inserted_bits, row, col, is_going_up, is_right)
        
    def _add_error_correction_code(self, data_str: str, row, col, is_going_up, is_right):
        # If version is above 2, need to break data in multiple blocks

        #data_str = "0100001101010101010001101000011001010111001001100101010111000010011101110011001000000110000100100000011001100111001001101111011011110110010000100000011101110110100001101111001000000111001001100101011000010110110001101100011110010010000001101011011011100110111101110111011100110010000001110111011010000110010101110010011001010010000001101000011010010111001100100000011101000110111101110111011001010110110000100000011010010111001100101110000011101100000100011110110000010001111011000001000111101100"

        #data_str="00100000010110110000101101111000110100010111001011011100010011010100001101000000111011000001000111101100000100011110110000010001"

        print(len(data_str))

        codewords = re.findall('.{8}', data_str)

        blocks_in_group_1 = 1
        data_codewords_per_group_1_block = 13
        blocks_in_group_2 = 0
        data_codewords_per_group_2_block = 0

        group_1_size = blocks_in_group_1 * data_codewords_per_group_1_block
        group_2_size = blocks_in_group_2 * data_codewords_per_group_2_block

        group_1 = codewords[:group_1_size]
        group_1 = [
            group_1[:data_codewords_per_group_1_block],
            group_1[data_codewords_per_group_1_block:]
        ]
        group_2 = codewords[group_1_size:]
        group_2 = [
            group_2[:data_codewords_per_group_2_block],
            group_2[data_codewords_per_group_2_block:]
        ]

        print("Group1")
        print(group_1)
        print("")

        codewords_to_generate = 13

        message_polynomial_coefficients = generate_message_polynomial(group_1[0])

        ec = perform_long_division(message_polynomial_coefficients, codewords_to_generate).as_integers()

        ec_str = [str(bin(x))[2:].zfill(8) for x in ec]

        print("AHH")
        print(len(ec))
        print(len("".join(ec_str)))

        for ec_byte in ec_str:
            row, col, is_going_up, is_right = self._push_byte(ec_byte, row, col, is_going_up, is_right)

        #print(ec)

        #print(message_polynomial_coefficients)

        #print(group_1)
        #print(group_2)

    def _add_data_mask(self):
        for row in range(self.size):
            for col in range(self.size):

                current_color = BLACK if self.matrix[row][col].get_color() == BLACK else WHITE
                alternate_color = WHITE if self.matrix[row][col].get_color() == BLACK else BLACK

                if self.matrix[row][col].is_reserved() or self.matrix[row][col].is_locked(): continue

                self.matrix[row][col].set_color(alternate_color if MaskPattern[0](row, col) else current_color)

    def _add_format_information_area(self):

        format_data = self.error_correction_level << 3
        format_data |= self.mask_pattern

        format_string = bose_chaudhuri_hocquenghem(format_data).zfill(15)

        paths = [[
            [8, 0],
            [8, 1],
            [8, 2],
            [8, 3],
            [8, 4],
            [8, 5],
            [8, 7],
            [8, 8],
            [7, 8],
            [5, 8],
            [4, 8],
            [3, 8],
            [2, 8],
            [1, 8],
            [0, 8],
        ], [
            [self.size - 1, 8],
            [self.size - 2, 8],
            [self.size - 3, 8],
            [self.size - 4, 8],
            [self.size - 5, 8],
            [self.size - 6, 8],
            [self.size - 7, 8],
            [8, self.size - 8],
            [8, self.size - 7],
            [8, self.size - 6],
            [8, self.size - 5],
            [8, self.size - 4],
            [8, self.size - 3],
            [8, self.size - 2],
            [8, self.size - 1],
        ]]

        for path in paths:
            for i in range(len(format_string)):
                if i >= len(path): break
                row, col = path[i]
                self.matrix[row][col].set_color(to_color(format_string[i]))

    def draw(self):
        img = Image.new(mode="RGBA", size=(self.size, self.size))
        pixels = img.load()
        for row in range(self.size):
            for col in range(self.size):
                pixels[col, row] = self.matrix[row][col].get_color()
        #img.show()
        img.save("out.png")

if __name__ == "__main__":
    qrcode = QRCode(
        version = 1,
        error_correction_level = ErrorCorrection.QUARTILE,
        mask_pattern = 0b100
    )
    #qrcode._generate_matrix()
    qrcode.add_data("HELLO WORLD")
    qrcode.generate()
    qrcode.draw()
    #qrcode.add_data("hello", Mode.ALPHANUMERIC)
