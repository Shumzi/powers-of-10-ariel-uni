import pygame

pygame.init()
screen = pygame.display.set_mode((1600, 919))
clock = pygame.time.Clock()

bg = pygame.image.load("big.jpg").convert()
image = pygame.image.load("small.png").convert()

# Viewport (your “canvas region”)
viewport_size = (720, 720)
viewport_surface = pygame.Surface(viewport_size)
viewport_rect = pygame.Rect(812, 76, *viewport_size)

# A rectangle defined in image-space
target_rect_img = pygame.Rect(400, 300, 200, 150)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # -----------------------------------------------------------------
    # Draw everything INSIDE THE VIEWPORT SURFACE
    # -----------------------------------------------------------------

    # 1. Draw the cropped image onto the viewport
    viewport_surface.blit(image, (0,0))

    # -----------------------------------------------------------------
    # Now blit the viewport onto the screen exactly once
    # -----------------------------------------------------------------
    screen.fill((30,30,30))
    screen.blit(bg, (0,0))

    screen.blit(viewport_surface, viewport_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
