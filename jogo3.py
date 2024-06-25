import pygame
import threading
import random
import time
import os

# Constantes do jogo
LARGURA_TELA = 800
ALTURA_TELA = 600
CORES = {
    'PRETO': (0, 0, 0),
    'BRANCO': (255, 255, 255),
    'VERMELHO': (255, 0, 0),
    'VERDE': (0, 255, 0)
}

# Mutexes
mutex_naves = threading.Lock()
mutex_foguetes = threading.Lock()
mutex_estado_jogo = threading.Lock()

# Estado do jogo
naves_abatidas = 0
naves_atingiram_solo = 0
jogo_ativo = True
vitoria = False
derrota = False
dificuldade = 'medio'  # Pode ser 'facil', 'medio' ou 'dificil'

IMG_DIR = 'imagens'

# Parâmetros de dificuldade
dificuldades = {
    'facil': {'foguetes': 30, 'naves': 20, 'velocidade_naves': 1},
    'medio': {'foguetes': 20, 'naves': 30, 'velocidade_naves': 2},
    'dificil': {'foguetes': 10, 'naves': 40, 'velocidade_naves': 3}
}

# Carregar imagens
def carregar_imagem(nome_arquivo):
    return pygame.image.load(os.path.join(IMG_DIR, nome_arquivo)).convert_alpha()

def selecionar_dificuldade():
    global dificuldade
    
    pygame.init()
    tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
    pygame.display.set_caption("Escolha a Dificuldade")
    
    fonte_titulo = pygame.font.Font(None, 48)
    fonte_opcao = pygame.font.Font(None, 36)
    
    texto_titulo = fonte_titulo.render('Escolha a Dificuldade:', True, CORES['BRANCO'])
    texto_facil = fonte_opcao.render('Fácil (pressione F)', True, CORES['BRANCO'])
    texto_medio = fonte_opcao.render('Médio (pressione M)', True, CORES['BRANCO'])
    texto_dificil = fonte_opcao.render('Difícil (pressione D)', True, CORES['BRANCO'])

    itens_menu = [texto_facil, texto_medio, texto_dificil]
    
    rodando = True
    
    while rodando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                return
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_f:
                    dificuldade = 'facil'
                    rodando = False
                elif evento.key == pygame.K_m:
                    dificuldade = 'medio'
                    rodando = False
                elif evento.key == pygame.K_d:
                    dificuldade = 'dificil'
                    rodando = False
                elif evento.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return
        
        tela.fill(CORES['PRETO'])
        tela.blit(texto_titulo, ((LARGURA_TELA - texto_titulo.get_width()) // 2, 150))
        
        for i, texto in enumerate(itens_menu):
            pos_y = 250 + i * 50
            tela.blit(texto, ((LARGURA_TELA - texto.get_width()) // 2, pos_y))
        
        pygame.display.flip()
    pygame.quit()


# Classe Nave
class Nave(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = carregar_imagem('nave.png')  # Substituir pelo nome da sua imagem de nave
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, LARGURA_TELA - self.rect.width)
        self.rect.y = 0
        self.speed = dificuldades[dificuldade]['velocidade_naves']

    def update(self):
        self.rect.y += self.speed
        if self.rect.y > ALTURA_TELA:
            with mutex_naves:
                global naves_atingiram_solo
                naves_atingiram_solo += 1
            self.kill()

# Classe Foguete
class Foguete(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        self.image = carregar_imagem('foguete.png')  # Substituir pelo nome da sua imagem de foguete
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = 10
        self.direction = direction

    def update(self):
        if self.direction == 'up':
            self.rect.y -= self.speed
        elif self.direction == 'left':
            self.rect.x -= self.speed
        elif self.direction == 'right':
            self.rect.x += self.speed
        elif self.direction == 'upleft':
            self.rect.x -= self.speed // 2
            self.rect.y -= self.speed // 2
        elif self.direction == 'upright':
            self.rect.x += self.speed // 2
            self.rect.y -= self.speed // 2

        if self.rect.y < 0 or self.rect.x < 0 or self.rect.x > LARGURA_TELA:
            self.kill()

# Classe Bateria
class Bateria(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = carregar_imagem('canhao.png')  # Substituir pelo nome da sua imagem de canhão
        self.rect = self.image.get_rect()
        self.rect.centerx = LARGURA_TELA // 2
        self.rect.bottom = ALTURA_TELA
        self.position = 'up'
        self.foguetes = dificuldades[dificuldade]['foguetes']
        self.lock = threading.Lock()

    def recarregar_foguetes(self):
        with self.lock:
            # time.sleep(3)  
            self.foguetes = dificuldades[dificuldade]['foguetes']

# Thread Principal do Jogo
def thread_principal_jogo():
    global jogo_ativo, naves_abatidas, naves_atingiram_solo, dificuldade, vitoria, derrota
    while jogo_ativo:
        if naves_abatidas >= dificuldades[dificuldade]['naves'] * 0.5:
            vitoria = True
            jogo_ativo = False
        elif naves_atingiram_solo >= dificuldades[dificuldade]['naves'] * 0.5:
            derrota = True
            jogo_ativo = False
        time.sleep(1)

# Thread de Movimentação das Naves
def thread_movimentacao_naves(naves, todas_as_sprites):
    global jogo_ativo
    while jogo_ativo:
        with mutex_naves:
            if len(naves) < 10:
                nave = Nave()
                naves.add(nave)
                todas_as_sprites.add(nave)
        time.sleep(1)

# Thread de Controle de Foguetes
def thread_controle_foguetes(direcao, bateria, naves, foguetes, todas_as_sprites):
    foguete = Foguete(bateria.rect.centerx, bateria.rect.top, direcao)
    foguetes.add(foguete)
    todas_as_sprites.add(foguete)
    global jogo_ativo
    while jogo_ativo:
        foguete.update()
        colisao = pygame.sprite.spritecollide(foguete, naves, True)
        if colisao:
            with mutex_estado_jogo:
                global naves_abatidas
                naves_abatidas += 1
            foguete.kill()
            break
        if foguete.rect.y < 0 or foguete.rect.x < 0 or foguete.rect.x > LARGURA_TELA:
            foguete.kill()
            break
        time.sleep(0.05)

# Função para exibir mensagens de vitória ou derrota
def exibir_mensagem(texto):
    pygame.init()
    tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
    tela.fill(CORES['PRETO'])
    fonte = pygame.font.Font(None, 48)
    texto_surface = fonte.render(texto, True, CORES['BRANCO'])
    texto_rect = texto_surface.get_rect()
    texto_rect.center = (LARGURA_TELA // 2, ALTURA_TELA // 2)
    tela.blit(texto_surface, texto_rect)
    pygame.display.flip()

    rodando = True
    while rodando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False

    pygame.quit()

# Função principal do jogo
def jogo():
    global jogo_ativo, vitoria, derrota

    selecionar_dificuldade()

    pygame.init()
    tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
    pygame.display.set_caption("Jogo de Defesa Antiaérea")

    todas_as_sprites = pygame.sprite.Group()
    naves = pygame.sprite.Group()
    foguetes = pygame.sprite.Group()

    bateria = Bateria()
    todas_as_sprites.add(bateria)

    thread_principal = threading.Thread(target=thread_principal_jogo)
    thread_movimentacao = threading.Thread(target=thread_movimentacao_naves, args=(naves, todas_as_sprites))

    thread_principal.start()
    thread_movimentacao.start()

    relogio = pygame.time.Clock()
    rodando = True

    while rodando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_a:
                    bateria.position = 'left'
                elif evento.key == pygame.K_d:
                    bateria.position = 'right'
                elif evento.key == pygame.K_w:
                    bateria.position = 'up'
                elif evento.key == pygame.K_s:
                    bateria.position = 'down'
                elif evento.key == pygame.K_q:
                    bateria.position = 'upleft'
                elif evento.key == pygame.K_e:
                    bateria.position = 'upright'
                elif evento.key == pygame.K_SPACE:
                    with mutex_foguetes:
                        if bateria.foguetes > 0:
                            threading.Thread(target=thread_controle_foguetes, args=(bateria.position, bateria, naves, foguetes, todas_as_sprites)).start()
                            bateria.foguetes -= 1
                elif evento.key == pygame.K_r:
                    threading.Thread(target=bateria.recarregar_foguetes).start()

        todas_as_sprites.update()

        tela.fill(CORES['PRETO'])
        todas_as_sprites.draw(tela)

        fonte = pygame.font.Font(None, 36)
        text_foguetes = fonte.render(f"Foguetes: {bateria.foguetes}", True, CORES['BRANCO'])
        tela.blit(text_foguetes, (10, 10))

        text_naves_abatidas = fonte.render(f"Naves abatidas: {naves_abatidas}", True, CORES['BRANCO'])
        tela.blit(text_naves_abatidas, (10, 50))
        text_naves_atingiram = fonte.render(f"Naves que atingiram o solo: {naves_atingiram_solo}", True, CORES['BRANCO'])
        tela.blit(text_naves_atingiram, (10, 90))

        pygame.display.flip()
        relogio.tick(60)

        if vitoria:
            exibir_mensagem("Vitória!")
            break
        elif derrota:
            exibir_mensagem("Derrota!")
            break

    jogo_ativo = False

    thread_principal.join()
    thread_movimentacao.join()

    pygame.quit()

if __name__ == "__main__":
    jogo()
