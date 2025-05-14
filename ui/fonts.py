import os
import pygame

class Font:
    def __init__(self, path):
        base_dir = os.path.dirname(__file__)
        self.font_dir = os.path.join(base_dir, "..", "fonts", path, "static")
        pygame.font.init()

    def font(self, size="sm", type="Regular"):
        size_map = {
            "sm": 18,
            "md": 24,
            "l": 28
        }

        pt_size = size_map[size]
        file_name = f"Inter_{pt_size}pt-{type}.ttf"
        file_path = os.path.join(self.font_dir, file_name)

        if os.path.exists(file_path):
            print("Found font file:", file_path)
            return file_path, pt_size
        else:
            raise FileNotFoundError(f"Font file not found: {file_path}")

    def load(self, size="sm", type="Regular"):
        font_path, pt_size = self.font(size=size, type=type)
        return pygame.font.Font(font_path, pt_size)


# Example
#font = Font(path="Inter")
#font.font(type="Regular")