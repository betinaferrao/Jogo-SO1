import pygame
import threading
import random
import time
import os

# Configurações iniciais
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Jogo Antiaéreo")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

# Diretório de imagens
IMG_DIR = "imagens"

# Parâmetros de dificuldade
dificuldades = {
    "fácil": {"k": 20, "velocidade_nave": 1, "quantidade_naves": 20, "intervalo_naves": (1, 3)},
    "médio": {"k": 15, "velocidade_nave": 2, "quantidade_naves": 30, "intervalo_naves": (0.5, 2)},
    "difícil": {"k": 10, "velocidade_nave": 3, "quantidade_naves": 50, "intervalo_naves": (0.1, 1)}
}

# Variáveis globais
naves = []
foguetes = []
threads_naves = []
threads_foguetes = []
threads_gerar_naves = []
threads_recarregar = []
mutex_naves = threading.Lock()
mutex_foguetes = threading.Lock()
mutex_recarga = threading.Lock()
foguetes_disponiveis = 0
recarregando = False
jogador_pos = 90  # Ângulo inicial do lançador
naves_abatidas = 0
naves_atingiram_solo = 0
estado_jogo = "menu"  # Pode ser "menu", "jogando", "vitoria" ou "derrota"
running = True

# Carregar imagens
def carregar_imagem(nome_arquivo):
    return pygame.image.load(os.path.join(IMG_DIR, nome_arquivo)).convert_alpha()

img_nave = carregar_imagem("nave.png")
img_foguete = carregar_imagem("foguete.png")
img_lancador = carregar_imagem("canhao.png")

nave_largura, nave_altura = img_nave.get_size()
foguete_largura, foguete_altura = img_foguete.get_size()
lancador_largura, lancador_altura = img_lancador.get_size()

# Classe Nave
class Nave(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.x = random.randint(0, 800 - nave_largura)
        self.y = 0
        self.velocidade = dificuldades[dificuldade]["velocidade_nave"]
        self.ativa = True

    def run(self):
        global naves_atingiram_solo, running
        while self.y < 600 and self.ativa and running:
            with mutex_naves:
                self.y += self.velocidade
            time.sleep(0.01)
        if self.ativa:
            with mutex_naves:
                naves_atingiram_solo += 1

# Classe Foguete
class Foguete(threading.Thread):
    def __init__(self, angulo):
        threading.Thread.__init__(self)
        self.x = 400
        self.y = 570
        self.angulo = angulo
        self.ativo = True

    def run(self):
        global naves_abatidas, running
        while self.y > 0 and self.ativo and running:
            with mutex_foguetes:
                if self.angulo == 90:
                    self.y -= 5
                elif self.angulo == 45:
                    self.y -= 5
                    self.x -= 5
                elif self.angulo == -45:
                    self.y -= 5
                    self.x += 5
                elif self.angulo == 180:
                    self.x -= 5
                elif self.angulo == -180:
                    self.x += 5
            self.verificar_colisao()
            time.sleep(0.01)

    def verificar_colisao(self):
        global naves, naves_abatidas
        with mutex_naves:
            for nave in naves:
                if nave.x < self.x < nave.x + nave_largura and nave.y < self.y < nave.y + nave_altura:
                    nave.ativa = False
                    naves.remove(nave)
                    naves_abatidas += 1
                    break

# Função de recarregar
def recarregar():
    global foguetes_disponiveis, recarregando
    with mutex_recarga:
        foguetes_disponiveis = dificuldades[dificuldade]["k"]
        recarregando = False

# Função para desenhar objetos na tela
def desenhar_tela():
    screen.fill((0, 0, 0))
    if estado_jogo == "menu":
        desenhar_menu()
    else:
        with mutex_naves:
            for nave in naves:
                screen.blit(img_nave, (nave.x, nave.y))
        with mutex_foguetes:
            for foguete in foguetes:
                screen.blit(img_foguete, (foguete.x, foguete.y))
        screen.blit(img_lancador, (400 - lancador_largura // 2, 600 - lancador_altura))  # Lançador na parte inferior da tela
        texto_foguetes = font.render(f"Foguetes: {foguetes_disponiveis}", True, (255, 255, 255))
        screen.blit(texto_foguetes, (10, 10))
        texto_abatidas = font.render(f"Naves Abatidas: {naves_abatidas}", True, (255, 255, 255))
        screen.blit(texto_abatidas, (10, 40))
        texto_atingiram_solo = font.render(f"Naves no Solo: {naves_atingiram_solo}", True, (255, 255, 255))
        screen.blit(texto_atingiram_solo, (10, 70))
        if estado_jogo in ["vitoria", "derrota"]:
            texto_resultado = font.render(f"{estado_jogo.capitalize()}!", True, (255, 255, 255))
            text_rect = texto_resultado.get_rect(center=(400, 300))
            screen.blit(texto_resultado, text_rect)
    pygame.display.flip()

# Função para desenhar o menu
def desenhar_menu():
    titulo = font.render("Jogo Antiaéreo", True, (255, 255, 255))
    screen.blit(titulo, (300, 100))
    facil = font.render("1. Fácil", True, (255, 255, 255))
    screen.blit(facil, (350, 200))
    medio = font.render("2. Médio", True, (255, 255, 255))
    screen.blit(medio, (350, 250))
    dificil = font.render("3. Difícil", True, (255, 255, 255))
    screen.blit(dificil, (350, 300))

# Função para gerar naves
def gerar_naves():
    global running
    while estado_jogo == "jogando" and running:
        if len(naves) < dificuldades[dificuldade]["quantidade_naves"]:
            nave = Nave()
            nave.start()
            with mutex_naves:
                naves.append(nave)
            threads_naves.append(nave)  # Adiciona a thread à lista de threads de naves
        time.sleep(random.uniform(*dificuldades[dificuldade]["intervalo_naves"]))  # Tempo aleatório para criar novas naves

# Função principal do jogo
def main():
    global recarregando, foguetes_disponiveis, jogador_pos, naves_abatidas, naves_atingiram_solo, estado_jogo, dificuldade, running, threads_gerar_naves, threads_recarregar

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if estado_jogo == "menu":
                    if event.key == pygame.K_1:
                        dificuldade = "fácil"
                        foguetes_disponiveis = dificuldades[dificuldade]["k"]
                        estado_jogo = "jogando"
                        # Iniciar thread de gerar naves ao começar o jogo
                        t = threading.Thread(target=gerar_naves, daemon=True)
                        t.start()
                        threads_gerar_naves.append(t)
                    elif event.key == pygame.K_2:
                        dificuldade = "médio"
                        foguetes_disponiveis = dificuldades[dificuldade]["k"]
                        estado_jogo = "jogando"
                        # Iniciar thread de gerar naves ao começar o jogo
                        t = threading.Thread(target=gerar_naves, daemon=True)
                        t.start()
                        threads_gerar_naves.append(t)
                    elif event.key == pygame.K_3:
                        dificuldade = "difícil"
                        foguetes_disponiveis = dificuldades[dificuldade]["k"]
                        estado_jogo = "jogando"
                        # Iniciar thread de gerar naves ao começar o jogo
                        t = threading.Thread(target=gerar_naves, daemon=True)
                        t.start()
                        threads_gerar_naves.append(t)
                elif estado_jogo == "jogando":
                    if event.key == pygame.K_SPACE and foguetes_disponiveis > 0:
                        foguete = Foguete(jogador_pos)
                        foguete.start()
                        with mutex_foguetes:
                            foguetes.append(foguete)
                        threads_foguetes.append(foguete)  # Adiciona a thread à lista de threads de foguetes
                        with mutex_recarga:
                            foguetes_disponiveis -= 1
                    elif event.key == pygame.K_r and not recarregando:
                        recarregando = True
                        t = threading.Thread(target=recarregar, daemon=True)
                        t.start()
                        threads_recarregar.append(t)
                    elif event.key == pygame.K_a:
                        jogador_pos = 180  # Lado esquerdo
                    elif event.key == pygame.K_q:
                        jogador_pos = 45  # Diagonal esquerda
                    elif event.key == pygame.K_w:
                        jogador_pos = 90  # Para cima
                    elif event.key == pygame.K_e:
                        jogador_pos = -45  # Diagonal direita
                    elif event.key == pygame.K_d:
                        jogador_pos = -180  # Lado direito

        desenhar_tela()
        if estado_jogo == "jogando":
            verificar_estado_jogo()
        clock.tick(30)

    # Aguarda todas as threads terminarem
    for t in threads_naves:
        t.join()
    for t in threads_foguetes:
        t.join()
    for t in threads_gerar_naves:
        t.join()
    for t in threads_recarregar:
        t.join()

    pygame.quit()

def verificar_estado_jogo():
    global naves_abatidas, naves_atingiram_solo, naves, foguetes, estado_jogo, threads_gerar_naves, threads_recarregar
    total_naves = dificuldades[dificuldade]["quantidade_naves"]
    if estado_jogo == "jogando":
        if naves_abatidas >= total_naves / 2:
            estado_jogo = "vitoria"
        elif naves_atingiram_solo > total_naves / 2:
            estado_jogo = "derrota"
        if estado_jogo in ["vitoria", "derrota"]:
            with mutex_naves:
                for nave in naves:
                    nave.ativa = False
                naves.clear()
            with mutex_foguetes:
                for foguete in foguetes:
                    foguete.ativo = False
                foguetes.clear()


if __name__ == "__main__":
    main()
