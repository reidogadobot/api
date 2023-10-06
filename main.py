import os
import threading
from flask import Flask, request, jsonify,send_from_directory
import imageio
import tempfile
import atexit
import schedule
import tempfile
import time
import uuid
import shutil

app = Flask(__name__)

@app.route('/')
def enviar_mensagem():
    mensagem = "Olá, esta é a rota '/' enviando uma mensagem!"
    return mensagem

# Caminho para o diretório temporário onde os arquivos serão salvos
diretorio_temporario = "temp"

# Limpa a pasta temporária à meia-noite
def limpar_temporario():
    for arquivo in os.listdir(diretorio_temporario):
        arquivo_path = os.path.join(diretorio_temporario, arquivo)
        try:
            if os.path.isfile(arquivo_path):
                os.unlink(arquivo_path)
            elif os.path.isdir(arquivo_path):
                # Se for um diretório, exclua-o recursivamente
                for root, dirs, files in os.walk(arquivo_path):
                    for arquivo_dir in files:
                        os.unlink(os.path.join(root, arquivo_dir))
                    for dir_path in dirs:
                        os.rmdir(os.path.join(root, dir_path))
                os.rmdir(arquivo_path)
        except Exception as e:
            print(f"Erro ao excluir arquivo/diretório {arquivo_path}: {e}")

# Agenda a limpeza da pasta temporária à meia-noite
schedule.every().day.at("09:13").do(limpar_temporario)

# Função para iniciar a programação de tarefas
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)
        
@app.route('/converter', methods=['POST'])
def converter_video():
    nome_arquivo = str(uuid.uuid4())[:8]
# Caminho completo para o arquivo de saída
    video_saida = os.path.join(diretorio_temporario, f'{nome_arquivo}.mp4')
    try:
        # Verifica se o arquivo 'video' foi enviado na requisição POST
        if 'video' not in request.files:
            return jsonify({'error': 'Nenhum arquivo de vídeo foi enviado'}), 400

        video_file = request.files['video']

        # Verifica a extensão do arquivo (deve ser .webp)
        if not video_file.filename.endswith('.webp'):
            return jsonify({'error': 'O arquivo deve ter a extensão .webp'}), 400

        # Cria o diretório onde os quadros serão salvos como imagens PNG
        diretorio_frames = os.path.join(diretorio_temporario, 'frames')
        os.makedirs(diretorio_frames, exist_ok=True)

        # Salva o arquivo de vídeo no diretório temporário
        video_path = os.path.join(diretorio_temporario, f'{nome_arquivo}.webp')
        video_file.save(video_path)

        # Lê o arquivo de vídeo e extrai os quadros
        reader = imageio.get_reader(video_path)
        frame_count = 0
        for frame in reader:
            frame_file = os.path.join(diretorio_frames, f'frame_{nome_arquivo}{frame_count:04d}.png')
            imageio.imwrite(frame_file, frame)
            frame_count += 1

        # Fecha o leitor
        reader.close()

        # Obtém as dimensões de um dos quadros (todos os quadros devem ter o mesmo tamanho)
        frame = imageio.imread(os.path.join(diretorio_frames, f'frame_{nome_arquivo}0000.png'))
        height, width, layers = frame.shape

        # Cria o escritor de vídeo
        writer = imageio.get_writer(video_saida, fps=30)

        # Adiciona cada quadro ao vídeo
        for i in range(frame_count):
            frame_file = os.path.join(diretorio_frames, f'frame_{nome_arquivo}{i:04d}.png')
            frame = imageio.imread(frame_file)
            writer.append_data(frame)

        # Fecha o escritor de vídeo
        writer.close()

        # Remove o diretório e todo o seu conteúdo
        shutil.rmtree(diretorio_frames, ignore_errors=True)

        # Retorna o caminho do arquivo de vídeo de saída
        return jsonify({'video_saida': f"download/{nome_arquivo}.mp4"}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<path:filename>')
def download_file(filename):
    # Garante que o caminho absoluto seja usado para evitar problemas
    diretorio_completo = os.path.join(os.getcwd(), diretorio_temporario)
    return send_from_directory(diretorio_completo, filename)
if __name__ == '__main__':
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()

    app.run()
