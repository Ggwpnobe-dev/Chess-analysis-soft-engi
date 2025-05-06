import pygame
from Main import Board, Piece

# Initialize Pygame
pygame.init()

# Screen dimensions
SQUARE_SIZE = 80
WIDTH = 8 * SQUARE_SIZE
HEIGHT = 8 * SQUARE_SIZE
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess Game")

# Colors
WHITE = (240, 217, 181)
BLACK = (181, 136, 99)
LIGHT_HIGHLIGHT = (255, 255, 102)
DARK_HIGHLIGHT = (173, 216, 230)

# Load piece images
piece_images = {}
pieces = ["wp", "wr", "wn", "wb", "wq", "wk", "bp", "br", "bn", "bb", "bq", "bk"]
for piece in pieces:
    piece_images[piece] = pygame.image.load(f"images/{piece}.png")
    piece_images[piece] = pygame.transform.scale(piece_images[piece], (SQUARE_SIZE, SQUARE_SIZE))

def draw_board(highlighted_squares=None, selected_square=None):
    if highlighted_squares is None:
        highlighted_squares = []
    for row in range(8):
        for col in range(8):
            color = WHITE if (row + col) % 2 == 0 else BLACK
            pygame.draw.rect(SCREEN, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
            board_coords = (7 - row, col)
            if board_coords in highlighted_squares:
                highlight_color = LIGHT_HIGHLIGHT if (row + col) % 2 == 0 else DARK_HIGHLIGHT
                pygame.draw.rect(SCREEN, highlight_color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 5)
            if selected_square == board_coords:
                pygame.draw.rect(SCREEN, (0, 255, 0), (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 5) # Green border for selected

def draw_pieces(board):
    for row in range(8):
        for col in range(8):
            piece = board.squares[7 - row][col]
            if piece:
                color_code = piece.color[0].lower()
                type_code = piece.type[0].lower() if piece.type != "knight" else "n"  # Use 'n' for knight
                piece_name = f"{color_code}{type_code}"
                SCREEN.blit(piece_images[piece_name], (col * SQUARE_SIZE, row * SQUARE_SIZE))

def get_clicked_square(pos):
    x, y = pos
    col = x // SQUARE_SIZE
    row = y // SQUARE_SIZE
    return 7 - row, col

def main():
    board = Board()
    running = True
    selected_piece_pos = None
    legal_moves = []

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                clicked_row, clicked_col = get_clicked_square(pos)
                clicked_pos = (clicked_row, clicked_col)

                if selected_piece_pos:
                    # Try to move the piece
                    if clicked_pos in legal_moves:
                        board.squares[clicked_row][clicked_col] = board.squares[selected_piece_pos[0]][selected_piece_pos[1]]
                        board.squares[selected_piece_pos[0]][selected_piece_pos[1]] = None
                        selected_piece_pos = None
                        legal_moves = []
                    else:
                        # Deselect if clicking on a non-legal move square
                        selected_piece_pos = None
                        legal_moves = []
                else:
                    # Select a piece
                    piece = board.squares[clicked_row][clicked_col]
                    if piece: # For now, let's allow selecting any piece
                        selected_piece_pos = clicked_pos
                        legal_moves = board.get_legal_moves(clicked_row, clicked_col)

        draw_board(legal_moves, selected_piece_pos)
        draw_pieces(board)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()