import re, copy
from typing import Dict, List, Tuple, Optional
from Main import Board, Piece

class PGNParser:
    def __init__(self):
        self.file_to_coord = {
            'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7
        }
        self.coord_to_file = {v: k for k, v in self.file_to_coord.items()}
        
    def parse_pgn(self, pgn_text: str) -> Dict:
        """Parse a PGN string and return game data"""
        lines = pgn_text.strip().split('\n')
        
        # Parse headers
        headers = {}
        move_text = ""
        in_headers = True
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('[') and line.endswith(']'):
                # Header line
                match = re.match(r'\[(\w+)\s+"([^"]*)"\]', line)
                if match:
                    headers[match.group(1)] = match.group(2)
            else:
                # Move text
                in_headers = False
                move_text += line + " "
        
        # Parse moves
        moves = self.parse_moves(move_text.strip())
        
        return {
            'headers': headers,
            'moves': moves
        }
    
    def parse_moves(self, move_text: str) -> List[Dict]:
        """Parse the move text and return list of moves"""
        # Remove comments and variations (basic implementation)
        move_text = re.sub(r'\{[^}]*\}', '', move_text)  # Remove comments
        move_text = re.sub(r'\([^)]*\)', '', move_text)  # Remove variations
        
        # Split into tokens
        tokens = move_text.split()
        
        moves = []
        move_number = 1
        expecting_white = True
        
        for token in tokens:
            # Skip move numbers
            if re.match(r'\d+\.', token):
                move_number = int(token.rstrip('.'))
                expecting_white = True
                continue
            
            # Skip result markers
            if token in ['1-0', '0-1', '1/2-1/2', '*']:
                break
            
            # Parse actual move
            parsed_move = self.parse_single_move(token)
            if parsed_move:
                moves.append({
                    'move_number': move_number,
                    'color': 'white' if expecting_white else 'black',
                    'algebraic': token,
                    'parsed': parsed_move
                })
                
                if not expecting_white:
                    move_number += 1
                expecting_white = not expecting_white
        
        return moves
    
    def parse_single_move(self, move_str: str) -> Optional[Dict]:
        """Parse a single move in algebraic notation"""
        # Remove check/checkmate indicators
        original_move = move_str
        move_str = move_str.rstrip('+#')
        
        # Castling
        if move_str == 'O-O':
            return {'type': 'castle', 'side': 'kingside'}
        elif move_str == 'O-O-O':
            return {'type': 'castle', 'side': 'queenside'}
        
        # Regular move pattern
        pattern = r'^([NBRQK]?)([a-h]?)([1-8]?)(x?)([a-h][1-8])(?:=([NBRQ]))?$'
        match = re.match(pattern, move_str)
        
        if not match:
            return None
        
        piece, from_file, from_rank, capture, to_square, promotion = match.groups()
        
        return {
            'type': 'move',
            'piece': piece or 'P',  # Pawn if no piece specified
            'from_file': from_file,
            'from_rank': from_rank,
            'to_square': to_square,
            'capture': bool(capture),
            'promotion': promotion,
            'check': '+' in original_move,
            'checkmate': '#' in original_move
        }
    
    def square_to_coords(self, square: str) -> Tuple[int, int]:
        """Convert algebraic square to board coordinates"""
        file_char = square[0]
        rank_char = square[1]
        col = self.file_to_coord[file_char]
        row = int(rank_char) - 1  # Convert to 0-7, top to bottom
        return row, col
    
    def coords_to_square(self, row: int, col: int) -> str:
        """Convert board coordinates to algebraic square"""
        file_char = self.coord_to_file[col]
        rank_char = str(row + 1)
        return file_char + rank_char

class PGNGameImporter:
    """Imports PGN games into your chess board"""
    
    def __init__(self, board_class, piece_class):
        self.Board = board_class
        self.piece = piece_class
        self.parser = PGNParser()
    
    def import_game(self, pgn_text: str):
        """Import a PGN game and return board states for each move"""
        game_data = self.parser.parse_pgn(pgn_text)
        
        # Create fresh board
        board = self.Board()
        game_states = [self.copy_board_state(board)]  # Initial position
        
        for move_info in game_data['moves']:
            success = self.apply_move_to_board(board, move_info)
            if success:
                game_states.append(self.copy_board_state(board))
            else:
                print(f"Failed to apply move: {move_info['algebraic']}")
                break
        
        return {
            'headers': game_data['headers'],
            'moves': game_data['moves'],
            'board_states': game_states
        }
    
    def apply_move_to_board(self, board, move_info: Dict) -> bool:
        """Apply a parsed move to the board"""
        parsed = move_info['parsed']
        color = move_info['color']
        
        if parsed['type'] == 'castle':
            return self.apply_castle(board, color, parsed['side'])
        elif parsed['type'] == 'move':
            return self.apply_regular_move(board, color, parsed)
        
        return False
    
    def apply_castle(self, board, color: str, side: str) -> bool:
        """Apply castling move"""
        row = 0 if color == 'white' else 7
        
        if side == 'kingside':
            king_start = (row, 4)
            king_end = (row, 6)
            move_type = "kingside_castle"
        else:  # queenside
            king_start = (row, 4)
            king_end = (row, 2)
            move_type = "queenside_castle"
        
        # Check if castling is legal (basic check)
        king = board.squares[king_start[0]][king_start[1]]
        if king and king.type == 'king' and king.color == color:
            success, _ = board.make_move(king_start, king_end, move_type)
            return success
        
        return False
    
    def apply_regular_move(self, board, color: str, parsed: Dict) -> bool:
        """Apply regular piece move"""
        piece_type = parsed['piece'].lower()
        if piece_type == 'p':
            piece_type = 'pawn'
        elif piece_type == 'n':
            piece_type = 'knight'
        elif piece_type == 'b':
            piece_type = 'bishop'
        elif piece_type == 'r':
            piece_type = 'rook'
        elif piece_type == 'q':
            piece_type = 'queen'
        elif piece_type == 'k':
            piece_type = 'king'
        
        to_row, to_col = self.parser.square_to_coords(parsed['to_square'])
        
        # Find the piece that can make this move
        start_pos = self.find_piece_for_move(board, color, piece_type, 
                                           parsed['from_file'], parsed['from_rank'], 
                                           (to_row, to_col))
        
        if start_pos:
            move_type = None
            
            # Check for en passant
            if (piece_type == 'pawn' and parsed['capture'] and 
                board.squares[to_row][to_col] is None):
                move_type = "en_passant"
            
            success, _ = board.make_move(start_pos, (to_row, to_col), move_type)
            
            # Handle promotion
            if success and parsed['promotion']:
                promo_piece = parsed['promotion'].lower()
                if promo_piece == 'n':
                    promo_piece = 'knight'
                elif promo_piece == 'b':
                    promo_piece = 'bishop'
                elif promo_piece == 'r':
                    promo_piece = 'rook'
                elif promo_piece == 'q':
                    promo_piece = 'queen'
                
                # Replace pawn with promoted piece
                # Adjust import as needed
                board.squares[to_row][to_col] = self.piece(color, promo_piece)
            
            return success
        
        return False
    
    def find_piece_for_move(self, board, color: str, piece_type: str, 
                           from_file: str, from_rank: str, to_pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Find which piece can make the specified move"""
        print(f"DEBUG find_piece_for_move: Seeking {color} {piece_type} to {to_pos}, from_file='{from_file}', from_rank='{from_rank}'")
        candidates = []
        
        # Find all pieces of the right type and color
        for r_idx in range(8): # Changed to r_idx to avoid conflict if you print row, col from board
            for c_idx in range(8):
                piece = board.squares[r_idx][c_idx]
                if piece and piece.color == color and piece.type == piece_type:
                    # Check if this piece can legally move to the target
                    # Temporarily print current piece being considered
                    # print(f"DEBUG find_piece_for_move: Considering {piece.color} {piece.type} at ({r_idx}, {c_idx})")
                    try:
                        current_piece_legal_moves = board.get_legal_moves(r_idx, c_idx)
                    except Exception as e:
                        print(f"DEBUG ERROR in board.get_legal_moves for ({r_idx}, {c_idx}): {e}")
                        current_piece_legal_moves = []

                    for move in current_piece_legal_moves:
                        if (move[0], move[1]) == to_pos:
                            # print(f"DEBUG find_piece_for_move: Found potential candidate at ({r_idx}, {c_idx}) that can move to {to_pos}")
                            candidates.append((r_idx, c_idx))
                            break
        print(f"DEBUG find_piece_for_move: Initial candidates for {piece_type} to {to_pos}: {candidates}")
        
        # Filter by file/rank if specified
        if from_file:
            file_col = self.parser.file_to_coord[from_file]
            candidates = [pos for pos in candidates if pos[1] == file_col]
        
        if from_rank:
            pgn_rank_char = from_rank 
            board_row_for_rank = int(pgn_rank_char) - 1
            candidates = [pos for pos in candidates if pos[0] == board_row_for_rank]
            print(f"DEBUG find_piece_for_move: Candidates after from_rank '{from_rank}' (row {board_row_for_rank}): {candidates}")
        
        # Should have exactly one candidate
        if len(candidates) == 1:
            print(f"DEBUG find_piece_for_move: Successfully found unique piece at {candidates[0]}")
            return candidates[0]
        elif len(candidates) == 0:
            print(f"DEBUG find_piece_for_move: FAILED - No candidate piece found for {color} {piece_type} to {to_pos} (from_file='{from_file}', from_rank='{from_rank}')")
            # You might want to print the board state here to see why no piece fits
            # print(board) 
            return None
        else: # len(candidates) > 1
            print(f"DEBUG find_piece_for_move: FAILED - Ambiguous move. Multiple candidates found for {color} {piece_type} to {to_pos}: {candidates} (from_file='{from_file}', from_rank='{from_rank}')")
            # print(board)
            return None    
    def copy_board_state(self, board):
        """Create a copy of the current board state"""
        # This depends on your Board implementation
        return copy.deepcopy(board.squares)

# Usage example
def load_pgn_into_game(pgn_text: str, board_class, piece_class):
    """Main function to load PGN into your chess game"""
    importer = PGNGameImporter(board_class, piece_class)
    game_data = importer.import_game(pgn_text)
    
    return game_data
