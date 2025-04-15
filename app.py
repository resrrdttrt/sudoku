import pygame
import sys
import time
import random
import copy
import json
import os
from enum import Enum
import math

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 600, 700
BOARD_SIZE = 450
GRID_SIZE = BOARD_SIZE // 9
BUTTON_WIDTH, BUTTON_HEIGHT = 150, 50
FONT_SIZE = 30
SMALL_FONT_SIZE = 20
# LOGO_WIDTH = WIDTH // 2  
# LOGO_HEIGHT = HEIGHT // 3 


# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
LIGHT_GRAY = (230, 230, 230)
HIGHLIGHT_COLOR = (173, 216, 230)  # Light blue
SELECTED_COLOR = (255, 255, 0)  # Yellow
ORIGINAL_COLOR = (0, 0, 0)  # Black
USER_INPUT_COLOR = (0, 0, 255)  # Blue
HINT_COLOR = (0, 128, 0)  # Green
ERROR_COLOR = (255, 0, 0)  # Red
BUTTON_COLOR = (100, 149, 237)  # Cornflower blue
BUTTON_HOVER_COLOR = (70, 130, 230)

# Themes
class Theme(Enum):
    CLASSIC = {
        "bg": (255, 255, 255),
        "grid": (0, 0, 0),
        "original": (0, 0, 0),
        "user_input": (0, 0, 255),
        "hint": (0, 128, 0),
        "selected": (255, 255, 0),
        "highlight": (173, 216, 230),
        "button": (100, 149, 237),
        "button_hover": (70, 130, 230),
        "text": (0, 0, 0)
    }
    DARK = {
        "bg": (40, 40, 40),
        "grid": (200, 200, 200),
        "original": (255, 255, 255),
        "user_input": (100, 149, 237),
        "hint": (0, 200, 0),
        "selected": (200, 200, 0),
        "highlight": (70, 90, 120),
        "button": (70, 90, 120),
        "button_hover": (90, 110, 140),
        "text": (255, 255, 255)
    }
    PASTEL = {
        "bg": (253, 245, 230),
        "grid": (100, 100, 100),
        "original": (100, 100, 100),
        "user_input": (70, 130, 180),
        "hint": (107, 142, 35),
        "selected": (255, 223, 0),
        "highlight": (173, 216, 230),
        "button": (188, 143, 143),
        "button_hover": (210, 180, 180),
        "text": (100, 100, 100)
    }

back=pygame.image.load('data/bg2.jpg')

# Game state
class GameState(Enum):
    WELCOME = 0
    NEW_GAME = 1
    SETTINGS = 2
    HIGH_SCORES = 3
    QUIT_CONFIRM = 4
    ALGORITHM_SELECT = 5

# Difficulty levels
class Difficulty(Enum):
    EASY = {"name": "Easy", "empty_cells": 30}
    MEDIUM = {"name": "Medium", "empty_cells": 45}
    HARD = {"name": "Hard", "empty_cells": 55}

class SudokuGame:
    def __init__(self):
        # Set up the window
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Sudoku Game")
        
        # Set up fonts
        self.large_font = pygame.font.SysFont('Arial', FONT_SIZE)
        self.medium_font = pygame.font.SysFont('Arial', SMALL_FONT_SIZE)
        self.small_font = pygame.font.SysFont('Arial', 16)
        
        # Game state
        self.current_state = GameState.WELCOME
        self.previous_state = None
        self.active_cell = None
        self.marked_cells = set()
        
        # Board state
        self.board = [[0 for _ in range(9)] for _ in range(9)]
        self.original_board = [[0 for _ in range(9)] for _ in range(9)]
        self.solved_board = [[0 for _ in range(9)] for _ in range(9)]
        self.cell_status = [[0 for _ in range(9)] for _ in range(9)]  # 0: original, 1: user input, 2: hint
        
        # Game settings
        self.theme = Theme.CLASSIC
        self.current_colors = self.theme.value
        self.difficulty = Difficulty.MEDIUM
        self.sound_volume = 0.5
        self.high_scores = []
        
        # Game stats
        self.start_time = None
        self.elapsed_time = 0
        self.paused = False
        self.hints_used = 0
        self.algo_solve_time = 0
        
        # Load game data if exists
        self.load_data()
        

        self.logo = pygame.image.load("data/lg2.jpg")  # Replace with your image path
        original_width, original_height = self.logo.get_size()

        # Resize to half of the original size
        new_width = original_width // 2
        new_height = original_height // 2
        self.logo = pygame.transform.scale(self.logo, (new_width, new_height))
        
        # Saved game state
        if os.path.exists('data/saved_game.json'):
            self.has_saved_game = True
        else:
            self.has_saved_game = False
        
        # Initialize sound
        self.initialize_sounds()
    
    def initialize_sounds(self):
        # Create placeholder sound effects
        self.button_sound = pygame.mixer.Sound(self.create_beep_sound(440, 100))  # A4 note
        self.error_sound = pygame.mixer.Sound(self.create_beep_sound(220, 300))   # A3 note
        self.success_sound = pygame.mixer.Sound(self.create_beep_sound(880, 200)) # A5 note
        self.solve_sound = pygame.mixer.Sound('data/win.wav')
        # Set volume
        self.button_sound.set_volume(self.sound_volume)
        self.error_sound.set_volume(self.sound_volume)
        self.success_sound.set_volume(self.sound_volume)
        self.solve_sound.set_volume(self.sound_volume)
    
    def create_beep_sound(self, frequency, duration):
        # Create a basic beep sound since we can't include external files
        sample_rate = 44100
        bits = 16
        
        pygame.mixer.pre_init(sample_rate, -bits, 2)
        
        # Create a simple sine wave
        buf = bytearray()
        max_sample = 2**(bits - 1) - 1
        for i in range(0, int(sample_rate * duration / 1000)):
            sample = 0.5 * max_sample * math.sin(2 * math.pi * frequency * i / sample_rate)
            buf.extend(int(sample).to_bytes(2, byteorder='little', signed=True))
        
        return pygame.mixer.Sound(buffer=bytes(buf))
        
    def load_data(self):
        # Create data directory if it doesn't exist
        if not os.path.exists('data'):
            os.makedirs('data')
        
        # Load high scores if file exists
        try:
            if os.path.exists('data/high_scores.json'):
                with open('data/high_scores.json', 'r') as f:
                    self.high_scores = json.load(f)
        except:
            self.high_scores = []
            
        # Load settings if file exists
        try:
            if os.path.exists('data/settings.json'):
                with open('data/settings.json', 'r') as f:
                    settings = json.load(f)
                    self.theme = Theme[settings.get('theme', 'CLASSIC')]
                    self.current_colors = self.theme.value
                    self.difficulty = Difficulty[settings.get('difficulty', 'MEDIUM')]
                    self.sound_volume = settings.get('sound_volume', 0.5)
        except:
            pass
            
        # Load saved game if exists
        try:
            if os.path.exists('data/saved_game.json'):
                with open('data/saved_game.json', 'r') as f:
                    saved_game = json.load(f)
                    self.has_saved_game = True
        except:
            self.has_saved_game = False
    
    def save_data(self):
        # Save high scores
        with open('data/high_scores.json', 'w') as f:
            json.dump(self.high_scores, f)
            
        # Save settings
        with open('data/settings.json', 'w') as f:
            settings = {
                'theme': self.theme.name,
                'difficulty': self.difficulty.name,
                'sound_volume': self.sound_volume
            }
            json.dump(settings, f)
    
    def save_game(self):
        # Save current game state
        with open('data/saved_game.json', 'w') as f:
            saved_game = {
                'board': self.board,
                'original_board': self.original_board,
                'solved_board': self.solved_board,
                'cell_status': self.cell_status,
                'elapsed_time': self.elapsed_time,
                'hints_used': self.hints_used,
                'difficulty': self.difficulty.name
            }
            json.dump(saved_game, f)
        self.has_saved_game = True
        self.play_sound(self.success_sound)
    
    def load_game(self):
        # Load saved game
        try:
            if os.path.exists('data/saved_game.json'):
                with open('data/saved_game.json', 'r') as f:
                    saved_game = json.load(f)
                    self.board = saved_game['board']
                    self.original_board = saved_game['original_board']
                    self.solved_board = saved_game['solved_board']
                    self.cell_status = saved_game['cell_status']
                    self.elapsed_time = saved_game['elapsed_time']
                    self.hints_used = saved_game['hints_used']
                    self.difficulty = Difficulty[saved_game['difficulty']]
                    self.start_time = time.time()
                    self.paused = False
                    self.current_state = GameState.NEW_GAME
        except:
            self.new_game()
    
    def play_sound(self, sound):
        # Play sound effect with current volume
        sound.set_volume(self.sound_volume)
        sound.play()
    
    def generate_board(self):
        # Reset the board
        self.board = [[0 for _ in range(9)] for _ in range(9)]
        
        # Generate a solved board
        self.solve_empty_board()
        
        # Store the solved board
        self.solved_board = copy.deepcopy(self.board)
        
        # Remove cells based on difficulty
        self.remove_cells(self.difficulty.value["empty_cells"])
        
        # Store the original board
        self.original_board = copy.deepcopy(self.board)
        
        # Reset cell status
        self.cell_status = [[0 if self.board[i][j] != 0 else 1 for j in range(9)] for i in range(9)]
        
        # Reset game stats
        self.start_time = time.time()
        self.elapsed_time = 0
        self.paused = False
        self.hints_used = 0
        self.marked_cells = set()
    
    def solve_empty_board(self):
        # Fill the diagonal boxes first (these can be filled independently)
        for i in range(0, 9, 3):
            self.fill_box(i, i)
        
        # Solve the rest of the board
        self.solve_board()
    
    def fill_box(self, row, col):
        # Fill a 3x3 box with random numbers
        nums = list(range(1, 10))
        random.shuffle(nums)
        
        index = 0
        for i in range(3):
            for j in range(3):
                self.board[row + i][col + j] = nums[index]
                index += 1
    
    def solve_board(self):
        # Solve the board using backtracking
        empty = self.find_empty()
        if not empty:
            return True
        
        row, col = empty
        
        # Shuffle numbers for more randomness
        nums = list(range(1, 10))
        random.shuffle(nums)
        
        for num in nums:
            if self.is_valid(row, col, num):
                self.board[row][col] = num
                
                if self.solve_board():
                    return True
                
                # If placing the number didn't lead to a solution, backtrack
                self.board[row][col] = 0
        
        return False
    
    def find_empty(self):
        # Find an empty cell in the board
        for i in range(9):
            for j in range(9):
                if self.board[i][j] == 0:
                    return (i, j)
        return None
    
    def is_valid(self, row, col, num):
        # Check if placing 'num' at position (row, col) is valid
        # Check row
        for j in range(9):
            if self.board[row][j] == num:
                return False
        
        # Check column
        for i in range(9):
            if self.board[i][col] == num:
                return False
        
        # Check 3x3 box
        box_row, box_col = 3 * (row // 3), 3 * (col // 3)
        for i in range(box_row, box_row + 3):
            for j in range(box_col, box_col + 3):
                if self.board[i][j] == num:
                    return False
        
        return True
    
    def remove_cells(self, count):
        # Remove 'count' cells from the board
        cells = [(i, j) for i in range(9) for j in range(9)]
        random.shuffle(cells)
        
        for i, j in cells[:count]:
            self.board[i][j] = 0
    
    def new_game(self):
        # Generate a new game board
        self.generate_board()
        self.current_state = GameState.NEW_GAME
        
        # Delete saved game if exists
        if os.path.exists('data/saved_game.json'):
            os.remove('data/saved_game.json')
            self.has_saved_game = False
    
    def draw_welcome_screen(self):
        # Clear the screen
        self.screen.fill(self.current_colors["bg"])
        self.screen.blit(back,(0,0))
        # Draw logo (could be replaced with an image)
        # logo_text = self.large_font.render("SUDOKU", True, self.current_colors["text"])
        logo_rect = self.logo.get_rect(center=(WIDTH//2, HEIGHT//4))
        self.screen.blit(self.logo, logo_rect)
        self.algo_solve_time = 0
        # Draw buttons
        buttons = []
        buttons.append(self.create_button("NEW GAME", WIDTH // 2, HEIGHT // 2 - 60, self.start_new_game))

        if self.has_saved_game:
            buttons.append(self.create_button("CONTINUE", WIDTH // 2, HEIGHT // 2, self.load_game))
        else:
            # Create a disabled button
            disabled_button = self.create_button("CONTINUE", WIDTH // 2, HEIGHT // 2, None)
            buttons.append(disabled_button)

        buttons.append(self.create_button("SETTINGS", WIDTH // 2, HEIGHT // 2 + 60, self.open_settings))
        buttons.append(self.create_button("HIGH SCORES", WIDTH // 2, HEIGHT // 2 + 120, self.open_high_scores))
        buttons.append(self.create_button("QUIT", WIDTH // 2, HEIGHT // 2 + 180, self.confirm_quit))

        # Handle button events and draw them
        for button in buttons:
            self.handle_button(button)
            self.draw_button(button)
    
    def draw_board(self):
        # Calculate the offset to center the board
        offset_x = (WIDTH - BOARD_SIZE) // 2
        offset_y = (HEIGHT - BOARD_SIZE) // 2 - 50  # Adjusted to make room for buttons
        
        # Draw the background for the board
        pygame.draw.rect(self.screen, LIGHT_GRAY, (offset_x, offset_y, BOARD_SIZE, BOARD_SIZE))
        
        # Draw the cells
        for i in range(9):
            for j in range(9):
                cell_x = offset_x + j * GRID_SIZE
                cell_y = offset_y + i * GRID_SIZE
                
                # Determine cell color
                cell_color = self.current_colors["bg"]
                if (i, j) == self.active_cell:
                    cell_color = self.current_colors["selected"]
                elif (i, j) in self.marked_cells:
                    cell_color = self.current_colors["highlight"]
                
                # Draw cell background
                pygame.draw.rect(self.screen, cell_color, (cell_x, cell_y, GRID_SIZE, GRID_SIZE))
                
                # Draw number if cell is not empty
                if self.board[i][j] != 0:
                    # Determine number color based on cell status
                    if self.cell_status[i][j] == 0:  # Original
                        num_color = self.current_colors["original"]
                    elif self.cell_status[i][j] == 1:  # User input
                        num_color = self.current_colors["user_input"]
                    else:  # Hint
                        num_color = self.current_colors["hint"]
                    
                    num_text = self.large_font.render(str(self.board[i][j]), True, num_color)
                    num_rect = num_text.get_rect(center=(cell_x + GRID_SIZE // 2, cell_y + GRID_SIZE // 2))
                    self.screen.blit(num_text, num_rect)
        
        # Draw the grid lines
        for i in range(10):
            line_width = 3 if i % 3 == 0 else 1
            
            # Vertical lines
            pygame.draw.line(self.screen, self.current_colors["grid"], 
                            (offset_x + i * GRID_SIZE, offset_y), 
                            (offset_x + i * GRID_SIZE, offset_y + BOARD_SIZE), line_width)
            
            # Horizontal lines
            pygame.draw.line(self.screen, self.current_colors["grid"], 
                            (offset_x, offset_y + i * GRID_SIZE), 
                            (offset_x + BOARD_SIZE, offset_y + i * GRID_SIZE), line_width)
    
    def draw_game_screen(self):
        # Clear the screen
        self.screen.fill(self.current_colors["bg"])
        
        # Draw the board
        self.draw_board()
        
        # Draw game info
        self.draw_game_info()

        button_y = HEIGHT - 75
        # Draw buttons
        buttons = []
        buttons.append(self.create_button("HINT", WIDTH // 6, button_y, self.give_hint))
        buttons.append(self.create_button("MARK", WIDTH // 6 * 2, button_y, self.toggle_mark))
        buttons.append(self.create_button("CLEAR", WIDTH // 6 * 3, button_y, self.clear_board))
        buttons.append(self.create_button("SAVE", WIDTH // 6 * 4, button_y, self.save_game))
        buttons.append(self.create_button("SOLVE", WIDTH // 6 * 5, button_y, self.select_algorithm))
        buttons.append(self.create_button("BACK", 300, 40, self.go_back))
        
        # Handle button events and draw them
        for button in buttons:
            self.handle_button(button)
            self.draw_button(button)
        
        # Update elapsed time if game is active
        if self.start_time and not self.paused:
            self.elapsed_time = time.time() - self.start_time + self.elapsed_time
            self.start_time = time.time()
    
    def clear_board(self):
        # Clear all user inputs and marked cells from the board
        for i in range(9):
            for j in range(9):
                if self.original_board[i][j] == 0:  # Only clear user input cells
                    self.board[i][j] = 0  # Set the cell to empty
                    # self.cell_status[i][j] = 0  # Reset cell status to original
        
        # Clear all marked cells
        self.marked_cells.clear()  # Remove all marked cells
        self.algo_solve_time = 0
        self.play_sound(self.button_sound)  # Optional: Play sound when cleared

    def draw_game_info(self):
        # self.screen.blit(back,(0,0))
        # Draw difficulty
        diff_text = self.medium_font.render(f"Difficulty: {self.difficulty.value['name']}", True, self.current_colors["text"])
        self.screen.blit(diff_text, (20, 20))
        
        # Draw time
        time_str = self.format_time(self.elapsed_time)
        time_text = self.medium_font.render(f"Time: {time_str}", True, self.current_colors["text"])
        self.screen.blit(time_text, (WIDTH - 150, 20))
        
        # Draw hints used
        hint_text = self.medium_font.render(f"Hints: {self.hints_used}", True, self.current_colors["text"])
        self.screen.blit(hint_text, (WIDTH - 150, 50))
        
        # Draw algorithm solve time if applicable
        if self.algo_solve_time > 0:
            algo_text = self.small_font.render(f"Solve time: {self.algo_solve_time:.6f}s", True, self.current_colors["text"])
            self.screen.blit(algo_text, (20, 50))
    
    def draw_settings_screen(self):
        # Clear the screen
        self.screen.fill(self.current_colors["bg"])
        
        # Draw title
        title_text = self.large_font.render("SETTINGS", True, self.current_colors["text"])
        title_rect = title_text.get_rect(center=(WIDTH//2, 60))
        self.screen.blit(title_text, title_rect)
        
        # Draw difficulty setting
        diff_text = self.medium_font.render("Difficulty:", True, self.current_colors["text"])
        self.screen.blit(diff_text, (WIDTH//4 - 100, HEIGHT//4))
        
        # Difficulty buttons
        diff_buttons = []
        difficulties = list(Difficulty)
        for i, diff in enumerate(difficulties):
            btn = self.create_button(diff.value["name"], WIDTH//2, HEIGHT//4 + i * 60, 
                                     lambda d=diff: self.set_difficulty(d))
            btn["active"] = self.difficulty == diff
            diff_buttons.append(btn)
        
        # Draw theme setting
        theme_text = self.medium_font.render("Theme:", True, self.current_colors["text"])
        self.screen.blit(theme_text, (WIDTH//4 - 100, HEIGHT//2))
        
        # Theme buttons
        theme_buttons = []
        themes = list(Theme)
        for i, theme in enumerate(themes):
            btn = self.create_button(theme.name.capitalize(), WIDTH//2, HEIGHT//2 + i * 60, 
                                    lambda t=theme: self.set_theme(t))
            btn["active"] = self.theme == theme
            theme_buttons.append(btn)
        
        # Draw volume setting
        vol_text = self.medium_font.render(f"Volume: {int(self.sound_volume * 100)}%", True, self.current_colors["text"])
        self.screen.blit(vol_text, (WIDTH//4 - 100, HEIGHT * 3//4))
        
        # Volume slider (simplified)
        slider_width = 200
        slider_x = WIDTH//2 - slider_width//2
        slider_y = HEIGHT * 3//4 + 10
        
        # Draw slider background
        pygame.draw.rect(self.screen, GRAY, (slider_x, slider_y, slider_width, 10))
        
        # Draw slider handle
        handle_x = slider_x + int(self.sound_volume * slider_width)
        pygame.draw.circle(self.screen, self.current_colors["button"], (handle_x, slider_y + 5), 10)
        
        # Check if slider is being dragged
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        
        if mouse_pressed and slider_y - 10 <= mouse_pos[1] <= slider_y + 20:
            if slider_x <= mouse_pos[0] <= slider_x + slider_width:
                self.sound_volume = (mouse_pos[0] - slider_x) / slider_width
                self.sound_volume = max(0, min(1, self.sound_volume))
        
        # Back button
        back_button = self.create_button("BACK", WIDTH//2, HEIGHT - 50, self.go_back)
        
        # Handle buttons
        for button in diff_buttons + theme_buttons + [back_button]:
            self.handle_button(button)
            self.draw_button(button)
    
    # def draw_high_scores_screen(self):
    #     # Clear the screen
    #     self.screen.fill(self.current_colors["bg"])
        
    #     # Draw title
    #     title_text = self.large_font.render("HIGH SCORES", True, self.current_colors["text"])
    #     title_rect = title_text.get_rect(center=(WIDTH//2, 60))
    #     self.screen.blit(title_text, title_rect)
        
    #     # Sort high scores by score (lower is better)
    #     sorted_scores = sorted(self.high_scores, key=lambda x: x["score"])
        
    #     # Draw high scores (top 10)
    #     if sorted_scores:
    #         for i, score in enumerate(sorted_scores[:10]):
    #             # Format the score entry
    #             diff_name = score["difficulty"]
    #             time_str = self.format_time(score["time"])
    #             hints = score["hints"]
                
    #             # Calculate y position
    #             y_pos = 150 + i * 40
                
    #             # Draw rank
    #             rank_text = self.medium_font.render(f"{i+1}.", True, self.current_colors["text"])
    #             self.screen.blit(rank_text, (WIDTH//4 - 80, y_pos))
                
    #             # Draw difficulty
    #             diff_text = self.medium_font.render(diff_name, True, self.current_colors["text"])
    #             self.screen.blit(diff_text, (WIDTH//4, y_pos))
                
    #             # Draw time
    #             time_text = self.medium_font.render(time_str, True, self.current_colors["text"])
    #             self.screen.blit(time_text, (WIDTH//2, y_pos))
                
    #             # Draw hints
    #             hints_text = self.medium_font.render(f"Hints: {hints}", True, self.current_colors["text"])
    #             self.screen.blit(hints_text, (WIDTH * 3//4, y_pos))
    #     else:
    #         # Display message if no high scores
    #         no_scores_text = self.medium_font.render("No high scores yet!", True, self.current_colors["text"])
    #         no_scores_rect = no_scores_text.get_rect(center=(WIDTH//2, HEIGHT//2))
    #         self.screen.blit(no_scores_text, no_scores_rect)
        
    #     # Back button
    #     back_button = self.create_button("BACK", WIDTH//2, HEIGHT - 50, self.go_back)
    #     self.handle_button(back_button)
    #     self.draw_button(back_button)
    
    def draw_high_scores_screen(self):
        # Clear the screen
        self.screen.fill(self.current_colors["bg"])
        
        # Draw title
        title_text = self.large_font.render("HIGH SCORES", True, self.current_colors["text"])
        title_rect = title_text.get_rect(center=(WIDTH//2, 60))
        self.screen.blit(title_text, title_rect)
        
        # Sort high scores by score (lower is better)
        sorted_scores = sorted(self.high_scores, key=lambda x: x["score"])
        
        # Draw high scores (top 10)
        if sorted_scores:
            for i, score in enumerate(sorted_scores[:10]):
                # Format the score entry
                name = score["name"][:7]
                diff_name = score["difficulty"]
                time_str = self.format_time(score["time"])
                hints = score["hints"]
                
                # Calculate y position
                y_pos = 150 + i * 40
                
                # Draw rank
                rank_text = self.medium_font.render(f"{i+1}.", True, self.current_colors["text"])
                self.screen.blit(rank_text, (WIDTH//4 - 80, y_pos))
                
                # Draw name
                name_text = self.medium_font.render(name, True, self.current_colors["text"])
                self.screen.blit(name_text, (WIDTH//4, y_pos))
                
                # Draw difficulty
                diff_text = self.medium_font.render(diff_name, True, self.current_colors["text"])
                self.screen.blit(diff_text, (WIDTH//2 - 50, y_pos))
                
                # Draw time
                time_text = self.medium_font.render(time_str, True, self.current_colors["text"])
                self.screen.blit(time_text, (WIDTH//2 + 60, y_pos))
                
                # Draw hints
                hints_text = self.medium_font.render(f"Hints: {hints}", True, self.current_colors["text"])
                self.screen.blit(hints_text, (WIDTH * 3//4, y_pos))
        else:
            # Display message if no high scores
            no_scores_text = self.medium_font.render("No high scores yet!", True, self.current_colors["text"])
            no_scores_rect = no_scores_text.get_rect(center=(WIDTH//2, HEIGHT//2))
            self.screen.blit(no_scores_text, no_scores_rect)
        
        # Back button
        back_button = self.create_button("BACK", WIDTH//2, HEIGHT - 50, self.go_back)
        self.handle_button(back_button)
        self.draw_button(back_button)


    def draw_quit_confirm_screen(self):
        # Clear the screen
        self.screen.fill(self.current_colors["bg"])
        
        # Draw confirmation message
        quit_text = self.large_font.render("Are you sure you want to quit?", True, self.current_colors["text"])
        quit_rect = quit_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
        self.screen.blit(quit_text, quit_rect)
        
        # Draw buttons
        yes_button = self.create_button("YES", WIDTH//2 - 75, HEIGHT//2 + 50, self.quit_game)
        no_button = self.create_button("NO", WIDTH//2 + 75, HEIGHT//2 + 50, self.go_back)
        
        # Handle button events and draw them
        self.handle_button(yes_button)
        self.draw_button(yes_button)
        self.handle_button(no_button)
        self.draw_button(no_button)
    
    def draw_algorithm_select_screen(self):
        # Clear the screen
        self.screen.fill(self.current_colors["bg"])
        
        # Draw title
        title_text = self.large_font.render("SELECT SOLVING ALGORITHM", True, self.current_colors["text"])
        title_rect = title_text.get_rect(center=(WIDTH//2, HEIGHT//3 - 50))
        self.screen.blit(title_text, title_rect)
        
        # Draw buttons
        backtrack_button = self.create_button("Backtracking", WIDTH//2, HEIGHT//2 - 30, 
                                             lambda: self.solve_puzzle("backtracking"))
        constraint_button = self.create_button("Constraint Propagation Backtracking", WIDTH//2, HEIGHT//2 + 30, 
                                              lambda: self.solve_puzzle("constraint"))
        back_button = self.create_button("BACK", WIDTH//2, HEIGHT//2 + 90, self.go_back)
        
        # Handle button events and draw them
        self.handle_button(backtrack_button)
        self.draw_button(backtrack_button)
        self.handle_button(constraint_button)
        self.draw_button(constraint_button)
        self.handle_button(back_button)
        self.draw_button(back_button)
    
    def create_button(self, text, x, y, action=None):
        # Create a button dictionary
        text_surf = self.medium_font.render(text, True, self.current_colors["text"])
        text_rect = text_surf.get_rect(center=(x, y))
        button_rect = pygame.Rect(text_rect.left - 10, text_rect.top - 5, 
                                text_rect.width + 20, text_rect.height + 10)
        
        return {
            "rect": button_rect,
            "text": text,
            "text_surf": text_surf,
            "text_rect": text_rect,
            "action": action,
            "hover": False,
            "active": False
        }
    
    def handle_button(self, button):
        # Handle button hover and click events
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()[0]
        
        # Check if mouse is over button
        button["hover"] = button["rect"].collidepoint(mouse_pos)
        
        # Check if button is clicked
        if button["hover"] and mouse_click and button["action"]:
            # Small delay to prevent accidental double clicks
            pygame.time.delay(100)
            self.play_sound(self.button_sound)
            button["action"]()
    
    def draw_button(self, button):
        # Draw button background
        if button["active"]:
            color = self.current_colors["button"]
        elif button["hover"]:
            color = self.current_colors["button_hover"]
        else:
            color = self.current_colors["button"]
        
        pygame.draw.rect(self.screen, color, button["rect"], border_radius=5)
        pygame.draw.rect(self.screen, BLACK, button["rect"], 2, border_radius=5)
        pygame.draw.rect(self.screen, color, button["rect"], border_radius=5)
        pygame.draw.rect(self.screen, BLACK, button["rect"], 2, border_radius=5)
        
        # Draw button text
        self.screen.blit(button["text_surf"], button["text_rect"])
    
    def format_time(self, seconds):
        # Format time as mm:ss
        minutes, seconds = divmod(int(seconds), 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def start_new_game(self):
        # Start a new game
        self.new_game()
        self.play_sound(self.button_sound)
    
    def open_settings(self):
        # Open the settings screen
        self.previous_state = self.current_state
        self.current_state = GameState.SETTINGS
        self.play_sound(self.button_sound)
    
    def open_high_scores(self):
        # Open the high scores screen
        self.previous_state = self.current_state
        self.current_state = GameState.HIGH_SCORES
        self.play_sound(self.button_sound)
    
    def go_back(self):
        # Go back to the previous screen
        # if self.previous_state:
        #     self.current_state = self.previous_state
        #     self.previous_state = None
        # else:
        self.current_state = GameState.WELCOME
        self.play_sound(self.button_sound)
    
    def confirm_quit(self):
        # Show quit confirmation screen
        self.previous_state = self.current_state
        self.current_state = GameState.QUIT_CONFIRM
        self.play_sound(self.button_sound)
    
    def quit_game(self):
        # Save data before quitting
        self.save_data()
        pygame.quit()
        sys.exit()
    
    def set_difficulty(self, difficulty):
        # Set the game difficulty
        self.difficulty = difficulty
        self.play_sound(self.button_sound)
    
    def set_theme(self, theme):
        # Set the game theme
        self.theme = theme
        self.current_colors = self.theme.value
        self.play_sound(self.button_sound)
    
    def select_algorithm(self):
        # Open algorithm selection screen
        self.previous_state = self.current_state
        self.current_state = GameState.ALGORITHM_SELECT
        self.play_sound(self.button_sound)
    
    def give_hint(self):
        # Provide a hint if a cell is selected
        if self.active_cell:
            row, col = self.active_cell
            
            # Only give hint for empty or user-filled cells
            if self.board[row][col] == 0 or self.cell_status[row][col] == 1:
                # Get the correct value from the solved board
                correct_value = self.solved_board[row][col]
                
                # Update the board and cell status
                self.board[row][col] = correct_value
                self.cell_status[row][col] = 2  # Mark as hint
                
                # Increment hint counter
                self.hints_used += 1
                
                self.play_sound(self.success_sound)
            else:
                self.play_sound(self.error_sound)
    
    def toggle_mark(self):
        # Toggle marking of a cell
        if self.active_cell:
            if self.active_cell in self.marked_cells:
                self.marked_cells.remove(self.active_cell)
            else:
                self.marked_cells.add(self.active_cell)
            self.play_sound(self.button_sound)
    
    def solve_puzzle(self, algorithm):
        # Solve the puzzle using the selected algorithm
        start_time = time.perf_counter()
        print(start_time)
        if algorithm == "backtracking":
            self.solve_with_backtracking()
        else:  # constraint propagation
            self.solve_with_constraint_propagation()
        
        # Calculate the time it took to solve
        self.algo_solve_time = time.perf_counter() - start_time 
        print(self.algo_solve_time)
        
        # Update the board with the solution
        self.board = copy.deepcopy(self.solved_board)
        
        # Go back to the game screen
        self.current_state = GameState.NEW_GAME
        self.play_sound(self.success_sound)
    
    def solve_with_backtracking(self):
        # Create a copy of the current board
        temp_board = copy.deepcopy(self.original_board)
        
        # Solve using backtracking
        def backtrack():
            empty = self.find_empty_in_board(temp_board)
            if not empty:
                return True
            
            row, col = empty
            
            for num in range(1, 10):
                if self.is_valid_in_board(temp_board, row, col, num):
                    temp_board[row][col] = num
                    
                    if backtrack():
                        return True
                    
                    temp_board[row][col] = 0
            
            return False
        
        backtrack()
        
        # Update the solved board
        self.solved_board = copy.deepcopy(temp_board)
        self.paused = True
    
    def find_empty_in_board(self, board):
        # Find an empty cell in the given board
        for i in range(9):
            for j in range(9):
                if board[i][j] == 0:
                    return (i, j)
        return None
    
    def is_valid_in_board(self, board, row, col, num):
        # Check if placing 'num' at position (row, col) is valid in the given board
        # Check row
        for j in range(9):
            if board[row][j] == num:
                return False
        
        # Check column
        for i in range(9):
            if board[i][col] == num:
                return False
        
        # Check 3x3 box
        box_row, box_col = 3 * (row // 3), 3 * (col // 3)
        for i in range(box_row, box_row + 3):
            for j in range(box_col, box_col + 3):
                if board[i][j] == num:
                    return False
        
        return True
    
    def solve_with_constraint_propagation(self):
        # Implement a more efficient solving algorithm using constraint propagation
        # This is a simplified version of the algorithm
        
        # Create a copy of the current board
        temp_board = copy.deepcopy(self.original_board)
        
        # Create a dictionary of possible values for each cell
        possible_values = {}
        for i in range(9):
            for j in range(9):
                if temp_board[i][j] == 0:
                    possible_values[(i, j)] = set(range(1, 10))
                    
                    # Remove values that are already in the row, column, or box
                    for k in range(9):
                        # Check row
                        if temp_board[i][k] != 0:
                            possible_values[(i, j)].discard(temp_board[i][k])
                        
                        # Check column
                        if temp_board[k][j] != 0:
                            possible_values[(i, j)].discard(temp_board[k][j])
                    
                    # Check box
                    box_row, box_col = 3 * (i // 3), 3 * (j // 3)
                    for r in range(box_row, box_row + 3):
                        for c in range(box_col, box_col + 3):
                            if temp_board[r][c] != 0:
                                possible_values[(i, j)].discard(temp_board[r][c])
        
        # Solve using constraint propagation and backtracking
        def constraint_backtrack():
            # If no more empty cells, puzzle is solved
            if not possible_values:
                return True
            
            # Find the cell with the fewest possible values
            min_cell = min(possible_values, key=lambda cell: len(possible_values[cell]))
            
            # Try each possible value
            for value in list(possible_values[min_cell]):
                row, col = min_cell
                
                # Check if placing value is still valid
                if self.is_valid_in_board(temp_board, row, col, value):
                    # Place the value
                    temp_board[row][col] = value
                    
                    # Remove the cell from possible_values
                    del_possible_values = possible_values.pop(min_cell)
                    
                    # Store affected cells and their previous possible values
                    affected_cells = {}
                    
                    # Update possible values for affected cells
                    for i in range(9):
                        # Row cells
                        if (i, col) in possible_values and value in possible_values[(i, col)]:
                            affected_cells[(i, col)] = possible_values[(i, col)].copy()
                            possible_values[(i, col)].discard(value)
                        
                        # Column cells
                        if (row, i) in possible_values and value in possible_values[(row, i)]:
                            affected_cells[(row, i)] = possible_values[(row, i)].copy()
                            possible_values[(row, i)].discard(value)
                    
                    # Box cells
                    box_row, box_col = 3 * (row // 3), 3 * (col // 3)
                    for i in range(box_row, box_row + 3):
                        for j in range(box_col, box_col + 3):
                            if (i, j) in possible_values and value in possible_values[(i, j)]:
                                affected_cells[(i, j)] = possible_values[(i, j)].copy()
                                possible_values[(i, j)].discard(value)
                    
                    # Continue with backtracking
                    if constraint_backtrack():
                        return True
                    
                    # If not successful, backtrack
                    temp_board[row][col] = 0
                    
                    # Restore affected cells
                    for cell, prev_values in affected_cells.items():
                        possible_values[cell] = prev_values
                    
                    # Restore the current cell
                    possible_values[min_cell] = del_possible_values
            
            return False
        
        constraint_backtrack()
        
        # Update the solved board
        self.solved_board = copy.deepcopy(temp_board)

    
    def check_if_valid(self):
    # Check each cell in the board
        for row in range(9):
            for col in range(9):
                num = self.board[row][col]
                if num != 0:  # Ignore empty cells
                    # Temporarily clear the cell to check validity
                    self.board[row][col] = 0
                    if not self.is_valid(row, col, num):
                        self.board[row][col] = num  # Restore the cell
                        return False
                    self.board[row][col] = num  # Restore the cell
        return True
    
    # def add_high_score(self):
    #     # Calculate score (lower is better)
    #     # Formula: time + (hints_used * 30 seconds penalty)
    #     score = self.elapsed_time + (self.hints_used * 30)
        
    #     # Add to high scores
    #     self.high_scores.append({
    #         "difficulty": self.difficulty.value["name"],
    #         "time": self.elapsed_time,
    #         "hints": self.hints_used,
    #         "score": score
    #     })
        
    #     # Save high scores
    #     self.save_data()

    def add_high_score(self, player_name):
        # Calculate score (lower is better)
        score = self.elapsed_time + (self.hints_used * 30)
        
        # Add to high scores
        self.high_scores.append({
            "name": player_name,
            "difficulty": self.difficulty.value["name"],
            "time": self.elapsed_time,
            "hints": self.hints_used,
            "score": score
        })
        
        # Save high scores
        self.save_data()


    def input_player_name(self):
        # Simple input mechanism for getting player's name
        player_name = ""
        input_active = True

        # Define the messages
        congrats_message = "Congratulations! You've completed the puzzle!"
        name_prompt = "Please type your name:"

        while input_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:  # Enter key to finish input
                        input_active = False
                    elif event.key == pygame.K_BACKSPACE:
                        player_name = player_name[:-1]  # Remove last character
                    else:
                        player_name += event.unicode  # Add character to name

            # Clear the screen and redraw everything
            self.screen.fill(self.current_colors["bg"])

            # Render the messages
            congrats_surf = self.medium_font.render(congrats_message, True, self.current_colors["text"])
            name_prompt_surf = self.medium_font.render(name_prompt, True, self.current_colors["text"])
            player_name_surf = self.medium_font.render(player_name, True, self.current_colors["text"])

            # Get the rectangles for positioning
            congrats_rect = congrats_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
            name_prompt_rect = name_prompt_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
            player_name_rect = player_name_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60))

            # Draw the messages on the screen
            self.screen.blit(congrats_surf, congrats_rect)
            self.screen.blit(name_prompt_surf, name_prompt_rect)
            self.screen.blit(player_name_surf, player_name_rect)

            # Update the display
            pygame.display.flip()
        return player_name

    
    def handle_events(self):
        # Handle pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.save_data()
                pygame.quit()
                sys.exit()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Handle mouse clicks
                if event.button == 1:  # Left click
                    if self.current_state == GameState.NEW_GAME:
                        # Check if click is on the board
                        offset_x = (WIDTH - BOARD_SIZE) // 2
                        offset_y = (HEIGHT - BOARD_SIZE) // 2 - 50
                        
                        mouse_pos = pygame.mouse.get_pos()
                        if (offset_x <= mouse_pos[0] <= offset_x + BOARD_SIZE and
                            offset_y <= mouse_pos[1] <= offset_y + BOARD_SIZE):
                            # Calculate cell coordinates
                            cell_x = (mouse_pos[0] - offset_x) // GRID_SIZE
                            cell_y = (mouse_pos[1] - offset_y) // GRID_SIZE
                            
                            # Set active cell
                            self.active_cell = (cell_y, cell_x)
            
            elif event.type == pygame.KEYDOWN:
                # Handle key presses
                if self.current_state == GameState.NEW_GAME and self.active_cell:
                    row, col = self.active_cell
                    
                    # Only allow input for empty cells or user-filled cells
                    if self.original_board[row][col] == 0:
                        if event.key == pygame.K_BACKSPACE or event.key == pygame.K_DELETE:
                            # Clear the cell
                            self.board[row][col] = 0
                        
                        elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3,
                                          pygame.K_4, pygame.K_5, pygame.K_6,
                                          pygame.K_7, pygame.K_8, pygame.K_9]:
                            # Get the number from the key
                            num = event.key - pygame.K_0
                            
                            # Place the number
                            self.board[row][col] = num
                            self.cell_status[row][col] = 1  # Mark as user input
                        

                            if self.check_if_valid() and self.algo_solve_time !=0:
                                # Get player name
                                self.play_sound(self.solve_sound)
                                player_name = self.input_player_name()
                                # Add high score
                                self.add_high_score(player_name)
                                
                                # Display message
                                print("Puzzle solved!")
                                
                                self.ask_play_again()

                            #     else:

    
    def restart_game(self):
        self = SudokuGame()
        clock = pygame.time.Clock()
        # self.current_state == GameState.NEW_GAME
        self.start_new_game()
        while True:
        # Handle events
            self.handle_events()
            # Draw the current screen
            if self.current_state == GameState.WELCOME:
                self.draw_welcome_screen()
            elif self.current_state == GameState.NEW_GAME:
                self.draw_game_screen()
            elif self.current_state == GameState.SETTINGS:
                self.draw_settings_screen()
            elif self.current_state == GameState.HIGH_SCORES:
                self.draw_high_scores_screen()
            elif self.current_state == GameState.QUIT_CONFIRM:
                self.draw_quit_confirm_screen()
            elif self.current_state == GameState.ALGORITHM_SELECT:
                self.draw_algorithm_select_screen()
            clock.tick(60)
            pygame.display.flip()

    def go_to_main_menu(self):
        self = SudokuGame()
        self.run()  # Restart the game
    # def ask_play_again(self):
    #     # Define the messages
    #     question = "Do you want to play again?"
    #     yes_option = "Yes"
    #     no_option = "No"

    #     # Set up a variable for input
    #     input_active = True
    #     selected_option = 0  # 0 for Yes, 1 for No

    #     while input_active:
    #         for event in pygame.event.get():
    #             if event.type == pygame.QUIT:
    #                 pygame.quit()
    #                 sys.exit()
    #             elif event.type == pygame.KEYDOWN:
    #                 if event.key == pygame.K_RETURN:  # Enter key to select
    #                     input_active = False
    #                 elif event.key == pygame.K_UP:
    #                     selected_option = (selected_option - 1) % 2  # Toggle up
    #                 elif event.key == pygame.K_DOWN:
    #                     selected_option = (selected_option + 1) % 2  # Toggle down

    #         # Clear the screen
    #         self.screen.fill(self.current_colors["bg"])

    #         # Render the messages
    #         question_surf = self.medium_font.render(question, True, self.current_colors["text"])
    #         yes_surf = self.medium_font.render(yes_option, True, self.current_colors["text"] if selected_option == 0 else (150, 150, 150))
    #         no_surf = self.medium_font.render(no_option, True, self.current_colors["text"] if selected_option == 1 else (150, 150, 150))

    #         # Get the rectangles for positioning
    #         question_rect = question_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
    #         yes_rect = yes_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
    #         no_rect = no_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60))

    #         # Draw the messages on the screen
    #         self.screen.blit(question_surf, question_rect)
    #         self.screen.blit(yes_surf, yes_rect)
    #         self.screen.blit(no_surf, no_rect)

    #         # Update the display
    #         pygame.display.flip()

    #     # Return the selection
    #     return selected_option == 0  # True if Yes, False if No
    def ask_play_again(self):
        # Clear the screen
        self.screen.fill(self.current_colors["bg"])

        # Draw confirmation message
        question_text = self.large_font.render("Do you want to play again?", True, self.current_colors["text"])
        question_rect = question_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        self.screen.blit(question_text, question_rect)

        # Create buttons for Yes and No
        yes_button = self.create_button("YES", WIDTH // 2 - 75, HEIGHT // 2 + 50, self.restart_game)  # Restart game function
        no_button = self.create_button("NO", WIDTH // 2 + 75, HEIGHT // 2 + 50, self.go_to_main_menu)  # Main menu function

        # Handle button events and draw them
        self.handle_button(yes_button)
        self.draw_button(yes_button)
        self.handle_button(no_button)
        self.draw_button(no_button)

        # Event loop for handling button clicks
        input_active = True
        while input_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:  # Allow quitting with Escape
                        input_active = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if yes_button["rect"].collidepoint(event.pos):
                        self.restart_game()  # Call the restart function
                        input_active = False
                    elif no_button["rect"].collidepoint(event.pos):
                        self.go_to_main_menu()  # Call the main menu function
                        input_active = False

            # Update the display
            pygame.display.flip()

    def run(self):
        # Main game loop
        clock = pygame.time.Clock()
        
        while True:
            # Handle events
            self.handle_events()
            
            # Draw the current screen
            if self.current_state == GameState.WELCOME:
                self.draw_welcome_screen()
            elif self.current_state == GameState.NEW_GAME:
                self.draw_game_screen()
            elif self.current_state == GameState.SETTINGS:
                self.draw_settings_screen()
            elif self.current_state == GameState.HIGH_SCORES:
                self.draw_high_scores_screen()
            elif self.current_state == GameState.QUIT_CONFIRM:
                self.draw_quit_confirm_screen()
            elif self.current_state == GameState.ALGORITHM_SELECT:
                self.draw_algorithm_select_screen()
            
            # Update the display
            pygame.display.flip()
            
            # Cap the frame rate
            clock.tick(60)

# Run the game
if __name__ == "__main__":
    game = SudokuGame()
    game.run()