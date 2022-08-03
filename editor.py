import time

import pygame
import sys
import json

import utilities
import Greedy

pygame.init()


class Editor:
    WINDOW_WIDTH = 1400
    WINDOW_HEIGHT = 700

    ARENA_WIDTH = WINDOW_HEIGHT
    ARENA_HEIGHT = WINDOW_HEIGHT

    ARENA_MAX_ZOOM = 20000.0
    ARENA_MIN_ZOOM = 1.0
    ARENA_ZOOM_SPEED = 1.2

    FONT_SIZE = 50
    FONT_PATH = "fonts/Buran USSR.ttf"
    FONT = pygame.font.Font(FONT_PATH, FONT_SIZE)

    ZOOM_TEXT_VERTICAL_OFFSET = 20

    PLAY_PATH = "images/play.png"
    STOP_PATH = "images/stop.png"
    PlAYSTOP_VERTICAL_OFFSET = -20

    MIN_POINT_COORD = 0.0
    MAX_POINT_COORD = 1000.0
    POINT_COORD_RANGE = (MIN_POINT_COORD, MAX_POINT_COORD)

    NODE_SIZE = 5

    def __init__(self):
        self.window = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))

        self.arena = pygame.Surface((self.ARENA_WIDTH, self.ARENA_HEIGHT))

        self.arena_zoom = self.ARENA_MIN_ZOOM
        self.zoom_focus_point = [self.MIN_POINT_COORD, self.MIN_POINT_COORD]  # in left top corner
        self.swiping_active = False

        self.objects_to_display = {}  # format: {"object_name": [item, (coord_x, coord_y)], ...}
        self.set_arena_zoom_text(self.arena_zoom)

        self.playstop_images = {"playing": None, "stopped": None}
        self.play_mode = "playing"
        self.playstop_rect = None
        self.prepare_playstop_button()

        self.points = []
        self.connections = {}
        self.fill_points_from_file("data/json1")
        self.get_connections_from_points()

        self.greedy_results = Greedy.greedy_search_solve(self.points, self.connections)

    def prepare_playstop_button(self):
        """
        - Called in __init__. Initializes playstop button.
        - Takes no arguments, returns None.
        """
        playimg = pygame.image.load(self.PLAY_PATH).convert()
        stopimg = pygame.image.load(self.STOP_PATH).convert()
        rect = playimg.get_rect()

        rect.bottom = self.ARENA_HEIGHT + self.PlAYSTOP_VERTICAL_OFFSET
        rect.centerx = self.horizontal_middle_of_menu_area()

        self.playstop_images["stopped"] = playimg
        self.playstop_images["playing"] = stopimg
        self.objects_to_display["playstop"] = [self.playstop_images[self.play_mode], rect.topleft]

        self.playstop_rect = rect

    def toggle_playstop(self):
        if self.play_mode == "playing":
            self.play_mode = "stopped"
        elif self.play_mode == "stopped":
            self.play_mode = "playing"
        self.objects_to_display["playstop"][0] = self.playstop_images[self.play_mode]


    def size_ratio(self):
        """
        Returns a floating point number representing a ratio of
        display size to actual point space size, including the zoom.
        """
        size_for_points = self.MAX_POINT_COORD - self.MIN_POINT_COORD
        return (self.ARENA_WIDTH / size_for_points) * self.arena_zoom

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

    def point_under_mouse(self):
        return self.arena_coords_to_true(pygame.mouse.get_pos())

    def sorted_points_by_distance_to(self, other_point):
        return sorted(self.points, key=utilities.distance_sort_key_maker(other_point))

    def closest_point_to_(self, other_point):
        return min(self.points, key=utilities.distance_sort_key_maker(other_point))

    def horizontal_middle_of_menu_area(self):
        return self.ARENA_WIDTH + (self.WINDOW_WIDTH - self.ARENA_WIDTH) / 2

    def set_arena_zoom_text(self, num):
        text = self.FONT.render(f'Zoom: x{round(num, 1)}', True, (0, 0, 0))
        horizontal_offset = int(self.horizontal_middle_of_menu_area() - (text.get_width() / 2))
        self.objects_to_display["arena_zoom_text"] = (text, (horizontal_offset, self.ZOOM_TEXT_VERTICAL_OFFSET))

    def fill_points_from_file(self, file_path):
        with open(file_path) as infile:
            self.points = json.load(infile)

    def save_changes_to_file(self, file_path):
        with open(file_path, "w") as outfile:
            json.dump(self.points, outfile)

    def get_connections_from_points(self):
        self.connections = {index: dict() for index, _ in enumerate(self.points)}
        for index1, point1 in enumerate(self.points):
            for index2, point2 in enumerate(self.points):
                distance = utilities.euclidean_distance(point1, point2)
                self.connections[index1][index2] = distance
                self.connections[index2][index1] = distance

    def draw_points_on_arena(self):
        for point in self.points:
            pygame.draw.circle(self.arena, (0, 0, 0), self.true_coords_to_arena(point), self.NODE_SIZE)

        closest_point = self.closest_point_to_(self.point_under_mouse())
        is_selected = self.does_point_collide_with_mouse(closest_point)
        if is_selected:
            pygame.draw.circle(self.arena, (255, 0, 0), self.true_coords_to_arena(closest_point), self.NODE_SIZE)

    def TEST_draw_connections_on_arena(self):
        for point1 in self.points:
            arena_coord1 = self.true_coords_to_arena(point1)
            for point2 in self.points:
                if point1 == point2:
                    continue
                arena_coord2 = self.true_coords_to_arena(point2)
                pygame.draw.line(self.arena, (0, 0, 255), arena_coord1, arena_coord2, 1)

    def draw_greedy_results_on_arena(self):
        for id1, id2 in zip(self.greedy_results, self.greedy_results[1:]):
            arena_coord1 = self.true_coords_to_arena(self.points[id1])
            arena_coord2 = self.true_coords_to_arena(self.points[id2])

            pygame.draw.line(self.arena, (255, 0, 0), arena_coord1, arena_coord2, 2)

    def does_point_collide_with_mouse(self, point):
        return utilities.euclidean_distance(self.true_coords_to_arena(point), pygame.mouse.get_pos()) <= self.NODE_SIZE

    def handle_exit(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.save_changes_to_file("data/json1")
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
        self.interpret_zoom_wheel_movement(events)

        # handing zooming process
        new_size_ratio = self.size_ratio()
        new_displacement = mouse_pos[0] / new_size_ratio, mouse_pos[1] / new_size_ratio
        self.zoom_focus_point = [point_under_mouse[0] - new_displacement[0],
                                 point_under_mouse[1] - new_displacement[1]]

        # repositioning focus point if it's too far in any of the directions
        self.check_focus_point_borders()

    def interpret_zoom_wheel_movement(self, events):
        wheel_movement = 0
        for event in events:
            if event.type == pygame.MOUSEWHEEL:
                wheel_movement = event.y

        if wheel_movement > 0:
            self.arena_zoom *= self.ARENA_ZOOM_SPEED
        if wheel_movement < 0:
            self.arena_zoom /= self.ARENA_ZOOM_SPEED

        if self.arena_zoom > self.ARENA_MAX_ZOOM:
            self.arena_zoom = self.ARENA_MAX_ZOOM
        if self.arena_zoom < self.ARENA_MIN_ZOOM:
            self.arena_zoom = self.ARENA_MIN_ZOOM

        self.set_arena_zoom_text(self.arena_zoom)

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

    def handle_playstop(self, events):
        if not self.playstop_rect.collidepoint(pygame.mouse.get_pos()):
            return

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
                self.toggle_playstop()


    def process_inputs(self):
        events = pygame.event.get()
        self.handle_exit(events)

        self.handle_zoom(events)
        self.handle_playstop(events)

        self.handle_swiping(events)
        self.handle_add_delete_node(events)


    def render_window(self):
        self.window.fill((255, 255, 255))
        self.arena.fill((220, 220, 220))
        # self.TEST_draw_connections_on_arena()
        # self.draw_greedy_results_on_arena()
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

    list_o_points = [(random.uniform(*Editor.POINT_COORD_RANGE),
                      random.uniform(*Editor.POINT_COORD_RANGE))
                     for _ in range(100)]
    with open("data/json1", "w") as outfile:
        json.dump(list_o_points, outfile)
