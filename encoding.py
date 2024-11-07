# https://www.arscreatio.com/repositorio/images/n_23/SC031-N-1915-18004Text.pdf#page=33
def to_alphanumeric(data: str) -> int:
    base45_data = [lookup_alphanumeric_value(c) for c in data]
    bit_data = 0
    for i in range(0, len(base45_data), 2):
        current_data = base45_data[i]
        if i+1 < len(base45_data):
            current_data *= 45
            current_data += base45_data[i+1]
            bit_data = bit_data << 11
            bit_data = bit_data | current_data
        else:
            bit_data = bit_data << 6
            bit_data = bit_data | current_data
    bit_string = 0
    mode_bits = 0b0010
    mode_bits_size = 4
    # TODO: Apparently character count size indicate changes based on teh version, yay https://www.thonky.com/qr-code-tutorial/data-encoding . So, fix that
    length_bits = len(data)
    length_bits_size = 9
    data_binary_length = 11*(length_bits // 2) + 6*(length_bits % 2)
    bit_string <<= mode_bits_size
    bit_string |= mode_bits
    bit_string <<= length_bits_size
    bit_string |= length_bits
    bit_string <<= data_binary_length
    bit_string |= bit_data
    return str(bin(bit_string))[2:].zfill(mode_bits_size + length_bits_size + data_binary_length)

def lookup_alphanumeric_value(c: chr) -> int:
    return list("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:").index(c)

if __name__ == "__main__":
    print(to_alphanumeric("AC-42"))
    #print(lookup_alphanumeric_value("H"))
    #print(lookup_alphanumeric_value("E"))
    #print(lookup_alphanumeric_value("H") * 45 + lookup_alphanumeric_value("E"))

