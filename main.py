import os
import cv2
import io
import tempfile
from flask import Flask, request, jsonify, send_file
import imageio
import shutil

app = Flask(__name__)

# Caminho para o diretório temporário onde os arquivos serão salvos
diretorio_temporario = "temp"

# Função para criar um diretório temporário único para cada solicitação
def criar_diretorio_temporario():
    return os.path.join(diretorio_temporario)

@app.route('/converter', methods=['POST'])
def converter_video():
    try:
        # Verifica se o arquivo 'video' foi enviado na requisição POST
        if 'video' not in request.files:
            return jsonify({'error': 'Nenhum arquivo de vídeo foi enviado'}), 400

        video_file = request.files['video']

        # Lê o arquivo WebP em um buffer
        video_buffer = video_file.read()

        # Cria um diretório temporário único para esta solicitação
        diretorio_temporario_atual = criar_diretorio_temporario()
        os.makedirs(diretorio_temporario_atual)

        # Caminho para o arquivo de entrada no formato WebP
        video_path = os.path.join(diretorio_temporario_atual, 'video.webp')

        # Salva o buffer no arquivo de entrada
        with open(video_path, 'wb') as video_file:
            video_file.write(video_buffer)

        # Caminho para o arquivo de saída em MP4
        video_saida_path = os.path.join(diretorio_temporario_atual, 'video.mp4')

        # Lê o arquivo WebP e extrai os quadros como imagens PNG
        reader = imageio.get_reader(video_path)
        frames = [frame for frame in reader]

        # Obtém as dimensões dos quadros
        height, width, layers = frames[0].shape

        # Configura o objeto de gravação de vídeo
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(video_saida_path, fourcc, 30, (width, height))

        # Escreve os quadros no arquivo de vídeo
        for frame in frames:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            video_writer.write(frame_rgb)

        # Fecha o objeto de gravação de vídeo
        video_writer.release()

        # Lê o arquivo MP4 em bytes
        with open(video_saida_path, 'rb') as mp4_file:
            mp4_data = mp4_file.read()

        # Retorna o arquivo MP4 como resposta
        response = send_file(io.BytesIO(mp4_data), as_attachment=True, download_name='video.mp4')

        # Remove o diretório temporário e todos os seus conteúdos
        shutil.rmtree(diretorio_temporario_atual, ignore_errors=True)

        return response, 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()
