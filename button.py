import pygame

class Button():
    def __init__(self, surface, x, y, image=None, width=None, height=None):
        self.surface = surface
        self.clicked = False

        if image and width is not None and height is not None:
            self.image = pygame.transform.scale(image, (width, height))
            self.rect = self.image.get_rect(topleft=(x, y))
        elif image:
            # If no dimensions are given, use the image's original dimensions
            self.image = image
            self.rect = self.image.get_rect(topleft=(x, y))
        else:
            # If no image, a width and height are required for the hitbox (xrisimopoieitai sto camp)
            if width is None or height is None:
                raise ValueError("Width and height are required for a button without an image.")
            self.image = None
            self.rect = pygame.Rect(x, y, width, height)

    def draw(self):
        action = False
        pos = pygame.mouse.get_pos()

        # click
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] and not self.clicked:
                self.clicked = True
                action = True

        if not pygame.mouse.get_pressed()[0]:
            self.clicked = False

        # Draw the image if it exists
        if self.image:
            self.surface.blit(self.image, self.rect)

        return action