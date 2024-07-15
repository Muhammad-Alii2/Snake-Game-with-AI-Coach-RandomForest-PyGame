import pygame
import sys
import random
import warnings
import joblib
import pandas as pd
import csv
import os
from AICoachTrainer import MLTrainer

# Suppress future warnings from sklearn
warnings.filterwarnings("ignore", category=FutureWarning, module="sklearn")

pygame.init()

# Screen dimensions and constants
SW, SH = 750, 750
TOP_MARGIN = 50
BLOCK_SIZE = 50
FONT = pygame.font.Font(None, 30)

# Available colors for the snake
AVAILABLE_COLORS = {
    "Green": (0, 255, 0),
    "Orange": (255, 165, 0),
    "Yellow": (255, 255, 0),
    "Purple": (160, 32, 240)
}

# Set up the display
screen = pygame.display.set_mode((SW, SH + TOP_MARGIN))
pygame.display.set_caption("SNAKE!")
clock = pygame.time.Clock()

# Load the AI model
model = joblib.load(r"..\Output Files\snake_ai_model.pkl")

data_collection = []  # Collect game data for saving


def saveDataToCsv(data, filename=r"..\Required Files\game_data.csv"):
    # Save game data to CSV
    file_exists = os.path.isfile(filename)

    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)

        # Write header if file does not exist
        if not file_exists:
            writer.writerow(["head_x", "head_y", "xdirection", "ydirection", "food_x", "food_y", "collision"])

        writer.writerows(data)


class Snake:
    def __init__(self, color):
        # Initialize snake attributes
        self.x, self.y = BLOCK_SIZE, BLOCK_SIZE + TOP_MARGIN
        self.xdirection = 1
        self.ydirection = 0
        self.head = pygame.Rect(self.x, self.y, BLOCK_SIZE, BLOCK_SIZE)
        self.body = [pygame.Rect(self.x - BLOCK_SIZE, self.y, BLOCK_SIZE, BLOCK_SIZE)]
        self.dead = False
        self.powered_up = False
        self.power_up_timer = 0
        self.color = color

    def reset(self):
        # Reset snake position and state
        self.x, self.y = BLOCK_SIZE, BLOCK_SIZE + TOP_MARGIN
        self.head = pygame.Rect(self.x, self.y, BLOCK_SIZE, BLOCK_SIZE)
        self.body = [pygame.Rect(self.x - BLOCK_SIZE, self.y, BLOCK_SIZE, BLOCK_SIZE)]
        self.xdirection = 1
        self.ydirection = 0
        self.dead = False

    def update(self):
        global power_up, data_collection

        collision = 0
        # Check for collisions with obstacles
        if not self.powered_up:
            for obstacle in obstacles:
                if self.head.colliderect(obstacle.rect):
                    self.dead = True
                    collision = 1

        # Check for self-collision
        for square in self.body:
            if self.head.x == square.x and self.head.y == square.y:
                self.dead = True
                collision = 1

        # Check for wall collisions
        if self.head.x not in range(0, SW) or self.head.y not in range(TOP_MARGIN, SH + TOP_MARGIN):
            self.dead = True
            collision = 1

        # Record game data for analysis
        data_collection.append(
            [self.head.x, self.head.y, self.xdirection, self.ydirection, food.x, food.y, collision])

        if self.dead:
            return True

        # Update snake's body
        self.body.append(self.head)
        for i in range(len(self.body) - 1):
            self.body[i].x, self.body[i].y = self.body[i + 1].x, self.body[i + 1].y
        self.head.x += self.xdirection * BLOCK_SIZE
        self.head.y += self.ydirection * BLOCK_SIZE
        self.body.remove(self.head)

        # Handle power-up state
        if self.powered_up:
            self.power_up_timer -= 1
            if self.power_up_timer <= 0:
                self.powered_up = False
                self.color = 'Green'

        return False


class Food:
    def __init__(self):
        # Generate initial food position
        self.x, self.y, self.rect = self.generateFoodPosition()

    def generateFoodPosition(self):
        # Randomly generate food position avoiding obstacles
        while True:
            x = int(random.randint(0, SW - BLOCK_SIZE) / BLOCK_SIZE) * BLOCK_SIZE
            y = int(random.randint(TOP_MARGIN, SH + TOP_MARGIN - BLOCK_SIZE) / BLOCK_SIZE) * BLOCK_SIZE
            new_rect = pygame.Rect(x, y, BLOCK_SIZE, BLOCK_SIZE)

            collision = False
            for obstacle in obstacles:
                if new_rect.colliderect(obstacle.rect):
                    collision = True
                    break

            if not collision:
                return x, y, new_rect

    def update(self):
        # Draw the food on the screen
        pygame.draw.rect(screen, 'Red', self.rect)


class PowerUp:
    def __init__(self, last_collected):
        # Initialize power-up attributes
        self.x = -1000
        self.y = -1000
        self.rect = pygame.Rect(self.x, self.y, BLOCK_SIZE, BLOCK_SIZE)
        self.active = False
        self.last_collected_at = last_collected

    def update(self):
        # Activate power-up based on score and draw it
        if not self.active and (len(snake.body) - 1) != 0 and (len(snake.body) - 1) % 3 == 0:
            self.spawn()

        pygame.draw.rect(screen, "Blue", self.rect)

    def spawn(self):
        # Spawn a new power-up if conditions are met
        current_score = len(snake.body) - 1
        if current_score >= self.last_collected_at + 3:
            self.x, self.y, self.rect = self.generatePowerUpPosition()
            self.active = True

    def generatePowerUpPosition(self):
        # Randomly generate power-up position avoiding obstacles
        while True:
            x = int(random.randint(0, SW - BLOCK_SIZE) / BLOCK_SIZE) * BLOCK_SIZE
            y = int(random.randint(TOP_MARGIN, SH + TOP_MARGIN - BLOCK_SIZE) / BLOCK_SIZE) * BLOCK_SIZE
            new_rect = pygame.Rect(x, y, BLOCK_SIZE, BLOCK_SIZE)

            collision = False
            for obstacle in obstacles:
                if new_rect.colliderect(obstacle.rect):
                    collision = True
                    break

            if not collision:
                return x, y, new_rect

    def apply_power_up(self, snake):
        # Apply power-up effects to the snake
        snake.powered_up = True
        snake.power_up_timer = 20
        snake.color = 'Blue'
        self.active = False
        self.last_collected_at = len(snake.body) - 1
        return self.last_collected_at


class Obstacle:
    def __init__(self, x, y):
        # Initialize obstacle position
        self.rect = pygame.Rect(x, y, BLOCK_SIZE, BLOCK_SIZE)

    def update(self):
        # Draw the obstacle on the screen
        pygame.draw.rect(screen, 'White', self.rect)


class Button:
    def __init__(self, x, y, width, height, color, text, font):
        # Initialize button attributes
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.text = text
        self.font = font

    def draw(self, screen, outline_color=None):
        # Draw the button on the screen
        if outline_color:
            pygame.draw.rect(screen, outline_color, self.rect.inflate(10, 10), 10)
        pygame.draw.rect(screen, self.color, self.rect)
        text_surface = self.font.render(self.text, True, 'Black')
        screen.blit(text_surface, (
            self.rect.x + (self.rect.width - text_surface.get_width()) // 2,
            self.rect.y + (self.rect.height - text_surface.get_height()) // 2
        ))

    def is_clicked(self, pos):
        # Check if the button is clicked
        return self.rect.collidepoint(pos)


def generateObstacles():
    # Create a set of obstacles at predetermined positions
    obstacles = []
    center_x = (SW // 2 // BLOCK_SIZE) * BLOCK_SIZE
    center_y = ((SH + TOP_MARGIN) // 2 // BLOCK_SIZE) * BLOCK_SIZE
    obstacles.append(Obstacle(center_x, center_y))

    small_center_x = (SW // 4 // BLOCK_SIZE) * BLOCK_SIZE
    small_center_y = ((SH + TOP_MARGIN) // 4 // BLOCK_SIZE) * BLOCK_SIZE
    obstacles.append(Obstacle(small_center_x, small_center_y))

    small_center_x = (3 * SW // 4 // BLOCK_SIZE) * BLOCK_SIZE
    small_center_y = ((SH + TOP_MARGIN) // 4 // BLOCK_SIZE) * BLOCK_SIZE
    obstacles.append(Obstacle(small_center_x, small_center_y))

    small_center_x = (SW // 4 // BLOCK_SIZE) * BLOCK_SIZE
    small_center_y = (3 * (SH + TOP_MARGIN) // 4 // BLOCK_SIZE) * BLOCK_SIZE
    obstacles.append(Obstacle(small_center_x, small_center_y))

    small_center_x = (3 * SW // 4 // BLOCK_SIZE) * BLOCK_SIZE
    small_center_y = (3 * (SH + TOP_MARGIN) // 4 // BLOCK_SIZE) * BLOCK_SIZE
    obstacles.append(Obstacle(small_center_x, small_center_y))

    return obstacles


def drawGrid():
    # Draw a grid on the screen
    for x in range(0, SW, BLOCK_SIZE):
        for y in range(TOP_MARGIN, SH + TOP_MARGIN, BLOCK_SIZE):
            rectangle = pygame.Rect(x, y, BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(screen, 'Grey', rectangle, 1)


def getAIFeedback(snake, steps=5):
    # Provide feedback from the AI model based on the snake's current state
    future_head_x, future_head_y = snake.head.x, snake.head.y
    for _ in range(steps):
        future_head_x += snake.xdirection * BLOCK_SIZE
        future_head_y += snake.ydirection * BLOCK_SIZE

        # Prepare input for the AI model
        X_new = pd.DataFrame([[future_head_x, future_head_y, snake.xdirection, snake.ydirection, food.x, food.y]],
                             columns=["head_x", "head_y", "xdirection", "ydirection", "food_x", "food_y"])
        collision_prob = model.predict_proba(X_new)[0][1]
        if collision_prob > 0.5:
            return "High risk of collision! Change direction!"

    return ""


def displayStartScreen():
    # Display the start screen and handle color selection
    screen.fill('Black')
    title = FONT.render("Press SPACE to Start", True, 'White')
    color_prompt = FONT.render("Select Snake Color:", True, 'White')
    screen.blit(title, (SW // 2 - title.get_width() // 2, SH // 2 - 100))
    screen.blit(color_prompt, (SW // 2 - color_prompt.get_width() // 2, SH // 2))

    buttons = []
    color_names = list(AVAILABLE_COLORS.keys())
    button_width, button_height = 150, 40
    x = SW // 2 - button_width // 2
    y = SH // 2 + 50
    for color_name in color_names:
        buttons.append(Button(x, y, button_width, button_height, AVAILABLE_COLORS[color_name], color_name, FONT))
        y += 50

    selected_color_index = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return color_names[selected_color_index]
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for i, button in enumerate(buttons):
                    if button.is_clicked(pos):
                        selected_color_index = i

        screen.fill('Black')
        screen.blit(title, (SW // 2 - title.get_width() // 2, SH // 2 - 100))
        screen.blit(color_prompt, (SW // 2 - color_prompt.get_width() // 2, SH // 2))

        for i, button in enumerate(buttons):
            button.draw(screen, 'White' if i == selected_color_index else None)

        pygame.display.update()


def displayGameOverScreen(score):
    # Display the game over screen and handle user input
    screen.fill('Black')
    game_over_text = FONT.render("GAME OVER", True, 'White')
    score_text = FONT.render(f"Score: {score}", True, 'White')
    restart_text = FONT.render("Press SPACE to Restart", True, 'White')
    quit_text = FONT.render("Press ESC to Quit", True, 'White')

    screen.blit(game_over_text, (SW // 2 - game_over_text.get_width() // 2, SH // 2 - 100))
    screen.blit(score_text, (SW // 2 - score_text.get_width() // 2, SH // 2 - 50))
    screen.blit(restart_text, (SW // 2 - restart_text.get_width() // 2, SH // 2))
    screen.blit(quit_text, (SW // 2 - quit_text.get_width() // 2, SH // 2 + 50))

    pygame.display.update()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                saveDataToCsv(data_collection)
                MLTrainer()
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    waiting = False
                if event.key == pygame.K_ESCAPE:
                    saveDataToCsv(data_collection)
                    MLTrainer()
                    pygame.quit()
                    sys.exit()


# Generate obstacles for the game
obstacles = generateObstacles()
drawGrid()
selected_color = displayStartScreen()
snake_color = AVAILABLE_COLORS[selected_color]
snake = Snake(snake_color)
food = Food()
power_up = PowerUp(-999)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            saveDataToCsv(data_collection)
            MLTrainer()
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            # Handle snake direction changes
            if event.key == pygame.K_LEFT and snake.xdirection == 0:
                snake.ydirection = 0
                snake.xdirection = -1
            elif event.key == pygame.K_RIGHT and snake.xdirection == 0:
                snake.ydirection = 0
                snake.xdirection = 1
            elif event.key == pygame.K_UP and snake.ydirection == 0:
                snake.ydirection = -1
                snake.xdirection = 0
            elif event.key == pygame.K_DOWN and snake.ydirection == 0:
                snake.ydirection = 1
                snake.xdirection = 0

    # Update the snake and check for game over
    if snake.update():
        displayGameOverScreen(len(snake.body) - 1)
        snake.color = selected_color
        snake.reset()
        food = Food()
        power_up = PowerUp(-999)

    screen.fill('Black')
    drawGrid()
    food.update()
    power_up.update()

    for obstacle in obstacles:
        obstacle.update()

    # Draw the snake
    pygame.draw.rect(screen, snake.color, snake.head)

    for square in snake.body:
        pygame.draw.rect(screen, snake.color, square)

    last_collected = -999
    # Check for power-up collision
    if snake.head.colliderect(power_up.rect):
        last_collected = power_up.apply_power_up(snake)
        power_up = PowerUp(last_collected)

    score = FONT.render(f"Score: {len(snake.body) - 1}", True, 'White')
    screen.blit(score, (50, 10))

    # Check for food collision
    if snake.head.colliderect(food.rect):
        snake.body.append(pygame.Rect(square.x, square.y, BLOCK_SIZE, BLOCK_SIZE))
        food = Food()

    feedback = getAIFeedback(snake)
    feedback_message = FONT.render(f"AI Coach: {feedback}", True, 'Red' if feedback else 'White')
    screen.blit(feedback_message, (200, 10))

    pygame.display.update()
    clock.tick(5)  # Control game speed
