import json
import os
import sys
import math
from random import randint, random
from typing import List, Tuple, Optional

import pygame as pg

# Инициализация PyGame
pg.init()
pg.font.init()

# --- КОНСТАНТЫ И НАСТРОЙКИ ---
SCREEN_WIDTH, SCREEN_HEIGHT = 960, 720
GRID_SIZE = 24
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE
SCREEN_CENTER = (
    (GRID_WIDTH // 2) * GRID_SIZE,
    (GRID_HEIGHT // 2) * GRID_SIZE
)

# Направления движения
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
OPPOSITE_DIRECTIONS = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}

# Цвета в стиле Dungeon
BG_TILE_1 = (35, 35, 35)
BG_TILE_2 = (25, 25, 25)
SNAKE_HEAD_COLOR = (50, 205, 50)
SNAKE_BODY_COLOR = (34, 139, 34)
APPLE_COLOR = (220, 20, 60)
GOLD_COLOR = (255, 215, 0)
POISON_COLOR = (148, 0, 211)
GHOST_COLOR = (0, 255, 255)
WALL_COLOR = (105, 105, 105)
PORTAL_1_COLOR = (30, 144, 255)
PORTAL_2_COLOR = (255, 140, 0)
TEXT_NORMAL = (200, 200, 200)
TEXT_ACTIVE = (0, 255, 100)

# Ретро-шрифты
FONT_XS = pg.font.SysFont('Courier New', 18, bold=True)
FONT_SM = pg.font.SysFont('Courier New', 24, bold=True)
FONT_MD = pg.font.SysFont('Courier New', 36, bold=True)
FONT_LG = pg.font.SysFont('Courier New', 56, bold=True)

HIGH_SCORE_FILE = os.path.join(os.path.dirname(__file__), 'highscore.json')


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (ПИКСЕЛЬ-АРТ) ---
def draw_block(surface, color, rect):
    """Рисует 3D-куб в стиле Minecraft."""
    pg.draw.rect(surface, color, rect)
    light = (min(255, color[0]+50), min(255, color[1]+50), min(255, color[2]+50))
    dark = (max(0, color[0]-50), max(0, color[1]-50), max(0, color[2]-50))

    pg.draw.line(surface, light, rect.topleft, rect.topright, 2)
    pg.draw.line(surface, light, rect.topleft, rect.bottomleft, 2)
    pg.draw.line(surface, dark, rect.bottomleft, rect.bottomright, 2)
    pg.draw.line(surface, dark, rect.topright, rect.bottomright, 2)


def draw_icon(surface, item_type, x, y):
    """Рисует иконку предмета для легенды и игры."""
    rect = pg.Rect(x + 2, y + 2, GRID_SIZE - 4, GRID_SIZE - 4)
    if item_type == 'apple':
        draw_block(surface, APPLE_COLOR, rect)
        pg.draw.rect(surface, (0, 255, 0), (x + GRID_SIZE//2 - 2, y, 4, 6))
    elif item_type == 'golden':
        draw_block(surface, GOLD_COLOR, rect)
        pg.draw.rect(surface, (255, 255, 255), (x + 6, y + 6, 4, 4))
    elif item_type == 'poison':
        draw_block(surface, POISON_COLOR, rect)
        pg.draw.rect(surface, (0, 0, 0), (x + 8, y + 8, GRID_SIZE-16, GRID_SIZE-16))
    elif item_type == 'ghost':
        rect1 = pg.Rect(x + 4, y + 8, 8, 8)
        rect2 = pg.Rect(x + 12, y + 8, 8, 8)
        draw_block(surface, (255, 255, 255), rect1)
        draw_block(surface, GHOST_COLOR, rect2)
    elif item_type == 'wall':
        draw_block(surface, WALL_COLOR, pg.Rect(x, y, GRID_SIZE, GRID_SIZE))
    elif item_type == 'portal':
        pg.draw.rect(surface, PORTAL_1_COLOR, (x+2, y+2, GRID_SIZE-4, GRID_SIZE-4), 3)
        pg.draw.rect(surface, (255, 255, 255), (x+8, y+8, GRID_SIZE-16, GRID_SIZE-16))


# --- СИСТЕМА ЧАСТИЦ ---
class Particle:
    def __init__(self, pos, color):
        self.x = pos[0] + GRID_SIZE // 2
        self.y = pos[1] + GRID_SIZE // 2
        angle = random() * math.pi * 2
        speed = random() * 4 + 2
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = 255
        self.color = color
        self.size = randint(3, 6)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 15

    def draw(self, surface):
        if self.life > 0:
            rect = pg.Rect(int(self.x), int(self.y), self.size, self.size)
            pg.draw.rect(surface, self.color, rect)


# --- ИГРОВЫЕ ОБЪЕКТЫ ---
class Item:
    def __init__(self, color, duration=0, item_type='apple'):
        self.color = color
        self.position = (-100, -100)
        self.active = False
        self.timer = duration
        self.max_duration = duration
        self.item_type = item_type

    def spawn(self, occupied):
        self.active = True
        self.timer = self.max_duration
        while True:
            pos = (randint(0, GRID_WIDTH - 1) * GRID_SIZE, randint(0, GRID_HEIGHT - 1) * GRID_SIZE)
            if pos not in occupied:
                self.position = pos
                break

    def update(self):
        if self.active and self.max_duration > 0:
            self.timer -= 1
            if self.timer <= 0:
                self.active = False

    def draw(self, surface):
        if not self.active: return
        if self.max_duration > 0 and self.timer < 30 and self.timer % 4 < 2: return
        draw_icon(surface, self.item_type, self.position[0], self.position[1])


class Snake:
    def __init__(self):
        self.reset()

    def update_direction(self, next_dir):
        last_dir = self.dir_queue[-1] if self.dir_queue else self.direction
        if next_dir != last_dir and next_dir != OPPOSITE_DIRECTIONS.get(last_dir):
            if len(self.dir_queue) < 2:
                self.dir_queue.append(next_dir)

    def move(self):
        if self.dir_queue:
            self.direction = self.dir_queue.pop(0)

        hx, hy = self.positions[0]
        sx, sy = self.direction
        new_head = ((hx + sx * GRID_SIZE) % SCREEN_WIDTH, (hy + sy * GRID_SIZE) % SCREEN_HEIGHT)

        self.positions.insert(0, new_head)
        if len(self.positions) > self.length:
            self.positions.pop()

    def draw(self, surface):
        body_color = SNAKE_BODY_COLOR if not self.is_ghost else (100, 200, 200)
        head_color = SNAKE_HEAD_COLOR if not self.is_ghost else (200, 255, 255)

        for pos in self.positions[1:]:
            rect = pg.Rect(pos[0]+1, pos[1]+1, GRID_SIZE-2, GRID_SIZE-2)
            draw_block(surface, body_color, rect)

        hx, hy = self.positions[0]
        rect = pg.Rect(hx+1, hy+1, GRID_SIZE-2, GRID_SIZE-2)
        draw_block(surface, head_color, rect)

        off1, off2 = (0, 0), (0, 0)
        if self.direction == UP: off1, off2 = (4, 4), (16, 4)
        elif self.direction == DOWN: off1, off2 = (4, 16), (16, 16)
        elif self.direction == LEFT: off1, off2 = (4, 4), (4, 16)
        elif self.direction == RIGHT: off1, off2 = (16, 4), (16, 16)

        pg.draw.rect(surface, (0, 0, 0), (hx + off1[0], hy + off1[1], 4, 4))
        pg.draw.rect(surface, (0, 0, 0), (hx + off2[0], hy + off2[1], 4, 4))

    def reset(self):
        self.length = 3
        self.positions = [SCREEN_CENTER, (SCREEN_CENTER[0]-GRID_SIZE, SCREEN_CENTER[1]), (SCREEN_CENTER[0]-GRID_SIZE*2, SCREEN_CENTER[1])]
        self.direction = RIGHT
        self.dir_queue = []
        self.is_ghost = False
        self.ghost_timer = 0


# --- МЕНЕДЖЕР ИГРЫ ---
class GameManager:
    def __init__(self):
        self.display = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.canvas = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        pg.display.set_caption('Snake: Dungeon Edition')
        self.clock = pg.time.Clock()

        self.state = 'MENU'
        self.menu_index = 0       # 0: Старт, 1: Настройки, 2: Выход
        self.pause_index = 0      # 0: Продолжить, 1: Главное меню

        # Настройки
        self.settings_index = 0   # 0: Скорость, 1: Сложность, 2: Назад
        self.speed_options = list(range(5, 26)) # От 5 до 25 включительно
        self.curr_speed_idx = 7   # По умолчанию 12 (индекс 7)
        self.diff_options = [1, 2, 3, 4]
        self.curr_diff_idx = 2    # По умолчанию 3

        self.high_score = self.load_score()
        self.particles = []
        self.shake_timer = 0
        self.portal_timer = 0

        self.generate_dungeon_bg()
        self.reset_game()

    def generate_dungeon_bg(self):
        self.bg_surface = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                color = BG_TILE_1 if (x + y) % 2 == 0 else BG_TILE_2
                rect = pg.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                pg.draw.rect(self.bg_surface, color, rect)
                pg.draw.line(self.bg_surface, (20,20,20), rect.topleft, rect.bottomleft)
                pg.draw.line(self.bg_surface, (20,20,20), rect.topleft, rect.topright)

    def load_score(self):
        try:
            with open(HIGH_SCORE_FILE, 'r') as f: return json.load(f).get('best', 0)
        except: return 0

    def save_score(self):
        with open(HIGH_SCORE_FILE, 'w') as f: json.dump({'best': self.high_score}, f)

    def reset_game(self):
        self.score = 0
        self.level = 0
        self.snake = Snake()
        self.apple = Item(APPLE_COLOR, item_type='apple')
        self.apple.spawn(self.snake.positions)
        self.golden = Item(GOLD_COLOR, duration=60, item_type='golden')
        self.poison = Item(POISON_COLOR, duration=80, item_type='poison')
        self.ghost_pill = Item(GHOST_COLOR, duration=100, item_type='ghost')
        self.walls = set()
        self.portals = []

    def generate_level(self):
        diff = self.diff_options[self.curr_diff_idx]
        if diff >= 3:
            new_level = self.score // 10
            if new_level > self.level and new_level <= 5:
                self.level = new_level
                self.walls.clear()
                self.portals.clear()

                px1 = (randint(2, GRID_WIDTH-3)*GRID_SIZE, randint(2, GRID_HEIGHT-3)*GRID_SIZE)
                px2 = (randint(2, GRID_WIDTH-3)*GRID_SIZE, randint(2, GRID_HEIGHT-3)*GRID_SIZE)
                self.portals = [px1, px2]

                for _ in range(self.level * 10):
                    wx = randint(0, GRID_WIDTH-1) * GRID_SIZE
                    wy = randint(0, GRID_HEIGHT-1) * GRID_SIZE
                    if abs(wx - SCREEN_CENTER[0]) > 100 and abs(wy - SCREEN_CENTER[1]) > 100:
                        self.walls.add((wx, wy))

    def spawn_particles(self, pos, color, count=15):
        for _ in range(count):
            self.particles.append(Particle(pos, color))

    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit(); sys.exit()

            if event.type == pg.KEYDOWN:
                # --- ГЛАВНОЕ МЕНЮ ---
                if self.state == 'MENU':
                    if event.key == pg.K_UP:
                        self.menu_index = (self.menu_index - 1) % 3
                    elif event.key == pg.K_DOWN:
                        self.menu_index = (self.menu_index + 1) % 3
                    elif event.key in (pg.K_RETURN, pg.K_SPACE):
                        if self.menu_index == 0:
                            self.state = 'TUTORIAL' # Переход к правилам
                        elif self.menu_index == 1:
                            self.state = 'SETTINGS'
                        elif self.menu_index == 2:
                            pg.quit(); sys.exit()

                # --- ЭКРАН ПРАВИЛ ---
                elif self.state == 'TUTORIAL':
                    if event.key in (pg.K_SPACE, pg.K_RETURN, pg.K_ESCAPE):
                        self.reset_game()
                        self.state = 'PLAYING'

                # --- МЕНЮ НАСТРОЕК ---
                elif self.state == 'SETTINGS':
                    if event.key == pg.K_UP:
                        self.settings_index = (self.settings_index - 1) % 3
                    elif event.key == pg.K_DOWN:
                        self.settings_index = (self.settings_index + 1) % 3

                    elif event.key == pg.K_LEFT:
                        if self.settings_index == 0:
                            self.curr_speed_idx = (self.curr_speed_idx - 1) % len(self.speed_options)
                        elif self.settings_index == 1:
                            self.curr_diff_idx = (self.curr_diff_idx - 1) % len(self.diff_options)

                    elif event.key == pg.K_RIGHT:
                        if self.settings_index == 0:
                            self.curr_speed_idx = (self.curr_speed_idx + 1) % len(self.speed_options)
                        elif self.settings_index == 1:
                            self.curr_diff_idx = (self.curr_diff_idx + 1) % len(self.diff_options)

                    elif event.key in (pg.K_RETURN, pg.K_SPACE, pg.K_ESCAPE):
                        if self.settings_index == 2 or event.key == pg.K_ESCAPE:
                            self.state = 'MENU'

                # --- ИГРА ---
                elif self.state == 'PLAYING':
                    if event.key in (pg.K_ESCAPE, pg.K_SPACE):
                        self.state = 'PAUSED'
                        self.pause_index = 0
                    elif event.key == pg.K_UP: self.snake.update_direction(UP)
                    elif event.key == pg.K_DOWN: self.snake.update_direction(DOWN)
                    elif event.key == pg.K_LEFT: self.snake.update_direction(LEFT)
                    elif event.key == pg.K_RIGHT: self.snake.update_direction(RIGHT)

                # --- ПАУЗА ---
                elif self.state == 'PAUSED':
                    if event.key == pg.K_UP:
                        self.pause_index = (self.pause_index - 1) % 2
                    elif event.key == pg.K_DOWN:
                        self.pause_index = (self.pause_index + 1) % 2
                    elif event.key in (pg.K_RETURN, pg.K_SPACE):
                        if self.pause_index == 0:
                            self.state = 'PLAYING'
                        else:
                            self.state = 'MENU'
                    elif event.key == pg.K_ESCAPE:
                        self.state = 'PLAYING'

                # --- GAME OVER ---
                elif self.state == 'GAME_OVER':
                    if event.key == pg.K_SPACE:
                        self.reset_game()
                        self.state = 'PLAYING'
                    elif event.key == pg.K_ESCAPE:
                        self.state = 'MENU'

    def update(self):
        if self.state != 'PLAYING': return

        self.golden.update()
        self.poison.update()
        self.ghost_pill.update()
        self.portal_timer += 1

        if self.snake.is_ghost:
            self.snake.ghost_timer -= 1
            if self.snake.ghost_timer <= 0:
                self.snake.is_ghost = False

        self.snake.move()
        head = self.snake.positions[0]
        occupied = self.snake.positions + list(self.walls) + self.portals
        diff = self.diff_options[self.curr_diff_idx]

        # 1. Сбор яблока
        if head == self.apple.position:
            self.snake.length += 1
            self.score += 1
            self.apple.spawn(occupied)
            self.spawn_particles(self.apple.position, APPLE_COLOR)

            if diff >= 3: self.generate_level()

            # Спавн лута в зависимости от сложности
            if diff >= 3:
                if not self.golden.active and random() < 0.15: self.golden.spawn(occupied)
                if not self.ghost_pill.active and random() < 0.05: self.ghost_pill.spawn(occupied)
            if diff >= 2:
                if not self.poison.active and random() < 0.1: self.poison.spawn(occupied)

        # 2. Золотое яблоко
        if self.golden.active and head == self.golden.position:
            self.snake.length += 2
            self.score += 3
            self.golden.active = False
            self.shake_timer = 10
            self.spawn_particles(head, GOLD_COLOR, 30)

        # 3. Яд
        if self.poison.active and head == self.poison.position:
            self.snake.length = max(3, self.snake.length - 1)
            self.poison.active = False
            self.spawn_particles(head, POISON_COLOR)

        # 4. Призрак
        if self.ghost_pill.active and head == self.ghost_pill.position:
            self.snake.is_ghost = True
            self.snake.ghost_timer = 100
            self.ghost_pill.active = False
            self.spawn_particles(head, GHOST_COLOR)

        # 5. Порталы
        if self.portals:
            if head == self.portals[0]:
                self.snake.positions[0] = self.portals[1]
                self.spawn_particles(self.portals[0], PORTAL_1_COLOR)
            elif head == self.portals[1]:
                self.snake.positions[0] = self.portals[0]
                self.spawn_particles(self.portals[1], PORTAL_2_COLOR)

        # 6. Смерть
        hit_wall = head in self.walls
        hit_tail = head in self.snake.positions[1:] and not self.snake.is_ghost

        if hit_wall or hit_tail:
            self.state = 'GAME_OVER'
            self.shake_timer = 20
            if self.score > self.high_score:
                self.high_score = self.score
                self.save_score()

    def draw(self):
        # Отрисовка фона и объектов игры
        self.canvas.blit(self.bg_surface, (0, 0))
        for wall in self.walls:
            rect = pg.Rect(wall, (GRID_SIZE, GRID_SIZE))
            draw_block(self.canvas, WALL_COLOR, rect)

        if self.portals:
            for i, p in enumerate(self.portals):
                color = PORTAL_1_COLOR if i == 0 else PORTAL_2_COLOR
                cx, cy = p[0], p[1]
                offset = (self.portal_timer // 2) % 4
                pg.draw.rect(self.canvas, color, (cx + offset, cy + offset, GRID_SIZE - offset*2, GRID_SIZE - offset*2), 3)
                pg.draw.rect(self.canvas, (255, 255, 255), (cx + 8, cy + 8, GRID_SIZE - 16, GRID_SIZE - 16))

        self.apple.draw(self.canvas)
        self.golden.draw(self.canvas)
        self.poison.draw(self.canvas)
        self.ghost_pill.draw(self.canvas)
        self.snake.draw(self.canvas)

        for p in self.particles[:]:
            p.update()
            p.draw(self.canvas)
            if p.life <= 0: self.particles.remove(p)

        # Игровой UI
        if self.state in ['PLAYING', 'PAUSED']:
            score_t = FONT_SM.render(f'СЧЕТ: {self.score}', True, (255,255,255))
            hi_t = FONT_SM.render(f'РЕКОРД: {self.high_score}', True, GOLD_COLOR)
            lvl_t = FONT_SM.render(f'СЛОЖНОСТЬ: {self.diff_options[self.curr_diff_idx]}', True, (150,150,150))
            self.canvas.blit(score_t, (20, 20))
            self.canvas.blit(hi_t, (SCREEN_WIDTH - hi_t.get_width() - 20, 20))
            self.canvas.blit(lvl_t, (SCREEN_WIDTH//2 - lvl_t.get_width()//2, 20))

        # ОВЕРЛЕИ И МЕНЮ
        if self.state != 'PLAYING':
            dark = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SRCALPHA)
            dark.fill((0, 0, 0, 200))
            self.canvas.blit(dark, (0, 0))

            cx = SCREEN_WIDTH // 2

            if self.state == 'MENU':
                title = FONT_LG.render('SNAKE: DUNGEON', True, SNAKE_HEAD_COLOR)
                self.canvas.blit(title, (cx - title.get_width()//2, 200))

                menu_items = ['ИГРАТЬ', 'НАСТРОЙКИ', 'ВЫХОД']
                for i, item in enumerate(menu_items):
                    color = TEXT_ACTIVE if i == self.menu_index else TEXT_NORMAL
                    prefix = "> " if i == self.menu_index else "  "
                    text = FONT_MD.render(f'{prefix}{item}', True, color)
                    self.canvas.blit(text, (cx - 100, 350 + i * 50))

            elif self.state == 'TUTORIAL':
                title = FONT_MD.render('ПРАВИЛА И БОНУСЫ', True, GOLD_COLOR)
                self.canvas.blit(title, (cx - title.get_width()//2, 100))

                rules = [
                    ('apple', 'ОБЫЧНОЕ ЯБЛОКО: +1 очко и +1 длина.'),
                    ('poison', 'ЯД (СЛОЖНОСТЬ 2+): отнимает 1 блок длины.'),
                    ('golden', 'ЗОЛОТО (СЛОЖНОСТЬ 3+): +3 очка, исчезает.'),
                    ('ghost', 'ПИЛЮЛЯ (СЛОЖНОСТЬ 3+): проход сквозь себя.'),
                    ('wall', 'СТЕНА (СЛОЖНОСТЬ 3+): верная смерть.'),
                    ('portal', 'ПОРТАЛ (СЛОЖНОСТЬ 3+): телепорт в другую точку.')
                ]

                for i, (icon, text) in enumerate(rules):
                    draw_icon(self.canvas, icon, cx - 350, 180 + i * 60)
                    t_surf = FONT_SM.render(text, True, (220, 220, 220))
                    self.canvas.blit(t_surf, (cx - 310, 180 + i * 60))

                sub = FONT_SM.render('НАЖМИ [ПРОБЕЛ] ДЛЯ СТАРТА', True, TEXT_ACTIVE)
                self.canvas.blit(sub, (cx - sub.get_width()//2, 600))

            elif self.state == 'SETTINGS':
                title = FONT_LG.render('НАСТРОЙКИ', True, SNAKE_HEAD_COLOR)
                self.canvas.blit(title, (cx - title.get_width()//2, 150))

                s_val = self.speed_options[self.curr_speed_idx]
                d_val = self.diff_options[self.curr_diff_idx]

                menu_items = [
                    f'СКОРОСТЬ: < {s_val:02d} >',
                    f'СЛОЖНОСТЬ: < {d_val} >',
                    '[ НАЗАД ]'
                ]
                for i, item in enumerate(menu_items):
                    color = TEXT_ACTIVE if i == self.settings_index else TEXT_NORMAL
                    text = FONT_MD.render(item, True, color)
                    self.canvas.blit(text, (cx - text.get_width()//2, 300 + i * 60))

                diff_desc = [
                    "УР. 1: СПОКОЙНАЯ ИГРА. ТОЛЬКО ЯБЛОКА.",
                    "УР. 2: ОПАСНОСТЬ. ПОЯВЛЯЕТСЯ ЯД.",
                    "УР. 3: ПОЛНЫЙ НАБОР. СТЕНЫ, ЗЕЛЬЯ, БОНУСЫ.",
                    "УР. 4: ХАРДКОР. ПОЛНЫЙ НАБОР + УСКОРЕНИЕ."
                ]
                desc_text = FONT_SM.render(diff_desc[self.curr_diff_idx], True, GOLD_COLOR)
                self.canvas.blit(desc_text, (cx - desc_text.get_width()//2, 550))

            elif self.state == 'PAUSED':
                title = FONT_LG.render('ПАУЗА', True, (255, 255, 255))
                self.canvas.blit(title, (cx - title.get_width()//2, 250))

                pause_items = ['ПРОДОЛЖИТЬ', 'ГЛАВНОЕ МЕНЮ']
                for i, item in enumerate(pause_items):
                    color = TEXT_ACTIVE if i == self.pause_index else TEXT_NORMAL
                    prefix = "> " if i == self.pause_index else "  "
                    text = FONT_MD.render(f'{prefix}{item}', True, color)
                    self.canvas.blit(text, (cx - 150, 380 + i * 50))

            elif self.state == 'GAME_OVER':
                title = FONT_LG.render('ПОТРАЧЕНО', True, APPLE_COLOR)
                score_text = FONT_MD.render(f'СЧЕТ: {self.score}', True, (255, 255, 255))
                sub = FONT_SM.render('[ПРОБЕЛ] - РЕСТАРТ   [ESC] - МЕНЮ', True, (150, 150, 150))

                self.canvas.blit(title, (cx - title.get_width()//2, 280))
                self.canvas.blit(score_text, (cx - score_text.get_width()//2, 360))
                self.canvas.blit(sub, (cx - sub.get_width()//2, 450))

        # Тряска экрана
        render_offset = (0, 0)
        if self.shake_timer > 0:
            self.shake_timer -= 1
            render_offset = (randint(-6, 6), randint(-6, 6))

        self.display.blit(self.canvas, render_offset)
        pg.display.update()

    def run(self):
        while True:
            base_speed = self.speed_options[self.curr_speed_idx]
            diff = self.diff_options[self.curr_diff_idx]

            if self.state == 'PLAYING' and diff == 4:
                current_speed = min(base_speed + (self.score // 5), base_speed + 10)
            else:
                current_speed = base_speed

            self.clock.tick(current_speed)
            self.handle_events()
            self.update()
            self.draw()


if __name__ == '__main__':
    game = GameManager()
    game.run()
