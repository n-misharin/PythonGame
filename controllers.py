import pygame
from game import Game, Unit, Field, Board
from pygame.sprite import Group, Sprite
from pygame.rect import Rect
from texture_loader import GROUNDS_TEXTURES, WORKERS_TEXTURES

DISPLAY_SIZE = DISPLAY_WIDTH, DISPLAY_HEIGHT = 1152, 864


def is_point_in_rect(point: [int, int], rect: Rect):
    return rect.x <= point[0] <= rect.x + rect.width and rect.y <= point[1] <= rect.y + rect.height


class LayerSprite(Sprite):
    def __init__(self, layer_num):
        super().__init__()
        self.layer_num = layer_num


class AnimatedSprite(LayerSprite):
    FRAME_DURATION = 0.1

    def __init__(self, layer_num, frames):
        super().__init__(layer_num)
        self.animation_delta = 1
        self.frames = frames
        self.cur_frame_time = 0
        self.cur_frame_x = 0
        self.cur_frame_y = 0
        self.image = self.frames[self.cur_frame_y][self.cur_frame_y]

    def update(self, delta_time=0, camera=None, key_controller=None):
        self.cur_frame_time += delta_time
        if self.cur_frame_time >= self.FRAME_DURATION:
            self.cur_frame_time = 0
            self.cur_frame_x = (self.cur_frame_x + self.animation_delta) % len(self.frames[self.cur_frame_y])
            self.image = self.frames[self.cur_frame_y][self.cur_frame_x]

    def set_frame_y(self, y):
        self.cur_frame_y = y
        self.cur_frame_x = 0


class UnitSprite(AnimatedSprite):
    ANIMATION_WORK = 0
    ANIMATION_STAY = 1
    ANIMATION_MOVE = 2

    def __init__(self, player_num, unit: Unit, pos):
        self.unit = unit
        super().__init__(GameLayerController.UNIT_LAYER,
                         WORKERS_TEXTURES[player_num].copy())
        self.rect = Rect(pos, (64, 64))
        self.is_selected = True
        self.set_animation(self.ANIMATION_MOVE)

    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)

    def set_animation(self, animation_line: int = ANIMATION_STAY):
        if animation_line == self.ANIMATION_MOVE:
            self.animation_delta = -1
        else:
            self.animation_delta = 1
        animation_line += len(self.frames) // 2 if self.is_selected else 0
        self.set_frame_y(animation_line)


class FieldSprite(LayerSprite):
    def __init__(self, field: Field, pos):
        super().__init__(GameLayerController.GROUND_LAYER)
        self.field = field
        self.image = GROUNDS_TEXTURES[self.field.type].copy()
        self.rect = Rect(pos, (94, 94))

    def update(self, *args, **kwargs):
        # self.image = GROUNDS_TEXTURES[self.field.type].copy()
        super().update(*args, **kwargs)


class LayerController:
    def __init__(self):
        self.layers = []

    def add_sprite(self, sprite: LayerSprite):
        if sprite.layer_num < 0 or len(self.layers) <= sprite.layer_num:
            raise Exception('Недопустимый номер слоя')
        self.layers[sprite.layer_num].add(sprite)

    def add_layer(self):
        self.layers.append(Group())

    def get_layer_num(self, sprite: LayerSprite):
        for i in range(len(self.layers)):
            if sprite in self.layers[i]:
                return i
        return None

    def update(self, *args, **kwargs):
        for i in range(len(self.layers) - 1, -1, -1):
            self.layers[i].update(*args, **kwargs)

    def draw(self, surface):
        for group in self.layers:
            group.draw(surface)


class GameLayerController(LayerController):
    GROUND_LAYER = 0
    GROUND_UNDER_LAYER = 1
    UNIT_UNDER_LAYER = 2
    UNIT_LAYER = 3
    UNIT_ABOVE_LAYER = 4
    GUI_LAYER = 5

    def __init__(self):
        super().__init__()
        [self.add_layer() for _ in range(6)]


class KeyController:
    def __init__(self):
        self.is_mouse_down = False
        self.mouse_down_button = None
        self.mouse_down_pos = None
        self.mouse_pos = None

        self.is_key_pressed = False
        self.last_pressed_key = None

        self.is_drag = False
        self.is_quit = False

    def update(self, *args, **kwargs):
        self.is_key_pressed = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_quit = True

            if event.type == pygame.KEYDOWN:
                self.last_pressed_key = event.key
                self.is_key_pressed = True

            if event.type == pygame.MOUSEBUTTONDOWN:
                self.is_mouse_down = True
                self.mouse_down_pos = event.pos

            if event.type == pygame.MOUSEBUTTONUP:
                self.is_mouse_down = False
                self.mouse_down_button = event.button

            if event.type == pygame.MOUSEMOTION:
                self.mouse_pos = event.pos

    def is_click_on(self, sprite: LayerSprite):
        return self.is_mouse_down and self.mouse_down_button == pygame.BUTTON_LEFT and \
               is_point_in_rect(self.mouse_pos, sprite.rect)

    def is_drag(self):
        return self.is_mouse_down and self.mouse_down_button == pygame.BUTTON_RIGHT

    def __str__(self):
        return [(k.__str__(), v.__str__()) for k, v in self.__dict__.items()]


class Scene:
    def __init__(self, layer_controller: LayerController):
        self.layer_controller = layer_controller

    def add(self, sprite):
        self.layer_controller.add_sprite(sprite)

    def draw(self, screen):
        self.layer_controller.draw(screen)

    def update(self, *args, **kwargs):
        self.layer_controller.update(*args, **kwargs)


class GameScene(Scene):
    def __init__(self, layer_controller: GameLayerController, game: Game):
        super().__init__(layer_controller)
        board = game.get_board()
        for y in range(board.size[1]):
            for x in range(board.size[0]):
                field = board.get_field((x, y))
                field_pos = (x * 94, y * 94)
                sprite = FieldSprite(field, field_pos)
                self.add(sprite)
                k = 0
                for unit in field.units:
                    unit_sprite = UnitSprite(
                        game.get_player_num(unit.player),
                        unit,
                        (field_pos[0] + 20, field_pos[1] + 30 * (k - 1)))
                    self.add(unit_sprite)
                    k += 1


class Display:
    def __init__(self, display_size=DISPLAY_SIZE, scenes=None):
        self.display_size = display_size
        self.screen = pygame.display.set_mode(self.display_size)
        self.scenes = scenes if scenes is not None else []
        self.cur_scene_num = 0
        self.running = True
        self.key_controller = KeyController()

    def draw(self):
        self.scenes[self.cur_scene_num].draw(self.screen)

    def update(self, *args, **kwargs):
        self.key_controller.update(*args, **kwargs)
        self.scenes[self.cur_scene_num].update(*args, **kwargs)

    def flip(self):
        pygame.display.flip()

    def quit(self):
        pygame.display.quit()

    def __call__(self, *args, **kwargs):
        return self.screen


pygame.init()

display = Display(
    scenes=[
        GameScene(layer_controller=GameLayerController(),
                  game=Game(['Вася', 'Петя', 'John']))
    ])

clock = pygame.time.Clock()

while not display.key_controller.is_quit:
    delta_time = clock.tick(60) / 1000

    display.update(delta_time=delta_time)
    display.draw()
    display.flip()
display.quit()

