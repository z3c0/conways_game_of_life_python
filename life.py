import math
import time
import pygame
import datetime as dt
import threading as thr


DEBUG = False

AUTO_ADVANCE = pygame.USEREVENT + 1

SCREEN_SIZES = [(1920, 1080), (1280, 720), (640, 480)]

GRID_SIZE = 16

HEADER_SIZE = 64


class LifeController:

    def __init__(self):
        self._screen = None
        self._grid_surface = None
        self._header_surface = None
        self._header_font = None
        self._game = None
        self._initial_state = None
        self._processing_turn = False
        self._mouse_down = False
        self._painting = False

    def main(self):
        pygame.init()
        pygame.display.set_caption('Conway\'s Game of Life')

        # intialize components
        screen_size_x, screen_size_y = SCREEN_SIZES[1]
        self._screen = pygame.display.set_mode((screen_size_x, screen_size_y))
        self._grid_surface = \
            pygame.Surface((screen_size_x, screen_size_y - HEADER_SIZE))
        self._header_surface = \
            pygame.Surface((screen_size_x, HEADER_SIZE))
        self._header_font = pygame.font.SysFont('Consolas', 16)
        self._game = Life()

        # begin
        while self._set_initial_state():
            if self._run_game():
                continue
            break

        pygame.quit()

    def _refresh_grid(self):
        self._screen.blit(self._grid_surface, (0, HEADER_SIZE))

    def _refresh_header(self):
        self._header_surface.fill('#000000')

        cell_count_text = f'living: {self._game.count}'
        cell_count_image = \
            self._header_font.render(cell_count_text, False, '#ffffff')

        self._header_surface.blit(cell_count_image, (16, 16))
        self._screen.blit(self._header_surface, (0, 0))

    def _set_initial_state(self):
        self._initial_state = set()
        screen_size_x, screen_size_y = self._grid_surface.get_size()

        columns = [((max(ln * GRID_SIZE - 1, 0), 0),
                   (max(ln * GRID_SIZE - 1, 0), screen_size_y))
                   for ln in range(math.ceil(screen_size_x / GRID_SIZE) + 1)]

        rows = [((0, max(ln * GRID_SIZE - 1, 0)),
                (screen_size_x, max(ln * GRID_SIZE - 1, 0)))
                for ln in range(math.ceil(screen_size_y / GRID_SIZE) + 1)]

        # draw columns
        for start_pos, end_pos in columns:
            pygame.draw.line(self._grid_surface, '#ffffff', start_pos, end_pos)

        # draw rows
        for start_pos, end_pos in rows:
            pygame.draw.line(self._grid_surface, '#ffffff', start_pos, end_pos)

        self._refresh_grid()
        self._refresh_header()

        running = True
        last_click_time = None
        last_click_duration = None
        while running:
            pygame.display.update()

            if self._mouse_down and not self._painting:
                last_click_duration = dt.datetime.now() - last_click_time

                self._painting = last_click_duration.microseconds > 200000

            if self._painting:
                self._paint_current_cell()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._initial_state = None
                    running = False
                    break

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self._mouse_down = True
                    last_click_time = dt.datetime.now()

                elif event.type == pygame.MOUSEBUTTONUP:
                    self._mouse_down = False

                    if not self._painting:
                        self._click_current_cell()
                    else:
                        self._painting = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._initial_state = None
                        running = False
                        break

                    elif event.key == pygame.K_RETURN:
                        running = False

                    elif event.key == pygame.K_SPACE:
                        running = False
                        event = pygame.event.Event(AUTO_ADVANCE)
                        pygame.event.post(event)
                        break

        if self._initial_state:
            self._game.set_initial_state(self._initial_state)

        return bool(self._initial_state)

    def _run_game(self):
        self._grid_surface.fill('#000000')
        self._draw_current_state()

        running = True
        auto_advance = False
        while running:
            pygame.display.update()

            if auto_advance and not self._processing_turn:
                event = pygame.event.Event(AUTO_ADVANCE)
                pygame.event.post(event)
                time.sleep(.4)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False

                elif event.type == AUTO_ADVANCE:
                    auto_advance = True

                    if not self._processing_turn:
                        turn_thread = thr.Thread(target=self._advance_turn)
                        turn_thread.daemon = True
                        turn_thread.start()

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if not self._processing_turn:
                            turn_thread = thr.Thread(target=self._advance_turn)
                            turn_thread.daemon = True
                            turn_thread.start()

                    elif event.key == pygame.K_SPACE:
                        auto_advance = not auto_advance

                    elif event.key == pygame.K_ESCAPE:
                        running = False

        return True

    def _paint_current_cell(self):
        x, y = pygame.mouse.get_pos()
        y -= HEADER_SIZE
        screen_x, screen_y = self._grid_surface.get_size()

        x_scale = screen_x / (screen_x / GRID_SIZE)
        y_scale = screen_y / (screen_y / GRID_SIZE)

        x_rounded = int(x / x_scale)
        y_rounded = int(y / y_scale)

        x_cell_pos = x_rounded * x_scale
        y_cell_pos = y_rounded * y_scale

        new_cell_coord = (x_rounded, y_rounded)
        if new_cell_coord not in self._initial_state:
            self._initial_state.add(new_cell_coord)
            rect = (x_cell_pos, y_cell_pos, GRID_SIZE, GRID_SIZE)
            pygame.draw.rect(self._grid_surface, '#ffffff', rect)

        self._refresh_grid()
        self._refresh_header()

    def _click_current_cell(self):
        x, y = pygame.mouse.get_pos()
        y -= HEADER_SIZE
        grid_x, grid_y = self._grid_surface.get_size()

        x_scale = grid_x / (grid_x / GRID_SIZE)
        y_scale = grid_y / (grid_y / GRID_SIZE)

        x_rounded = int(x / x_scale)
        y_rounded = int(y / y_scale)

        x_cell_pos = x_rounded * x_scale
        y_cell_pos = y_rounded * y_scale

        new_cell_coord = (x_rounded, y_rounded)
        if new_cell_coord not in self._initial_state:
            self._initial_state.add(new_cell_coord)
            rect = (x_cell_pos, y_cell_pos, GRID_SIZE, GRID_SIZE)
            pygame.draw.rect(self._grid_surface, '#ffffff', rect)

        elif new_cell_coord in self._initial_state:
            self._last_click_short = False
            self._initial_state.remove(new_cell_coord)
            rect = (x_cell_pos, y_cell_pos, GRID_SIZE - 1, GRID_SIZE - 1)
            pygame.draw.rect(self._grid_surface, '#000000', rect)

        self._refresh_grid()
        self._refresh_header()

    def _draw_current_state(self):
        self._draw_live_cells()
        self._erase_dead_cells()

    def _advance_turn(self):
        self._processing_turn = True
        self._game.run(1)
        self._draw_current_state()
        self._processing_turn = False

    def _draw_live_cells(self):
        points = self._game.grid.points

        for x, y in points:
            if self._game.grid.get_point(x, y):
                x = x * GRID_SIZE
                y = y * GRID_SIZE
                rect = (x, y, GRID_SIZE, GRID_SIZE)
                pygame.draw.rect(self._grid_surface, '#ffffff', rect)

        self._refresh_grid()
        self._refresh_header()

    def _erase_dead_cells(self):
        points = self._game.grid.points

        for x, y in points:
            if not self._game.grid.get_point(x, y):
                x = x * GRID_SIZE
                y = y * GRID_SIZE
                rect = (x, y, GRID_SIZE, GRID_SIZE)
                pygame.draw.rect(self._grid_surface, '#666666', rect)

        self._refresh_grid()
        self._refresh_header()

    def _draw_empty_cells(self):
        screen_size = self._grid_surface.get_size()
        points = self._game.grid.inverse_points

        for x, y in points:
            x = (screen_size[0] / 2) + (x * GRID_SIZE)
            y = (screen_size[1] / 2) + (y * GRID_SIZE)
            rect = (x, y, GRID_SIZE, GRID_SIZE)
            pygame.draw.rect(self._grid_surface, '#333344', rect)

        self._refresh_grid()
        self._refresh_header()


class Life:
    def __init__(self):
        self._grid = SparseGrid()

    @property
    def count(self):
        return len({p for p in self._grid.points if self._grid.get_point(*p)})

    @property
    def grid(self):
        return self._grid

    def set_initial_state(self, cells: list):
        self._points = dict()
        for cell in cells:
            if type(cell) is not tuple:
                raise TypeError

            if type(cell[0]) is not int or type(cell[1]) is not int:
                raise TypeError

            self._grid.set_point(*cell, True)

    def run(self, number_of_turns: int):
        if number_of_turns is None:
            number_of_turns = math.inf

        turn_number = 0
        while number_of_turns > turn_number:
            for x, y in self._grid.points:
                point_value = self._grid.get_point(x, y)
                if point_value:
                    continue

                self._grid.del_point(x, y)

            born_cells, dead_cells = self.evaluate_next_turn()

            for x, y in dead_cells:
                self._grid.set_point(x, y, False)

            for x, y in born_cells:
                self._grid.set_point(x, y, True)

            turn_number += 1

    def evaluate_next_turn(self):
        empty_cells = set((x, y) for x, y in self._grid.inverse_points)
        all_cells = self._grid.points.union(empty_cells)

        born_cells = set()
        dead_cells = set()

        living_cells = set(p for p in self.grid.points
                           if self.grid.get_point(*p))

        for cell in all_cells:
            neighbors = self._grid.get_neighbors(*cell)
            living_neighbors = len(neighbors & living_cells)
            is_alive = self._grid.get_point(*cell)

            if is_alive and not (4 > living_neighbors > 1):
                dead_cells.add(cell)
            elif not is_alive and living_neighbors == 3:
                born_cells.add(cell)

        return born_cells, dead_cells


class SparseGrid:

    def __init__(self):
        self._points = dict()

    def __repr__(self):
        return str(self._points)

    @property
    def max_point(self):
        if self._points:
            max_x = max(x for x, _ in self._points)
            max_y = max(y for _, y in self._points)
        else:
            max_x, max_y = 0, 0
        return (max_x, max_y)

    @property
    def min_point(self):
        if self._points:
            min_y = min(y for _, y in self._points)
            min_x = min(x for x, _ in self._points)
        else:
            min_y, min_x = 0, 0
        return (min_x, min_y)

    @property
    def count(self):
        return len(self._points)

    @property
    def points(self):
        return set(self._points.keys())

    @property
    def inverse_points(self):
        # pad grid range by 1 to account for cells that might be born the next
        # turn
        x_range = range(self.min_point[0] - 1, self.max_point[0] + 2)
        y_range = range(self.min_point[1] - 1, self.max_point[1] + 2)

        empty_points = set()

        for x in x_range:
            for y in y_range:
                if (x, y) in self._points:
                    continue
                for neighbor in self.get_neighbors(x, y):
                    if neighbor in self._points:
                        empty_points.add((x, y))
                        break

        return empty_points

    def del_point(self, x: int, y: int):
        del self._points[(x, y)]

    def set_point(self, x: int, y: int, value: object):
        self._points[(x, y)] = value

    def get_point(self, x: int, y: int):
        try:
            return self._points[(x, y)]
        except KeyError:
            return None

    @staticmethod
    def get_neighbors(x: int, y: int):
        return {(x - 1, y - 1), (x, y - 1), (x + 1, y - 1),
                (x - 1, y),                 (x + 1, y),
                (x - 1, y + 1), (x, y + 1), (x + 1, y + 1)}


if __name__ == '__main__':
    interface = LifeController()
    interface.main()
    # game.set_initial_state(initial_values)
