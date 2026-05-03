from random import randint

import pygame as pg

# Инициализация PyGame:
pg.init()

# Константы для размеров поля и сетки:
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE
SCREEN_CENTER = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

# Направления движения:
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# Блок цветов
BOARD_BACKGROUND_COLOR = (0, 0, 0)
BORDER_COLOR = (93, 216, 228)
APPLE_COLOR = (255, 0, 0)
SNAKE_COLOR = (0, 255, 0)

# Словарь возможных направлений.
DIRECTIONS = {
    (LEFT, pg.K_UP): UP,
    (RIGHT, pg.K_UP): UP,
    (LEFT, pg.K_DOWN): DOWN,
    (RIGHT, pg.K_DOWN): DOWN,
    (UP, pg.K_LEFT): LEFT,
    (DOWN, pg.K_LEFT): LEFT,
    (UP, pg.K_RIGHT): RIGHT,
    (DOWN, pg.K_RIGHT): RIGHT,
}

# Скорость движения змейки:
SPEED = 10

# Настройка игрового окна:
screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)

# Заголовок окна игрового поля:
pg.display.set_caption('Змейка')

# Настройка времени:
clock = pg.time.Clock()


class GameObject:
    """Базовый класс для всех игровых объектов."""

    def __init__(self, body_color=SNAKE_COLOR):
        self.position = SCREEN_CENTER
        self.body_color = body_color

    def draw_cell(self, position, color=None, border_color=BORDER_COLOR):
        if color is None:
            color = self.body_color
        rect = pg.Rect(position, (GRID_SIZE, GRID_SIZE))
        pg.draw.rect(screen, color, rect)
        pg.draw.rect(screen, border_color, rect, 1)

    def draw(self):
        """Определяет метод отрисовки для подклассов."""
        raise NotImplementedError('Метод draw должен быть переопределен')


class Apple(GameObject):
    """Класс, описывающий яблоко и логику его появления."""

    def __init__(self, occupied_slots=None):
        """Инициализирует яблоко и задает случайную позицию."""
        super().__init__(APPLE_COLOR)
        if occupied_slots is None:
            occupied_slots = [SCREEN_CENTER]
        self.randomize_position(occupied_slots)

    def randomize_position(self, occupied_slots):
        """Установить случайное положение яблока на свободном игровом поле."""
        while True:
            x = randint(0, GRID_WIDTH - 1) * GRID_SIZE
            y = randint(0, GRID_HEIGHT - 1) * GRID_SIZE
            new_pos = (x, y)
            if new_pos not in occupied_slots:
                self.position = new_pos
                break

    def draw(self):
        """Отрисовать яблоко на игровом экране."""
        self.draw_cell(self.position)


class Snake(GameObject):
    """Класс описывающий змейку и ее движения."""

    def __init__(self):
        super().__init__(SNAKE_COLOR)
        self.reset()

    def update_direction(self, new_direction):
        """Обновляет направление движения змейки."""
        self.direction = new_direction

    def get_head_position(self):
        """Возвращает позицию головы змейки."""
        return self.positions[0]

    def move(self):
        """Обновить позицию змейки, добавив новую голову и удалив хвост."""
        head_x, head_y = self.get_head_position()
        step_x, step_y = self.direction
        new_x = (head_x + step_x * GRID_SIZE) % SCREEN_WIDTH
        new_y = (head_y + step_y * GRID_SIZE) % SCREEN_HEIGHT
        new_head = (new_x, new_y)

        if new_head in self.positions:
            self.reset()
        else:
            self.positions.insert(0, new_head)
            if len(self.positions) > self.length:
                self.last = self.positions.pop()
            else:
                self.last = None

    def draw(self):
        """Отрисовать змейку на экране, обновляя только голову и хвост."""
        if self.last:
            self.draw_cell(
                self.last,
                BOARD_BACKGROUND_COLOR,
                BOARD_BACKGROUND_COLOR
            )
        self.draw_cell(self.positions[0])

    def reset(self):
        """Сбрасывает змейку в начальное положение."""
        self.length = 1
        self.positions = [SCREEN_CENTER]
        self.direction = RIGHT
        self.next_direction = None
        self.last = None
        screen.fill(BOARD_BACKGROUND_COLOR)


def handle_keys(snake):
    """Обработка действий пользователя."""
    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.quit()
            raise SystemExit
        if event.type == pg.KEYDOWN:
            new_direction = DIRECTIONS.get((snake.direction, event.key))
            if new_direction:
                snake.update_direction(new_direction)


def main():
    """Запустить основной игровой цикл."""
    snake = Snake()
    apple = Apple(snake.positions)
    screen.fill(BOARD_BACKGROUND_COLOR)

    while True:
        clock.tick(SPEED)
        handle_keys(snake)
        snake.move()

        if snake.get_head_position() == apple.position:
            snake.length += 1
            apple.randomize_position(snake.positions)
        elif snake.get_head_position() in snake.positions[1:]:
            snake.reset()

        apple.draw()
        snake.draw()
        pg.display.update()


if __name__ == '__main__':
    main()
