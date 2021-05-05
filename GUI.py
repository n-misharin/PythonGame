from controllers import LayerSprite, GameLayerController
import pygame


class Panel(LayerSprite):
    def __init__(self, display_size: [int, int]):
        super().__init__(GameLayerController.GUI_LAYER)
        self.image = pygame.surface.Surface((display_size[0], 50))

    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
