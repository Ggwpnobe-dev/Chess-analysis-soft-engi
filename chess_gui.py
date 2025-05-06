import pygame
from Main import Board, Piece  # Assuming your board and piece classes are in main.py

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

# Load piece images (you'll need to provide these)
piece_images = {}
pieces = ["wp", "wr", "wn", "wb", "wq", "wk", "bp", "br", "bn", "bb", "bq", "bk"]
for piece in pieces:
    piece_images[piece] = pygame.image.load(f"images/{piece}.png")
    piece_images[piece] = pygame.transform.scale(piece_images[piece], (SQUARE_SIZE, SQUARE_SIZE))

def draw_board():
    for row in range(8):
        for col in range(8):
            color = WHITE if (row + col) % 2 == 0 else BLACK
            pygame.draw.rect(SCREEN, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

def draw_pieces(board):
    for row in range(8):
        for col in range(8):
            piece = board.squares[7 - row][col]  # Adjust row index for Pygame's coordinate system
            if piece:
                piece_name = f"{piece.color[0].lower()}{piece.type[0].lower()}"
                SCREEN.blit(piece_images[piece_name], (col * SQUARE_SIZE, row * SQUARE_SIZE))

def main():
    board = Board()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        draw_board()
        draw_pieces(board)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()