import socket
import threading
from sys import stdout
import sys
import logging

# SERVER_IP define o endereço IP do servidor ao qual o cliente se conectará.
# UDP_PORT é a porta utilizada para receber os dados via UDP.
# TCP_PORT é a porta utilizada para comunicação de controle via TCP.
# BUFFER_SIZE define o tamanho do buffer para a leitura dos pacotes de dados.

SERVER_IP = "localhost"
UDP_PORT = 5005
TCP_PORT = 5006
NEW_TCP_PORT = 5007
BUFFER_SIZE = 1400

# Configuração básica de logging para registrar informações, erros e mensagens importantes no cliente.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Função responsável por receber o stream de vídeo via UDP.
def receive_udp_stream():
    try:
        # Criação do socket UDP para receber os dados do vídeo.
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        address = (SERVER_IP, UDP_PORT)
        udp_sock.sendto(b'ola', address)  # Envia uma mensagem inicial para o servidor, indicando que está pronto para receber dados.
        
        id = 0  # Contador de pacotes recebidos.
        video_data = bytearray()  # Armazena temporariamente os dados do vídeo recebidos.

        while True:
            data, _ = udp_sock.recvfrom(BUFFER_SIZE)  # Recebe um pacote UDP do servidor.
            if not data:
                break  # Se o pacote estiver vazio, significa que a transmissão terminou.

            video_data += data  # Acumula os dados do vídeo no buffer.
            id += 1        

            # A cada 10 pacotes recebidos, os dados são processados e enviados para a saída padrão (stdout).
            if id == 10:
                for i in range(0, len(video_data), BUFFER_SIZE):
                    stdout.buffer.write(video_data[i:i+BUFFER_SIZE])
                    sys.stdout.buffer.flush()
                id = 0  # Reseta o contador de pacotes.
                video_data = bytearray()  # Limpa o buffer de vídeo após o envio dos dados.
                tcp_sock.send(b'NEXT')  # Envia uma mensagem TCP para o servidor, indicando que o cliente está pronto para o próximo lote de pacotes.
            
        udp_sock.close()  # Fecha o socket UDP ao final da transmissão.
    except Exception as e:
        logging.error(f"Error in streaming the video: {e}")

# Função responsável por estabelecer a conexão de controle via TCP com o servidor.
def send_tcp_control():
    try:
        global tcp_sock  # Define tcp_sock como uma variável global para ser usada em outras partes do código.
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.connect((SERVER_IP, TCP_PORT))  # Conecta-se ao servidor na porta TCP definida.
    except Exception as e:
        logging.error(f"Error in connecting TCP: {e}")

def seek_control():
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.connect((SERVER_IP, NEW_TCP_PORT))
    print("Conexão de controle TCP estabelecida.")

    while True:#p: pausar, c: continuar, s: sair
        command = input()
        tcp_sock.send(command.encode())
        if command == "STOP":
            break

    tcp_sock.close()

# Bloco principal do código, executado quando o script é iniciado.
if __name__ == "__main__":
    # Estabelece a conexão TCP para controle de fluxo.
    send_tcp_control()
    
    seek_thread = threading.Thread(target=seek_control)
    seek_thread.start()

    try:
        # Cria uma thread separada para receber o stream de vídeo via UDP, permitindo que o cliente continue responsivo.
        udp_thread = threading.Thread(target=receive_udp_stream)
        udp_thread.start()
        udp_thread.join()  # Aguarda até que a thread UDP termine antes de continuar.
    except Exception as e:
        logging.error(f"Error creating UDP thread: {e}")
        
    tcp_sock.close()  # Fecha a conexão TCP ao final da transmissão.
