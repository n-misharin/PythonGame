import pygame
from game import Game, Unit, Field, Board, ResourcesTypes, get_dist
from pygame.sprite import Group, Sprite
from pygame.rect import Rect
from texture_loader import GROUNDS_TEXTURES, WORKERS_TEXTURES, CURSOR_TEXTURES

DISPLAY_SIZE = DISPLAY_WIDTH, DISPLAY_HEIGHT = 1280, 720
PLAYERS_NAMES = ['Игрок1', 'Игрок2', 'Игрок3', 'Игрок4']


def is_point_in_rect(point: [int, int], rect: Rect):
    return rect.x <= point[0] <= rect.x + rect.width and rect.y <= point[1] <= rect.y + rect.height


class LayerSprite(Sprite):
    def __init__(self, layer_num):
        super().__init__()
        self.layer_num = layer_num
        self.is_selected = False
        self.is_dragable = True

    def update(self, *args, **kwargs):
        if self.is_dragable:
            camera = kwargs['camera']
            camera.apply(self.rect)
        super().update(*args, **kwargs)


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

    def update(self, *args, **kwargs):
        self.play_anim(kwargs['delta_time'])
        super().update(*args, **kwargs)

    def play_anim(self, delta_time: float):
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
    ANIMATION_MOVE_2 = 3

    MOVE_SPEED = 10  # pixels per second

    def __init__(self, player_num, unit: Unit, pos):
        self.unit = unit
        super().__init__(GameLayerController.UNIT_LAYER,
                         WORKERS_TEXTURES[player_num].copy())
        self.rect = Rect(pos, (64, 64))
        self.toward_point = Rect(pos, (64, 64))
        self.delta_move = (0, 0)
        self.set_animation(self.ANIMATION_STAY)

    def update(self, *args, **kwargs):
        key_controller = kwargs['key_controller']
        if key_controller.is_click_on(self):
            for sprite in self.groups()[0]:
                sprite.is_selected = False
            self.is_selected = True
            key_controller.mouse_down_button = None
        # camera = kwargs['camera']
        # camera.apply(self.toward_point)
        # d_time = kwargs['delta_time']
        # if abs(self.toward_point.x - self.rect.x) <= 2 and abs(self.toward_point.y - self.rect.y) <= 2:
        #     self.toward_point = self.rect.copy()
        # else:
        #     self.delta_move = (self.toward_point.x - self.rect.x) * d_time * self.MOVE_SPEED, \
        #                       (self.toward_point.y - self.rect.y) * d_time * self.MOVE_SPEED
        #     self.rect.x += self.delta_move[0]
        #     self.rect.y += self.delta_move[1]
        super().update(*args, **kwargs)
        self.set_animation(self.cur_frame_y)

    def set_animation(self, animation_line: int = ANIMATION_STAY):
        d = len(self.frames) // 2
        if animation_line % d == self.ANIMATION_MOVE:
            self.animation_delta = -1
        else:
            self.animation_delta = 1
        animation_line %= d
        animation_line += d if self.is_selected else 0
        if animation_line % d == self.cur_frame_y % d:
            self.cur_frame_y = animation_line
        else:
            self.set_frame_y(animation_line)


class FieldSprite(LayerSprite):
    def __init__(self, field: Field, pos):
        super().__init__(GameLayerController.GROUND_LAYER)
        self.field = field
        self.rect = Rect(pos, (94, 94))
        self.init()

    def init(self):
        self.image = GROUNDS_TEXTURES[self.field.type].copy()
        text = str(self.field.cur_health)
        font_sur = pygame.font.SysFont('Arial', 14, False). \
            render(text, True, pygame.color.Color('gray'))
        self.image.blit(font_sur, (0, 0))

    def update(self, *args, **kwargs):
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
    CURSOR_LAYER = 6

    def __init__(self):
        super().__init__()
        [self.add_layer() for _ in range(7)]


class KeyController:
    def __init__(self):
        self.is_mouse_down = False
        self.mouse_down_button = None
        self.mouse_down_pos = None
        self.mouse_up_pos = None
        self.mouse_pos = None
        self.pre_mouse_pos = None

        self.is_key_pressed = False
        self.last_pressed_key = None

        self.is_quit = False

    def update(self, *args, **kwargs):
        self.is_key_pressed = False
        self.pre_mouse_pos = self.mouse_pos

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_quit = True

            if event.type == pygame.KEYDOWN:
                self.last_pressed_key = event.key
                self.is_key_pressed = True

            if event.type == pygame.MOUSEBUTTONDOWN:
                self.is_mouse_down = True
                self.mouse_down_pos = event.pos
                self.mouse_down_button = event.button

            if event.type == pygame.MOUSEBUTTONUP:
                self.is_mouse_down = False
                # self.mouse_down_button = None
                self.mouse_up_pos = event.pos

            if event.type == pygame.MOUSEMOTION:
                self.mouse_pos = event.pos

    def is_click_on(self, sprite: LayerSprite):
        return self.mouse_down_button == pygame.BUTTON_LEFT and \
               not self.is_mouse_down and \
               is_point_in_rect(self.mouse_down_pos, sprite.rect) and \
               is_point_in_rect(self.mouse_up_pos, sprite.rect)

    def is_drag(self):
        return self.is_mouse_down and self.mouse_down_button == pygame.BUTTON_RIGHT

    def get_delta(self):
        if self.is_mouse_down and self.is_drag():
            return self.mouse_pos[0] - self.pre_mouse_pos[0], \
                   self.mouse_pos[1] - self.pre_mouse_pos[1]
        else:
            return 0, 0

    def __str__(self):
        return [(k.__str__(), v.__str__()) for k, v in self.__dict__.items()]


class Scene:
    def __init__(self, layer_controller: LayerController):
        pygame.mouse.set_visible(True)
        self.layer_controller = layer_controller
        self._select = None
        self.is_game_over = False

    def add(self, sprite):
        self.layer_controller.add_sprite(sprite)

    def draw(self, screen):
        self.layer_controller.draw(screen)

    def update(self, *args, **kwargs):
        self.layer_controller.update(*args, **kwargs)

    @property
    def select(self):
        return self._select


class Camera:
    def __init__(self, pos: [int, int] = (0, 0)):
        self.pos = pos
        self.delta = (0, 0)

    def apply(self, rect: Rect):
        rect.x += self.delta[0]
        rect.y += self.delta[1]

    def update(self, delta: [int, int]):
        self.delta = delta
        self.pos = (self.pos[0] + self.delta[0], self.pos[1] + self.delta[1])


class Label:
    BACK_COLOR = pygame.color.Color(40, 40, 40)
    TEXT_COLOR = pygame.color.Color(255, 255, 255)
    MARGIN = 5

    def __init__(self, size: [int, int], text='', font_size=30, color=TEXT_COLOR):
        self.size = size
        self.text = text
        self.color = color
        self.font = pygame.font.SysFont('Comic Sans MS', font_size)

    def draw(self, surface, pos):
        surface.fill(self.BACK_COLOR, rect=Rect(pos, self.size))
        surface.blit(self.font.render(self.text, True, self.color), (pos[0] + self.MARGIN, pos[1]))


class Button:
    BACK_COLOR = pygame.color.Color(40, 40, 40)
    TEXT_COLOR = pygame.color.Color(255, 255, 255)
    BORDER_COLOR = pygame.color.Color(0, 0, 0)
    CHECKED_COLOR = pygame.color.Color('yellow')
    MARGIN = 5
    PADDING = 2

    def __init__(self, size: [int, int], text='', font_size=25, pos: [int, int] = (0, 0)):
        self.size = size
        self.text = text
        self.pos = pos
        self.checked = False
        self.font = pygame.font.SysFont('Comic Sans MS', font_size)

    def is_click(self, pos):
        return is_point_in_rect(pos, Rect(self.pos, self.size))

    def draw(self, surface):
        surface.fill(self.BORDER_COLOR if not self.checked else self.CHECKED_COLOR,
                     rect=Rect(self.pos, self.size))
        surface.fill(self.BACK_COLOR,
                     rect=Rect((self.pos[0] + self.PADDING, self.pos[1] + self.PADDING),
                               (self.size[0] - self.PADDING * 2, self.size[1] - self.PADDING * 2)))
        surface.blit(self.font.render(self.text, True, self.TEXT_COLOR), (self.pos[0] + self.MARGIN, self.pos[1]))


class Panel(LayerSprite):
    COLOR = pygame.color.Color(120, 120, 120)
    BACK_COLOR = pygame.color.Color(60, 60, 60)
    PLAYERS_COLORS = [
        pygame.color.Color(255, 0, 0),
        pygame.color.Color(0, 0, 255),
        pygame.color.Color(0, 255, 0),
        pygame.color.Color(255, 255, 255)
    ]
    MARGIN = 2
    HEIGHT = 50

    def __init__(self, display_size: [int, int]):
        super().__init__(GameLayerController.GUI_LAYER)
        self.rect = Rect((0, display_size[1] - self.HEIGHT), (display_size[0], self.HEIGHT))
        self.image = pygame.surface.Surface((display_size[0], self.HEIGHT))
        self.image.fill(self.BACK_COLOR)
        self.image.fill(self.COLOR,
                        rect=Rect(0 + self.MARGIN,
                                  0 + self.MARGIN,
                                  self.rect.width - self.MARGIN * 2,
                                  self.rect.height - self.MARGIN * 2))
        self.set_player_label('Vania')
        self.set_resources_labels((0, 0, 0))
        self.set_unit_label()
        self.is_dragable = False

        self.buttons = [
            Button(size=(80, self.HEIGHT - 4 * self.MARGIN), text='идти', pos=(850, self.MARGIN * 2)),
            Button(size=(90, self.HEIGHT - 4 * self.MARGIN), text='выбор', pos=(940, self.MARGIN * 2)),
            Button(size=(100, self.HEIGHT - 4 * self.MARGIN), text='купить', pos=(1040, self.MARGIN * 2)),
            Button(size=(80, self.HEIGHT - 4 * self.MARGIN), text='след.', pos=(1150, self.MARGIN * 2))
        ]
        for button in self.buttons:
            button.draw(self.image)

    def check_button(self, num):
        for button in self.buttons:
            button.checked = False
            button.draw(self.image)
        self.buttons[num].checked = True
        self.buttons[num].draw(self.image)

    def set_unit_label(self, unit: Unit = None):
        speed = None
        if unit is not None:
            speed = unit.cur_speed
        Label(size=(230, self.HEIGHT - 4 * self.MARGIN),
              text='Скорость: ' + str(speed)).draw(self.image, (610, self.MARGIN * 2))

    def set_resources_labels(self, resources):
        resources = list(map(str, resources))
        Label(size=(220, self.HEIGHT - 4 * self.MARGIN),
              text=ResourcesTypes.VISIBLE_NAMES[0] + ': ' + resources[0],
              color=pygame.color.Color('Cyan')). \
            draw(self.image, (190, self.MARGIN * 2))
        Label(size=(180, self.HEIGHT - 4 * self.MARGIN),
              text=ResourcesTypes.VISIBLE_NAMES[1] + ': ' + resources[1],
              color=pygame.color.Color('yellow')). \
            draw(self.image, (420, self.MARGIN * 2))
        # oil PANEl
        # Label(size=(150, self.HEIGHT - 4 * self.MARGIN),
        #       text=ResourcesTypes.NAMES[2] + ': ' + resources[2]).draw(self.image, (630, self.MARGIN * 2))

    def set_player_label(self, name, color=PLAYERS_COLORS[0]):
        Label(size=(180, self.HEIGHT - 4 * self.MARGIN),
              text=name, color=color).draw(self.image, (self.MARGIN * 2, self.MARGIN * 2))

    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)


class MoveAnimation:
    def __init__(self, sprite: UnitSprite, start_pos: [int, int], end_pos: [int, int]):
        self.sprite = sprite
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.cur_pos = start_pos[:]

    def update(self, delta_time: float):
        if abs(self.cur_pos[0] - self.end_pos[0]) + abs(self.cur_pos[1] - self.end_pos[1]) <= 5:
            self.cur_pos = self.end_pos[0], self.end_pos[1]
        else:
            dx = (self.end_pos[0] - self.start_pos[0]) * delta_time * 2
            dy = (self.end_pos[1] - self.start_pos[1]) * delta_time * 2
            self.cur_pos = self.cur_pos[0] + dx, self.cur_pos[1] + dy
            if dx > 0:
                self.sprite.set_animation(UnitSprite.ANIMATION_MOVE_2)
            else:
                self.sprite.set_animation(UnitSprite.ANIMATION_MOVE)

        self.sprite.rect.x = self.cur_pos[0]
        self.sprite.rect.y = self.cur_pos[1]
        self.sprite.play_anim(delta_time=delta_time)


class MoveAnimationController:
    def __init__(self):
        self.animations = []

    def add_anim(self, anim: MoveAnimation):
        self.animations.append(anim)

    def update(self, delta_time: float):
        if len(self.animations) == 0:
            return
        del_list = []
        for anim in self.animations:
            anim.update(delta_time)
            if anim.cur_pos[0] == anim.end_pos[0] and anim.cur_pos[1] == anim.end_pos[1]:
                del_list.append(anim)
        if len(del_list) > 0:
            self.animations.remove(del_list[0])


class GameScene(Scene):
    def __init__(self, layer_controller: GameLayerController, game: Game):
        super().__init__(layer_controller)
        pygame.mouse.set_visible(False)
        self._is_anim = False
        self.game = game
        board = self.game.get_board()
        self.camera = Camera(pos=(0, 0))

        self.anim_controller = MoveAnimationController()

        self.cur_sprite = AnimatedSprite(GameLayerController.CURSOR_LAYER, CURSOR_TEXTURES)
        self.cur_sprite.cur_frame_y = 0
        self.cur_sprite.rect = Rect(0, 0, 25, 25)
        layer_controller.add_sprite(self.cur_sprite)

        self.gui = Panel(DISPLAY_SIZE)
        layer_controller.add_sprite(self.gui)

        self.gui.set_player_label(self.game.get_cur_player().name, color=Panel.PLAYERS_COLORS[0])
        self.gui.set_resources_labels(self.game.get_cur_player().resources)
        self.gui.check_button(1)

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

    def redraw(self):
        for field_sprite in self.layer_controller.layers[GameLayerController.GROUND_LAYER].sprites():
            field_sprite.init()

    def redraw_field(self, field_pos):
        k = 0
        for unit_sprite in self.layer_controller.layers[GameLayerController.UNIT_LAYER].sprites():
            field = self.game.get_field_by_coord(field_pos)
            sp = None
            for field_sprite in self.layer_controller.layers[GameLayerController.GROUND_LAYER].sprites():
                if field_sprite.field == field:
                    sp = field_sprite
            if unit_sprite.unit in field.units:
                unit_sprite.rect.x = sp.rect.x + 20
                unit_sprite.rect.y = sp.rect.y + (k - 1) * 30
                k += 1

    def get_unit_sprite_pos(self, unit_id):
        sp = None
        unit = self.game.get_unit_by_id(unit_id)
        field_pos = self.game.get_unit_by_id(unit_id).pos
        field = self.game.get_field_by_coord(field_pos)
        for field_sprite in self.layer_controller.layers[GameLayerController.GROUND_LAYER].sprites():
            if field_sprite.field == field:
                sp = field_sprite
        return sp.rect.x + 20, \
               sp.rect.y + (self.game.get_units_on_field(field_pos).index(unit) - 1) * 30

    @property
    def select(self):
        self._select = None
        for unit_sprite in self.layer_controller.layers[GameLayerController.UNIT_LAYER].sprites():
            if unit_sprite.is_selected:
                self._select = unit_sprite
        return self._select

    def update(self, *args, **kwargs):

        if len(self.anim_controller.animations) != 0:
            self.anim_controller.update(kwargs['delta_time'])
            self.cur_sprite.cur_frame_y = 0
            self.gui.check_button(1)
            self._is_anim = True
            return
        else:
            if self._is_anim:
                self._is_anim = False
                self.redraw_field(self.select.unit.pos)
                self.select.set_animation(UnitSprite.ANIMATION_STAY)

        if self.select:
            self.gui.set_unit_label(self.select.unit)
        else:
            self.gui.set_unit_label(unit=None)

        key_controller = kwargs['key_controller']

        if key_controller.is_key_pressed:
            if key_controller.last_pressed_key == pygame.K_q:
                for unit in self.game.get_units(self.game.get_cur_player()):
                    for sprite in self.layer_controller.layers[GameLayerController.UNIT_LAYER].sprites():
                        if sprite.unit == unit:
                            sprite.set_animation(UnitSprite.ANIMATION_WORK)
                self.game.next_turn()
                self.is_game_over = self.game.is_game_over()
                self.redraw()
                self.cur_sprite.cur_frame_y = 0
                self.gui.set_player_label(
                    self.game.get_cur_player().name,
                    color=Panel.PLAYERS_COLORS[self.game._players.index(self.game.get_cur_player())])
                self.gui.set_resources_labels(self.game.get_cur_player().resources)
                key_controller.last_pressed_key = pygame.K_c
                for unit in self.game.get_units(self.game.get_cur_player()):
                    for sprite in self.layer_controller.layers[GameLayerController.UNIT_LAYER].sprites():
                        if sprite.unit == unit:
                            sprite.set_animation(UnitSprite.ANIMATION_STAY)
                self.gui.check_button(3)
                self.cur_sprite.cur_frame_y = 0
            elif key_controller.last_pressed_key == pygame.K_b:
                if self.game.buy_unit():
                    player_num = self.game._players.index(self.game.get_cur_player())
                    base = self.game.get_bases_coord()[player_num]
                    self.layer_controller.add_sprite(UnitSprite(
                        player_num=player_num,
                        unit=self.game.get_unit_by_id(self.game.unit_count - 1),
                        pos=base[0]))
                    self.redraw_field(base[0])
                    self.redraw_field(base[1])
                    self.gui.set_resources_labels(self.game.get_cur_player().resources)
                self.gui.check_button(2)
                self.cur_sprite.cur_frame_y = 0
            elif key_controller.last_pressed_key == pygame.K_m and self.select:
                self.cur_sprite.cur_frame_y = 1
                self.gui.check_button(0)
            elif key_controller.last_pressed_key == pygame.K_c:
                self.cur_sprite.cur_frame_y = 0
                self.gui.check_button(1)
            elif key_controller.last_pressed_key == pygame.K_ESCAPE:
                self.is_game_over = True

        if key_controller.last_pressed_key == pygame.K_c:
            self.camera.update(delta=key_controller.get_delta())
        else:
            self.camera.update(delta=(0, 0))

        if self.select and key_controller.last_pressed_key == pygame.K_m:
            x = key_controller.mouse_pos[0] - self.camera.pos[0]
            y = key_controller.mouse_pos[1] - self.camera.pos[1]
            field_pos = (x // 94, y // 94)

            if self.cur_sprite.cur_frame_y >= 1:
                if get_dist(field_pos, self.select.unit.pos) != 1 or not self.select.unit.is_can_move(field_pos) or \
                        not self.game.is_unit_can_move(self.select.unit.id, field_pos):
                    self.cur_sprite.cur_frame_y = 2
                else:
                    self.cur_sprite.cur_frame_y = 1

            if self.cur_sprite.cur_frame_y == 1 and key_controller.mouse_down_button == pygame.BUTTON_LEFT and \
                    key_controller.is_mouse_down:
                # if self.select.unit.player == self.game.get_cur_player():
                #     if self.select.unit.cur_speed == 0:
                #         self.select.set_animation(UnitSprite.ANIMATION_WORK)
                #     else:
                #         self.select.set_animation(UnitSprite.ANIMATION_MOVE)
                old_unit_pos = self.select.unit.pos
                if self.game.move_unit(self.select.unit.id, field_pos):
                    self.redraw_field(old_unit_pos)
                    # self.redraw_field(field_pos)
                    self.select.set_animation(UnitSprite.ANIMATION_MOVE)
                    self.anim_controller.add_anim(
                        MoveAnimation(
                            self.select,
                            (self.select.rect.x, self.select.rect.y),
                            self.get_unit_sprite_pos(self.select.unit.id)
                        ))

        if self.select and self.cur_sprite.cur_frame_y != 0:
            key_controller.mouse_down_button = None
        kwargs['camera'] = self.camera
        super().update(*args, **kwargs)
        self.cur_sprite.rect.x = key_controller.mouse_pos[0]
        self.cur_sprite.rect.y = key_controller.mouse_pos[1]

        if self.is_game_over:
            kwargs['display'].add_scene(GameOver(self.game))
            kwargs['display'].next()


class Menu(Scene):
    START_BUTTON_SIZE = (180, 60)
    FONT_SIZE = 40

    def __init__(self, layer_controller: LayerController):
        layer_controller.add_layer()
        self.camera = Camera()
        super().__init__(layer_controller=layer_controller)
        self.sprite = LayerSprite(0)
        self.sprite.image = pygame.surface.Surface(DISPLAY_SIZE)
        self.sprite.rect = Rect((0, 0), DISPLAY_SIZE)
        center_x = DISPLAY_SIZE[0] // 2 - self.START_BUTTON_SIZE[0] // 2
        center_y = DISPLAY_SIZE[1] // 2 - self.START_BUTTON_SIZE[1] // 2
        self.player_cnt_buttons = [
            Button(
                size=self.START_BUTTON_SIZE,
                text='2 игрока',
                font_size=self.FONT_SIZE,
                pos=(center_x, center_y - self.START_BUTTON_SIZE[1])),
            Button(
                size=self.START_BUTTON_SIZE,
                text='3 игрока',
                font_size=self.FONT_SIZE,
                pos=(center_x, center_y)),
            Button(
                size=self.START_BUTTON_SIZE,
                text='4 игрока',
                font_size=self.FONT_SIZE,
                pos=(center_x, center_y + self.START_BUTTON_SIZE[1])),
        ]

        [btn.draw(self.sprite.image) for btn in self.player_cnt_buttons]

        layer_controller.add_sprite(self.sprite)

    def update(self, *args, **kwargs):
        kwargs['camera'] = self.camera
        super().update(*args, **kwargs)
        key_controller = kwargs['key_controller']
        if key_controller.is_mouse_down:
            for i in range(len(self.player_cnt_buttons)):
                if self.player_cnt_buttons[i].is_click(key_controller.mouse_pos):
                    kwargs['display'].add_scene(
                        GameScene(
                            layer_controller=GameLayerController(),
                            game=Game(PLAYERS_NAMES[:i + 2], board_size=(10 + 3 * i, 10 + 3 * i))))
                    kwargs['display'].next()
                    break


class GameOver(Scene):
    LABEL_SIZE = (430, 50)
    START_POS = (0, 200)
    MARGIN = 80

    def __init__(self, game: Game):
        super().__init__(layer_controller=LayerController())
        self.sprite = LayerSprite(0)
        self.sprite.image = pygame.surface.Surface(DISPLAY_SIZE)
        self.camera = Camera()
        self.sprite.rect = Rect(self.START_POS, DISPLAY_SIZE)

        winners = sorted([(game._players[i].resources[0], game._players[i].name, i) for i in range(len(game._players))],
                         reverse=True)

        for i in range(len(winners)):
            lbl = Label(
                size=self.LABEL_SIZE,
                text=' '.join([
                    str(i + 1) + ' место:',
                    str(winners[i][1]) + ',',
                    str(winners[i][0]) + ' очков'
                ]),
                color=Panel.PLAYERS_COLORS[winners[i][2]])
            lbl.draw(self.sprite.image, (DISPLAY_SIZE[0] // 2 - self.LABEL_SIZE[0] // 2, i * self.MARGIN))

        self.layer_controller.add_layer()
        self.layer_controller.add_sprite(self.sprite)

    def update(self, *args, **kwargs):
        kwargs['camera'] = self.camera
        super().update(*args, **kwargs)
        key_controller = kwargs['key_controller']
        if key_controller.is_key_pressed and key_controller.last_pressed_key == pygame.K_ESCAPE:
            kwargs['display'].add_scene(Menu(LayerController()))
            kwargs['display'].next()


class Display:
    def __init__(self, display_size=DISPLAY_SIZE, scene: Scene = None):
        self.display_size = display_size
        self.screen = pygame.display.set_mode(self.display_size)
        self.scenes = [scene]
        self.cur_scene = None
        self.running = True
        self.key_controller = KeyController()
        self.next()

    def add_scene(self, scene: Scene):
        self.scenes.append(scene)

    def next(self):
        self.cur_scene = self.scenes.pop()

    def draw(self):
        self.screen.fill(color=pygame.color.Color(0, 0, 0),
                         rect=Rect((0, 0), self.display_size))
        if self.cur_scene is not None:
            self.cur_scene.draw(self.screen)

    def update(self, *args, **kwargs):
        self.key_controller.update(*args, **kwargs)
        if self.cur_scene is not None:
            self.cur_scene.update(
                *args,
                key_controller=self.key_controller,
                display=self,
                **kwargs)

    def flip(self):
        pygame.display.flip()

    def quit(self):
        pygame.display.quit()

    def __call__(self, *args, **kwargs):
        return self.screen


pygame.init()
pygame.font.init()

display = Display(scene=Menu(layer_controller=LayerController()))

clock = pygame.time.Clock()

while not display.key_controller.is_quit:
    delta_time = clock.tick(60) / 1000
    display.update(delta_time=delta_time)
    display.draw()
    display.flip()
display.quit()
