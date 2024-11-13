from abc import ABC, abstractmethod
from math import ceil, floor
import os
import re
from typing import overload, override

from encoding import ENCODING, lookup_alphanumeric_value
from PIL import Image

from anchor_position import AnchorPosition
from color import BLACK, GREEN, WHITE
from constants import alignment_patterns_locations
from encoding import (
    CodewordBlockInformation,
    encode,
    get_codeword_block_information,
    get_data_bit_capacity,
    get_data_codeword_capacity,
)
from error_correction import ErrorCorrection
from mask_pattern import MaskPattern
from mode import Mode
from polynomials import generate_error_correction_codewords, generate_message_polynomial
from qrcode_drawer import QRCodeDrawer
from square import Square
from utils import bose_chaudhuri_hocquenghem, golay, interleave, to_color

# TODO: Have this QRCode class be no frills, then make a SimpleQRCode subclass which does lots of the stuff for you

# from typing import Callable, Concatenate, TypeVar, ParamSpec
#
# T = TypeVar("T")
# P = ParamSpec("P")
#
#
# def is_setup(
#    func: Callable[Concatenate["QRCode", P], T],
# ) -> Callable[Concatenate["QRCode", P], T]:
#    def wrapper(self: "QRCode", *args: P.args, **kwargs: P.kwargs) -> T:
#        if self.version is None or self.size is None:
#            raise ValueError("Cannot run function while not setup")
#        if self.drawer is None:
#            raise ValueError("Cannot run function without a drawer")
#        return func(self, *args, **kwargs)
#
#    return wrapper


class AbstractQRCode(ABC):
    _version: int | None = None
    size: int | None = None
    error_correction_level: ErrorCorrection | None = None
    _mask_pattern: int | None = None
    matrix: list[list[Square]] = [[]]
    drawer: QRCodeDrawer | None = None

    def __init__(
        self,
        version: int | None = None,
        error_correction_level: ErrorCorrection | None = None,
        mask_pattern: int | None = None,
    ):
        self.version = version
        # size is automatically set when version is updated
        self.error_correction_level = error_correction_level
        self.mask_pattern = mask_pattern

    def generate(self) -> None:
        self._generate_matrix()
        self.drawer = QRCodeDrawer(self.matrix)
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

    @property
    def version(self) -> int | None:
        return self._version

    @version.setter
    def version(self, version: int | None) -> None:
        if version is None:
            self._version = version
            self.size = None
        elif 1 <= version <= 40:
            self._version = version
            self.size = (4 * version) + 17
        else:
            raise ValueError(f"Cannot set version. {version} is an invalid version number.")

    @property
    def mask_pattern(self) -> int | None:
        return self._mask_pattern

    @mask_pattern.setter
    def mask_pattern(self, mask_pattern: int | None):
        if mask_pattern is None:
            self._mask_pattern = mask_pattern
        elif 0 <= mask_pattern <= 7:
            self._mask_pattern = mask_pattern
        else:
            raise ValueError(f"Cannot set mask pattern {mask_pattern}. Expected to be None (auto) or an integer 0-7")

    def _generate_matrix(self) -> None:
        if self.size is None:
            raise ValueError(f"Cannot initialize a matrix with version {self.version}")

        self.matrix = [[Square() for _ in range(self.size)] for _ in range(self.size)]

    def _add_finder_patterns(self) -> None:
        if self.drawer is None:
            raise ValueError("Cannot add separators with a NoneType drawer")

        finder_pattern: list[list[tuple[int, int, int] | None]] = [
            [BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK],
            [BLACK, WHITE, WHITE, WHITE, WHITE, WHITE, BLACK],
            [BLACK, WHITE, BLACK, BLACK, BLACK, WHITE, BLACK],
            [BLACK, WHITE, BLACK, BLACK, BLACK, WHITE, BLACK],
            [BLACK, WHITE, BLACK, BLACK, BLACK, WHITE, BLACK],
            [BLACK, WHITE, WHITE, WHITE, WHITE, WHITE, BLACK],
            [BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK],
        ]

        self.drawer.place_artifact(finder_pattern, AnchorPosition.TOP_LEFT)
        self.drawer.place_artifact(finder_pattern, AnchorPosition.TOP_RIGHT)
        self.drawer.place_artifact(finder_pattern, AnchorPosition.BOTTOM_LEFT)

    def _add_separators(self) -> None:
        if self.drawer is None:
            raise ValueError("Cannot add separators with a NoneType drawer")

        separator_pattern: list[list[tuple[int, int, int] | None]] = [
            [None, None, None, None, None, None, None, WHITE],
            [None, None, None, None, None, None, None, WHITE],
            [None, None, None, None, None, None, None, WHITE],
            [None, None, None, None, None, None, None, WHITE],
            [None, None, None, None, None, None, None, WHITE],
            [None, None, None, None, None, None, None, WHITE],
            [None, None, None, None, None, None, None, WHITE],
            [WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE],
        ]

        self.drawer.place_artifact(separator_pattern, AnchorPosition.TOP_LEFT)
        self.drawer.place_artifact(separator_pattern, AnchorPosition.TOP_RIGHT)
        self.drawer.place_artifact(separator_pattern, AnchorPosition.BOTTOM_LEFT)

    # From https://www.arscreatio.com/repositorio/images/n_23/SC031-N-1915-18004Text.pdf#page=87
    def _add_alignment_patterns(self) -> None:
        if self.version is None or self.size is None:
            raise ValueError("Cannot run function while not setup")
        if self.drawer is None:
            raise ValueError("Cannot add alignment patterns with a NoneType drawer")

        locations: list[int] = alignment_patterns_locations[self.version]

        alignment_pattern: list[list[tuple[int, int, int] | None]] = [
            [BLACK, BLACK, BLACK, BLACK, BLACK],
            [BLACK, WHITE, WHITE, WHITE, BLACK],
            [BLACK, WHITE, BLACK, WHITE, BLACK],
            [BLACK, WHITE, WHITE, WHITE, BLACK],
            [BLACK, BLACK, BLACK, BLACK, BLACK],
        ]

        # For every possible cross of locations, attempt to place an alignment
        # pattern there is it does not overlap with anything
        for row in locations:
            for col in locations:
                if self._check_overlap_exists(row, col, len(alignment_pattern) // 2):
                    continue
                self.drawer.place_artifact(
                    alignment_pattern,
                    AnchorPosition.TOP_LEFT,
                    padding_row=row - 2,
                    padding_column=col - 2,
                )

    def _check_overlap_exists(self, row: int, col: int, radius: int) -> bool:
        return self.matrix[row + radius][col - radius].is_locked() or self.matrix[row + radius][col + radius].is_locked() or self.matrix[row - radius][col - radius].is_locked() or self.matrix[row - radius][col + radius].is_locked()

    def _add_timing_patterns(self):
        if self.version is None or self.size is None:
            raise ValueError("Cannot run function while not setup")
        if self.drawer is None:
            raise ValueError("Cannot run function without a drawer")

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
            if i == self.size - 8:
                continue
            self.matrix[i][8].set_color(GREEN).reserve()

        for i in range(6):
            self.matrix[i][8].set_color(GREEN).reserve()
            self.matrix[8][i].set_color(GREEN).reserve()

        self.matrix[7][8].set_color(GREEN).reserve()
        self.matrix[8][7].set_color(GREEN).reserve()
        self.matrix[8][8].set_color(GREEN).reserve()

    def _add_version_information_area(self):
        # According to https://upload.wikimedia.org/wikipedia/commons/4/45/QRCode-2-Structure.png version info is only required when version >= 7
        # TODO: This feels a bit bad, maybe change this
        if self.version is None or self.size is None:
            raise ValueError("Cannot add version information nwhen version is None")

        if self.version < 7:
            return

        if self.drawer is None:
            raise ValueError("Cannot add version information area with a NoneType drawer")

        code = list(reversed(golay(self.version)))
        version_artifact: list[list[tuple[int, int, int] | None]] = [
            [to_color(c) for c in code[0:3]],
            [to_color(c) for c in code[3:6]],
            [to_color(c) for c in code[6:9]],
            [to_color(c) for c in code[9:12]],
            [to_color(c) for c in code[12:15]],
            [to_color(c) for c in code[15:18]],
        ]

        self.drawer.place_artifact(version_artifact, AnchorPosition.TOP_LEFT, padding_column=self.size - 11)

        # Rotate the array (modified from https://stackoverflow.com/a/8421412)
        version_artifact = list(zip(*version_artifact))

        self.drawer.place_artifact(version_artifact, AnchorPosition.TOP_LEFT, padding_row=self.size - 11)

    @abstractmethod
    def _make_data_stream(self) -> str:
        pass

    def _add_data(self):
        if self.version is None:
            raise Exception("Cannot add data when version is None")
        if self.size is None:
            raise Exception("Cannot add data when size is None")
        if self.error_correction_level is None:
            raise Exception("Cannot add data when error correction level is None")
        # TODO: Likely in SimpleQRCode here is the algorithm for getting the best/most efficient mores https://gcore.jsdelivr.net/gh/tonycrane/tonycrane.github.io/p/409d352d/ISO_IEC18004-2015.pdf#C062021e.indd%3AAnnex%20sec_J%3A60&page=108

        bit_stream: str = self._make_data_stream()

        data_bit_capacity = get_data_bit_capacity(self.version, self.error_correction_level)

        bit_stream = self._add_terminator(bit_stream, data_bit_capacity)

        bit_stream = self._add_padding_bytes(bit_stream, data_bit_capacity)

        if (len(bit_stream)) > get_data_bit_capacity(self.version, self.error_correction_level):
            raise Exception(f"Too much data to be properly stored in qrcode of version {self.version} with error correction level {self.error_correction_level.name}")

        self._add_error_correction_code(bit_stream)

    def _add_terminator(self, bit_stream: str, data_bit_capacity: int) -> str:
        assert self.version is not None
        assert self.error_correction_level is not None

        # Fill out the terminator if required
        maximum_terminator_length: int = 4
        terminator_required: int = min(data_bit_capacity, len(bit_stream) + maximum_terminator_length)
        return bit_stream.ljust(terminator_required, "0")

    def _add_padding_bytes(self, bit_stream: str, data_bit_capacity: int) -> str:
        # Fill out to the next full bit
        if len(bit_stream) % 8 != 0:
            next_multiple_of_8 = ceil(len(bit_stream) / 8) * 8
            bit_stream = bit_stream.ljust(next_multiple_of_8, "0")

        # Padd with alternating "11101100" and "00010001"s
        padding_bytes = ("11101100", "00010001")
        i = 0
        while len(bit_stream) < data_bit_capacity:
            bit_stream += padding_bytes[i % 2]
            i += 1

        return bit_stream

    def _get_required_remainder_bits(self) -> int:
        if self.version is None:
            raise Exception("Cannot calculated remainder bits with None version")
        if self.version <= 1:
            return 0
        elif self.version <= 6:
            return 7
        elif self.version <= 13:
            return 0
        elif self.version <= 20:
            return 3
        elif self.version <= 27:
            return 4
        elif self.version <= 34:
            return 3
        else:
            return 0

    def _add_error_correction_code(self, data_str: str) -> None:
        if self.version is None or self.size is None:
            raise ValueError("Cannot run function while not setup")
        if self.drawer is None:
            raise ValueError("Cannot run function without a drawer")

        # If version is above 2, need to break data in multiple blocks

        cwblock_info: CodewordBlockInformation = get_codeword_block_information(self.version, self.error_correction_level)

        # TODO: I think here I exclude data that would push us over the edge, but I don't think that's good
        # Split the data str into code words (8 bits)
        codewords = re.findall(".{8}", data_str)

        # Create 2 groups
        group_1_full: list[str] = codewords[: cwblock_info.group_1.size()]
        group_2_full: list[str] = codewords[cwblock_info.group_1.size() :]

        group_1: list[list[str]] = []
        # Split those groups into blocks
        for i in range(cwblock_info.group_1.block_count):
            group_1.append(group_1_full[: cwblock_info.group_1.codeword_count_per_block])
            group_1_full = group_1_full[cwblock_info.group_1.codeword_count_per_block :]

        group_2: list[list[str]] = []
        # Split those groups into blocks
        for i in range(cwblock_info.group_2.block_count):
            group_2.append(group_2_full[: cwblock_info.group_2.codeword_count_per_block])
            group_2_full = group_2_full[cwblock_info.group_2.codeword_count_per_block :]

        # This is new

        group_1_message_polynomials = [generate_message_polynomial(block) for block in group_1]
        group_2_message_polynomials = [generate_message_polynomial(block) for block in group_2]

        group_1_ec = [generate_error_correction_codewords(mp_coeff, cwblock_info.ec_codewords_per_block).as_integers() for mp_coeff in group_1_message_polynomials]

        group_2_ec = [generate_error_correction_codewords(mp_coeff, cwblock_info.ec_codewords_per_block).as_integers() for mp_coeff in group_2_message_polynomials]

        interleaving_data: list[str] = interleave(group_1, group_2)
        interleaving_ec_integers: list[int] = interleave(group_1_ec, group_2_ec)
        interleaving_ec: list[str] = [bin(value)[2:].zfill(8) for value in interleaving_ec_integers]

        bit_stream = "".join(interleaving_data) + "".join(interleaving_ec)

        # Add remainder bits if required
        bit_stream += "0" * self._get_required_remainder_bits()

        self.drawer.push_byte(bit_stream)

        self.write_to_png(file_name="partial.png")

    def _add_data_mask(self):
        if self.mask_pattern is None:
            best_mask = self._determine_best_data_mask()
            self.mask_pattern = best_mask

        self._apply_data_mask()

    def _determine_best_data_mask(self):
        # TODO: Move this to a test somehow...
        #
        # The matrix is an incorrectly generated matrix from https://www.thonky.com/qr-code-tutorial/data-masking used to compare the scores for each penalty.
        # To use it, I drew the matrix, but then you need to add in all of the features (alignment patterns, timings, etc) so they are reserved/locked. Then, you apply the data mask (0) to "undo" the data masking. Then you have the original (incorrect) matrix used to generate all of the penalty scores on the website.
        # Each index corresponds to one mask
        # self.matrix = [
        #    [Square(BLACK) if int(v) == 1 else Square(WHITE) for v in list(x)]
        #    for x in "111111101100001111111 100000101001001000001 101110101001101011101 101110101000001011101 101110101010001011101 100000100010001000001 111111101010101111111 000000001000000000000 011010110000101011111 010000001111000010001 001101110110001011000 011011010011010101110 100010101011101110101 000000001101001000101 111111101010000101100 100000100101101101000 101110101010001111111 101110100101010100010 101110101000111101001 100000101011010001011 111111100000111100001".split(
        #        " "
        #    )
        # ]

        # self.drawer = QRCodeDrawer(self.matrix)
        # self._add_finder_patterns()
        # self._add_separators()
        # self._add_alignment_patterns()
        # self._add_timing_patterns()
        # self._add_dark_module()
        # self._reserve_format_information_area()
        # self._add_version_information_area()
        # self.mask_pattern = 0b000
        # self._apply_data_mask()

        mask_pattern_count = 8
        scores: list[int] = []
        for i in range(mask_pattern_count):
            self.mask_pattern = i
            # if i == 0:
            #    self.write_to_png("partial.png")
            self._apply_data_mask()
            self._add_format_information_area()

            penalty = self._evaluate_data_mask()
            scores.append(penalty)
            # Applying the mask again will "unapply" it
            self._apply_data_mask()

        best_score = min(scores)
        best_mask = scores.index(best_score)
        print(f"Determined best mask was {best_mask} with a score of {best_score}")
        return best_mask

    def _apply_data_mask(self):
        if self.size is None:
            raise ValueError(f"Cannot apply data mask on qrcode of version {self.version}")
        for row in range(self.size):
            for col in range(self.size):
                alternate_color = WHITE if self.matrix[row][col].get_color() == BLACK else BLACK

                if self.matrix[row][col].is_reserved() or self.matrix[row][col].is_locked():
                    continue

                if self.mask_pattern is None:
                    raise Exception("Cannot apply a None mask")

                if MaskPattern[self.mask_pattern](row, col):
                    _ = self.matrix[row][col].set_color(alternate_color)

    def _add_format_information_area(self):
        if self.version is None or self.size is None:
            raise ValueError("Cannot run function while not setup")
        if self.drawer is None:
            raise ValueError("Cannot run function without a drawer")
        if self.error_correction_level is None:
            raise ValueError("Cannot run function without an error correction level")

        format_data: int = self.error_correction_level << 3
        if self.mask_pattern is None:
            raise Exception("A mask pattern has not yet been selected")
        format_data |= self.mask_pattern

        format_string = bose_chaudhuri_hocquenghem(format_data).zfill(15)

        paths: list[list[list[int]]] = [
            [
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
            ],
            [
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
            ],
        ]

        for path in paths:
            for i in range(len(format_string)):
                if i >= len(path):
                    break
                row, col = path[i]
                _ = self.matrix[row][col].set_color(to_color(format_string[i]))

    def _evaluate_data_mask(self):
        penalty_1 = self._evaluation_condition_1()
        penalty_2 = self._evaluation_condition_2()
        penalty_3 = self._evaluation_condition_3()
        penalty_4 = self._evaluation_condition_4()
        total_penalty = penalty_1 + penalty_2 + penalty_3 + penalty_4

        return total_penalty

    def _evaluation_condition_1(self):
        penalty = 0
        transpose_matrix: list[list[Square]] = [values for values in zip(*self.matrix)]
        for matrix in [self.matrix, transpose_matrix]:
            for row in matrix:
                count = 0
                prev_cell = None
                for cell in row:
                    if cell == prev_cell:
                        count += 1
                    else:
                        count = 1
                        prev_cell = cell

                    if count == 5:
                        penalty += 3
                    elif count > 5:
                        penalty += 1

        print(f"Penalty condition 1 is {penalty}")

        return penalty

    def _evaluation_condition_2(self):
        penalty = 0
        for row in range(len(self.matrix) - 1):
            for col in range(len(self.matrix[0]) - 1):
                cells = [
                    self.matrix[row + 0][col + 0],
                    self.matrix[row + 0][col + 1],
                    self.matrix[row + 1][col + 0],
                    self.matrix[row + 1][col + 1],
                ]
                if all(cell == cells[0] for cell in cells):
                    penalty += 3

        print(f"Penalty condition 2 is {penalty}")

        return penalty

    def _evaluation_condition_3(self):
        window_size = 11
        penalty = 0
        transpose_matrix = [list(values) for values in zip(*self.matrix)]
        match_patterns = [
            [
                BLACK,
                WHITE,
                BLACK,
                BLACK,
                BLACK,
                WHITE,
                BLACK,
                WHITE,
                WHITE,
                WHITE,
                WHITE,
            ],
            [
                WHITE,
                WHITE,
                WHITE,
                WHITE,
                BLACK,
                WHITE,
                BLACK,
                BLACK,
                BLACK,
                WHITE,
                BLACK,
            ],
        ]
        for matrix in [self.matrix, transpose_matrix]:
            for row in matrix:
                for col in range(len(row) + 1 - window_size):
                    window = row[col : col + window_size]
                    if window in match_patterns:
                        penalty += 40

        print(f"Penalty condition 3 is {penalty}")

        return penalty

    def _evaluation_condition_4(self):
        total_cells = len(self.matrix) * len(self.matrix[0])
        dark_cell_count = 0
        for row in self.matrix:
            for cell in row:
                if cell == BLACK:
                    dark_cell_count += 1
        percentage_dark = (float(dark_cell_count) / total_cells) * 100
        prev_multiple_of_5 = floor(percentage_dark / 5.0) * 5
        next_multiple_of_5 = ceil(percentage_dark / 5.0) * 5
        prev_multiple_of_5 = abs(prev_multiple_of_5 - 50)
        next_multiple_of_5 = abs(next_multiple_of_5 - 50)
        # Both should already be integers
        prev_multiple_of_5 = int(prev_multiple_of_5 / 5)
        next_multiple_of_5 = int(next_multiple_of_5 / 5)
        penalty = min(prev_multiple_of_5, next_multiple_of_5)

        print(f"Penalty condition 4 is {penalty}")
        return penalty

    def write_to_png(self, file_name: str | None = None, destination_folder: str | None = None, border: int = 4) -> None:
        if self.version is None or self.size is None:
            raise ValueError("Cannot run function while not setup")

        destination_folder = destination_folder or "out"
        file_name = file_name or "qrcode.png"
        file_path = os.path.join(destination_folder, file_name)

        img = Image.new(mode="RGBA", size=(self.size + 2 * border, self.size + 2 * border))
        pixels = img.load()

        if pixels is None:
            raise Exception("Unable to create image")

        for row in range(self.size + 2 * border):
            for col in range(self.size + 2 * border):
                pixels[col, row] = WHITE

        for row in range(self.size):
            for col in range(self.size):
                pixels[col + border, row + border] = self.matrix[row][col].get_color()

        if os.path.exists(destination_folder) and not os.path.isdir(destination_folder):
            raise Exception(f"Destination folder ({destination_folder}) appears to be a file. It must be deleted or destionation_folder must be changed so a folder can be created")
        elif os.path.exists(file_path) and not os.path.isfile(file_path):
            raise Exception(f"Destination path ({file_path}) appears to be a directory. It must be deleted or either destination_folder or file_name must be changed so a file can be created")

        if not os.path.exists(destination_folder):
            os.mkdir(destination_folder)

        img.save(file_path)

    @override
    def __str__(self) -> str:
        rows: list[str] = []
        for row in self.matrix:
            rows.append("".join([str(v) for v in row]))
        return "".join(rows)


class DetailedQRCode(AbstractQRCode):
    data: list[tuple[Mode, str]] = []

    def add_data(self, data: str, mode: Mode) -> None:
        self.data.append((mode, data))

    @override
    def _make_data_stream(self) -> str:
        if self.version is None:
            raise Exception("Cannot make data stream with None version")
        bit_stream = ""
        for mode, data in self.data:
            # TODO: Implement all other string types and do some checking for data length/type
            bit_stream += encode(data, self.version, mode)
        return bit_stream


class SimpleQRCode(AbstractQRCode):
    data: str = ""

    def add_data(self, data: str) -> None:
        self.data += data

    @override
    def _make_data_stream(self) -> str:
        if self.version is None:
            raise Exception("Cannot make data stream with None version")

        mode: Mode

        try:
            [lookup_alphanumeric_value(v) for v in self.data]
            mode = Mode.ALPHANUMERIC
        except Exception:
            try:
                _ = self.data.encode(ENCODING.LATIN1)
                mode = Mode.BINARY
            except Exception:
                try:
                    _ = self.data.encode(ENCODING.SHIFTJIS)
                    mode = Mode.KANJI
                except Exception:
                    raise Exception('No valid encoding scheme found for "{self.data}"')

        return encode(self.data, self.version, mode)


if __name__ == "__main__":
    qrcode = DetailedQRCode(
        version=5,
        error_correction_level=ErrorCorrection.LOW,
        mask_pattern=0b010,
    )

    # qrcode.add_data("THIS IS A LONG STRING OF TEXT THAT VERSION ", Mode.ALPHANUMERIC)
    # qrcode.add_data("314159265358979323846264338327950", Mode.NUMERIC)
    # qrcode.add_data("茗荷", Mode.KANJI)
    # qrcode.add_data(" Leicester city is number ", Mode.BINARY)
    # qrcode.add_data("1", Mode.NUMERIC)
    # qrcode.add_data(" BEST FOOTBALL TEAM", Mode.ALPHANUMERIC)
    # qrcode.add_data("!!!", Mode.BINARY)

    qrcode.add_data("Hello gamer!", Mode.BINARY)
    # qrcode.add_data("HELLO WORLá", Mode.BINARY)
    # qrcode.add_data("işçöá", Mode.BINARY)
    # qrcode.add_data("hello", Mode.BINARY)
    # qrcode.add_data("ΑΒΓΔΕ", Mode.BINARY)
    # qrcode.add_data("مرحبا بالعالم", Mode.BINARY)
    qrcode.generate()
    qrcode.write_to_png()

    simpleQRCode = SimpleQRCode(
        version=5,
        error_correction_level=ErrorCorrection.LOW,
        mask_pattern=0b010,
    )

    simpleQRCode.add_data("Hello ")
    simpleQRCode.add_data("gamer!")
    simpleQRCode.generate()
    simpleQRCode.write_to_png("simpCode.png")
