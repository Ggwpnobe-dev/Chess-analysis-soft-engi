class Piece:
    def __init__(self, color, piece_type):
        self.color = color
        self.type = piece_type

    def __repr__(self):
        return f"{self.color[0].upper()}{self.type.upper()}"

class Board:
    def __init__(self):
        self.squares = [[None for _ in range(8)] for _ in range(8)]
        self.setup_board()

    def setup_board(self):
        # Place white pieces
        self.squares[0][0] = Piece("white", "rook")
        self.squares[0][1] = Piece("white", "knight")
        self.squares[0][2] = Piece("white", "bishop")
        self.squares[0][3] = Piece("white", "queen")
        self.squares[0][4] = Piece("white", "king")
        self.squares[0][5] = Piece("white", "bishop")
        self.squares[0][6] = Piece("white", "knight")
        self.squares[0][7] = Piece("white", "rook")
        for i in range(8):
            self.squares[1][i] = Piece("white", "pawn")

        # Place black pieces
        self.squares[7][0] = Piece("black", "rook")
        self.squares[7][1] = Piece("black", "knight")
        self.squares[7][2] = Piece("black", "bishop")
        self.squares[7][3] = Piece("black", "queen")
        self.squares[7][4] = Piece("black", "king")
        self.squares[7][5] = Piece("black", "bishop")
        self.squares[7][6] = Piece("black", "knight")
        self.squares[7][7] = Piece("black", "rook")
        for i in range(8):
            self.squares[6][i] = Piece("black", "pawn")
    def __repr__(self):
        board_str = ""
        for row in self.squares:
            board_str += " ".join(str(piece) if piece else "--" for piece in row) + "\n"
        return board_str
    
    def get_legal_moves(self, row, col):
        piece = self.squares[row][col]
        if not piece:
            return []

        legal_moves = []
        piece_type = piece.type
        color = piece.color

        if piece_type == "pawn":
            legal_moves.extend(self._get_pawn_move(row, col, color))
        elif piece_type == "rook":
            legal_moves.extend(self._get_rook_move(row, col, color))
        elif piece_type == "knight":
            legal_moves.extend(self._get_knight_moves(row, col, color))
        elif piece_type == "bishop":
            legal_moves.extend(self._get_bishop_moves(row, col, color))
        elif piece_type == "queen":
            legal_moves.extend(self._get_rook_move(row, col, color))
            legal_moves.extend(self._get_bishop_moves(row, col, color))
        elif piece_type == "king":
            legal_moves.extend(self._get_king_moves(row, col, color))
        return legal_moves
    
    def _is_valid_move(self, row, col):
        return 0 <= row < 8 and 0 <= col < 8
    
    def _is_opponent(self, row, col, color):
        piece = self.squares[row][col]
        return piece and piece.color != color
    
    def _get_pawn_move(self, row, col, color):
        moves = []
        direction = -1 if color == "white" else 1
        start_row = 1 if color == "white" else 6

        #step forward
        new_row = row + direction
        if self._is_valid_move(new_row, col) and not self.squares[new_row][col]:
            moves.append((new_row, col))

            # Two steps forward
            if row == start_row:
                new_row_2 = row + 2 * direction
                if self._is_valid_move(new_row_2, col) and not self.squares[new_row_2][col]:
                    moves.append((new_row_2, col))
                    
         # Captures diagonally
        for dc in [-1, 1]:
            new_col = col + dc
            if self._is_valid_move(new_row, new_col) and self._is_opponent(new_row, new_col, color):
                moves.append((new_row, new_col))

        # TODO: En passant and promotion will be added later
        return moves

    def _get_rook_move(self, row, col, color):
        moves = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # Right, Left, Down, Up

        for dr, dc in directions:
            for i in range(1, 8):
                new_row, new_col = row + dr * i, col + dc * i
                if not self._is_valid_move(new_row, new_col):
                    break
                if not self.squares[new_row][new_col]:
                    moves.append((new_row, new_col))
                elif self._is_opponent(new_row, new_col, color):
                    moves.append((new_row, new_col))
                    break  # Stop after capturing
                else:
                    break  # Blocked by own piece
        return moves
    
    def _get_knight_moves(self, row, col, color):
        moves = []
        knight_moves = [(2, 1), (2, -1), (-2, 1), (-2, -1),
                        (1, 2), (1, -2), (-1, 2), (-1, -2)]

        for dr, dc in knight_moves:
            new_row, new_col = row + dr, col + dc
            if self._is_valid_move(new_row, new_col) and \
               (not self.squares[new_row][new_col] or self._is_opponent(new_row, new_col, color)):
                moves.append((new_row, new_col))
        return moves

    def _get_bishop_moves(self, row, col, color):
        moves = []
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]  # Diagonal directions

        for dr, dc in directions:
            for i in range(1, 8):
                new_row, new_col = row + dr * i, col + dc * i
                if not self._is_valid_move(new_row, new_col):
                    break
                if not self.squares[new_row][new_col]:
                    moves.append((new_row, new_col))
                elif self._is_opponent(new_row, new_col, color):
                    moves.append((new_row, new_col))
                    break  # Stop after capturing
                else:
                    break  # Blocked by own piece
        return moves

    def _get_king_moves(self, row, col, color):
        moves = []
        king_moves = [(0, 1), (0, -1), (1, 0), (-1, 0),
                      (1, 1), (1, -1), (-1, 1), (-1, -1)]

        for dr, dc in king_moves:
            new_row, new_col = row + dr, col + dc
            if self._is_valid_move(new_row, new_col) and \
               (not self.squares[new_row][new_col] or self._is_opponent(new_row, new_col, color)):
                moves.append((new_row, new_col))

        # TODO: Castling will be added later
        return moves


    def __repr__(self):
        board_str = ""
        for row in self.squares:
            board_str += " ".join(str(piece) if piece else "--" for piece in row) + "\n"
        return board_str

# Let's create a board instance
board = Board()

# Example: Get legal moves for the white pawn at A2 (row 1, column 0)
pawn_moves = board.get_legal_moves(1, 0)
print(f"Legal moves for white pawn at A2: {pawn_moves}")

# Example: Get legal moves for the black knight at B8 (row 7, column 1)
knight_moves = board.get_legal_moves(7, 1)
print(f"Legal moves for black knight at B8: {knight_moves}")

# Example: Get legal moves for the white rook at A1 (row 0, column 0)
rook_moves = board.get_legal_moves(0, 0)
print(f"Legal moves for white rook at A1: {rook_moves}")