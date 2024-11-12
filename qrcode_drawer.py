from anchor_position import AnchorPosition
from square import Square
from utils import to_color


class QRCodeDrawer:
    row: int
    col: int
    # By default, you start in bottom right so are going up and left
    is_going_up: bool = True
    is_right: bool = True

    matrix: list[list[Square]]
    size: int

    def __init__(self, matrix: list[list[Square]]):
        self.matrix = matrix
        self.size = len(self.matrix)
        self.row = self.size - 1
        self.col = self.size - 1

    def place_artifact(
        self,
        artifact: list[list[tuple[int, int, int] | None]],
        anchorPosition: AnchorPosition,
        padding_row: int = 0,
        padding_column: int = 0,
    ):
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
                current_color: tuple[int, int, int] | None = artifact[row][col]
                if current_color is None:
                    continue
                self.matrix[row + row_offset][col + column_offset].set_color(
                    current_color
                ).lock()

    def push_byte(self, byte_data: str) -> None:
        # print("Pushing byte...")
        bit_arr = list(byte_data)

        while len(bit_arr) > 0:
            if (
                not self.matrix[self.row][self.col].is_locked()
                and not self.matrix[self.row][self.col].is_reserved()
            ):
                _ = self.matrix[self.row][self.col].set_color(to_color(bit_arr.pop(0)))
                # print("setting color", self.matrix[row][col].get_color())

            if self.is_right:
                self.col -= 1
            else:
                self.col += 1
                if self.is_going_up:
                    self.row -= 1
                else:
                    self.row += 1

            self.is_right = not self.is_right

            if self.row < 0:
                self.row = 0
                self.col -= 2
                self.is_going_up = not self.is_going_up
            elif self.row >= self.size:
                self.row = self.size - 1
                self.col -= 2
                self.is_going_up = not self.is_going_up

            # Column 6 is a special case with no usable space, so skip it
            # https://www.thonky.com/qr-code-tutorial/module-placement-matrix > "Exception: Vertical Timing Pattern"
            if self.col == 6:
                self.col -= 1

            if self.col < 0:
                raise Exception("Trying to write off of the map")
