import random
import cv2
from cvzone.HandTrackingModule import HandDetector
import serial
import time

# Constantes e configurações
SERIAL_PORT = "COM5"
SERIAL_BAUDRATE = 9600
CAPTURE_DEVICE = 0
DETECTION_CONFIDENCE = 0.7
WAIT_KEY_DELAY = 1
CLOSE_HAND_CMD = "$00000"
GESTOS_COMANDOS = {"pedra": "$00000", "papel": "$11111", "tesoura": "$01100"}

# Inicializa a captura de vídeo e o detector de mãos
cap = cv2.VideoCapture(CAPTURE_DEVICE)
detector = HandDetector(maxHands=1, detectionCon=DETECTION_CONFIDENCE)

# Inicializa a comunicação serial
try:
    mySerial = serial.Serial(SERIAL_PORT, SERIAL_BAUDRATE)
except serial.SerialException:
    print("Erro: Não foi possível abrir a porta serial.")
    cap.release()
    cv2.destroyAllWindows()
    exit()

# Função para exibir texto na tela
def exibir_texto(img, texto, posicao, font_scale=1, cor=(255, 0, 0), thickness=2):
    cv2.putText(img, texto, posicao, cv2.FONT_HERSHEY_SIMPLEX, font_scale, cor, thickness, cv2.LINE_AA)

# Função para mostrar contagem regressiva
def desenhar_fundo(img, posicao, largura, altura, cor=(0, 0, 0), alpha=0):
    overlay = img.copy()
    cv2.rectangle(overlay, posicao, (posicao[0] + largura, posicao[1] + altura), cor, -1)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)

# Função para exibir a contagem regressiva
def show_clean_countdown(img):
    font_scale = 5  # Tamanho da fonte reduzido para uma exibição mais clean
    thickness = 10  # Ajuste da espessura
    largura_fundo, altura_fundo = 200, 150  # Tamanho do fundo semi-transparente

    for i in range(3, 0, -1):
        img_copy = img.copy()  # Criar uma cópia da imagem original
        (w, h), _ = cv2.getTextSize(str(i), cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        text_x = (img.shape[1] - w) // 2
        text_y = (img.shape[0] + h) // 2

        # Desenha fundo semi-transparente atrás do número
        desenhar_fundo(img_copy, (text_x - 20, text_y - h), largura_fundo, altura_fundo)

        # Exibe o número na tela
        cv2.putText(img_copy, str(i), (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
        cv2.imshow("Image", img_copy)
        cv2.waitKey(1000)  # Espera 1 segundo entre os números

# Função para exibir o resultado do jogo
def display_result(img, message, color):
    exibir_texto(img, message, (img.shape[1]//2 - 200, img.shape[0]//2), font_scale=2, cor=color, thickness=5)

# Função para fechar a mão mecânica
def fechar_mao():
    try:
        mySerial.write(CLOSE_HAND_CMD.encode())
        time.sleep(1)
    except serial.SerialException:
        print("Erro na comunicação com a mão mecânica.")

# Função principal do jogo
def jogar_rodada(img):
    success, img = cap.read()
    if not success:
        print("Erro ao capturar imagem da câmera.")
        return None
    
    hands, img = detector.findHands(img)
    if not hands:
        return None  # Nenhuma mão detectada

    escolha_maquina = random.choice(list(GESTOS_COMANDOS.keys()))
    fingers = detector.fingersUp(hands[0])  # Usamos a primeira mão detectada, sem diferenciação

    escolha_jogador = identificar_gesto(fingers)
    if escolha_jogador:
        mySerial.write(GESTOS_COMANDOS[escolha_jogador].encode())
        resultado_mensagem, cor = determinar_vencedor(escolha_jogador, escolha_maquina)
        fechar_mao()
        display_result(img, resultado_mensagem, cor)
        return img
    return None

# Função para identificar o gesto do jogador
def identificar_gesto(fingers):
    if fingers == [0, 0, 0, 0, 0]:
        return "pedra"
    elif fingers == [1, 1, 1, 1, 1]:
        return "papel"
    elif fingers == [0, 1, 1, 0, 0]:
        return "tesoura"
    return None  # Gesto não reconhecido

# Função para determinar o vencedor
def determinar_vencedor(escolha_jogador, escolha_maquina):
    if escolha_jogador == escolha_maquina:
        return "Empate!", (255, 255, 0)
    elif (escolha_jogador == "pedra" and escolha_maquina == "tesoura") or \
         (escolha_jogador == "papel" and escolha_maquina == "pedra") or \
         (escolha_jogador == "tesoura" and escolha_maquina == "papel"):
        return "Voce ganhou!", (0, 255, 0)
    else:
        return "Voce perdeu!", (0, 0, 255)

# Função principal do loop do jogo
def main_loop():
    fechar_mao()  # Garante que a mão começa fechada

    while True:
        success, img = cap.read()
        if not success:
            print("Erro ao capturar imagem da câmera.")
            break

        exibir_texto(img, "'s' para iniciar", (50, 50))
        cv2.imshow("Image", img)

        if cv2.waitKey(WAIT_KEY_DELAY) & 0xFF == ord('s'):
            show_clean_countdown(img)  # Chamada da função correta
            img = jogar_rodada(img)

            if img is not None:
                exibir_texto(img, "'r' para reiniciar |'q' para sair", (50, 100), cor=(0, 255, 0))
                cv2.imshow("Image", img)

                while True:
                    key = cv2.waitKey(WAIT_KEY_DELAY) & 0xFF
                    if key == ord('r'):
                        break  # Reinicia o jogo
                    elif key == ord('q'):
                        encerrar_jogo()

# Função para encerrar o jogo e liberar recursos
def encerrar_jogo():
    cap.release()
    cv2.destroyAllWindows()
    try:
        mySerial.close()  # Fechar porta serial
    except serial.SerialException:
        print("Erro ao fechar a porta serial.")
    exit()

# Executa o loop principal do jogo
main_loop()
