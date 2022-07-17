import time

import pygame
import sys
import json

pygame.init()


class Editor:
    WINDOW_WIDTH = 1400
    WINDOW_HEIGHT = 700

    ARENA_WIDTH = WINDOW_HEIGHT
    ARENA_HEIGHT = WINDOW_HEIGHT

    ARENA_MAX_ZOOM = 10.0
    ARENA_MIN_ZOOM = 1.0
    ARENA_ZOOM_SPEED = 0.1

    MAX_CLICK_DELAY_NS = 200000000

    FONT_SIZE = 50
    FONT_PATH = "fonts/Buran USSR.ttf"
    FONT = pygame.font.Font(FONT_PATH, FONT_SIZE)

    ZOOM_TEXT_VERTICAL_OFFSET = 20

    MIN_POINT_COORD = 0.0
    MAX_POINT_COORD = 1000.0

    NODE_SIZE = 5

    def __init__(self):
        self.window = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))

        self.arena = pygame.Surface((self.ARENA_WIDTH, self.ARENA_HEIGHT))

        self.arena_zoom = self.ARENA_MIN_ZOOM
        self.zoom_focus_point = [self.MIN_POINT_COORD, self.MIN_POINT_COORD]  # in left top corner
        self.swiping_active = False

        self.objects_to_display = {}  # format: {"object_name": [item, (coord_x, coord_y)], ...}
        self.set_arena_zoom_text(self.arena_zoom)

        self.points = []
        self.fill_points_from_file("data/json1")

    def size_ratio(self):
        """
        Returns a floating point number representing a ratio of
        display size to actual point space size, including the zoom.
        """
        size_for_points = self.MAX_POINT_COORD - self.MIN_POINT_COORD
        return (self.ARENA_WIDTH / size_for_points) * self.arena_zoom

    def point_under_mouse(self):
        return self.arena_coords_to_true(pygame.mouse.get_pos())

    def true_coords_to_arena(self, point):
        size_ratio = self.size_ratio()
        arena_point = [
            (point[0] - self.MIN_POINT_COORD - self.zoom_focus_point[0]) * size_ratio,
            (point[1] - self.MIN_POINT_COORD - self.zoom_focus_point[1]) * size_ratio
        ]
        return arena_point

    def arena_coords_to_true(self, point):
        size_ratio = self.size_ratio()
        displacement_from_focus = point[0] / size_ratio, point[1] / size_ratio
        return self.zoom_focus_point[0] + displacement_from_focus[0], \
               self.zoom_focus_point[1] + displacement_from_focus[1]

    @staticmethod
    def euclidean_distance(point1, point2):
        return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5

    @staticmethod
    def distance_sort_key_maker(focus_point):
        def key_function(point):
            return Editor.euclidean_distance(point, focus_point)

        return key_function

    def sorted_points_by_distance_to(self, other_point):
        return sorted(self.points, key=self.distance_sort_key_maker(other_point))

    def closest_point_to_(self, other_point):
        return min(self.points, key=self.distance_sort_key_maker(other_point))

    def set_arena_zoom_text(self, num):
        text = self.FONT.render(f'Zoom: x{round(num, 1)}', True, (0, 0, 0))
        horizontal_offset = int(self.ARENA_WIDTH + (self.WINDOW_WIDTH - self.ARENA_WIDTH) / 2 - (text.get_width() / 2))
        self.objects_to_display["arena_zoom_text"] = (text, (horizontal_offset, self.ZOOM_TEXT_VERTICAL_OFFSET))

    def fill_points_from_file(self, file_path):
        with open(file_path) as infile:
            self.points = json.load(infile)

    def draw_points_on_arena(self):
        for point in self.points:
            pygame.draw.circle(self.arena, (0, 0, 0), self.true_coords_to_arena(point), self.NODE_SIZE)

        closest_point = self.closest_point_to_(self.point_under_mouse())
        is_selected = self.does_point_collide_with_mouse(closest_point)
        print(is_selected)
        if is_selected:
            pygame.draw.circle(self.arena, (255, 0, 0), self.true_coords_to_arena(closest_point), self.NODE_SIZE)

    def does_point_collide_with_mouse(self, point):
        return self.euclidean_distance(self.true_coords_to_arena(point), pygame.mouse.get_pos()) <= self.NODE_SIZE

    def handle_exit(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                sys.exit()

    def handle_zoom(self, events):
        # zooming to the center if mouse is outside of arena
        mouse_pos = pygame.mouse.get_pos()
        if not self.is_mouse_in_arena():
            mouse_pos = self.ARENA_WIDTH / 2, self.ARENA_HEIGHT / 2

        # reading current zoom parameters
        size_ratio = self.size_ratio()

        displacement_from_focus = mouse_pos[0] / size_ratio, mouse_pos[1] / size_ratio
        point_under_mouse = self.zoom_focus_point[0] + displacement_from_focus[0], \
                            self.zoom_focus_point[1] + displacement_from_focus[1]

        # interpreting wheel movement
        wheel_movement = 0
        for event in events:
            if event.type == pygame.MOUSEWHEEL:
                wheel_movement = event.y

        self.arena_zoom += self.ARENA_ZOOM_SPEED * wheel_movement
        if self.arena_zoom > self.ARENA_MAX_ZOOM:
            self.arena_zoom = self.ARENA_MAX_ZOOM
        if self.arena_zoom < self.ARENA_MIN_ZOOM:
            self.arena_zoom = self.ARENA_MIN_ZOOM

        self.set_arena_zoom_text(self.arena_zoom)

        # handing zooming process
        new_size_ratio = self.size_ratio()
        new_displacement = mouse_pos[0] / new_size_ratio, mouse_pos[1] / new_size_ratio
        self.zoom_focus_point = [point_under_mouse[0] - new_displacement[0],
                                 point_under_mouse[1] - new_displacement[1]]

        # repositioning focus point if it's too far in any of the directions
        self.check_focus_point_borders()

    def check_focus_point_borders(self):
        if self.zoom_focus_point[0] < self.MIN_POINT_COORD:
            self.zoom_focus_point[0] = self.MIN_POINT_COORD
        if self.zoom_focus_point[1] < self.MIN_POINT_COORD:
            self.zoom_focus_point[1] = self.MIN_POINT_COORD

        bottom_right_displacement = self.ARENA_WIDTH / self.size_ratio(), self.ARENA_HEIGHT / self.size_ratio()

        if self.zoom_focus_point[0] + bottom_right_displacement[0] > self.MAX_POINT_COORD:
            self.zoom_focus_point[0] = self.MAX_POINT_COORD - bottom_right_displacement[0]
        if self.zoom_focus_point[1] + bottom_right_displacement[1] > self.MAX_POINT_COORD:
            self.zoom_focus_point[1] = self.MAX_POINT_COORD - bottom_right_displacement[1]

    def is_mouse_in_arena(self):
        mouse_pos = pygame.mouse.get_pos()
        if not self.arena.get_rect().collidepoint(*mouse_pos):
            return False
        else:
            return bool(pygame.mouse.get_focused())

    def handle_add_delete_node(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT \
                    and self.is_mouse_in_arena():
                selected_coords = self.point_under_mouse()
                closest_point = self.closest_point_to_(selected_coords) if self.points else None
                if closest_point is None or not self.does_point_collide_with_mouse(closest_point):
                    self.points.append(self.point_under_mouse())
                else:
                    self.points.remove(closest_point)

    def handle_swiping(self, events):
        if not self.swiping_active:
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_RIGHT \
                        and self.is_mouse_in_arena():
                    self.swiping_active = True
                    pygame.mouse.get_rel()
                    # ^ resetting the get_rel function

        else:  # if swiping active

            mouse_displacement = pygame.mouse.get_rel()
            size_ratio = self.size_ratio()
            move_vector = [- mouse_displacement[0] / size_ratio, - mouse_displacement[1] / size_ratio]

            self.zoom_focus_point[0] += move_vector[0]
            self.zoom_focus_point[1] += move_vector[1]
            self.check_focus_point_borders()

            if not self.is_mouse_in_arena():
                self.swiping_active = False

            for event in events:
                if event.type == pygame.MOUSEBUTTONUP and event.button == pygame.BUTTON_RIGHT:
                    self.swiping_active = False

    def process_inputs(self):
        events = pygame.event.get()
        self.handle_exit(events)
        self.handle_zoom(events)
        self.handle_swiping(events)
        self.handle_add_delete_node(events)

    def render_window(self):
        self.window.fill((255, 255, 255))
        self.arena.fill((220, 220, 220))
        self.draw_points_on_arena()
        self.window.blit(self.arena, (0, 0))
        for item, pos in self.objects_to_display.values():
            self.window.blit(item, pos)
        pygame.display.flip()

    def play(self):
        while True:
            self.process_inputs()
            self.render_window()


if __name__ == '__main__':
    import random

    list_o_points = [(random.uniform(Editor.MIN_POINT_COORD, Editor.MAX_POINT_COORD),
                      random.uniform(Editor.MIN_POINT_COORD, Editor.MAX_POINT_COORD))
                     for _ in range(100)]
    with open("data/json1", "w") as outfile:
        json.dump(list_o_points, outfile)
