# https://www.arscreatio.com/repositorio/images/n_23/SC031-N-1915-18004Text.pdf#page=61
MaskPattern = {
    0b000: lambda i, j: (i + j) % 2 == 0,
    0b001: lambda i, j: i % 2 == 0,
    0b010: lambda i, j: j % 3 == 0,
    0b011: lambda i, j: (i + j) % 3 == 0,
    0b100: lambda i, j: (i/2 + j/3) % 2 == 0,
    0b101: lambda i, j: (i*j) % 2 + (i*j) % 3 == 0,
    0b110: lambda i, j: ((i*j) % 3 + i + j) % 2 == 0,
    0b111: lambda i, j: ((i * j) % 3 + i*j) % 2 == 0,
}
