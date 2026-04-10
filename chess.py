import copy
import pygame
import sys

BOARD_SIZE = 8
SQUARE_SIZE = 84
BOARD_MARGIN = 20
BOARD_PIXEL = BOARD_SIZE * SQUARE_SIZE
WINDOW_WIDTH = BOARD_PIXEL + BOARD_MARGIN * 3 + 300
WINDOW_HEIGHT = BOARD_PIXEL + BOARD_MARGIN * 2
LIGHT_COLOR = (240, 217, 181)
DARK_COLOR = (181, 136, 99)
HIGHLIGHT_COLOR = (122, 184, 255)
MOVE_COLOR = (114, 196, 114)
CHECK_COLOR = (255, 139, 139)
BACKGROUND_COLOR = (36, 39, 43)
TEXT_COLOR = (242, 242, 242)
PANEL_COLOR = (32, 34, 39)
PIECE_SYMBOLS = {
    'wP': '♙', 'wN': '♘', 'wB': '♗', 'wR': '♖', 'wQ': '♕', 'wK': '♔',
    'bP': '♟', 'bN': '♞', 'bB': '♝', 'bR': '♜', 'bQ': '♛', 'bK': '♚',
}
FILES = 'abcdefgh'
RANKS = '87654321'

class ChessGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Beautiful Two-Player Chess')
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont(None, 26)
        self.font_medium = pygame.font.SysFont(None, 20)
        self.font_small = pygame.font.SysFont(None, 16)
        self.font_piece = self.load_piece_font(66)
        self.new_game()
        self.run()

    @staticmethod
    def load_piece_font(size):
        font_candidates = [
            'DejaVu Sans',
            'Noto Sans Symbols 2',
            'Noto Sans Symbols',
            'Segoe UI Symbol',
            'FreeSerif',
            'Arial Unicode MS',
        ]
        for font_name in font_candidates:
            font_path = pygame.font.match_font(font_name)
            if font_path:
                return pygame.font.Font(font_path, size)
        return pygame.font.SysFont(None, size)

    def new_game(self):
        self.board = [
            ['bR', 'bN', 'bB', 'bQ', 'bK', 'bB', 'bN', 'bR'],
            ['bP'] * 8,
            [''] * 8,
            [''] * 8,
            [''] * 8,
            [''] * 8,
            ['wP'] * 8,
            ['wR', 'wN', 'wB', 'wQ', 'wK', 'wB', 'wN', 'wR'],
        ]
        self.turn = 'w'
        self.selected_square = None
        self.legal_moves = []
        self.castling_rights = {'wK': True, 'wQ': True, 'bK': True, 'bQ': True}
        self.en_passant_target = None
        self.move_history = []
        self.captured_white = []
        self.captured_black = []
        self.game_over = False
        self.result_message = ''

    def run(self):
        while True:
            self.handle_events()
            self.draw()
            if self.game_over:
                self.draw_result_overlay()
            pygame.display.flip()
            self.clock.tick(60)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.new_game()
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.click(event.pos)

    def click(self, position):
        if self.game_over:
            return
        x, y = position
        board_left = BOARD_MARGIN
        board_top = BOARD_MARGIN
        if board_left <= x < board_left + BOARD_PIXEL and board_top <= y < board_top + BOARD_PIXEL:
            col = (x - board_left) // SQUARE_SIZE
            row = (y - board_top) // SQUARE_SIZE
            self.handle_board_click(int(row), int(col))

    def handle_board_click(self, row, col):
        piece = self.board[row][col]
        if self.selected_square and (row, col) in self.legal_moves:
            self.move_piece(self.selected_square, (row, col))
            self.selected_square = None
            self.legal_moves = []
            return
        if piece and piece[0] == self.turn:
            self.selected_square = (row, col)
            self.legal_moves = self.get_legal_moves_for_piece(row, col)
        else:
            self.selected_square = None
            self.legal_moves = []

    def move_piece(self, start, end):
        src_row, src_col = start
        dst_row, dst_col = end
        moving_piece = self.board[src_row][src_col]
        target_piece = self.board[dst_row][dst_col]

        if moving_piece[1] == 'P':
            if self.en_passant_target == (dst_row, dst_col) and src_col != dst_col and target_piece == '':
                capture_row = src_row
                captured_piece = self.board[capture_row][dst_col]
                self.board[capture_row][dst_col] = ''
                self.register_capture(captured_piece)

        if moving_piece[1] == 'K':
            self.disable_castling_for_color(self.turn)
            if abs(dst_col - src_col) == 2:
                self.perform_castling(start, end)
                return

        if moving_piece[1] == 'R':
            self.disable_castling_for_rook(start)

        if target_piece:
            self.register_capture(target_piece)

        self.board[dst_row][dst_col] = moving_piece
        self.board[src_row][src_col] = ''
        self.en_passant_target = None

        if moving_piece[1] == 'P' and abs(dst_row - src_row) == 2:
            self.en_passant_target = ((src_row + dst_row) // 2, src_col)

        if moving_piece[1] == 'P' and dst_row in (0, 7):
            self.board[dst_row][dst_col] = moving_piece[0] + 'Q'

        self.move_history.append(self.get_move_notation(start, end, moving_piece, target_piece))
        self.turn = 'b' if self.turn == 'w' else 'w'
        self.check_game_over()

    def perform_castling(self, start, end):
        src_row, src_col = start
        dst_row, dst_col = end
        king_piece = self.board[src_row][src_col]
        if dst_col == 6:
            rook_src = (src_row, 7)
            rook_dst = (src_row, 5)
        else:
            rook_src = (src_row, 0)
            rook_dst = (src_row, 3)
        self.board[dst_row][dst_col] = king_piece
        self.board[src_row][src_col] = ''
        self.board[rook_dst[0]][rook_dst[1]] = self.board[rook_src[0]][rook_src[1]]
        self.board[rook_src[0]][rook_src[1]] = ''
        self.disable_castling_for_color(self.turn)
        self.move_history.append('O-O' if dst_col == 6 else 'O-O-O')
        self.turn = 'b' if self.turn == 'w' else 'w'
        self.check_game_over()

    def disable_castling_for_color(self, color):
        if color == 'w':
            self.castling_rights['wK'] = False
            self.castling_rights['wQ'] = False
        else:
            self.castling_rights['bK'] = False
            self.castling_rights['bQ'] = False

    def disable_castling_for_rook(self, start):
        row, col = start
        if row == 7 and col == 0:
            self.castling_rights['wQ'] = False
        elif row == 7 and col == 7:
            self.castling_rights['wK'] = False
        elif row == 0 and col == 0:
            self.castling_rights['bQ'] = False
        elif row == 0 and col == 7:
            self.castling_rights['bK'] = False

    def register_capture(self, piece):
        if not piece:
            return
        if piece[0] == 'w':
            self.captured_white.append(piece)
        else:
            self.captured_black.append(piece)

    def get_move_notation(self, start, end, piece, capture):
        if piece[1] == 'K' and abs(start[1] - end[1]) == 2:
            return 'O-O' if end[1] == 6 else 'O-O-O'
        file_from = FILES[start[1]]
        rank_from = RANKS[start[0]]
        file_to = FILES[end[1]]
        rank_to = RANKS[end[0]]
        piece_letter = '' if piece[1] == 'P' else piece[1]
        capture_sign = 'x' if capture else ''
        return f'{piece_letter}{capture_sign}{file_to}{rank_to}'

    def check_game_over(self):
        if self.has_moves(self.turn):
            return
        if self.is_in_check(self.turn):
            winner = 'Black' if self.turn == 'w' else 'White'
            self.result_message = f'Checkmate! {winner} wins.'
        else:
            self.result_message = 'Stalemate! The game is a draw.'
        self.game_over = True

    def has_moves(self, color):
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board[row][col]
                if piece and piece[0] == color and self.get_legal_moves_for_piece(row, col):
                    return True
        return False

    def get_legal_moves_for_piece(self, row, col):
        piece = self.board[row][col]
        if not piece:
            return []
        moves = self.generate_pseudo_legal_moves(row, col)
        legal = [move for move in moves if not self.leaves_king_in_check((row, col), move)]
        return legal

    def leaves_king_in_check(self, start, end):
        board_copy = copy.deepcopy(self.board)
        src_row, src_col = start
        dst_row, dst_col = end
        piece = board_copy[src_row][src_col]
        board_copy[dst_row][dst_col] = piece
        board_copy[src_row][src_col] = ''
        if piece[1] == 'P' and self.en_passant_target == (dst_row, dst_col) and src_col != dst_col:
            board_copy[src_row][dst_col] = ''
        return self.is_in_check_on_board(piece[0], board_copy)

    def is_in_check(self, color):
        return self.is_in_check_on_board(color, self.board)

    def is_in_check_on_board(self, color, board):
        king_pos = self.find_king(color, board)
        if not king_pos:
            return False
        return self.is_square_attacked(king_pos[0], king_pos[1], self.opponent(color), board)

    @staticmethod
    def opponent(color):
        return 'b' if color == 'w' else 'w'

    def find_king(self, color, board):
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r][c] == f'{color}K':
                    return (r, c)
        return None

    def is_square_attacked(self, row, col, attacker_color, board):
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                piece = board[r][c]
                if piece and piece[0] == attacker_color:
                    for target in self.generate_pseudo_legal_moves(r, c, board=board, attacks_only=True):
                        if target == (row, col):
                            return True
        return False

    def generate_pseudo_legal_moves(self, row, col, board=None, attacks_only=False):
        board = board if board is not None else self.board
        piece = board[row][col]
        if not piece:
            return []
        color = piece[0]
        piece_type = piece[1]
        moves = []

        def add_move(r, c):
            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                target = board[r][c]
                if target == '' or target[0] != color:
                    moves.append((r, c))

        if piece_type == 'P':
            direction = -1 if color == 'w' else 1
            forward = (row + direction, col)
            if not attacks_only and self.is_empty_square(forward, board):
                moves.append(forward)
                double_forward = (row + 2 * direction, col)
                start_row = 6 if color == 'w' else 1
                if row == start_row and self.is_empty_square(double_forward, board) and self.is_empty_square(forward, board):
                    moves.append(double_forward)
            for dc in (-1, 1):
                capture = (row + direction, col + dc)
                if 0 <= capture[0] < BOARD_SIZE and 0 <= capture[1] < BOARD_SIZE:
                    if board[capture[0]][capture[1]] != '' and board[capture[0]][capture[1]][0] != color:
                        moves.append(capture)
                    if self.en_passant_target == capture and not attacks_only:
                        moves.append(capture)
        elif piece_type == 'N':
            for dr, dc in [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]:
                add_move(row + dr, col + dc)
        elif piece_type == 'B':
            self.add_sliding_moves(row, col, [(-1, -1), (-1, 1), (1, -1), (1, 1)], board, moves)
        elif piece_type == 'R':
            self.add_sliding_moves(row, col, [(-1, 0), (1, 0), (0, -1), (0, 1)], board, moves)
        elif piece_type == 'Q':
            self.add_sliding_moves(row, col, [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)], board, moves)
        elif piece_type == 'K':
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    add_move(row + dr, col + dc)
            if not attacks_only and piece[0] == self.turn:
                self.add_castling_moves(row, col, moves)

        return moves

    def add_sliding_moves(self, row, col, directions, board, moves):
        color = board[row][col][0]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                target = board[r][c]
                if target == '':
                    moves.append((r, c))
                else:
                    if target[0] != color:
                        moves.append((r, c))
                    break
                r += dr
                c += dc

    def add_castling_moves(self, row, col, moves):
        if self.turn == 'w' and row == 7 and col == 4:
            if self.castling_rights['wK'] and self.can_castle_kingside('w'):
                moves.append((7, 6))
            if self.castling_rights['wQ'] and self.can_castle_queenside('w'):
                moves.append((7, 2))
        if self.turn == 'b' and row == 0 and col == 4:
            if self.castling_rights['bK'] and self.can_castle_kingside('b'):
                moves.append((0, 6))
            if self.castling_rights['bQ'] and self.can_castle_queenside('b'):
                moves.append((0, 2))

    def can_castle_kingside(self, color):
        row = 7 if color == 'w' else 0
        if self.board[row][5] != '' or self.board[row][6] != '':
            return False
        if self.is_square_attacked(row, 4, self.opponent(color), self.board):
            return False
        if self.is_square_attacked(row, 5, self.opponent(color), self.board):
            return False
        if self.is_square_attacked(row, 6, self.opponent(color), self.board):
            return False
        return True

    def can_castle_queenside(self, color):
        row = 7 if color == 'w' else 0
        if self.board[row][1] != '' or self.board[row][2] != '' or self.board[row][3] != '':
            return False
        if self.is_square_attacked(row, 4, self.opponent(color), self.board):
            return False
        if self.is_square_attacked(row, 3, self.opponent(color), self.board):
            return False
        if self.is_square_attacked(row, 2, self.opponent(color), self.board):
            return False
        return True

    @staticmethod
    def is_empty_square(position, board):
        if position is None:
            return False
        row, col = position
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE and board[row][col] == ''

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        self.draw_board()
        self.draw_side_panel()

    def draw_board(self):
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                x = BOARD_MARGIN + col * SQUARE_SIZE
                y = BOARD_MARGIN + row * SQUARE_SIZE
                color = LIGHT_COLOR if (row + col) % 2 == 0 else DARK_COLOR
                pygame.draw.rect(self.screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))
        if self.selected_square:
            self.draw_highlight(self.selected_square, HIGHLIGHT_COLOR)
            for move in self.legal_moves:
                self.draw_highlight(move, MOVE_COLOR)
        if self.is_in_check(self.turn):
            king_pos = self.find_king(self.turn, self.board)
            if king_pos:
                self.draw_highlight(king_pos, CHECK_COLOR)
        self.draw_coordinates()
        self.draw_pieces()

    def draw_highlight(self, square, color):
        row, col = square
        x = BOARD_MARGIN + col * SQUARE_SIZE
        y = BOARD_MARGIN + row * SQUARE_SIZE
        overlay = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        overlay.fill((*color, 120))
        self.screen.blit(overlay, (x, y))

    def draw_coordinates(self):
        for col in range(BOARD_SIZE):
            x = BOARD_MARGIN + col * SQUARE_SIZE + SQUARE_SIZE // 2
            y = BOARD_MARGIN + BOARD_PIXEL + 12
            label = self.font_small.render(FILES[col], True, TEXT_COLOR)
            self.screen.blit(label, (x - label.get_width() // 2, y))
        for row in range(BOARD_SIZE):
            x = 6
            y = BOARD_MARGIN + row * SQUARE_SIZE + SQUARE_SIZE // 2 - 8
            label = self.font_small.render(RANKS[row], True, TEXT_COLOR)
            self.screen.blit(label, (x, y))

    def draw_pieces(self):
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board[row][col]
                if piece:
                    x = BOARD_MARGIN + col * SQUARE_SIZE + SQUARE_SIZE // 2
                    y = BOARD_MARGIN + row * SQUARE_SIZE + SQUARE_SIZE // 2
                    background_radius = int(SQUARE_SIZE * 0.8)
                    piece_bg = pygame.Surface((background_radius, background_radius), pygame.SRCALPHA)
                    pygame.draw.ellipse(piece_bg, (255, 255, 255, 70), piece_bg.get_rect())
                    self.screen.blit(piece_bg, (x - background_radius // 2, y - background_radius // 2))
                    symbol = PIECE_SYMBOLS.get(piece, '?')
                    outline_color = (34, 34, 34) if piece[0] == 'w' else (245, 245, 245)
                    fill_color = (245, 245, 245) if piece[0] == 'w' else (28, 28, 28)
                    outline = self.font_piece.render(symbol, True, outline_color)
                    text = self.font_piece.render(symbol, True, fill_color)
                    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        self.screen.blit(outline, (x - outline.get_width() // 2 + dx, y - outline.get_height() // 2 + dy))
                    self.screen.blit(text, (x - text.get_width() // 2, y - text.get_height() // 2))

    def draw_side_panel(self):
        x0 = BOARD_MARGIN * 2 + BOARD_PIXEL
        panel_rect = pygame.Rect(x0, BOARD_MARGIN, WINDOW_WIDTH - x0 - BOARD_MARGIN, WINDOW_HEIGHT - BOARD_MARGIN * 2)
        pygame.draw.rect(self.screen, PANEL_COLOR, panel_rect, border_radius=12)
        self.draw_text('Two-Player Chess', self.font_large, TEXT_COLOR, x0 + 20, BOARD_MARGIN + 20)
        self.draw_text('Controls', self.font_medium, TEXT_COLOR, x0 + 20, BOARD_MARGIN + 60)
        self.draw_text('Left click: select/move', self.font_small, TEXT_COLOR, x0 + 24, BOARD_MARGIN + 90)
        self.draw_text('R: reset game', self.font_small, TEXT_COLOR, x0 + 24, BOARD_MARGIN + 110)
        self.draw_text('Esc: quit', self.font_small, TEXT_COLOR, x0 + 24, BOARD_MARGIN + 130)
        current_text = 'White to move' if self.turn == 'w' else 'Black to move'
        self.draw_text(current_text, self.font_medium, TEXT_COLOR, x0 + 20, BOARD_MARGIN + 170)
        self.draw_text('Captured white:', self.font_small, TEXT_COLOR, x0 + 20, BOARD_MARGIN + 210)
        self.draw_text(' '.join(PIECE_SYMBOLS.get(p, '?') for p in self.captured_white), self.font_small, TEXT_COLOR, x0 + 20, BOARD_MARGIN + 230)
        self.draw_text('Captured black:', self.font_small, TEXT_COLOR, x0 + 20, BOARD_MARGIN + 260)
        self.draw_text(' '.join(PIECE_SYMBOLS.get(p, '?') for p in self.captured_black), self.font_small, TEXT_COLOR, x0 + 20, BOARD_MARGIN + 280)
        self.draw_text('Move history', self.font_medium, TEXT_COLOR, x0 + 20, BOARD_MARGIN + 320)
        history_start_y = BOARD_MARGIN + 350
        for idx, move in enumerate(self.move_history[-14:]):
            line = f'{idx + 1}. {move}'
            self.draw_text(line, self.font_small, TEXT_COLOR, x0 + 20, history_start_y + idx * 20)
        if self.game_over:
            self.draw_text(self.result_message, self.font_medium, (255, 200, 70), x0 + 20, BOARD_MARGIN + 620)

    def draw_text(self, text, font, color, x, y):
        rendered = font.render(text, True, color)
        self.screen.blit(rendered, (x, y))

    def draw_result_overlay(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((20, 20, 20, 180))
        self.screen.blit(overlay, (0, 0))
        box = pygame.Rect(BOARD_MARGIN + 40, BOARD_MARGIN + 120, BOARD_PIXEL - 80, 220)
        pygame.draw.rect(self.screen, (48, 50, 56), box, border_radius=16)
        pygame.draw.rect(self.screen, (255, 255, 255), box, width=2, border_radius=16)
        title = self.font_large.render('Game Over', True, TEXT_COLOR)
        self.screen.blit(title, (box.centerx - title.get_width() // 2, box.y + 30))
        message = self.font_medium.render(self.result_message, True, TEXT_COLOR)
        self.screen.blit(message, (box.centerx - message.get_width() // 2, box.y + 90))
        info = self.font_small.render('Press R to restart or Esc to quit.', True, TEXT_COLOR)
        self.screen.blit(info, (box.centerx - info.get_width() // 2, box.y + 150))

if __name__ == '__main__':
    ChessGame()
