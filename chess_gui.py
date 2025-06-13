import pygame
from Main import Board, Piece
import copy
from pgn_handler import PGNGameImporter, load_pgn_into_game # Or just PGNGameImporter if you prefer to instantiate directly
import tkinter as tk
from tkinter import filedialog
import os
from engine_handler import StockfishAnalyzer, MoveQuality
# Initialize Pygame
pygame.init()

# Screen dimensions
SQUARE_SIZE = 70
BOARD_WIDTH = 8 * SQUARE_SIZE
BOARD_HEIGHT = 8 * SQUARE_SIZE
INFO_PANEL_WIDTH = 300
WIDTH = BOARD_WIDTH + INFO_PANEL_WIDTH
HEIGHT = BOARD_HEIGHT 

SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess Analysis")

# Colors
INFO_PANEL_BG = (40, 40, 40)
TEXT_COLOR = (255, 255, 255)
EVAL_BAR_WHITE = (240, 240, 240)
EVAL_BAR_BLACK = (70, 70 ,70)
EVAL_BAR_BOARDER = (10, 10, 10)
WHITE = (240, 217, 181)
BLACK = (0, 0, 139)
LIGHT_HIGHLIGHT = (255, 255, 102)
DARK_HIGHLIGHT = (173, 216, 230)

BUTTON_HEIGHT = 40
BUTTON_PADDING = 20

LOAD_PGN_BUTTON_WIDTH = INFO_PANEL_WIDTH - (2 * BUTTON_PADDING)
LOAD_PGN_BUTTON_X = BOARD_WIDTH + BUTTON_PADDING
LOAD_PGN_BUTTON_Y = HEIGHT - BUTTON_HEIGHT - BUTTON_PADDING 

LOAD_PGN_BUTTON_RECT = pygame.Rect(
    LOAD_PGN_BUTTON_X,
    LOAD_PGN_BUTTON_Y,
    LOAD_PGN_BUTTON_WIDTH,
    BUTTON_HEIGHT
)
LOAD_PGN_BUTTON_BG_COLOR = (70, 70, 130) 
LOAD_PGN_BUTTON_TEXT = "Load PGN"

#fonts 
try:
    PRIMARY_FONT = pygame.font.SysFont("Arial", 20)
    HISTORY_FONT = pygame.font.SysFont("Consolas", 15)
except pygame.error:
    PRIMARY_FONT = pygame.font.SysFont(None, 28)
    HISTORY_FONT = pygame.font.SysFont(None, 22)

# Define Rects for UI areas
# Eval bar area (top of info panel)
# Make eval bar later on.
EVAL_TEXT_RECT = pygame.Rect(BOARD_WIDTH + 10, 10, INFO_PANEL_WIDTH - 20, 30)
EVAL_BAR_RECT = pygame.Rect(BOARD_WIDTH + 10, 45, INFO_PANEL_WIDTH - 20, 30) # Actual bar

# Move history area (below eval bar)
HISTORY_TITLE_RECT = pygame.Rect(BOARD_WIDTH + 10, 90, INFO_PANEL_WIDTH - 20, 30)
MOVE_HISTORY_DISPLAY_RECT = pygame.Rect(BOARD_WIDTH + 10, 125, INFO_PANEL_WIDTH - 20, HEIGHT - 135)

# Load piece images
piece_images = {}
pieces = ["wp", "wr", "wn", "wb", "wq", "wk", "bp", "br", "bn", "bb", "bq", "bk"]
for piece in pieces:
    piece_images[piece] = pygame.image.load(f"images/{piece}.png")
    piece_images[piece] = pygame.transform.scale(piece_images[piece], (SQUARE_SIZE, SQUARE_SIZE))

def draw_board(highlighted_squares=None, selected_square=None, en_passant_target = None):
    if highlighted_squares is None:
        highlighted_squares = []

    highlight_coords_set = {tuple(move_info[:2]) for move_info in highlighted_squares}

    for row in range(8):
        for col in range(8):
            color = WHITE if (row + col) % 2 == 0 else BLACK
            pygame.draw.rect(SCREEN, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
            board_coords = (7 - row, col)
            if board_coords == selected_square:
                pygame.draw.rect(SCREEN, (0, 255, 0), (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 5) 
            elif board_coords == en_passant_target:
                pygame.draw.rect(SCREEN, (255, 165, 0), (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 5) 
            elif board_coords in highlight_coords_set :
                highlight_color = LIGHT_HIGHLIGHT if (row + col) % 2 == 0 else DARK_HIGHLIGHT
                pygame.draw.rect(SCREEN, highlight_color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 5)
            

def draw_pieces(board):
    for row in range(8):
        for col in range(8):
            piece = board.squares[7 - row][col]
            if piece:
                color_code = piece.color[0].lower()
                type_code = piece.type[0].lower() if piece.type != "knight" else "n" 
                piece_name = f"{color_code}{type_code}"
                SCREEN.blit(piece_images[piece_name], (col * SQUARE_SIZE, row * SQUARE_SIZE))

def draw_load_pgn_button(screen):
    """Draws the Load PGN button on the screen."""
    # Draw button background
    pygame.draw.rect(screen, LOAD_PGN_BUTTON_BG_COLOR, LOAD_PGN_BUTTON_RECT, border_radius=5)
    
    # Render button text
    text_surf = PRIMARY_FONT.render(LOAD_PGN_BUTTON_TEXT, True, TEXT_COLOR)
    text_rect = text_surf.get_rect(center=LOAD_PGN_BUTTON_RECT.center)
    
    # Blit text onto the button
    screen.blit(text_surf, text_rect)

def get_clicked_square(pos):
    x, y = pos
    col = x // SQUARE_SIZE
    row = y // SQUARE_SIZE
    return 7 - row, col

def draw_promotion_choice(screen, piece_color, pawn_board_pos):
   
    promotion_piece_types = ["queen", "rook", "bishop", "knight"]
    drawn_rects_with_types = []

    # Determine visual properties
    num_choices = len(promotion_piece_types)
    choice_box_width = SQUARE_SIZE * num_choices
    choice_box_height = SQUARE_SIZE
    
  
    pawn_gui_col = pawn_board_pos[1]
    pawn_gui_row = 7 - pawn_board_pos[0] # 


    choice_box_x = (pawn_gui_col * SQUARE_SIZE) + (SQUARE_SIZE / 2) - (choice_box_width / 2)


    if choice_box_x < 0:
        choice_box_x = 0
    elif choice_box_x + choice_box_width > WIDTH:
        choice_box_x = WIDTH - choice_box_width

    if piece_color == "white": 
        choice_box_y = (pawn_gui_row * SQUARE_SIZE) + SQUARE_SIZE
        if choice_box_y + choice_box_height > HEIGHT: 
            choice_box_y = (pawn_gui_row * SQUARE_SIZE) - choice_box_height
    else:
        choice_box_y = (pawn_gui_row * SQUARE_SIZE) - choice_box_height
        if choice_box_y < 0:
            choice_box_y = (pawn_gui_row * SQUARE_SIZE) + SQUARE_SIZE
    
    if choice_box_y < 0: choice_box_y = 0
    if choice_box_y + choice_box_height > HEIGHT : choice_box_y = HEIGHT - choice_box_height


    pygame.draw.rect(screen, (220, 220, 220), (choice_box_x, choice_box_y, choice_box_width, choice_box_height))
    pygame.draw.rect(screen, (0, 0, 0), (choice_box_x, choice_box_y, choice_box_width, choice_box_height), 2) 

    for i, p_type in enumerate(promotion_piece_types):
        color_char = piece_color[0].lower()
        type_char = p_type[0].lower() if p_type != "knight" else "n"
        piece_key = f"{color_char}{type_char}"

        if piece_key in piece_images:
            img = piece_images[piece_key]
            img_x = choice_box_x + i * SQUARE_SIZE
            img_y = choice_box_y
            
            img_rect = pygame.Rect(img_x, img_y, SQUARE_SIZE, SQUARE_SIZE)
            screen.blit(img, img_rect)
            drawn_rects_with_types.append((img_rect, p_type))
        else:
            print(f"Warning: Image key {piece_key} not found for promotion.")

    return drawn_rects_with_types


def draw_move_history(screen, move_history, font, display_rect):
    pygame.draw.rect(screen, INFO_PANEL_BG, display_rect.inflate(20,20)) # Background for entire panel area

    title_surf = PRIMARY_FONT.render("Move History", True, TEXT_COLOR)
    screen.blit(title_surf, (display_rect.x, HISTORY_TITLE_RECT.y + 5)) # Use HISTORY_TITLE_RECT for y

    y_offset = 5 # Start drawing moves a bit below the title
    line_height = font.get_linesize()

    # Determine how many moves can fit
    max_visible_lines = display_rect.height // line_height

    # Display last N moves if history is too long (basic scrolling)
    start_index = 0
    if len(move_history) > max_visible_lines * 2 : 
        start_index = max(0, len(move_history) - max_visible_lines)


    current_move_number = 0
    formatted_line = ""

    for i in range(start_index, len(move_history)):
        log = move_history[i]

        if log["player"] == "white":
            current_move_number = (i // 2) + 1
            formatted_line = f"{current_move_number}. {log['simple_notation']}"
        else: 
            if formatted_line.startswith(f"{current_move_number}."):
                formatted_line += f"  {log['simple_notation']}"
            else: 
                formatted_line = f"   {log['simple_notation']}"

            move_surf = font.render(formatted_line, True, TEXT_COLOR)
            screen.blit(move_surf, (display_rect.x + 5, display_rect.y + y_offset))
            y_offset += line_height
            formatted_line = "" 

        
        if log["player"] == "white" and i == len(move_history) - 1:
            move_surf = font.render(formatted_line, True, TEXT_COLOR)
            screen.blit(move_surf, (display_rect.x + 5, display_rect.y + y_offset))
            y_offset += line_height

        if y_offset + line_height > display_rect.height: 
            break

def log_move_to_history(board_obj, player_color, piece_obj_moved, original_type_str,
                        start_tuple, end_tuple, captured_piece_obj, 
                        promotion_choice_str, is_check, results_in_mate_for_opponent, results_in_stalemate_for_opponent, 
                        special_move_type = None):
    """
    Helper function to create and append a log entry to board.move_history.
    is_check: Does THIS move put the opponent in check?
    
    """
    log_entry = {
        "player": player_color,
        "piece_type_moved": piece_obj_moved.type, 
        "original_type_moved": original_type_str,
        "start_sq_alg": board_obj._algebraic_square(start_tuple[0], start_tuple[1]),
        "end_sq_alg": board_obj._algebraic_square(end_tuple[0], end_tuple[1]),
        "is_capture": captured_piece_obj is not None,
        "captured_type": captured_piece_obj.type if captured_piece_obj else None,
        "promotion_to": promotion_choice_str.upper()[0] if promotion_choice_str else None,
        "gives_check": is_check,
        "results_in_mate": results_in_mate_for_opponent,
        "results_in_stalemate": results_in_stalemate_for_opponent,
        "special_move_type": special_move_type # Store it in the log
    }
    # Create a simple notation string (can be made more sophisticated for full SAN)
    move_text = ""
    if special_move_type == "kingside_castle":
        move_text = "O-O" 
    elif special_move_type == "queenside_castle":
        move_text = "O-O-O"
    else:
        notation_original_type = log_entry["original_type_moved"]
        notation_is_capture = log_entry["is_capture"]
        notation_start_file = log_entry["start_sq_alg"][0]
        notation_end_square = log_entry["end_sq_alg"]

        if notation_original_type == "pawn":
            if notation_is_capture:
                move_text = f"{notation_start_file}x{notation_end_square}"
            else:
                move_text = notation_end_square
        else:
            piece_char = notation_original_type[0].upper()
            if notation_original_type == "knight":
                piece_char = "N"
            
            move_text = f"{piece_char}{"x" if notation_is_capture else ""}{notation_end_square}"
        
        if log_entry["promotion_to"]:
            move_text += f"={log_entry['promotion_to']}"

    if log_entry["results_in_mate"]:
        move_text += "#"
    elif log_entry["gives_check"]:
        move_text += "+"

    log_entry["simple_notation"] = move_text
    board_obj.move_history.append(log_entry)
    print(f"Logged: {log_entry['simple_notation']}") # For debugging

def main():
    board = Board() 
    running = True
    selected_piece_pos = None
    legal_moves = []
    en_passant_target = None
    current_player = "white" # For interactive play
    in_check = False
    game_over = False # For interactive play
    winner = None
    STOCKFISH_PATH = "E:\School\SE\stockfish\stockfish-windows-x86-64-avx2.exe"
    analyzer = None

    try:
        analyzer = StockfishAnalyzer(STOCKFISH_PATH, depth=15)
        if not analyzer.engine:
            print("stockfish could not start")
            analyzer = None
    except Exception as e:
        print(f"Error starting Stockfish: {e}")
        analyzer = None

    current_move_analysis_results = {
        'eval_before_cp_white': None,   # Eval before move (White's perspective)
        'eval_after_cp_white': None,    # Eval after move (White's perspective)
        'best_move_before_san': None, # Stockfish's best move before the played move
        'played_move_san': None,      # The actual move played in the PGN
        'classification': None,       # e.g., MoveQuality.BLUNDER
        'player_who_moved': None,     # 'white' or 'black'
        'initial_pos_eval_cp_white': None, # For the very first position
        'initial_pos_best_move_san': None
    }

    is_promoting = False
    promotion_details = None
    promotion_choice_rects = []
    pending_log_info = {}

    # --- PGN Game Data State ---
    loaded_pgn_data = None 
    loaded_pgn_board_states = [] 
    current_pgn_state_index = -1 
    pgn_mode_active = False 


    # --- Sample PGN text (replace with file loading later) ---
    current_pgn_file_path = None

    clock = pygame.time.Clock()

    def get_centipawns_from_white_pov(score_obj):
        """Converts chess.engine.Score to centipawns from White's perspective."""
        if score_obj is None:
            return 0 
        if score_obj.is_mate():
            
            return score_obj.white().score(mate_score=30000) 
        else:
            return score_obj.white().score() 

    def update_pgn_analysis():
        nonlocal current_move_analysis_results, board, loaded_pgn_board_states, loaded_pgn_data, current_pgn_state_index, analyzer

        
        current_move_analysis_results = {
            'eval_before_cp_white': None, 'eval_after_cp_white': None,
            'best_move_before_san': None, 'played_move_san': None,
            'classification': None, 'player_who_moved': None,
            'initial_pos_eval_cp_white': None, 'initial_pos_best_move_san': None
        }

        if not analyzer or not analyzer.engine:
            print("DEBUG: Analyzer not available for update_pgn_analysis.")
            return

        analysis_time_ms = 750 

        if current_pgn_state_index == 0: 
            temp_initial_board = Board() #
            temp_initial_board.squares = copy.deepcopy(loaded_pgn_board_states[0])
            # temp_initial_board.move_history = [] # Should be empty for initial FEN

            eval_obj_initial = analyzer.evaluate_position(temp_initial_board, "white", time_limit_ms=analysis_time_ms)
            current_move_analysis_results['initial_pos_eval_cp_white'] = get_centipawns_from_white_pov(eval_obj_initial)
            current_move_analysis_results['initial_pos_best_move_san'] = analyzer.get_best_move_san(temp_initial_board, "white", time_limit_ms=analysis_time_ms)
            print(f"DEBUG Initial Pos Eval (White's POV): {current_move_analysis_results['initial_pos_eval_cp_white']}, Best SAN: {current_move_analysis_results['initial_pos_best_move_san']}")

        elif current_pgn_state_index > 0 and current_pgn_state_index <= len(loaded_pgn_data.get('moves', [])):
          
            move_data = loaded_pgn_data['moves'][current_pgn_state_index - 1]
            player_who_moved = move_data['color']
            played_move_san = move_data['algebraic'] # PGN algebraic notation

            # --- State BEFORE the played move ---
            temp_board_before = Board()
            temp_board_before.squares = copy.deepcopy(loaded_pgn_board_states[current_pgn_state_index - 1])
            temp_board_before.move_history = [m for i, m in enumerate(loaded_pgn_data['moves']) if i < current_pgn_state_index - 1]
            eval_obj_before = analyzer.evaluate_position(temp_board_before, player_who_moved, time_limit_ms=analysis_time_ms)
            best_move_san_before = analyzer.get_best_move_san(temp_board_before, player_who_moved, time_limit_ms=analysis_time_ms)
            eval_cp_before_white = get_centipawns_from_white_pov(eval_obj_before)

            # --- State AFTER the played move (current 'board' object) ---
            player_to_move_now = "black" if player_who_moved == "white" else "white"
            temp_board_after = Board()
            temp_board_after.squares = copy.deepcopy(board.squares) # Current state
            temp_board_after.move_history = [m for i, m in enumerate(loaded_pgn_data['moves']) if i < current_pgn_state_index]


            eval_obj_after = analyzer.evaluate_position(temp_board_after, player_to_move_now, time_limit_ms=analysis_time_ms)
            eval_cp_after_white = get_centipawns_from_white_pov(eval_obj_after)

            # --- Store results ---
            current_move_analysis_results['eval_before_cp_white'] = eval_cp_before_white
            current_move_analysis_results['eval_after_cp_white'] = eval_cp_after_white
            current_move_analysis_results['best_move_before_san'] = best_move_san_before
            current_move_analysis_results['played_move_san'] = played_move_san
            current_move_analysis_results['player_who_moved'] = player_who_moved

            classification = analyzer.classify_move(
                played_move_san,
                best_move_san_before,
                eval_cp_before_white,
                eval_cp_after_white,
                player_who_moved
            )
            current_move_analysis_results['classification'] = classification

            print(f"DEBUG Analysis for move {current_pgn_state_index} ({player_who_moved}'s {played_move_san}):")
            # print(f"  Eval Before (White POV): {eval_cp_before_white}, Best SAN for {player_who_moved}: {best_move_san_before}")
            # print(f"  Eval After (White POV): {eval_cp_after_white}")
            print(f"  Best SAN for {player_who_moved}: {best_move_san_before}")
            print(f"  Classification: {classification.value if classification else 'N/A'}")
        else:
            print(f"DEBUG: Skipping analysis. current_pgn_state_index={current_pgn_state_index}, moves_len={len(loaded_pgn_data.get('moves',[]))}")

    def select_pgn_file():
        pygame.display.iconify()
        
        # Create a temporary tkinter root window (hidden)
        root = tk.Tk()
        root.withdraw()  # Hide the main tkinter window
        root.attributes('-topmost', True)  # Bring file dialog to front
        
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Select PGN File",
            filetypes=[
                ("PGN files", "*.pgn"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ],
            initialdir=os.getcwd()  # Start in current directory
        )
        
        # Clean up tkinter
        root.destroy()
        
        # Restore pygame window
        pygame.display.set_mode(pygame.display.get_surface().get_size())
        
        return file_path if file_path else None
    
    def load_pgn_from_file(file_path):
        """Load PGN content from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                pgn_content = file.read()
            return pgn_content
        except FileNotFoundError:
            print(f"Error: File not found: {file_path}")
            return None
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    pgn_content = file.read()
                return pgn_content
            except Exception as e:
                print(f"Error reading file with latin-1 encoding: {e}")
                return None
        except Exception as e:
            print(f"Error reading file: {e}")
            return None

#     sample_pgn_to_load = """
# [Event "Casual Game"]
# [Site "Local"]
# [Date "2025.05.31"]
# [Round "-"]
# [White "Player1"]
# [Black "Player2"]
# [Result "*"]

# 1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O *
# """

    def load_pgn_game():
        """Load and parse the PGN game"""
        nonlocal loaded_pgn_data, loaded_pgn_board_states, current_pgn_state_index, pgn_mode_active, current_pgn_file_path

        file_path = select_pgn_file()
        if not file_path:
            print("No file selected.")
            return False
        
        # Load PGN content from file
        pgn_content = load_pgn_from_file(file_path)
        if not pgn_content:
            print("Failed to load PGN content from file.")
            return False

        try:
            # Import the PGN using your parser
            loaded_pgn_data = load_pgn_into_game(pgn_content, Board, Piece)
            loaded_pgn_board_states = loaded_pgn_data['board_states']
            
            if loaded_pgn_board_states:
                current_pgn_state_index = 0  # Start at initial position
                pgn_mode_active = True
                current_pgn_file_path = file_path                
                # Set board to initial PGN position
                board.squares = copy.deepcopy(loaded_pgn_board_states[current_pgn_state_index])
                
                # Reset interactive game state
                selected_piece_pos = None
                legal_moves = []
                
                print(f"Loaded PGN game from: {os.path.basename(file_path)}")
                print(f"Game: {loaded_pgn_data['headers'].get('White', 'Unknown')} vs {loaded_pgn_data['headers'].get('Black', 'Unknown')}")
                print(f"Event: {loaded_pgn_data['headers'].get('Event', 'Unknown')}")
                print(f"Date: {loaded_pgn_data['headers'].get('Date', 'Unknown')}")
                print(f"Total moves: {len(loaded_pgn_data['moves'])}")
                print("Use LEFT/RIGHT arrow keys to navigate, ESC to exit PGN mode")
                update_pgn_analysis()
                return True
            else:
                print("Failed to load PGN - no board states generated")
                return False
                
        except Exception as e:
            print(f"Error loading PGN: {e}")
            return False
        
    def exit_pgn_mode_action():
        nonlocal pgn_mode_active, current_pgn_state_index, loaded_pgn_data, loaded_pgn_board_states
        nonlocal current_player, game_over, in_check, selected_piece_pos, legal_moves, board, en_passant_target, current_pgn_file_path
        
        pgn_mode_active = False
        current_pgn_state_index = -1
        loaded_pgn_data = None
        loaded_pgn_board_states = []
        current_pgn_file_path = None
        
        board.setup_board()
        board.move_history = []
        
        current_player = "white"
        selected_piece_pos = None
        legal_moves = []
        en_passant_target = None
        game_over = False
        in_check = False
        print("Exited PGN mode. Returned to interactive play.")
        update_pgn_analysis()
        
    def load_pgn_from_predefined_path(file_path):
        """Load PGN from a specific file path without file dialog"""
        nonlocal loaded_pgn_data, loaded_pgn_board_states, current_pgn_state_index, pgn_mode_active, current_pgn_file_path
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return False
            
        pgn_content = load_pgn_from_file(file_path)
        if not pgn_content:
            return False
            
        try:
            loaded_pgn_data = load_pgn_into_game(pgn_content, Board, Piece)
            loaded_pgn_board_states = loaded_pgn_data['board_states']
            
            if loaded_pgn_board_states:
                current_pgn_state_index = 0
                pgn_mode_active = True
                current_pgn_file_path = file_path
                
                board.squares = copy.deepcopy(loaded_pgn_board_states[current_pgn_state_index])
                selected_piece_pos = None
                legal_moves = []
                
                print(f"Loaded PGN game from: {os.path.basename(file_path)}")
                return True
            return False
        except Exception as e:
            print(f"Error parsing PGN: {e}")
            return False
    

    while running: 
        # player_who_moved_this_turn = current_player # This is for interactive play

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if LOAD_PGN_BUTTON_RECT.collidepoint(mouse_pos):
                    if pgn_mode_active:
                        print("Reloading PGN...")
                    else:
                        print("Loading PGN game...")
                    load_pgn_game()
                    continue

            if pgn_mode_active:
                # Handle events specific to PGN mode
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    if LOAD_PGN_BUTTON_RECT.collidepoint(mouse_pos):
                        
                        print("Load PGN button clicked while PGN mode active (or to activate).")
                        load_pgn_game() # This will reset the PGN view
                        

                elif event.type == pygame.KEYDOWN: # Corrected indentation
                    if event.key == pygame.K_LEFT:
                        if current_pgn_state_index > 0:
                            current_pgn_state_index -= 1
                            board.squares = copy.deepcopy(loaded_pgn_board_states[current_pgn_state_index])
                            # Reset any interactive elements that shouldn't persist
                            selected_piece_pos = None
                            legal_moves = []
                            print(f"PGN: Displaying move state {current_pgn_state_index}")
                            update_pgn_analysis()
                    elif event.key == pygame.K_RIGHT:
                        if loaded_pgn_board_states and current_pgn_state_index < len(loaded_pgn_board_states) - 1:
                            current_pgn_state_index += 1
                            board.squares = copy.deepcopy(loaded_pgn_board_states[current_pgn_state_index])
                            # Reset any interactive elements
                            selected_piece_pos = None
                            legal_moves = []
                            print(f"PGN: Displaying move state {current_pgn_state_index}")
                            update_pgn_analysis()
                    elif event.key == pygame.K_ESCAPE:
                        exit_pgn_mode_action()

                # After handling PGN-specific events, skip the rest of the interactive play logic for this event
                continue

            # Interactive Play Event Handling (only if not in pgn_mode_active)
            elif is_promoting:
                if event.type == pygame.MOUSEBUTTONDOWN and promotion_details:
                    mouse_pos = pygame.mouse.get_pos()
                    for rect, chosen_promotion_piece_type_str in promotion_choice_rects:
                        if rect.collidepoint(mouse_pos):
                            log_start_pos = pending_log_info["start_pos_tuple"]
                            log_end_pos = pending_log_info["end_pos_tuple"]
                            # log_original_piece_obj = pending_log_info["piece_that_moved_obj"] # Use piece_that_moved_obj directly
                            log_captured_piece = pending_log_info["captured_piece_at_destination"]
                            log_player = pending_log_info["player_who_moved"]
                            
                            board.squares[log_end_pos[0]][log_end_pos[1]] = Piece(log_player, chosen_promotion_piece_type_str)
                            opponent_color = "black" if log_player == "white" else "white"
                            gives_check_after_promo = board.is_in_check(opponent_color)

                            log_move_to_history(board, log_player, board.squares[log_end_pos[0]][log_end_pos[1]], 
                                                "pawn", log_start_pos, log_end_pos, 
                                                log_captured_piece, chosen_promotion_piece_type_str, gives_check_after_promo, 
                                                False, False, # Mate/Stalemate determined later
                                                pending_log_info.get("special_move_type_from_board")) # Use .get for safety
                            
                            is_promoting = False
                            promotion_details = None
                            promotion_choice_rects = []
                            pending_log_info = {}
                            current_player = opponent_color
                            in_check = board.is_in_check(current_player)
                            # Check for game over *after* promotion is complete and player switched
                            # The main checkmate/stalemate loop will handle it.
                            break 
                # Ensure to break from event loop or manage flow if promotion click handled

            elif event.type == pygame.MOUSEBUTTONDOWN and not game_over and not pgn_mode_active:
                mouse_pos = pygame.mouse.get_pos()

                if 0 <= mouse_pos[0] < BOARD_WIDTH and 0 <= mouse_pos[1] < BOARD_HEIGHT: # Click on board

                    clicked_board_row, clicked_board_col = get_clicked_square(mouse_pos)
                    clicked_board_pos = (clicked_board_row, clicked_board_col)

                    if selected_piece_pos: 

                        is_move_valid_for_selected = False
                        chosen_move_tuple = None
                        for move_tuple_iter in legal_moves:
                            if (move_tuple_iter[0], move_tuple_iter[1]) == clicked_board_pos:
                                is_move_valid_for_selected = True
                                chosen_move_tuple = move_tuple_iter
                                break
                        
                        if is_move_valid_for_selected:
                            player_who_moved = current_player # Corrected: use current_player
                            piece_that_moved_obj = board.squares[selected_piece_pos[0]][selected_piece_pos[1]]
                            start_pos_tuple = selected_piece_pos
                            end_pos_tuple = clicked_board_pos
                            move_type = chosen_move_tuple[2] if len(chosen_move_tuple) > 2 else None

                            success, actual_captured_piece_for_log = board.make_move(
                                selected_piece_pos, clicked_board_pos, move_type=move_type
                            )

                            if success:
                                piece_now_at_destination = board.squares[end_pos_tuple[0]][end_pos_tuple[1]]
                                original_type_for_log = piece_that_moved_obj.type
                                if piece_now_at_destination and piece_now_at_destination.type == "pawn":
                                    # ... (promotion check logic, sets is_promoting & pending_log_info) ...
                                    pawn_color_moved = piece_now_at_destination.color
                                    pawn_final_row = end_pos_tuple[0]
                                    is_at_promotion_rank = (pawn_color_moved == "white" and pawn_final_row == 7) or \
                                                           (pawn_color_moved == "black" and pawn_final_row == 0)
                                    if is_at_promotion_rank:
                                        is_promoting = True
                                        promotion_details = (pawn_final_row, end_pos_tuple[1], pawn_color_moved)
                                        original_type_for_log = "pawn"
                                        pending_log_info = {
                                            "player_who_moved": player_who_moved,
                                            "piece_that_moved_obj": piece_that_moved_obj,
                                            "start_pos_tuple": start_pos_tuple,
                                            "end_pos_tuple": end_pos_tuple,
                                            "captured_piece_at_destination": actual_captured_piece_for_log,
                                            "special_move_type_from_board": move_type
                                        }
                                    else: # Not promoting pawn move
                                        opponent_color = "black" if player_who_moved == "white" else "white"
                                        gives_check_val = board.is_in_check(opponent_color)
                                        log_move_to_history(board, player_who_moved, piece_now_at_destination, original_type_for_log, 
                                                            start_pos_tuple, end_pos_tuple, actual_captured_piece_for_log, 
                                                            None, gives_check_val, False, False, move_type)
                                        current_player = opponent_color
                                        in_check = board.is_in_check(current_player)
                                else: # Not a pawn move, or non-promoting pawn move
                                    opponent_color = "black" if player_who_moved == "white" else "white"
                                    gives_check_val = board.is_in_check(opponent_color)
                                    log_move_to_history(board, player_who_moved, piece_now_at_destination, original_type_for_log,
                                                        start_pos_tuple, end_pos_tuple, actual_captured_piece_for_log,
                                                        None, gives_check_val, False, False, move_type)
                                    current_player = opponent_color
                                    in_check = board.is_in_check(current_player)
                                
                                if not is_promoting:
                                    selected_piece_pos = None
                                    legal_moves = []
                                    en_passant_target = None
                        else: # Clicked on invalid square or own piece again
                            new_click_piece = board.squares[clicked_board_row][clicked_board_col]
                            if new_click_piece and new_click_piece.color == current_player: # Clicked on another of own pieces
                                selected_piece_pos = clicked_board_pos

                                pseudo_moves = board.get_legal_moves(clicked_board_row, clicked_board_col)
                                valid_filtered_moves = []
                                current_en_passant_target_for_highlight = None
                                for p_move in pseudo_moves:
                                    p_end_r, p_end_c = p_move[:2]
                                    p_m_type = p_move[2] if len(p_move) > 2 else None
                                    temp_b = Board()
                                    temp_b.squares = copy.deepcopy(board.squares)
                                    temp_b.last_move = board.last_move
                                    temp_b.make_move(selected_piece_pos, (p_end_r, p_end_c), move_type=p_m_type)
                                    if not temp_b.is_in_check(current_player):
                                        valid_filtered_moves.append(p_move)
                                        if p_m_type == "en_passant":
                                            current_en_passant_target_for_highlight = (p_end_r, p_end_c)
                                legal_moves = valid_filtered_moves
                                en_passant_target = current_en_passant_target_for_highlight
                            else: # Clicked invalid or deselected
                                selected_piece_pos = None
                                legal_moves = []
                                en_passant_target = None
                    else: # No piece selected, try to select one
                        piece_to_select = board.squares[clicked_board_row][clicked_board_col]
                        if piece_to_select and piece_to_select.color == current_player:
                            selected_piece_pos = clicked_board_pos
                            pseudo_moves = board.get_legal_moves(clicked_board_row, clicked_board_col)
                            valid_filtered_moves = []
                            current_en_passant_target_for_highlight = None
                            for p_move in pseudo_moves:
                                p_end_r, p_end_c = p_move[:2]
                                p_m_type = p_move[2] if len(p_move) > 2 else None
                                temp_b = Board()
                                temp_b.squares = copy.deepcopy(board.squares)
                                temp_b.last_move = board.last_move
                                temp_b.make_move(selected_piece_pos, (p_end_r, p_end_c), move_type=p_m_type)
                                if not temp_b.is_in_check(current_player):
                                    valid_filtered_moves.append(p_move)
                                    if p_m_type == "en_passant":
                                        current_en_passant_target_for_highlight = (p_end_r, p_end_c)
                            legal_moves = valid_filtered_moves
                            en_passant_target = current_en_passant_target_for_highlight
                        else: # Clicked empty or opponent
                            selected_piece_pos = None
                            legal_moves = []
                            en_passant_target = None
                    # --- End of interactive move logic ---
            
        # --- Game Logic Updates (Checkmate/Stalemate for INTERACTIVE play) ---
        if not pgn_mode_active and not is_promoting and not game_over:
            is_player_in_check_for_eval = board.is_in_check(current_player) 
            has_any_legal_move_for_eval = False
            # ... (the full loop to check for any legal move for current_player)
            for r_start_eval in range(8):
                for c_start_eval in range(8):
                    piece_eval = board.squares[r_start_eval][c_start_eval]
                    if piece_eval and piece_eval.color == current_player:
                        pseudo_legal_for_piece_eval = board.get_legal_moves(r_start_eval, c_start_eval)
                        for p_move_eval in pseudo_legal_for_piece_eval:
                            p_end_r_eval, p_end_c_eval = p_move_eval[:2]
                            p_m_type_eval = p_move_eval[2] if len(p_move_eval) > 2 else None
                            temp_board_eval_instance = Board() # Renamed to avoid conflict
                            temp_board_eval_instance.squares = copy.deepcopy(board.squares)
                            temp_board_eval_instance.last_move = board.last_move
                            temp_board_eval_instance.make_move((r_start_eval, c_start_eval), (p_end_r_eval, p_end_c_eval), move_type=p_m_type_eval)
                            if not temp_board_eval_instance.is_in_check(current_player):
                                has_any_legal_move_for_eval = True
                                break 
                        if has_any_legal_move_for_eval: break
                if has_any_legal_move_for_eval: break
            
            if not has_any_legal_move_for_eval:
                game_over = True
                if is_player_in_check_for_eval: 
                    winner = "Black" if current_player == "white" else "White"
                    if board.move_history and not pending_log_info:
                        board.move_history[-1]["results_in_mate"] = True 
                    print(f"Checkmate! {winner} wins!")
                else:
                    winner = "Stalemate"
                    if board.move_history and not pending_log_info:
                        board.move_history[-1]["results_in_stalemate"] = True
                    print("Stalemate! The game is a draw.")
            in_check = is_player_in_check_for_eval # Update in_check for current interactive player

        # --- Drawing ---
        SCREEN.fill(INFO_PANEL_BG)
        
        
        draw_board(legal_moves if not pgn_mode_active else [], 
                   selected_piece_pos if not pgn_mode_active else None, 
                   en_passant_target if not pgn_mode_active else None)
        draw_pieces(board) 

        pygame.draw.rect(SCREEN, INFO_PANEL_BG, (BOARD_WIDTH, 0, INFO_PANEL_WIDTH, HEIGHT))
        draw_move_history(SCREEN, board.move_history, HISTORY_FONT, MOVE_HISTORY_DISPLAY_RECT) # Shows PGN moves if loaded
        draw_load_pgn_button(SCREEN) # Draw the button

        if is_promoting and not pgn_mode_active: # Promotion UI only for interactive play
            promotion_choice_rects = draw_promotion_choice(SCREEN, promotion_details[2], (promotion_details[0], promotion_details[1]))

        if pgn_mode_active and analyzer and analyzer.engine:
            analysis_y_start = MOVE_HISTORY_DISPLAY_RECT.bottom + 5 # Start below move history
            line_h = PRIMARY_FONT.get_height() + 2 # Height for each line of text

            analysis_texts = []

            if current_pgn_state_index == 0: # Initial position
                if current_move_analysis_results.get('initial_pos_eval_cp_white') is not None:
                    eval_val = current_move_analysis_results['initial_pos_eval_cp_white'] / 100.0
                    analysis_texts.append(f"Initial Eval: {eval_val:+.2f}")
                if current_move_analysis_results.get('initial_pos_best_move_san'):
                    analysis_texts.append(f"Suggested: {current_move_analysis_results['initial_pos_best_move_san']}")
            elif current_pgn_state_index > 0:
                player_moved = current_move_analysis_results.get('player_who_moved', '')
                played_san = current_move_analysis_results.get('played_move_san', 'N/A')
                classification = current_move_analysis_results.get('classification')
                
                move_desc = f"{player_moved.capitalize()}'s {played_san}"
                if classification:
                    move_desc += f" ({classification.value})"
                analysis_texts.append(move_desc)

                if current_move_analysis_results.get('eval_before_cp_white') is not None:
                    eval_b = current_move_analysis_results['eval_before_cp_white'] / 100.0
                    analysis_texts.append(f"  Eval Before: {eval_b:+.2f}")
                
                if current_move_analysis_results.get('best_move_before_san'):
                    analysis_texts.append(f"  Stockfish Best: {current_move_analysis_results['best_move_before_san']}")

                if current_move_analysis_results.get('eval_after_cp_white') is not None:
                    eval_a = current_move_analysis_results['eval_after_cp_white'] / 100.0
                    analysis_texts.append(f"  Eval After: {eval_a:+.2f}")
            
            for i, text_line in enumerate(analysis_texts):
                surf = HISTORY_FONT.render(text_line, True, TEXT_COLOR) # Use HISTORY_FONT for consistency
                SCREEN.blit(surf, (MOVE_HISTORY_DISPLAY_RECT.x + 5, analysis_y_start + (i * line_h)))
        # ------------------------------------
        caption_text = f"Chess Analysis - "
        if pgn_mode_active:
            if loaded_pgn_data and loaded_pgn_data['headers']:
                white_player = loaded_pgn_data['headers'].get('White', 'N/A')
                black_player = loaded_pgn_data['headers'].get('Black', 'N/A')
                caption_text += f"PGN: {white_player} vs {black_player} (Move {current_pgn_state_index})"
            else:
                caption_text += "PGN Mode"
        elif game_over:
            caption_text += f"Game Over! {winner}"
            if winner not in ["Stalemate", "Draw"]: caption_text += " wins!"
        else:
            caption_text += f"{current_player.capitalize()} to move"
            if in_check: caption_text += " (Check!)"
            if is_promoting: caption_text += " (Promoting Pawn)"
        pygame.display.set_caption(caption_text)

        pygame.display.flip()

    # --- Game Over Screen (Only for interactive game that ended) ---
    if game_over and not pgn_mode_active : # Check if game over was from interactive play
        try:
            game_over_font = pygame.font.SysFont("Arial", 60)
        except pygame.error:
            game_over_font = pygame.font.Font(None, 74) 
        text_content_final = f"Checkmate! {winner} wins!" if winner not in ["Stalemate","Draw"] else "Stalemate! Draw!"
        text_surface_final = game_over_font.render(text_content_final, True, (200, 0, 0))
        text_rect_final = text_surface_final.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        bg_rect_final = text_rect_final.inflate(40, 40)
        pygame.draw.rect(SCREEN, (50, 50, 50, 230), bg_rect_final)
        pygame.draw.rect(SCREEN, (255,255,255), bg_rect_final, 2)
        SCREEN.blit(text_surface_final, text_rect_final)
        pygame.display.flip()
        waiting_for_close = True
        while waiting_for_close:
            for event_loop_end in pygame.event.get():
                if event_loop_end.type == pygame.QUIT: waiting_for_close = False; running = False # Ensure outer loop also terminates
                if event_loop_end.type == pygame.KEYDOWN and event_loop_end.key == pygame.K_ESCAPE: waiting_for_close = False; running = False
            pygame.time.wait(30)
    if analyzer:
        analyzer.quit()
    
    pygame.quit()

if __name__ == "__main__":
    main()