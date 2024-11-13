from enum import StrEnum
from typing import override, Callable
from error_correction import ErrorCorrection
from constants import data_codeword_capacity
from mode import Mode
import re

from utils import split_into_segments

# TODO: I think data should be first encoded with utf-8. Then you analyze those hex chars. But also idk


# https://www.arscreatio.com/repositorio/images/n_23/SC031-N-1915-18004Text.pdf#page=103
def generate_most_efficient_modes(data: str, version: int):
    raise NotImplementedError("Generating the most efficient mode has not yet been implemented")
    version_index = 0 if version <= 9 else 1 if version <= 26 else 2
    # Select initial mode
    mode: Mode
    if in_exclusive_subset(data[0], Mode.BINARY):
        mode = Mode.BINARY
    elif in_exclusive_subset(data[0], Mode.KANJI):
        if in_exclusive_subset(data[1], Mode.NUMERIC) or in_exclusive_subset(data[1], Mode.ALPHANUMERIC):
            mode = Mode.KANJI

    mode = Mode.KANJI

    i: int = 1
    while i < len(data):
        # While in byte mode
        if mode == Mode.BINARY:
            pass
        # While in alphanumeric mode
        elif mode == Mode.ALPHANUMERIC:
            pass
        # While in numeric mode
        elif mode == Mode.NUMERIC:
            pass
        else:
            pass


def in_exclusive_subset(character: str, mode: Mode):
    raise NotImplementedError("Checking if a character is in the exclusive subset has not yet been implemented")
    if mode == Mode.NUMERIC:
        return 0x30 <= ord(character) <= 0x39
    elif mode == Mode.ALPHANUMERIC:
        return ord(character) in [
            0x20,
            0x24,
            0x25,
            0x2A,
            0x2B,
            0x2D,
            0x2E,
            0x2D,
            0x3A,
            0x41,
            0x42,
            0x43,
            0x44,
            0x45,
            0x46,
            0x47,
            0x48,
            0x49,
            0x4A,
            0x4B,
            0x4C,
            0x4D,
            0x4E,
            0x4F,
            0x50,
            0x51,
            0x52,
            0x53,
            0x54,
            0x55,
            0x56,
            0x57,
            0x58,
            0x59,
            0x5A,
        ]
    elif mode == Mode.BINARY:
        if 0x00 <= ord(character) <= 0x1F:
            return True
        elif 0x21 <= ord(character) <= 0x23:
            return True
        elif 0x26 <= ord(character) <= 0x29:
            return True
        elif ord(character) == 0x2C:
            return True
        elif 0x3B <= ord(character) <= 0x40:
            return True
        elif 0x5B <= ord(character) <= 0xFF:
            if 0x80 <= ord(character) <= 0x9F or 0xE0 <= ord(character) <= 0xFF:
                return False
            else:
                return True
        else:
            return False
    elif mode == Mode.KANJI:
        return is_in_first_kanji_range(ord(character)) or is_in_second_kanji_range(ord(character))


class ENCODING(StrEnum):
    LATIN1 = "iso-8859-1"


def get_character_count_indicator_length(mode: Mode, version: int) -> int:
    if 1 <= version <= 9:
        if mode == Mode.NUMERIC:
            return 10
        elif mode == Mode.ALPHANUMERIC:
            return 9
        elif mode == Mode.BINARY:
            return 8
        elif mode == Mode.KANJI:
            return 8
    elif version <= 26:
        if mode == Mode.NUMERIC:
            return 12
        elif mode == Mode.ALPHANUMERIC:
            return 11
        elif mode == Mode.BINARY:
            return 16
        elif mode == Mode.KANJI:
            return 10
    elif version <= 40:
        if mode == Mode.NUMERIC:
            return 14
        elif mode == Mode.ALPHANUMERIC:
            return 13
        elif mode == Mode.BINARY:
            return 16
        elif mode == Mode.KANJI:
            return 12

    raise Exception(f"Unable to calculate character count indicator for version {version} and mode {mode}")


def encode(data: str, version: int, mode: Mode) -> str:
    data_func: Callable[[str], tuple[int, int]]

    if mode == Mode.NUMERIC:
        data_func = to_numeric
    elif mode == Mode.ALPHANUMERIC:
        data_func = to_alphanumeric
    elif mode == Mode.BINARY:
        data_func = to_binary
    elif mode == Mode.KANJI:
        data_func = to_kanji
    else:
        raise NotImplementedError(f"Support for encoding type {mode} has not yet been implemented")

    mode_bits: int = mode
    mode_bits_size: int = 4
    length_bits: int = len(data)
    length_bits_size: int = get_character_count_indicator_length(mode, version)
    data_bits, data_bits_size = data_func(data)
    size: int = mode_bits_size + length_bits_size + data_bits_size

    bit_stream = 0
    bit_stream |= mode_bits
    bit_stream <<= length_bits_size
    bit_stream |= length_bits
    bit_stream <<= data_bits_size
    bit_stream |= data_bits

    return bin(bit_stream)[2:].zfill(size)


# https://www.arscreatio.com/repositorio/images/n_23/SC031-N-1915-18004Text.pdf#page=33
def to_alphanumeric(data: str) -> tuple[int, int]:
    try:
        base45_data = [lookup_alphanumeric_value(c) for c in data]
    except ValueError:
        raise ValueError(f"Attempted to encode {data} with alphanumeric mode, but not all characters are compatible")

    bit_data = 0
    for i in range(0, len(base45_data), 2):
        current_data = base45_data[i]
        if i + 1 < len(base45_data):
            current_data *= 45
            current_data += base45_data[i + 1]
            bit_data = bit_data << 11
            bit_data = bit_data | current_data
        else:
            bit_data = bit_data << 6
            bit_data = bit_data | current_data
    data_binary_length = 11 * (len(data) // 2) + 6 * (len(data) % 2)

    return bit_data, data_binary_length


def lookup_alphanumeric_value(character: str) -> int:
    return list("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:").index(character)


def to_numeric(data: str) -> tuple[int, int]:
    if not data.isnumeric():
        raise ValueError

    digit_groups: list[str] = re.findall(".{1,3}", data)

    data_bits: int = 0

    for digit_segment in digit_groups:
        segment_length: int | None = None
        if len(digit_segment) == 3:
            segment_length = 10
        elif len(digit_segment) == 2:
            segment_length = 7
        elif len(digit_segment) == 1:
            segment_length = 4

        assert segment_length is not None

        data_bits <<= segment_length
        data_bits |= int(digit_segment)

    r: int = 0
    if len(data) % 3 == 1:
        r = 4
    elif len(data) % 3 == 2:
        r = 7

    data_size = 10 * (len(data) // 3) + r

    return data_bits, data_size


def to_binary(data: str) -> tuple[int, int]:
    encoding: ENCODING = ENCODING.LATIN1
    data_bytes: bytes
    try:
        data_bytes = data.encode(encoding.value)
    except UnicodeEncodeError:
        raise ValueError("Input data has to be LATIN-1 (ISO 8859-1) compliant.")

    data_stream: int = 0
    for byte in data_bytes:
        # byte -= 0x20
        data_stream <<= 8
        data_stream |= byte

    data_size: int = 8 * len(data_bytes)

    return data_stream, data_size


def to_kanji(data: str) -> tuple[int, int]:
    try:
        data_bytes = data.encode("shift-jis")
    except UnicodeError:
        raise ValueError("Input data has to be shift-jis compliant.")

    # Turn each byte into a "double byte"
    double_bytes = [a * 256 + b for a, b in split_into_segments(list(data_bytes), 2)]

    data_stream = 0

    for double_byte in double_bytes:
        if is_in_first_kanji_range(double_byte):
            double_byte -= 0x8140
        elif is_in_second_kanji_range(double_byte):
            double_byte -= 0xC140
        else:
            raise Exception("All kanji data has to be in double byte range 0x8140 to 0x9FFC or 0xE040 to 0xEBBF")

        msb = (double_byte & 0xFF00) >> 8
        lsb = double_byte & 0x00FF

        resulting_binary = msb * 0xC0 + lsb

        data_stream <<= 13
        data_stream |= resulting_binary

    data_size = 13 * len(data)

    return data_stream, data_size


# WARNING: https://gcore.jsdelivr.net/gh/tonycrane/tonycrane.github.io/p/409d352d/ISO_IEC18004-2015.pdf#page=29 makes it confusing about the exact range. Cannot tell if 0xE37F would be valid...?
def is_in_first_kanji_range(double_byte: int):
    return 0x8140 <= double_byte <= 0x9FFC


def is_in_second_kanji_range(double_byte: int):
    return 0xE040 <= double_byte <= 0xEBBF


# TODO: I want Groups and CodewordBlockInformation to be better
class Group:
    block_count: int
    codeword_count_per_block: int

    def __init__(self, block_count: int, codeword_count_per_block: int):
        self.block_count = block_count
        self.codeword_count_per_block = codeword_count_per_block

    def size(self):
        return self.block_count * self.codeword_count_per_block

    @override
    def __str__(self):
        return f"Group({self.block_count=}, {self.codeword_count_per_block=})"


class CodewordBlockInformation:
    version: int
    ec_level: ErrorCorrection
    number_of_data_codewords: int
    ec_codewords_per_block: int
    group_1: Group
    group_2: Group

    def __init__(
        self,
        version: int,
        ec_level: ErrorCorrection,
        number_of_data_codewords: int,
        ec_codewords_per_block: int,
        number_of_blocks_in_group_1: int,
        number_of_codewords_in_each_block_group_1: int,
        number_of_blocks_in_group_2: int,
        number_of_codewords_in_each_block_group_2: int,
    ):
        self.version = version
        self.ec_level = ec_level
        self.number_of_data_codewords = number_of_data_codewords
        self.ec_codewords_per_block = ec_codewords_per_block
        self.group_1 = Group(number_of_blocks_in_group_1, number_of_codewords_in_each_block_group_1)
        self.group_2 = Group(number_of_blocks_in_group_2, number_of_codewords_in_each_block_group_2)

    @classmethod
    def from_line(cls, line: str) -> "CodewordBlockInformation":
        (
            version_ec,
            data_codewords,
            ec_codewords_per_block,
            blocks_in_group_1,
            codewords_in_each_block_group_1,
            blocks_in_group_2,
            codewords_in_each_block_group_2,
            _,
        ) = line.split("\t")
        version, ec_level_str = version_ec.split("-")
        version = int(version)
        data_codewords = int(data_codewords)
        ec_codewords_per_block = int(ec_codewords_per_block)
        blocks_in_group_1 = int(blocks_in_group_1)
        codewords_in_each_block_group_1 = int(codewords_in_each_block_group_1)
        blocks_in_group_2 = int(blocks_in_group_2 or "0")
        codewords_in_each_block_group_2 = int(codewords_in_each_block_group_2 or "0")
        ec_level = {
            "L": ErrorCorrection.LOW,
            "M": ErrorCorrection.MEDIUM,
            "Q": ErrorCorrection.QUARTILE,
            "H": ErrorCorrection.HIGH,
        }[ec_level_str]
        return CodewordBlockInformation(
            version,
            ec_level,
            data_codewords,
            ec_codewords_per_block,
            blocks_in_group_1,
            codewords_in_each_block_group_1,
            blocks_in_group_2,
            codewords_in_each_block_group_2,
        )

    @override
    def __str__(self):
        return "%s-%s\t%s\t%s\t%s\t%s\t%s\t%s" % (
            self.version,
            self.ec_level.name,
            self.number_of_data_codewords,
            self.ec_codewords_per_block,
            self.group_1.block_count,
            self.group_1.codeword_count_per_block,
            self.group_2.block_count,
            self.group_2.codeword_count_per_block,
        )

    @override
    def __eq__(self, other: object):
        if not isinstance(other, CodewordBlockInformation):
            raise Exception("Cannot compare equality of CodewordBlockInformation and {other.__class__.__name__}")

        return self.version == other.version and self.ec_level == other.ec_level


def get_codeword_block_information(version: int, ec_level: ErrorCorrection) -> CodewordBlockInformation:
    # TODO: Make this whole thing a lot less bad
    codeword_block_information: list[CodewordBlockInformation] = [
        CodewordBlockInformation.from_line(line)
        for line in """1-L	19	7	1	19			(19*1) = 19
    1-M	16	10	1	16			(16*1) = 16
    1-Q	13	13	1	13			(13*1) = 13
    1-H	9	17	1	9			(9*1) = 9
    2-L	34	10	1	34			(34*1) = 34
    2-M	28	16	1	28			(28*1) = 28
    2-Q	22	22	1	22			(22*1) = 22
    2-H	16	28	1	16			(16*1) = 16
    3-L	55	15	1	55			(55*1) = 55
    3-M	44	26	1	44			(44*1) = 44
    3-Q	34	18	2	17			(17*2) = 34
    3-H	26	22	2	13			(13*2) = 26
    4-L	80	20	1	80			(80*1) = 80
    4-M	64	18	2	32			(32*2) = 64
    4-Q	48	26	2	24			(24*2) = 48
    4-H	36	16	4	9			(9*4) = 36
    5-L	108	26	1	108			(108*1) = 108
    5-M	86	24	2	43			(43*2) = 86
    5-Q	62	18	2	15	2	16 	(15*2) + (16*2) = 62
    5-H	46	22	2	11	2	12 	(11*2) + (12*2) = 46
    6-L	136	18	2	68			(68*2) = 136
    6-M	108	16	4	27			(27*4) = 108
    6-Q	76	24	4	19			(19*4) = 76
    6-H	60	28	4	15			(15*4) = 60
    7-L	156	20	2	78			(78*2) = 156
    7-M	124	18	4	31			(31*4) = 124
    7-Q	88	18	2	14	4	15 	(14*2) + (15*4) = 88
    7-H	66	26	4	13	1	14 	(13*4) + (14*1) = 66
    8-L	194	24	2	97			(97*2) = 194
    8-M	154	22	2	38	2	39 	(38*2) + (39*2) = 154
    8-Q	110	22	4	18	2	19 	(18*4) + (19*2) = 110
    8-H	86	26	4	14	2	15 	(14*4) + (15*2) = 86
    9-L	232	30	2	116			(116*2) = 232
    9-M	182	22	3	36	2	37 	(36*3) + (37*2) = 182
    9-Q	132	20	4	16	4	17 	(16*4) + (17*4) = 132
    9-H	100	24	4	12	4	13 	(12*4) + (13*4) = 100
    10-L	274	18	2	68	2	69 	(68*2) + (69*2) = 274
    10-M	216	26	4	43	1	44 	(43*4) + (44*1) = 216
    10-Q	154	24	6	19	2	20 	(19*6) + (20*2) = 154
    10-H	122	28	6	15	2	16 	(15*6) + (16*2) = 122
    11-L	324	20	4	81			(81*4) = 324
    11-M	254	30	1	50	4	51 	(50*1) + (51*4) = 254
    11-Q	180	28	4	22	4	23 	(22*4) + (23*4) = 180
    11-H	140	24	3	12	8	13 	(12*3) + (13*8) = 140
    12-L	370	24	2	92	2	93 	(92*2) + (93*2) = 370
    12-M	290	22	6	36	2	37 	(36*6) + (37*2) = 290
    12-Q	206	26	4	20	6	21 	(20*4) + (21*6) = 206
    12-H	158	28	7	14	4	15 	(14*7) + (15*4) = 158
    13-L	428	26	4	107			(107*4) = 428
    13-M	334	22	8	37	1	38 	(37*8) + (38*1) = 334
    13-Q	244	24	8	20	4	21 	(20*8) + (21*4) = 244
    13-H	180	22	12	11	4	12 	(11*12) + (12*4) = 180
    14-L	461	30	3	115	1	116 	(115*3) + (116*1) = 461
    14-M	365	24	4	40	5	41 	(40*4) + (41*5) = 365
    14-Q	261	20	11	16	5	17 	(16*11) + (17*5) = 261
    14-H	197	24	11	12	5	13 	(12*11) + (13*5) = 197
    15-L	523	22	5	87	1	88 	(87*5) + (88*1) = 523
    15-M	415	24	5	41	5	42 	(41*5) + (42*5) = 415
    15-Q	295	30	5	24	7	25 	(24*5) + (25*7) = 295
    15-H	223	24	11	12	7	13 	(12*11) + (13*7) = 223
    16-L	589	24	5	98	1	99 	(98*5) + (99*1) = 589
    16-M	453	28	7	45	3	46 	(45*7) + (46*3) = 453
    16-Q	325	24	15	19	2	20 	(19*15) + (20*2) = 325
    16-H	253	30	3	15	13	16 	(15*3) + (16*13) = 253
    17-L	647	28	1	107	5	108 	(107*1) + (108*5) = 647
    17-M	507	28	10	46	1	47 	(46*10) + (47*1) = 507
    17-Q	367	28	1	22	15	23 	(22*1) + (23*15) = 367
    17-H	283	28	2	14	17	15 	(14*2) + (15*17) = 283
    18-L	721	30	5	120	1	121 	(120*5) + (121*1) = 721
    18-M	563	26	9	43	4	44 	(43*9) + (44*4) = 563
    18-Q	397	28	17	22	1	23 	(22*17) + (23*1) = 397
    18-H	313	28	2	14	19	15 	(14*2) + (15*19) = 313
    19-L	795	28	3	113	4	114 	(113*3) + (114*4) = 795
    19-M	627	26	3	44	11	45 	(44*3) + (45*11) = 627
    19-Q	445	26	17	21	4	22 	(21*17) + (22*4) = 445
    19-H	341	26	9	13	16	14 	(13*9) + (14*16) = 341
    20-L	861	28	3	107	5	108 	(107*3) + (108*5) = 861
    20-M	669	26	3	41	13	42 	(41*3) + (42*13) = 669
    20-Q	485	30	15	24	5	25 	(24*15) + (25*5) = 485
    20-H	385	28	15	15	10	16 	(15*15) + (16*10) = 385
    21-L	932	28	4	116	4	117 	(116*4) + (117*4) = 932
    21-M	714	26	17	42			(42*17) = 714
    21-Q	512	28	17	22	6	23 	(22*17) + (23*6) = 512
    21-H	406	30	19	16	6	17 	(16*19) + (17*6) = 406
    22-L	1006	28	2	111	7	112 	(111*2) + (112*7) = 1006
    22-M	782	28	17	46			(46*17) = 782
    22-Q	568	30	7	24	16	25 	(24*7) + (25*16) = 568
    22-H	442	24	34	13			(13*34) = 442
    23-L	1094	30	4	121	5	122 	(121*4) + (122*5) = 1094
    23-M	860	28	4	47	14	48 	(47*4) + (48*14) = 860
    23-Q	614	30	11	24	14	25 	(24*11) + (25*14) = 614
    23-H	464	30	16	15	14	16 	(15*16) + (16*14) = 464
    24-L	1174	30	6	117	4	118 	(117*6) + (118*4) = 1174
    24-M	914	28	6	45	14	46 	(45*6) + (46*14) = 914
    24-Q	664	30	11	24	16	25 	(24*11) + (25*16) = 664
    24-H	514	30	30	16	2	17 	(16*30) + (17*2) = 514
    25-L	1276	26	8	106	4	107 	(106*8) + (107*4) = 1276
    25-M	1000	28	8	47	13	48 	(47*8) + (48*13) = 1000
    25-Q	718	30	7	24	22	25 	(24*7) + (25*22) = 718
    25-H	538	30	22	15	13	16 	(15*22) + (16*13) = 538
    26-L	1370	28	10	114	2	115 	(114*10) + (115*2) = 1370
    26-M	1062	28	19	46	4	47 	(46*19) + (47*4) = 1062
    26-Q	754	28	28	22	6	23 	(22*28) + (23*6) = 754
    26-H	596	30	33	16	4	17 	(16*33) + (17*4) = 596
    27-L	1468	30	8	122	4	123 	(122*8) + (123*4) = 1468
    27-M	1128	28	22	45	3	46 	(45*22) + (46*3) = 1128
    27-Q	808	30	8	23	26	24 	(23*8) + (24*26) = 808
    27-H	628	30	12	15	28	16 	(15*12) + (16*28) = 628
    28-L	1531	30	3	117	10	118 	(117*3) + (118*10) = 1531
    28-M	1193	28	3	45	23	46 	(45*3) + (46*23) = 1193
    28-Q	871	30	4	24	31	25 	(24*4) + (25*31) = 871
    28-H	661	30	11	15	31	16 	(15*11) + (16*31) = 661
    29-L	1631	30	7	116	7	117 	(116*7) + (117*7) = 1631
    29-M	1267	28	21	45	7	46 	(45*21) + (46*7) = 1267
    29-Q	911	30	1	23	37	24 	(23*1) + (24*37) = 911
    29-H	701	30	19	15	26	16 	(15*19) + (16*26) = 701
    30-L	1735	30	5	115	10	116 	(115*5) + (116*10) = 1735
    30-M	1373	28	19	47	10	48 	(47*19) + (48*10) = 1373
    30-Q	985	30	15	24	25	25 	(24*15) + (25*25) = 985
    30-H	745	30	23	15	25	16 	(15*23) + (16*25) = 745
    31-L	1843	30	13	115	3	116 	(115*13) + (116*3) = 1843
    31-M	1455	28	2	46	29	47 	(46*2) + (47*29) = 1455
    31-Q	1033	30	42	24	1	25 	(24*42) + (25*1) = 1033
    31-H	793	30	23	15	28	16 	(15*23) + (16*28) = 793
    32-L	1955	30	17	115			(115*17) = 1955
    32-M	1541	28	10	46	23	47 	(46*10) + (47*23) = 1541
    32-Q	1115	30	10	24	35	25 	(24*10) + (25*35) = 1115
    32-H	845	30	19	15	35	16 	(15*19) + (16*35) = 845
    33-L	2071	30	17	115	1	116 	(115*17) + (116*1) = 2071
    33-M	1631	28	14	46	21	47 	(46*14) + (47*21) = 1631
    33-Q	1171	30	29	24	19	25 	(24*29) + (25*19) = 1171
    33-H	901	30	11	15	46	16 	(15*11) + (16*46) = 901
    34-L	2191	30	13	115	6	116 	(115*13) + (116*6) = 2191
    34-M	1725	28	14	46	23	47 	(46*14) + (47*23) = 1725
    34-Q	1231	30	44	24	7	25 	(24*44) + (25*7) = 1231
    34-H	961	30	59	16	1	17 	(16*59) + (17*1) = 961
    35-L	2306	30	12	121	7	122 	(121*12) + (122*7) = 2306
    35-M	1812	28	12	47	26	48 	(47*12) + (48*26) = 1812
    35-Q	1286	30	39	24	14	25 	(24*39) + (25*14) = 1286
    35-H	986	30	22	15	41	16 	(15*22) + (16*41) = 986
    36-L	2434	30	6	121	14	122 	(121*6) + (122*14) = 2434
    36-M	1914	28	6	47	34	48 	(47*6) + (48*34) = 1914
    36-Q	1354	30	46	24	10	25 	(24*46) + (25*10) = 1354
    36-H	1054	30	2	15	64	16 	(15*2) + (16*64) = 1054
    37-L	2566	30	17	122	4	123 	(122*17) + (123*4) = 2566
    37-M	1992	28	29	46	14	47 	(46*29) + (47*14) = 1992
    37-Q	1426	30	49	24	10	25 	(24*49) + (25*10) = 1426
    37-H	1096	30	24	15	46	16 	(15*24) + (16*46) = 1096
    38-L	2702	30	4	122	18	123 	(122*4) + (123*18) = 2702
    38-M	2102	28	13	46	32	47 	(46*13) + (47*32) = 2102
    38-Q	1502	30	48	24	14	25 	(24*48) + (25*14) = 1502
    38-H	1142	30	42	15	32	16 	(15*42) + (16*32) = 1142
    39-L	2812	30	20	117	4	118 	(117*20) + (118*4) = 2812
    39-M	2216	28	40	47	7	48 	(47*40) + (48*7) = 2216
    39-Q	1582	30	43	24	22	25 	(24*43) + (25*22) = 1582
    39-H	1222	30	10	15	67	16 	(15*10) + (16*67) = 1222
    40-L	2956	30	19	118	6	119 	(118*19) + (119*6) = 2956
    40-M	2334	28	18	47	31	48 	(47*18) + (48*31) = 2334
    40-Q	1666	30	34	24	34	25 	(24*34) + (25*34) = 1666
    40-H	1276	30	20	15	61	16 	(15*20) + (16*61) = 1276
    """.split("\n")[:-1]
    ]

    for value in codeword_block_information:
        if value.version == version and value.ec_level == ec_level:
            return value

    return CodewordBlockInformation.from_line("")
    # raise Exception(f"Unable to find codeword block with {version=} and {ec_level=}")


# https://gcore.jsdelivr.net/gh/tonycrane/tonycrane.github.io/p/409d352d/ISO_IEC18004-2015.pdf#page=41
def lookup_data_codeword_capacity(version: int, error_correction_level: ErrorCorrection) -> int:
    error_correction_index = {
        ErrorCorrection.LOW: 0,
        ErrorCorrection.MEDIUM: 1,
        ErrorCorrection.QUARTILE: 2,
        ErrorCorrection.HIGH: 3,
    }[error_correction_level]

    return data_codeword_capacity[version][error_correction_index]
