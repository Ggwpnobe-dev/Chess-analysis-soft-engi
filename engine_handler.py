import chess
import chess.engine
import os
from enum import Enum

class MoveQuality(Enum):
    BRILLIANT = "brilliant"
    GREAT = "great"
    GOOD = "good"
    INACCURACY = "inaccuracy"
    MISTAKE = "mistake"
    BLUNDER = "blunder"
    UNKNOWN = "unknown"

class StockfishAnalyzer:
    def __init__(self, stockfish_executable_path: str = "stockfish", depth: int = 15):
        self.stockfish_path = self._find_executable(stockfish_executable_path)
        self.depth = depth
        self.engine = None

        if not self.stockfish_path:
            print(f"ERROR: Stockfish executable not found near '{stockfish_executable_path}'.")
            return

        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
            print(f"Stockfish engine initialized from: {self.stockfish_path}")
        except Exception as e:
            print(f"Error initializing Stockfish engine: {e}")

    def _find_executable(self, initial_path):
        if os.path.exists(initial_path) and os.access(initial_path, os.X_OK):
            return initial_path

        common_names = [
            "stockfish.exe", "stockfish",
            "stockfish-windows-x86-64-avx2.exe", "stockfish_x86-64-avx2"
        ]
        if os.path.isdir(initial_path):
            for name in common_names:
                full_path = os.path.join(initial_path, name)
                if os.path.exists(full_path) and os.access(full_path, os.X_OK):
                    return full_path

        parent = os.path.dirname(initial_path)
        for name in common_names:
            full_path = os.path.join(parent, name)
            if os.path.exists(full_path) and os.access(full_path, os.X_OK):
                return full_path

        return None

    def _coord_to_file(self, col):
        """Convert column index to chess file letter"""
        return chr(ord('a') + col)

    def _custom_board_to_fen(self, board, current_player):
        fen_rows = []
        for r in range(7, -1, -1):  
            row_fen = ''
            empty = 0
            for c in range(8):
                piece = board.squares[r][c]
                if piece:
                    if empty > 0:
                        row_fen += str(empty)
                        empty = 0
            
                    piece_map = {
                        'pawn': 'p',
                        'rook': 'r', 
                        'knight': 'n',
                        'bishop': 'b',
                        'queen': 'q',
                        'king': 'k'
                    }
                    char = piece_map.get(piece.type.lower(), piece.type[0].lower())
                    row_fen += char.upper() if piece.color == 'white' else char
                else:
                    empty += 1
            if empty > 0:
                row_fen += str(empty)
            fen_rows.append(row_fen)

        active_color = 'w' if current_player == 'white' else 'b'
        
        # Castling rights - you'll need to implement this based on your board structure
        castling = self._get_castling_rights(board) if hasattr(self, '_get_castling_rights') else '-'
        
        # En passant target square
        ep_target = '-'
        if hasattr(board, 'last_move') and board.last_move:
            (start_r, start_c), (end_r, end_c) = board.last_move
            moved_piece = board.squares[end_r][end_c]
            if moved_piece and moved_piece.type.lower() == 'pawn' and abs(start_r - end_r) == 2:
                ep_rank = (start_r + end_r) // 2 + 1  
                ep_file = self._coord_to_file(end_c)
                ep_target = f"{ep_file}{ep_rank}"

        halfmove = "0"  
        fullmove = str((len(getattr(board, 'move_history', [])) // 2) + 1)
        
        return f"{'/'.join(fen_rows)} {active_color} {castling} {ep_target} {halfmove} {fullmove}"

    def _get_castling_rights(self, board):
        """
        Determine castling rights based on king and rook positions and move history.
        This is a simplified version - you may need to adapt based on your board structure.
        """
        rights = ""
        
        # Check white castling rights
        white_king = board.squares[0][4]  # e1
        if white_king and white_king.type.lower() == 'king' and white_king.color == 'white':
            # Check kingside castling (h1 rook)
            h1_rook = board.squares[0][7]
            if h1_rook and h1_rook.type.lower() == 'rook' and h1_rook.color == 'white':
                rights += 'K'
            
            # Check queenside castling (a1 rook)
            a1_rook = board.squares[0][0]
            if a1_rook and a1_rook.type.lower() == 'rook' and a1_rook.color == 'white':
                rights += 'Q'
        
        # Check black castling rights
        black_king = board.squares[7][4]  # e8
        if black_king and black_king.type.lower() == 'king' and black_king.color == 'black':
            # Check kingside castling (h8 rook)
            h8_rook = board.squares[7][7]
            if h8_rook and h8_rook.type.lower() == 'rook' and h8_rook.color == 'black':
                rights += 'k'
            
            # Check queenside castling (a8 rook)
            a8_rook = board.squares[7][0]
            if a8_rook and a8_rook.type.lower() == 'rook' and a8_rook.color == 'black':
                rights += 'q'
        
        return rights if rights else '-'

    def get_best_move_san(self, board, current_player, time_limit_ms=1000):
        if not self.engine:
            return None
            
        try:
            fen = self._custom_board_to_fen(board, current_player)
            cb = chess.Board(fen)
            result = self.engine.play(cb, chess.engine.Limit(time=time_limit_ms / 1000))
            return cb.san(result.move) if result.move else None
        except Exception as e:
            print(f"Error getting best move: {e}")
            return None

    def evaluate_position(self, board, current_player, time_limit_ms=1000):
        if not self.engine:
            return None
            
        try:
            fen = self._custom_board_to_fen(board, current_player)
            cb = chess.Board(fen)
            info = self.engine.analyse(cb, chess.engine.Limit(time=time_limit_ms / 1000))
            return info.get("score")
        except Exception as e:
            print(f"Error evaluating position: {e}")
            return None

    def classify_move(self, played_move_san, best_move_san, prev_eval_cp, current_eval_cp, player_color):
        
        # Handle None evaluations
        if prev_eval_cp is None or current_eval_cp is None:
            return MoveQuality.UNKNOWN
            
        # Calculate evaluation loss from the player's perspective
        if player_color == "white":
            eval_loss = prev_eval_cp - current_eval_cp
        else:
            eval_loss = current_eval_cp - prev_eval_cp

        # Check if the played move matches the best move
        is_best_move = played_move_san == best_move_san

        if is_best_move:
            if eval_loss < -50:  # Move actually improves position significantly
                return MoveQuality.BRILLIANT
            elif eval_loss < 20:  # Small or no loss
                return MoveQuality.GREAT
            else:
                return MoveQuality.GOOD
        else:
            # Move is not the best, classify by evaluation loss
            if eval_loss < 30:
                return MoveQuality.GOOD
            elif eval_loss < 150:
                return MoveQuality.INACCURACY
            elif eval_loss < 250:
                return MoveQuality.MISTAKE
            else:
                return MoveQuality.BLUNDER

    def quit(self):
        if self.engine:
            self.engine.quit()
            self.engine = None
            print("Stockfish engine terminated.")