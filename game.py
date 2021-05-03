import os
import json


def get_dist(pos1: [int, int], pos2: [int, int]):
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def get_field_properties():
    with open(os.path.join('res', 'values', 'ground_properties.json'), encoding='utf-8') as data:
        return json.load(data)['grounds']


FIELD_PROPERTIES = get_field_properties()


class FieldTypes:
    TUNNEL = 0
    SOIL = 1
    OIL = 2
    DIAMOND = 3
    GOLD = 4
    LAVA = 5
    STONE = 6


class ResourcesTypes:
    DIAMOND = 0
    GOLD = 1
    OIL = 2

    NAMES = ["diamond", "gold", "oil"]

    @staticmethod
    def get_type(res_name):
        return ResourcesTypes.NAMES.index(res_name)


class Player:
    def __init__(self, name: str, resources: [int, int, int]):
        self.name = name
        self.resources = resources

    def __str__(self):
        return f'Player name={self.name}, resources={self.resources}'


class Unit:
    def __init__(self, pos: [int, int], max_speed: int, player: Player, unit_id: int):
        self.pos = pos
        self.player = player
        self.cur_speed = max_speed
        self.max_speed = max_speed
        self.id = unit_id
        self.is_speed_up = False

    def speed_up(self):
        if not self.is_speed_up:
            self.cur_speed += 1
            self.is_speed_up = True

    def move(self, new_pos: [int, int]):
        if self.is_can_move(new_pos):
            self.cur_speed -= get_dist(self.pos, new_pos)
            self.pos = new_pos

    def is_can_move(self, new_pos):
        return get_dist(self.pos, new_pos) <= self.cur_speed

    def update(self, cur_player):
        if cur_player == self.player:
            self.is_speed_up = False
            self.cur_speed = self.max_speed

    def __str__(self):
        return f'Unit id={self.id}, speed={self.cur_speed}, player={self.player.name}'


class Field(object):
    def __init__(self, field_type=FieldTypes.TUNNEL, units=None):
        self.type = 0
        self.cur_health = 0
        self.units = units[:] if units is not None and len(units) != 0 else list()
        self.init(field_type)

    def init(self, field_type):
        self.type = field_type
        self.cur_health = FIELD_PROPERTIES[field_type]['max_health']

    def add_unit(self, unit: Unit):
        self.units.append(unit)

    def pop_unit(self, unit: Unit) -> Unit or None:
        if unit in self.units:
            return self.units.pop(self.units.index(unit))
        return None

    def excavate(self):
        self.init(FIELD_PROPERTIES[self.type]['next_ground'])

    def update(self, cur_player):
        player_unit_count = len([unit for unit in self.units if unit.player == cur_player])
        self.cur_health -= player_unit_count
        res_name = FIELD_PROPERTIES[self.type]['resource']
        if res_name is not None:
            res_type = ResourcesTypes.get_type(res_name)
            cur_player.resources[res_type] += player_unit_count
        if self.cur_health <= 0:
            self.excavate()
        [unit.update(cur_player) for unit in self.units]

    def __str__(self):
        return f'''Field type={FIELD_PROPERTIES[self.type]['title']}, health={self.cur_health}'''


class Board(object):
    def __init__(self, size=(10, 10)):
        self.size = size
        import random
        self._fields = []
        for y in range(size[1]):
            self._fields.append([])
            for x in range(size[0]):
                self._fields[y].append(Field(random.choice([1, 2, 4, 5, 6])))
        for i in range(10):
            y = random.randint(0, size[1] - 1)
            x = random.randint(0, size[0] - 1)
            self._fields[y][x] = Field(FieldTypes.DIAMOND)

    def get_field(self, pos: [int, int]) -> Field or None:
        if 0 <= pos[1] < len(self._fields) and 0 <= pos[0] < len(self._fields[pos[1]]):
            return self._fields[pos[1]][pos[0]]
        return None

    def update(self, cur_player):
        for line in self._fields:
            for field in line:
                field.update(cur_player)

    def __str__(self):
        return str([[field.__str__() for field in line] for line in self._fields])


class Game(object):
    MAX_UNITS_ON_FIELD = 3
    MAX_UNIT_SPEED = 3
    UNIT_COST = 5
    SPEED_UP_COST = 2
    START_UNIT_COUNT = 3
    START_RESOURCES_COUNT = [0, 10, 0]

    def __init__(self, players_names: list, board_size: [int, int] = (10, 10)):
        self.unit_count = 0
        self.turn_number = 0
        self._units = []
        self._board = None
        self._players = []
        self.init_game(players_names, board_size)

    def get_board(self):
        return self._board

    def init_game(self, players_names, board_size):
        self._board = Board(size=board_size)
        self._players = [Player(name, self.START_RESOURCES_COUNT[:]) for name in players_names]
        bases = self.get_bases_coord()
        for i in range(len(self._players)):
            self._board.get_field(bases[i][0]).init(FieldTypes.TUNNEL)
            self._board.get_field(bases[i][1]).init(FieldTypes.TUNNEL)
            for j in range(self.START_UNIT_COUNT):
                self.add_unit(bases[i][0])
            self.next_turn()
        self.turn_number = 0

    def get_bases_coord(self):
        w = self._board.size[0] - 1
        h = self._board.size[1] - 1
        return ((0, h // 2), (0, h // 2 + 1)), \
               ((w // 2, 0), (w // 2 + 1, 0)),\
               ((w, h // 2), (w, h // 2 + 1)),\
               ((w // 2, h), (w // 2 + 1, h))

    def next_turn(self):
        self.turn_number += 1
        self._board.update(self.get_cur_player())

    def get_cur_player(self):
        return self._players[self.turn_number % len(self._players)]

    def add_unit(self, field_pos: [int, int]):
        field = self._board.get_field(field_pos)
        if field is not None:
            self._units.append(Unit(field_pos, self.MAX_UNIT_SPEED, self.get_cur_player(), self.unit_count))
            field.add_unit(self._units[len(self._units) - 1])
            self.unit_count += 1
            return True
        return False

    def speed_up_unit(self, unit_id):
        unit = self.get_unit_by_id(unit_id)
        if unit is not None:
            if not unit.is_speed_up:
                if self.get_cur_player().resources[ResourcesTypes.OIL] >= self.SPEED_UP_COST:
                    unit.speed_up()
                    return True
        return False

    def buy_unit(self):
        if self.get_cur_player().resources[ResourcesTypes.GOLD] >= self.UNIT_COST:
            self.get_cur_player().resources[ResourcesTypes.GOLD] -= self.UNIT_COST
            self.add_unit(self.get_bases_coord()[self._players.index(self.get_cur_player())])
            return True
        return False

    def move_unit(self, unit_id: int, new_pos: [int, int]) -> bool:
        unit = self.get_unit_by_id(unit_id)
        if unit is not None and self.get_cur_player() == unit.player:
            old_field = self.get_field_by_coord(unit.pos)
            new_field = self.get_field_by_coord(new_pos)
            if old_field is not None and new_field is not None:
                if unit.is_can_move(new_pos):
                    unit.move(new_pos)
                    new_field.add_unit(old_field.pop_unit(unit))
                    return True
        return False

    def get_field_by_coord(self, pos: [int, int]) -> Field or None:
        return self._board.get_field(pos)

    def get_unit_by_id(self, unit_id: int) -> Unit or None:
        return self._units[unit_id] if 0 <= unit_id < len(self._units) else None

    def get_units_on_field(self, field_pos: [int, int]):
        field = self.get_field_by_coord(field_pos)
        return field.units if field is not None else []

    def get_player(self):
        return self._players

    def get_player_num(self, player: Player):
        return self._players.index(player)

    def get_units(self, player: Player = None):
        if player is None:
            return self._units
        return list(filter(lambda u: u.player == player, self._units))


class ConsoleGameController:
    def __init__(self, game):
        self.game = game
        self.field_pos = None
        self.unit_id = None

    def show_unit(self):
        if self.field_pos is not None:
            units = self.game.get_units_on_field(self.field_pos)
            print('units:\n', '\n'.join([u.__str__() for u in units]), sep='')
        else:
            print('units', None)

    def take_field(self, com):
        pos = int(com[1]), int(com[2])
        self.field_pos = pos
        field = self.game.get_field_by_coord(self.field_pos)
        if field is not None:
            print(f'taken field by ({com[1]}, {com[2]}): {field.__str__()}')
        else:
            print('taken', None)

    def take_unit(self, com):
        unit_index = int(com[1])
        units = self.game.get_units_on_field(self.field_pos)
        if self.field_pos is not None and len(units) > 0:
            self.unit_id = units[unit_index].id
            print('taken', units[unit_index])
        else:
            print('taken', None)

    def move_unit(self, com):
        print('selected unit id', self.unit_id)
        if self.unit_id is not None:
            new_pos = (int(com[1]), int(com[2]))
            res = self.game.move_unit(self.unit_id, new_pos)
            if res:
                print(f'{self.game.get_unit_by_id(self.unit_id)} moved to {new_pos}')
            else:
                print('not moved')
        else:
            print('not moved')

    def next_turn(self):
        self.game.next_turn()
        player = self.game.get_cur_player()
        print(f'Turn {self.game.turn_number}, player {player.name}')

    def get_players_info(self):
        print('\n'.join([player.__str__() for player in self.game._players]))

    def buy_unit(self):
        print('Buying', self.game.buy_unit())

    def speed_up(self):
        print('Speed up', self.game.speed_up_unit(self.unit_id))

    def parse(self, com):
        com = com.split()
        if com[0] == 'take_field':
            self.take_field(com)
            self.show_unit()
        elif com[0] == 'show_unit':
            self.show_unit()
        elif com[0] == 'take_unit':
            self.take_unit(com)
        elif 'move_unit' == com[0]:
            self.move_unit(com)
        elif 'next_turn' == com[0]:
            self.next_turn()
        elif 'players' == com[0]:
            self.get_players_info()
        elif 'buy_unit' == com[0]:
            self.buy_unit()
        elif 'speed_up_unit' == com[0]:
            self.speed_up()


if __name__ == '__main__':
    game = Game(['Вася', 'Петя', 'John'])
    console_game_controller = ConsoleGameController(game)

    running = True
    while running:
        console_game_controller.parse(input())

# take_field 2 2
# show_unit
# move_unit 3 3
