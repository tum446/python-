
import os
import sys
import pygame
from utils import *
from config import *

'''游戏主程序'''


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('乐乐消消乐')

    # 1. 加载背景音乐
    pygame.mixer.init()
    bgm_list = [
        os.path.join(ROOTDIR, "resources/audios/bgm.flac"),
        os.path.join(ROOTDIR, "resources/audios/bg.flac")
    ]
    bgm_player = BgmPlayer(bgm_list)

    # 2. 加载音效
    sounds = {}
    sounds['mismatch'] = pygame.mixer.Sound(os.path.join(ROOTDIR, 'resources/audios/badswap.wav'))
    sounds['match'] = []
    for i in range(6):
        sounds['match'].append(pygame.mixer.Sound(os.path.join(ROOTDIR, 'resources/audios/match%s.wav' % i)))

    # 3. 加载字体
    font = pygame.font.Font(os.path.join(ROOTDIR, 'resources/font.TTF'), 25)

    # 4. 图片加载
    gem_imgs = []
    for i in range(1, 8):
        gem_imgs.append(os.path.join(ROOTDIR, 'resources/images/gem%s.png' % i))

    # 5. 实例化游戏并进入主循环
    game = gemGame(screen, sounds, font, gem_imgs, bgm_player)  

    while True:
        score = game.start()
        flag = False

        # 结算界面
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE):
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYUP and event.key == pygame.K_r:
                    flag = True
                elif event.type == pygame.USEREVENT:
                    bgm_player.next_bgm()  # 结算时继续切歌

            if flag:
                break
            screen.fill((135, 206, 235))
            text0 = 'Final score: %s' % score
            text1 = 'Press <R> to restart the game.'
            text2 = 'Press <Esc> to quit the game.'
            y = 150
            for idx, text in enumerate([text0, text1, text2]):
                text_render = font.render(text, 1, (85, 65, 0))
                rect = text_render.get_rect()
                if idx == 0:
                    rect.left, rect.top = (212, y)
                elif idx == 1:
                    rect.left, rect.top = (122.5, y)
                else:
                    rect.left, rect.top = (126.5, y)
                y += 100
                screen.blit(text_render, rect)
            pygame.display.update()
            pygame.time.Clock().tick(FPS)

        game.reset()


if __name__ == '__main__':
    main()