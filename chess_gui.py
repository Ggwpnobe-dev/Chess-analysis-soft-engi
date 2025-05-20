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
BLACK = (0, 0, 139)
LIGHT_HIGHLIGHT = (255, 255, 102)
DARK_HIGHLIGHT = (173, 216, 230)

# Load piece images
piece_images = {}
pieces = ["wp", "wr", "wn", "wb", "wq", "wk", "bp", "br", "bn", "bb", "bq", "bk"]
for piece in pieces:
    piece_images[piece] = pygame.image.load(f"images/{piece}.png")
    piece_images[piece] = pygame.transform.scale(piece_images[piece], (SQUARE_SIZE, SQUARE_SIZE))

def draw_board(highlighted_squares=None, selected_square=None, en_passant_target = None):
    if highlighted_squares is None:
        highlighted_squares = []
    for row in range(8):
        for col in range(8):
            color = WHITE if (row + col) % 2 == 0 else BLACK
            pygame.draw.rect(SCREEN, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
            board_coords = (7 - row, col)
            if board_coords == selected_square:
                pygame.draw.rect(SCREEN, (0, 255, 0), (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 5) 
            elif board_coords in highlighted_squares and en_passant_target != board_coords:
                highlight_color = LIGHT_HIGHLIGHT if (row + col) % 2 == 0 else DARK_HIGHLIGHT
                pygame.draw.rect(SCREEN, highlight_color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 5)
            elif board_coords == en_passant_target:
                pygame.draw.rect(SCREEN, (255, 165, 0), (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 5) 

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
    en_passant_target = None
    current_player = "white"
    in_check = False
    game_over = False
    winner = None

    while running and not game_over: # Added game_over to the loop condition
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                clicked_row, clicked_col = get_clicked_square(pos)
                clicked_pos = (clicked_row, clicked_col)

                if selected_piece_pos:
                    start_row, start_col = selected_piece_pos
                    selected_piece = board.squares[start_row][start_col]
                    if selected_piece and selected_piece.color == current_player:
                        possible_moves = board.get_legal_moves(start_row, start_col)
                        for move in possible_moves:
                            end_row, end_col = move[:2]
                            move_type = move[2] if len(move) > 2 else None
                            temp_board = Board()
                            temp_board.squares = [row[:] for row in board.squares]
                            temp_board.make_move(selected_piece_pos, (end_row, end_col))
                            if not temp_board.is_in_check(current_player):
                                if clicked_pos == (end_row, end_col):
                                    board.make_move(selected_piece_pos, clicked_pos)
                                    if move_type == "en_passant":
                                        capture_row = start_row
                                        capture_col = end_col
                                        board.squares[capture_row][capture_col] = None
                                    selected_piece_pos = None
                                    legal_moves = []
                                    en_passant_target = None
                                    current_player = "black" if current_player == "white" else "white"
                                    in_check = board.is_in_check(current_player)
                                    break
                            elif clicked_pos == (end_row, end_col):
                                pass
                        else:
                            selected_piece_pos = None
                            legal_moves = []
                            en_passant_target = None
                    else:
                        selected_piece_pos = None
                        legal_moves = []
                        en_passant_target = None
                else:
                    piece = board.squares[clicked_row][clicked_col]
                    if piece and piece.color == current_player:
                        all_legal_moves = board.get_legal_moves(clicked_row, clicked_col)
                        valid_moves = []
                        for move in all_legal_moves:
                            end_row, end_col = move[:2]
                            temp_board = Board()
                            temp_board.squares = [row[:] for row in board.squares]
                            temp_board.make_move((clicked_row, clicked_col), (end_row, end_col))
                            if not temp_board.is_in_check(current_player):
                                valid_moves.append(move)
                        legal_moves = valid_moves
                        selected_piece_pos = clicked_pos
                        en_passant_target = None
                        for move in legal_moves:
                            if len(move) > 2 and move[2] == "en_passant":
                                en_passant_target = (move[0], move[1])
                                break
                    else:
                        selected_piece_pos = None
                        legal_moves = []
                        en_passant_target = None

        if not game_over:
            if board.is_in_check(current_player):
                has_truly_legal_moves = False  # Use a more descriptive name
                for r_start in range(8):      # Iterate through all squares for starting piece
                    for c_start in range(8):
                        piece = board.squares[r_start][c_start]
                        if piece and piece.color == current_player:
                            pseudo_legal_moves = board.get_legal_moves(r_start, c_start) # Get potential moves
                            for move in pseudo_legal_moves:
                                end_row, end_col = move[:2]
                                move_type = move[2] if len(move) > 2 else None

                                # Create a temporary board to test the move
                                temp_board_checkmate = Board()
                                # Deep copy the board state
                                temp_board_checkmate.squares = [row_copy[:] for row_copy in board.squares]
                                # Also copy the last_move if your Board class uses it for things like en-passant validation internally
                                # (though _get_pawn_move seems to use self.last_move from the original board)
                                temp_board_checkmate.last_move = board.last_move 

                                # Make the move on the temporary board
                                temp_board_checkmate.make_move((r_start, c_start), (end_row, end_col))

                                # *** Crucial: Handle en-passant capture on the temporary board ***
                                # The Board.make_move only moves the pawn. The actual capture of the en-passant pawn
                                # is handled in chess_gui.py. This needs to be replicated for the temp board.
                                if move_type == "en_passant":
                                    # The pawn being captured is on the same row as the moving pawn's start,
                                    # but at the destination column.
                                    temp_board_checkmate.squares[r_start][end_col] = None

                                # Check if this move gets the player out of check
                                if not temp_board_checkmate.is_in_check(current_player):
                                    has_truly_legal_moves = True
                                    break  # Found a legal move for this piece
                            if has_truly_legal_moves:
                                break  # Found a legal move for the current player
                    if has_truly_legal_moves:
                        break  # Exit outer loop as well
                
                if board.is_in_check(current_player) and not has_truly_legal_moves: # Check condition again before declaring
                    game_over = True
                    winner = "Black" if current_player == "white" else "White"
                    print(f"Checkmate! {winner} wins!")
                    # Your checkmate screen display will then trigger outside the loop
                # Add stalemate logic here if desired:
                # elif not board.is_in_check(current_player) and not has_truly_legal_moves:
                # game_over = True
                # winner = "Stalemate" 
                # print("Stalemate! The game is a draw.")
                        
        draw_board(legal_moves, selected_piece_pos, en_passant_target)
        draw_pieces(board)
        pygame.display.set_caption(f"Chess Game - {current_player.capitalize()} to move")
        pygame.display.flip()

        if game_over:
            font = pygame.font.Font(None, 74)
            text_content = f"Checkmate! {winner} wins! \n press esc to close" if winner not in ["Stalemate"] else "Stalemate! Draw!"
            text = font.render(text_content, True, (255, 0, 0))
            text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            SCREEN.blit(text, text_rect)
            pygame.display.flip()
            waiting_for_close = True
            while waiting_for_close:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        waiting_for_close = False
                        running = False 
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE: # Example: Press ESC to close
                            waiting_for_close = False
                            running = False

                # Keep the screen updated (optional, but good practice if you add more elements)
                SCREEN.blit(text, text_rect)
                pygame.display.flip()
    pygame.quit()
    

if __name__ == "__main__":
    main()