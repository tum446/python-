'''
Function:
	工具函数
'''
import sys
import time
import random
import pygame
from config import *

'''拼图精灵类'''


class gemSprite(pygame.sprite.Sprite):
    def __init__(self, img_path, size, position, downlen, **kwargs):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load(img_path)
        self.image = pygame.transform.smoothscale(self.image, size)
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = position
        self.downlen = downlen
        self.target_x = position[0]
        self.target_y = position[1] + downlen
        self.type = img_path.split('/')[-1].split('.')[0]
        self.fixed = False
        self.speed_x = 10
        self.speed_y = 10
        self.direction = 'down'

    def move(self):
        if self.direction == 'down':
            self.rect.top = min(self.target_y, self.rect.top + self.speed_y)
            if self.target_y == self.rect.top:
                self.fixed = True
        elif self.direction == 'up':
            self.rect.top = max(self.target_y, self.rect.top - self.speed_y)
            if self.target_y == self.rect.top:
                self.fixed = True
        elif self.direction == 'left':
            self.rect.left = max(self.target_x, self.rect.left - self.speed_x)
            if self.target_x == self.rect.left:
                self.fixed = True
        elif self.direction == 'right':
            self.rect.left = min(self.target_x, self.rect.left + self.speed_x)
            if self.target_x == self.rect.left:
                self.fixed = True

    def getPosition(self):
        return self.rect.left, self.rect.top

    def setPosition(self, position):
        self.rect.left, self.rect.top = position


'''背景音乐管理器类'''


class BgmPlayer():
    def __init__(self, bgm_list, volume=0.6):
        self.bgm_list = bgm_list
        self.current_index = 0
        pygame.mixer.music.set_volume(volume)
        self.play_current()

    def play_current(self):
        pygame.mixer.music.load(self.bgm_list[self.current_index])
        pygame.mixer.music.play()
        pygame.mixer.music.set_endevent(pygame.USEREVENT)

    def next_bgm(self):
        self.current_index = (self.current_index + 1) % len(self.bgm_list)
        self.play_current()


'''游戏类'''


class gemGame():
    def __init__(self, screen, sounds, font, gem_imgs, bgm_player, **kwargs):
        self.info = 'Gemgem-微信公众号:Charles的皮卡丘'
        self.screen = screen
        self.sounds = sounds
        self.font = font
        self.gem_imgs = gem_imgs
        self.bgm_player = bgm_player  # 接收音乐管理器
        self.reset()

    def start(self):
        clock = pygame.time.Clock()
        overall_moving = True
        individual_moving = False
        gem_selected_xy = None
        gem_selected_xy2 = None
        swap_again = False
        add_score = 0
        add_score_showtimes = 10
        time_pre = pygame.time.get_ticks()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE):
                    pygame.quit()
                    sys.exit()
                # --- 在此处监听音乐播放结束，实现无限循环 ---
                elif event.type == pygame.USEREVENT:
                    self.bgm_player.next_bgm()
                # --------------------------------------------
                elif event.type == pygame.MOUSEBUTTONUP:
                    if (not overall_moving) and (not individual_moving) and (not add_score):
                        position = pygame.mouse.get_pos()
                        if gem_selected_xy is None:
                            gem_selected_xy = self.checkSelected(position)
                        else:
                            gem_selected_xy2 = self.checkSelected(position)
                            if gem_selected_xy2:
                                if self.swapGem(gem_selected_xy, gem_selected_xy2):
                                    individual_moving = True
                                    swap_again = False
                                else:
                                    gem_selected_xy = None

            if overall_moving:
                overall_moving = not self.dropGems(0, 0)
                if not overall_moving:
                    res_match = self.isMatch()
                    add_score = self.removeMatched(res_match)
                    if add_score > 0:
                        overall_moving = True

            if individual_moving:
                gem1 = self.getGemByPos(*gem_selected_xy)
                gem2 = self.getGemByPos(*gem_selected_xy2)
                gem1.move()
                gem2.move()
                if gem1.fixed and gem2.fixed:
                    res_match = self.isMatch()
                    if res_match[0] == 0 and not swap_again:
                        swap_again = True
                        self.swapGem(gem_selected_xy, gem_selected_xy2)
                        self.sounds['mismatch'].play()
                    else:
                        add_score = self.removeMatched(res_match)
                        overall_moving = True
                        individual_moving = False
                        gem_selected_xy = None
                        gem_selected_xy2 = None

            self.screen.fill((135, 206, 235))
            self.drawGrids()
            self.gems_group.draw(self.screen)
            if gem_selected_xy:
                self.drawBlock(self.getGemByPos(*gem_selected_xy).rect)

            if add_score:
                if add_score_showtimes == 10:
                    random.choice(self.sounds['match']).play()
                self.drawAddScore(add_score)
                add_score_showtimes -= 1
                if add_score_showtimes < 1:
                    add_score_showtimes = 10
                    add_score = 0

            current_time = pygame.time.get_ticks()
            if current_time - time_pre >= 1000:
                self.remaining_time -= (current_time - time_pre) // 1000
                time_pre = current_time

            self.showRemainingTime()
            self.drawScore()
            if self.remaining_time <= 0:
                return self.score
            pygame.display.update()
            clock.tick(FPS)

    def reset(self):
        while True:
            self.all_gems = []
            self.gems_group = pygame.sprite.Group()
            for x in range(NUMGRID):
                self.all_gems.append([])
                for y in range(NUMGRID):
                    gem = gemSprite(img_path=random.choice(self.gem_imgs), size=(GRIDSIZE, GRIDSIZE),
                                    position=[XMARGIN + x * GRIDSIZE, YMARGIN + y * GRIDSIZE - NUMGRID * GRIDSIZE],
                                    downlen=NUMGRID * GRIDSIZE)
                    self.all_gems[x].append(gem)
                    self.gems_group.add(gem)
            if self.isMatch()[0] == 0:
                break
        self.score = 0
        self.reward = 10
        self.remaining_time = 600

    def showRemainingTime(self):
        remaining_time_render = self.font.render('CountDown: %ss' % str(self.remaining_time), 1, (85, 65, 0))
        rect = remaining_time_render.get_rect()
        rect.left, rect.top = (WIDTH - 201, 6)
        self.screen.blit(remaining_time_render, rect)

    def drawScore(self):
        score_render = self.font.render('SCORE:' + str(self.score), 1, (85, 65, 0))
        rect = score_render.get_rect()
        rect.left, rect.top = (10, 6)
        self.screen.blit(score_render, rect)

    def drawAddScore(self, add_score):
        score_render = self.font.render('+' + str(add_score), 0, (255, 100, 100))
        rect = score_render.get_rect()
        rect.left, rect.top = (250, 250)
        self.screen.blit(score_render, rect)

    '''生成新的拼图块'''

    def generateNewGems(self, res_match):
        # 如果是横向消除 (1)
        if res_match[0] == 1:
            start_x, start_y, count = res_match[1], res_match[2], res_match[3]
            # 1. 彻底清除被消除的块
            for i in range(count):
                gem = self.getGemByPos(start_x + i, start_y)
                if gem:
                    self.gems_group.remove(gem)
                    self.all_gems[start_x + i][start_y] = None
            # 2. 每一列独立进行下落和生成
            for i in range(count):
                x = start_x + i
                # 收集当前列上面还活着的所有块
                alive_gems = []
                for y in range(start_y - 1, -1, -1):
                    gem = self.getGemByPos(x, y)
                    if gem:
                        alive_gems.append(gem)
                        self.all_gems[x][y] = None
                # 让活着块重新落位
                current_y = start_y
                for gem in alive_gems:
                    gem.target_y = YMARGIN + current_y * GRIDSIZE
                    gem.fixed = False
                    gem.direction = 'down'
                    self.all_gems[x][current_y] = gem
                    current_y -= 1
                # 在顶部生成新块
                for y in range(current_y, -1, -1):
                    gem = gemSprite(img_path=random.choice(self.gem_imgs), size=(GRIDSIZE, GRIDSIZE),
                                    position=[XMARGIN + x * GRIDSIZE, YMARGIN + y * GRIDSIZE - GRIDSIZE * (count)],
                                    downlen=GRIDSIZE * (count))
                    self.gems_group.add(gem)
                    self.all_gems[x][y] = gem

        # 如果是纵向消除 (2)
        elif res_match[0] == 2:
            start_x, start_y, count = res_match[1], res_match[2], res_match[3]
            # 1. 清除
            for i in range(count):
                gem = self.getGemByPos(start_x, start_y + i)
                if gem:
                    self.gems_group.remove(gem)
                    self.all_gems[start_x][start_y + i] = None
            # 2. 该列上方存活块下落
            alive_gems = []
            for y in range(start_y - 1, -1, -1):
                gem = self.getGemByPos(start_x, y)
                if gem:
                    alive_gems.append(gem)
                    self.all_gems[start_x][y] = None

            current_y = start_y + count - 1
            for gem in alive_gems:
                gem.target_y = YMARGIN + current_y * GRIDSIZE
                gem.fixed = False
                gem.direction = 'down'
                self.all_gems[start_x][current_y] = gem
                current_y -= 1
            # 3. 顶部生成新块
            for y in range(current_y, -1, -1):
                gem = gemSprite(img_path=random.choice(self.gem_imgs), size=(GRIDSIZE, GRIDSIZE),
                                position=[XMARGIN + start_x * GRIDSIZE, YMARGIN + y * GRIDSIZE - GRIDSIZE * (count)],
                                downlen=GRIDSIZE * (count))
                self.gems_group.add(gem)
                self.all_gems[start_x][y] = gem

    def removeMatched(self, res_match):
        if res_match[0] > 0:
            count = res_match[3]
            add_score = 10 + (count - 3) * 10
            self.generateNewGems(res_match)
            self.score += add_score
            return add_score
        return 0

    def drawGrids(self):
        for x in range(NUMGRID):
            for y in range(NUMGRID):
                rect = pygame.Rect((XMARGIN + x * GRIDSIZE, YMARGIN + y * GRIDSIZE, GRIDSIZE, GRIDSIZE))
                self.drawBlock(rect, color=(0, 0, 255), size=1)

    def drawBlock(self, block, color=(255, 0, 255), size=4):
        pygame.draw.rect(self.screen, color, block, size)

    def dropGems(self, x, y):
        if not self.getGemByPos(x, y).fixed:
            self.getGemByPos(x, y).move()
        if x < NUMGRID - 1:
            x += 1
            return self.dropGems(x, y)
        elif y < NUMGRID - 1:
            x = 0
            y += 1
            return self.dropGems(x, y)
        else:
            return self.isFull()

    def isFull(self):
        for x in range(NUMGRID):
            for y in range(NUMGRID):
                if not self.getGemByPos(x, y).fixed:
                    return False
        return True

    def checkSelected(self, position):
        for x in range(NUMGRID):
            for y in range(NUMGRID):
                if self.getGemByPos(x, y).rect.collidepoint(*position):
                    return [x, y]
        return None

    def isMatch(self):
        for x in range(NUMGRID):
            for y in range(NUMGRID):
                if x + 2 < NUMGRID:
                    if self.getGemByPos(x, y).type == self.getGemByPos(x + 1, y).type == self.getGemByPos(x + 2,
                                                                                                          y).type:
                        count = 3
                        while x + count < NUMGRID and self.getGemByPos(x, y).type == self.getGemByPos(x + count,
                                                                                                      y).type:
                            count += 1
                        return [1, x, y, count]
                if y + 2 < NUMGRID:
                    if self.getGemByPos(x, y).type == self.getGemByPos(x, y + 1).type == self.getGemByPos(x,
                                                                                                          y + 2).type:
                        count = 3
                        while y + count < NUMGRID and self.getGemByPos(x, y).type == self.getGemByPos(x,
                                                                                                      y + count).type:
                            count += 1
                        return [2, x, y, count]
        return [0, x, y, 0]

    def getGemByPos(self, x, y):
        return self.all_gems[x][y]

    def swapGem(self, gem1_pos, gem2_pos):
        margin = gem1_pos[0] - gem2_pos[0] + gem1_pos[1] - gem2_pos[1]
        if abs(margin) != 1:
            return False
        gem1 = self.getGemByPos(*gem1_pos)
        gem2 = self.getGemByPos(*gem2_pos)
        if gem1_pos[0] - gem2_pos[0] == 1:
            gem1.direction = 'left'
            gem2.direction = 'right'
        elif gem1_pos[0] - gem2_pos[0] == -1:
            gem2.direction = 'left'
            gem1.direction = 'right'
        elif gem1_pos[1] - gem2_pos[1] == 1:
            gem1.direction = 'up'
            gem2.direction = 'down'
        elif gem1_pos[1] - gem2_pos[1] == -1:
            gem2.direction = 'up'
            gem1.direction = 'down'
        gem1.target_x = gem2.rect.left
        gem1.target_y = gem2.rect.top
        gem1.fixed = False
        gem2.target_x = gem1.rect.left
        gem2.target_y = gem1.rect.top
        gem2.fixed = False
        self.all_gems[gem2_pos[0]][gem2_pos[1]] = gem1
        self.all_gems[gem1_pos[0]][gem1_pos[1]] = gem2
        return True

    def __repr__(self):
        return self.info