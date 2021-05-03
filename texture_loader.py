import json
import pygame
import os

DEFAULT_COLORKEY = -1

RESOURCES_DIRECTORY = 'res'
IMAGES_DIRECTORY = 'images'
VALUES_DIRECTORY = 'values'

IMAGES_DIRECTORY_PATH = os.path.join(RESOURCES_DIRECTORY, IMAGES_DIRECTORY)
VALUES_DIRECTORY_PATH = os.path.join(RESOURCES_DIRECTORY, VALUES_DIRECTORY)


class ImageHandler:
    @staticmethod
    def load_image(image_name, colorkey=None):
        full_path = os.path.join(IMAGES_DIRECTORY_PATH, image_name)
        if not os.path.isfile(full_path):
            raise Exception(f'Файл {full_path} не найден')
        else:
            return ImageHandler.convert_alpha(pygame.image.load(full_path), colorkey)

    @staticmethod
    def convert_alpha(image, colorkey=None):
        if colorkey is not None:
            image = image.convert()
            if colorkey == DEFAULT_COLORKEY:
                colorkey = image.get_at((0, 0))
            image.set_colorkey(colorkey)
        else:
            image = image.convert_alpha()
        return image

    @staticmethod
    def join(*images):
        size = max([img.get_width() for img in images]), max([img.get_height() for img in images])
        surface = images[0]
        for img in images[1:]:
            surface.blit(img, pygame.rect.Rect(0, 0, img.get_width(), img.get_height()))
        return ImageHandler.convert_alpha(surface)

    @staticmethod
    def cut_sheet(sheet, frame_size: tuple):
        frames = []
        for j in range(sheet.get_height() // frame_size[1]):
            for i in range(sheet.get_width() // frame_size[0]):
                frame_location = (frame_size[0] * i, frame_size[1] * j)
                frames.append(sheet.subsurface(pygame.Rect(
                    frame_location,
                    frame_size)))
        return frames

    @staticmethod
    def get_frames_sheet(frames: list, typed_dict: dict):
        res = []
        for key, val in typed_dict.items():
            res.append(*[frames[val[0]:val[1] + 1]])
        return res


class TextureLoader:
    def __init__(self, json_file):
        json_file = os.path.join(VALUES_DIRECTORY_PATH, json_file)
        self.json = dict()
        self.sheets = dict()
        with open(json_file, encoding='utf-8') as base_data:
            self.json = json.load(base_data)

    def load(self):
        return []


class TextureWorkerLoader(TextureLoader):
    def __init__(self, json_file='units_sprites.json'):
        super().__init__(json_file)

    def load(self):
        worker_dict = self.json['worker']

        images = [ImageHandler.load_image(file_name) for file_name in worker_dict['files'][:-1]]
        image_back = ImageHandler.load_image(worker_dict['files'][-1])

        workers_images = []

        for image in images:
            joined_image = ImageHandler.join(image_back, image)

            normal_frames = ImageHandler.cut_sheet(image, worker_dict['frame_size'])
            joined_frames = ImageHandler.cut_sheet(joined_image, worker_dict['frame_size'])

            workers_images.append(
                ImageHandler.get_frames_sheet(normal_frames, worker_dict['animation_rows']) +
                ImageHandler.get_frames_sheet(joined_frames, worker_dict['animation_rows']))

        return workers_images


class TextureGroundLoader(TextureLoader):
    def __init__(self, json_file='ground_sprites.json'):
        super().__init__(json_file)

    def load(self):
        ground_dict = self.json['ground']

        image = ImageHandler.load_image(ground_dict['files'][0])
        frames = ImageHandler.cut_sheet(image, ground_dict['frame_size'])

        textures = [frame[0] for frame in ImageHandler.get_frames_sheet(frames, ground_dict['animation_rows'])]
        return [
            textures[7],
            textures[5],
            textures[4],
            textures[0],
            textures[2],
            textures[8],
            textures[6],
        ]


pygame.init()
screen = pygame.display.set_mode((1000, 800))

WORKERS_TEXTURES = TextureWorkerLoader().load()
GROUNDS_TEXTURES = TextureGroundLoader().load()

if __name__ == '__main__':
    running = True

    gg = pygame.sprite.Group()
    for i in range(len(GROUNDS_TEXTURES)):
        s = pygame.sprite.Sprite()
        s.rect = pygame.rect.Rect(i * 100, 0, 94, 94)
        s.image = GROUNDS_TEXTURES[i]
        gg.add(s)

    g = pygame.sprite.Group()
    for i in range(len(WORKERS_TEXTURES)):
        for j in range(len(WORKERS_TEXTURES[i])):
            for k in range(len(WORKERS_TEXTURES[i][j])):
                s = pygame.sprite.Sprite()
                s.rect = pygame.rect.Rect((k + ((i * 6) // 12) * 8) * 65, (j + (i * 6) % 12) * 65, 64, 64)
                s.image = WORKERS_TEXTURES[i][j][k]
                g.add(s)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        gg.draw(screen)
        g.draw(screen)
        pygame.display.flip()

    pygame.quit()