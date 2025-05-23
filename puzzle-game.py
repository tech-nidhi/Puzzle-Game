import pygame
import sys
import random
import time
import os

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)
BLUE = (0, 0, 255)
GREEN = (0, 200, 0)
RED = (200, 0, 0)

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Enhanced Sliding Puzzle")
clock = pygame.time.Clock()

# Load sounds
try:
    move_sound = pygame.mixer.Sound("move.wav")
    success_sound = pygame.mixer.Sound("success.wav")
    click_sound = pygame.mixer.Sound("click.wav")
    hint_sound = pygame.mixer.Sound("hint.wav")
except:
    # Create placeholder sounds if files don't exist
    move_sound = pygame.mixer.Sound(pygame.sndarray.array([0] * 8000))
    success_sound = pygame.mixer.Sound(pygame.sndarray.array([0] * 8000))
    click_sound = pygame.mixer.Sound(pygame.sndarray.array([0] * 8000))
    hint_sound = pygame.mixer.Sound(pygame.sndarray.array([0] * 8000))

# Sample images for puzzles
sample_images = [
    {"name": "Numbers", "type": "generated"},
    {"name": "Grid", "type": "generated"},
    {"name": "Nature", "type": "generated"},
]

class Tile:
    def __init__(self, value, x, y, image=None, image_rect=None):
        self.value = value  # The number on the tile (0 represents the empty tile)
        self.x = x  # Grid position x
        self.y = y  # Grid position y
        self.image = image  # Portion of the image for this tile
        self.image_rect = image_rect  # Source rectangle in the original image
        self.rect = None  # Will be set when grid size is determined
        self.target_x = 0
        self.target_y = 0
        self.current_x = 0
        self.current_y = 0
        self.moving = False

    def set_position(self, grid_size, tile_size):
        self.rect = pygame.Rect(self.x * tile_size, self.y * tile_size, tile_size, tile_size)
        self.target_x = self.x * tile_size
        self.target_y = self.y * tile_size
        self.current_x = self.target_x
        self.current_y = self.target_y

    def update(self):
        # Smooth movement animation
        if self.moving:
            move_speed = 10
            dx = self.target_x - self.current_x
            dy = self.target_y - self.current_y

            if abs(dx) < move_speed:
                self.current_x = self.target_x
            else:
                self.current_x += move_speed if dx > 0 else -move_speed

            if abs(dy) < move_speed:
                self.current_y = self.target_y
            else:
                self.current_y += move_speed if dy > 0 else -move_speed

            if self.current_x == self.target_x and self.current_y == self.target_y:
                self.moving = False

        self.rect.x = self.current_x
        self.rect.y = self.current_y

    def draw(self, tile_size):
        if self.value != 0:  # Don't draw the empty tile
            if self.image:
                screen.blit(self.image, self.rect)
                pygame.draw.rect(screen, BLACK, self.rect, 2)
            else:
                pygame.draw.rect(screen, BLUE, self.rect, border_radius=10)
                pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=10)

                # Draw the number
                font = pygame.font.Font(None, 36)
                text = font.render(str(self.value), True, WHITE)
                text_rect = text.get_rect(center=self.rect.center)
                screen.blit(text, text_rect)

    def move_to(self, x, y, tile_size):
        self.x = x
        self.y = y
        self.target_x = x * tile_size
        self.target_y = y * tile_size
        self.moving = True

class PuzzleGame:
    def __init__(self, difficulty=3, image_choice="Numbers"):
        self.tiles = []
        self.grid_size = difficulty  # 3x3, 4x4, or 5x5
        self.board_size = min(500, min(SCREEN_WIDTH, SCREEN_HEIGHT) - 100)
        self.tile_size = self.board_size // self.grid_size
        self.board_x = (SCREEN_WIDTH - self.board_size) // 2
        self.board_y = (SCREEN_HEIGHT - self.board_size) // 2 + 30

        self.empty_x = self.grid_size - 1
        self.empty_y = self.grid_size - 1
        self.moves = 0
        self.solved = False
        self.start_time = time.time()
        self.elapsed_time = 0
        self.image_choice = image_choice
        self.full_image = None
        self.hint_active = False
        self.hint_tile = None
        self.hint_timer = 0

        self.create_puzzle()

    def create_puzzle(self):
        # Create the full image based on choice
        self.create_image()

        # Create ordered tiles
        self.tiles = []
        value = 1
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                if y == self.grid_size - 1 and x == self.grid_size - 1:
                    # Last tile is empty (0)
                    tile = Tile(0, x, y)
                else:
                    # Create image tile if we have an image
                    if self.full_image:
                        # Calculate the portion of the image for this tile
                        image_rect = pygame.Rect(
                            x * self.tile_size,
                            y * self.tile_size,
                            self.tile_size,
                            self.tile_size
                        )
                        tile_image = pygame.Surface((self.tile_size, self.tile_size))
                        tile_image.blit(self.full_image, (0, 0), image_rect)
                        tile = Tile(value, x, y, tile_image, image_rect)
                    else:
                        tile = Tile(value, x, y)

                tile.set_position(self.grid_size, self.tile_size)
                self.tiles.append(tile)
                value += 1

        # Shuffle the puzzle
        self.shuffle()

    def create_image(self):
        if self.image_choice == "Numbers":
            self.full_image = None  # Just use numbers
        elif self.image_choice == "Grid":
            # Create a colorful grid pattern
            self.full_image = pygame.Surface((self.board_size, self.board_size))
            for y in range(self.grid_size):
                for x in range(self.grid_size):
                    color = ((x * 50) % 255, (y * 50) % 255, ((x+y) * 30) % 255)
                    rect = pygame.Rect(
                        x * self.tile_size,
                        y * self.tile_size,
                        self.tile_size,
                        self.tile_size
                    )
                    pygame.draw.rect(self.full_image, color, rect)
                    pygame.draw.rect(self.full_image, BLACK, rect, 2)
        else:  # Nature or any other option - create a gradient
            self.full_image = pygame.Surface((self.board_size, self.board_size))
            for y in range(self.board_size):
                for x in range(self.board_size):
                    r = int(255 * x / self.board_size)
                    g = int(255 * y / self.board_size)
                    b = int(255 * (x + y) / (2 * self.board_size))
                    self.full_image.set_at((x, y), (r, g, b))

    def shuffle(self):
        # Make random valid moves to shuffle
        moves = self.grid_size * self.grid_size * 20  # More moves for larger puzzles
        for _ in range(moves):
            possible_moves = []

            # Check all four directions
            if self.empty_x > 0:
                possible_moves.append((-1, 0))  # Left
            if self.empty_x < self.grid_size - 1:
                possible_moves.append((1, 0))   # Right
            if self.empty_y > 0:
                possible_moves.append((0, -1))  # Up
            if self.empty_y < self.grid_size - 1:
                possible_moves.append((0, 1))   # Down

            # Choose a random direction
            dx, dy = random.choice(possible_moves)
            self.move_tile(self.empty_x + dx, self.empty_y + dy, play_sound=False)

        # Reset moves counter and timer after shuffling
        self.moves = 0
        self.start_time = time.time()
        self.elapsed_time = 0
        self.solved = False

    def get_tile_at(self, x, y):
        for tile in self.tiles:
            if tile.x == x and tile.y == y:
                return tile
        return None

    def move_tile(self, x, y, play_sound=True):
        if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
            # Check if the clicked tile is adjacent to the empty tile
            if (abs(x - self.empty_x) == 1 and y == self.empty_y) or \
               (abs(y - self.empty_y) == 1 and x == self.empty_x):

                # Find the tile at the clicked position
                tile = self.get_tile_at(x, y)
                if tile:
                    # Swap positions
                    tile.move_to(self.empty_x, self.empty_y, self.tile_size)
                    self.empty_x, self.empty_y = x, y
                    self.moves += 1

                    if play_sound:
                        move_sound.play()
                    
                    if self.moves > 0:
                        self.check_solved()
                        return True
        return False

    def check_solved(self):
        # Check if the puzzle is solved
        self.solved = True
        value = 1

        for y in range(self.grid_size):
            for x in range(self.grid_size):
                if y == self.grid_size - 1 and x == self.grid_size - 1:
                    # Last position should be empty
                    tile = self.get_tile_at(x, y)
                    if tile is None or tile.value != 0:
                        self.solved = False
                        break
                else:
                    tile = self.get_tile_at(x, y)
                    if tile is None or tile.value != value:
                        self.solved = False
                        break
                    value += 1

        if self.solved:
            self.elapsed_time = time.time() - self.start_time
            success_sound.play()

    def show_hint(self):
        # Find a tile that's out of place and highlight it
        self.hint_active = True
        self.hint_timer = 3 * FPS  # Show hint for 3 seconds

        # Find the first tile that's out of position
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                expected_value = y * self.grid_size + x + 1
                if y == self.grid_size - 1 and x == self.grid_size - 1:
                    expected_value = 0

                tile = self.get_tile_at(x, y)
                if tile and tile.value != expected_value:
                    self.hint_tile = tile
                    hint_sound.play()
                    return

    def update(self):
        for tile in self.tiles:
            tile.update()

        if not self.solved:
            self.elapsed_time = time.time() - self.start_time

        if self.hint_active:
            self.hint_timer -= 1
            if self.hint_timer <= 0:
                self.hint_active = False
                self.hint_tile = None

    def draw(self):
        # Draw background for the board
        board_rect = pygame.Rect(self.board_x, self.board_y, self.board_size, self.board_size)
        pygame.draw.rect(screen, GRAY, board_rect)

        # Draw tiles
        for tile in self.tiles:
            # Adjust tile position to board position
            original_x = tile.rect.x
            original_y = tile.rect.y
            tile.rect.x += self.board_x
            tile.rect.y += self.board_y

            tile.draw(self.tile_size)

            # Highlight hint tile
            if self.hint_active and tile == self.hint_tile:
                pygame.draw.rect(screen, (255, 255, 0), tile.rect, 4)

            # Restore original position for game logic
            tile.rect.x = original_x
            tile.rect.y = original_y

        # Draw moves counter and timer
        font = pygame.font.Font(None, 36)
        moves_text = font.render(f"Moves: {self.moves}", True, BLACK)
        screen.blit(moves_text, (10, 10))

        # Format time as minutes:seconds
        minutes = int(self.elapsed_time) // 60
        seconds = int(self.elapsed_time) % 60
        time_text = font.render(f"Time: {minutes:02d}:{seconds:02d}", True, BLACK)
        screen.blit(time_text, (10, 50))

        # Draw difficulty
        diff_text = font.render(f"Difficulty: {self.grid_size}x{self.grid_size}", True, BLACK)
        diff_rect = diff_text.get_rect(topright=(SCREEN_WIDTH - 10, 10))
        screen.blit(diff_text, diff_rect)

        # Draw image type
        img_text = font.render(f"Image: {self.image_choice}", True, BLACK)
        img_rect = img_text.get_rect(topright=(SCREEN_WIDTH - 10, 50))
        screen.blit(img_text, img_rect)

        # Draw solved message
        if self.solved:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            screen.blit(overlay, (0, 0))

            font = pygame.font.Font(None, 72)
            solved_text = font.render("SOLVED!", True, GREEN)
            text_rect = solved_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            screen.blit(solved_text, text_rect)

            font = pygame.font.Font(None, 36)
            stats_text = font.render(f"Moves: {self.moves}   Time: {minutes:02d}:{seconds:02d}", True, WHITE)
            stats_rect = stats_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
            screen.blit(stats_text, stats_rect)

class Button:
    def __init__(self, x, y, width, height, text, color=BLUE, hover_color=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color or (min(color[0] + 50, 255), min(color[1] + 50, 255), min(color[2] + 50, 255))
        self.is_hovered = False

    def draw(self):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=5)

        font = pygame.font.Font(None, 28)
        text = font.render(self.text, True, WHITE)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class Menu:
    def __init__(self):
        self.state = "main"  # main, game, difficulty, image_select
        self.game = None
        self.difficulty = 3
        self.image_choice = "Numbers"

        # Create buttons for main menu
        button_width = 200
        button_height = 50
        center_x = SCREEN_WIDTH // 2 - button_width // 2

        self.main_buttons = [
            Button(center_x, 200, button_width, button_height, "Start Game"),
            Button(center_x, 270, button_width, button_height, "Select Difficulty"),
            Button(center_x, 340, button_width, button_height, "Select Image"),
            Button(center_x, 410, button_width, button_height, "Quit")
        ]

        self.difficulty_buttons = [
            Button(center_x, 200, button_width, button_height, "Easy (3x3)", GREEN),
            Button(center_x, 270, button_width, button_height, "Medium (4x4)", BLUE),
            Button(center_x, 340, button_width, button_height, "Hard (5x5)", RED),
            Button(center_x, 410, button_width, button_height, "Back")
        ]

        self.image_buttons = []
        y_pos = 200
        for image in sample_images:
            self.image_buttons.append(Button(center_x, y_pos, button_width, button_height, image["name"]))
            y_pos += 70
        self.image_buttons.append(Button(center_x, y_pos, button_width, button_height, "Back"))

        self.game_buttons = [
            Button(center_x - 110, SCREEN_HEIGHT - 70, button_width - 40, button_height, "Restart"),
            Button(center_x + 70, SCREEN_HEIGHT - 70, button_width - 40, button_height, "Menu"),
            Button(SCREEN_WIDTH - 100, SCREEN_HEIGHT - 70, 80, button_height, "Hint")
        ]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()

            if self.state == "main":
                for i, button in enumerate(self.main_buttons):
                    if button.is_clicked(pos):
                        click_sound.play()
                        if i == 0:  # Start Game
                            self.game = PuzzleGame(self.difficulty, self.image_choice)
                            self.state = "game"
                        elif i == 1:  # Select Difficulty
                            self.state = "difficulty"
                        elif i == 2:  # Select Image
                            self.state = "image_select"
                        elif i == 3:  # Quit
                            return False

            elif self.state == "difficulty":
                for i, button in enumerate(self.difficulty_buttons):
                    if button.is_clicked(pos):
                        click_sound.play()
                        if i == 0:  # Easy
                            self.difficulty = 3
                            self.state = "main"
                        elif i == 1:  # Medium
                            self.difficulty = 4
                            self.state = "main"
                        elif i == 2:  # Hard
                            self.difficulty = 5
                            self.state = "main"
                        elif i == 3:  # Back
                            self.state = "main"

            elif self.state == "image_select":
                for i, button in enumerate(self.image_buttons):
                    if button.is_clicked(pos):
                        click_sound.play()
                        if i < len(sample_images):  # Image selection
                            self.image_choice = sample_images[i]["name"]
                            self.state = "main"
                        else:  # Back button
                            self.state = "main"

            elif self.state == "game":
                # Check game buttons
                for i, button in enumerate(self.game_buttons):
                    if button.is_clicked(pos):
                        click_sound.play()
                        if i == 0:  # Restart
                            self.game = PuzzleGame(self.difficulty, self.image_choice)
                        elif i == 1:  # Menu
                            self.state = "main"
                        elif i == 2:  # Hint
                            self.game.show_hint()

                # Check tile clicks
                if self.game:
                    board_x = self.game.board_x
                    board_y = self.game.board_y
                    tile_size = self.game.tile_size

                    # Adjust click position to board coordinates
                    board_pos = (pos[0] - board_x, pos[1] - board_y)

                    if (0 <= board_pos[0] < self.game.board_size and
                        0 <= board_pos[1] < self.game.board_size):
                        tile_x = board_pos[0] // tile_size
                        tile_y = board_pos[1] // tile_size
                        self.game.move_tile(tile_x, tile_y)

        return True

    def update(self):
        mouse_pos = pygame.mouse.get_pos()

        if self.state == "main":
            for button in self.main_buttons:
                button.check_hover(mouse_pos)
        elif self.state == "difficulty":
            for button in self.difficulty_buttons:
                button.check_hover(mouse_pos)
        elif self.state == "image_select":
            for button in self.image_buttons:
                button.check_hover(mouse_pos)
        elif self.state == "game" and self.game:
            self.game.update()
            for button in self.game_buttons:
                button.check_hover(mouse_pos)

    def draw(self):
        screen.fill(WHITE)

        if self.state == "main":
            # Draw title
            font = pygame.font.Font(None, 72)
            title = font.render("Sliding Puzzle", True, BLACK)
            title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
            screen.blit(title, title_rect)

            # Draw current settings
            font = pygame.font.Font(None, 28)
            settings = font.render(f"Difficulty: {self.difficulty}x{self.difficulty}   Image: {self.image_choice}", True, BLACK)
            settings_rect = settings.get_rect(center=(SCREEN_WIDTH // 2, 150))
            screen.blit(settings, settings_rect)

            # Draw buttons
            for button in self.main_buttons:
                button.draw()

        elif self.state == "difficulty":
            font = pygame.font.Font(None, 72)
            title = font.render("Select Difficulty", True, BLACK)
            title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
            screen.blit(title, title_rect)

            for button in self.difficulty_buttons:
                button.draw()

        elif self.state == "image_select":
            font = pygame.font.Font(None, 72)
            title = font.render("Select Image", True, BLACK)
            title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
            screen.blit(title, title_rect)

            for button in self.image_buttons:
                button.draw()

        elif self.state == "game" and self.game:
            self.game.draw()

            # Draw game buttons
            for button in self.game_buttons:
                button.draw()

# Create menu
menu = Menu()

# Game loop
running = True
while running:
    # Keep loop running at the right speed
    clock.tick(FPS)

    # Process input (events)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if menu.state == "game":
                    menu.state = "main"
                else:
                    running = False

        # Let menu handle other events
        if not menu.handle_event(event):
            running = False

    # Update
    menu.update()

    # Draw / render
    menu.draw()

    # Flip the display
    pygame.display.flip()

pygame.quit()
sys.exit()