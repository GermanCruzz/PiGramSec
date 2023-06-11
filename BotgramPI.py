#Librerías
import telebot
from telebot import types
import time
import os
import datetime as dt
from datetime import datetime
from dotenv import load_dotenv
import subprocess
import nextcloud_client
import psutil
load_dotenv()

def OnlyMe (chat_id) :
    if chat_id != 5011347260 : return 0
    return 1

TOKEN = os.getenv("TOKEN")
USERS_DIR = "/home/usuarios.txt"

# Crea un objeto de bot
bot = telebot.TeleBot(TOKEN)

comandos = {
    "start": "Iniciar bot",
    "foto": "Hacer foto del cortijo y subirla a drive.",
    "video": "Grabar video y subirla a drive.",
    "live": "Ver lo que pasa en todo momento en el cortijo en streaming.",
    "parar": "Para la alarma en caso de apertura de puerta.",
    "iniciar": "Volver a iniciar la alarma",
    "ayuda": "Mostrar los comandos disponibles en el Bot"
}

# Acción para el comando "ayuda"
def mostrar_ayuda(chat_id):
    mensaje = "Puedes hacer todos estos comandos:\n\n"
    for comando, descripcion in comandos.items():
        mensaje += f"{comando}: {descripcion}\n"
    bot.send_message(chat_id, mensaje)
    
# Función para registrar los datos del usuario que envió un mensaje
def log_usuario(message):
    # Obtener la información del usuario que envió el mensaje
    user = message.from_user

    # Guardar los datos del usuario en un archivo
    with open(USERS_DIR, "a") as f:
        f.write(f"{user.id}, {user.first_name}, {user.last_name}, {user.username}\n")

#Parar alarma

def parar_alarma(chat_id):
      nombre_script = 'alarma.py'
      nombre_proceso = 'cvlc'
      #Comando
      os.system(f"pkill -f {nombre_script}")
      os.system(f"pkill -f {nombre_proceso}")
      bot.send_message(chat_id, f"Se ha parado con éxito el script y la alarma")

import subprocess

def parar_alarma(chat_id):
    nombre_script = 'alarma.py'
    nombre_proceso = 'cvlc'

    # Verificar si el script de alarma está en ejecución
    output = subprocess.getoutput(f"pgrep -fl {nombre_script}")
    lines = output.split('\n')
    if len(lines) > 1:
        # Proceso en ejecución, detenerlo
        os.system(f"pkill -f {nombre_script}")
        os.system(f"pkill -f {nombre_proceso}")
        bot.send_message(chat_id, "Se ha detenido el script de alarma")
    else:
        bot.send_message(chat_id, "El script de alarma no está en ejecución, puedes iniciarlo")


def iniciar_alarma(chat_id):
    nombre_script = "/home/gpena166/alarma.py"
    try:
        # Verificar si el script ya está en ejecución
        try:
            output = subprocess.check_output(['pgrep', '-f', 'python3 ' + nombre_script]).decode('utf-8')
            if output.strip() != "":
                bot.send_message(chat_id, "El script de alarma ya está en ejecución")
                return
        except subprocess.CalledProcessError:
            pass

        # Ejecutar el script de la alarma
        subprocess.Popen(['python3', nombre_script])
        bot.send_message(chat_id, "Se ha iniciado el script de alarma")
    except Exception as e:
        print(f"Error al iniciar el script de alarma: {e}")
        bot.send_message(chat_id, f"Error al iniciar el script de alarma: {e}")


def accionador_comandos(message):
    # Obtener el texto del mensaje
    text = message.text

    # Dividir el texto en palabras
    words = text.split()

    if len(words) > 0:
        # Obtener el comando (la primera palabra del mensaje)
        command = words[0].lower()

        # Realizar las acciones correspondientes según el comando
        if command == "foto":
            # Tomar foto y enviarla al chat de Telegram
            FotoAlChat(message.chat.id)
        elif command == "video":
            # Grabar video y enviarlo al chat de Telegram
            VideoAlChat(message.chat.id)
        elif command == "live":
            # Enviar stream al chat de Telegram
            StreamAlChat(message.chat.id)
        elif command == "parar":
            # Detener servicio de la alarma del sensor
            parar_alarma(message.chat.id)
        elif command == "iniciar":
            # Volver a iniciar servicio de la alarma del sensor
            iniciar_alarma(message.chat.id)
        elif command == "ayuda":
            # Ayuda con los comandos
            mostrar_ayuda(message.chat.id)
        else:
            # Comando desconocido, enviar mensaje de error
            bot.reply_to(message, "Puedes hacer el comando sin la / para más comodidad")
    else:
        # El mensaje no contiene comandos, enviar mensaje de error
        bot.reply_to(message, "Mensaje sin comandos válidos.")


@bot.message_handler(commands=['start'])
def handle_start(message):
    # Registrar los datos del usuario
    log_usuario(message)

    # Acción para el comando "start"
    bot.reply_to(message, "¡Hola! Bienvenido a PIAlarma_bot.")

# Ejemplo de uso en la función de manejo de mensajes
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Registrar los datos del usuario
    log_usuario(message)

    # Ejecutar el accionador de comandos
    accionador_comandos(message)

#-------------- FUNCIONES DE CÁMARA Y ALMACENAMIENTO-----------------------


#Subir a nextcloud
instancia_nextcloud = os.getenv('instancia_nextcloud')
usuario_nextcloud = os.getenv('usuario_nextcloud')
password_nextcloud = os.getenv('password_nextcloud')
nxc_fotos = os.getenv('nxc_fotos')
nexc_videos = os.getenv('nxc_videos')

def to_nextcloud(foto_local, video_local,chat_id):
    # Crear una instancia del cliente Nextcloud
    nc = nextcloud_client.Client(instancia_nextcloud)
    nc.login(usuario_nextcloud, password_nextcloud)

    # Subir la foto a Nextcloud en la carpeta especificada
    if foto_local:
        fotocam = os.path.basename(foto_local)
        nc.put_file(f"{nxc_fotos}/{fotocam}", foto_local)
        bot.send_message(chat_id, f"Se ha subido la foto {fotocam} a Nextcloud")

    # Subir el video a Nextcloud en la carpeta especificada
    if video_local:
        video_cam = os.path.basename(video_local)
        nc.put_file(f"{nexc_videos}/{video_cam}", video_local)
        bot.send_message(chat_id, f"Se ha subido el video {video_cam} a Nextcloud")



def FotoAlChat(chat_id):
     if OnlyMe(chat_id):
        # Tomar la foto con la aplicación fswebcam y guardarla en un archivo con el nombre "Foto-fecha.jpg"
        fotojpg = "/ToRubbish/Foto-" + datetime.now().strftime("%Y-%m-%d_%H:%M:%S") + ".jpg"
        os.system("sudo -n /usr/bin/systemctl stop motion")
        subprocess.run(["fswebcam", "-r", "1280x720", "--no-banner", fotojpg])
        # Envíar la foto al chat de Telegram
        with open(fotojpg, "rb") as f:
            bot.send_photo(chat_id, f)

        to_nextcloud(fotojpg, None,chat_id)

        # Elimina el archivo de la foto después de enviarla
        os.remove(fotojpg)
        os.system("sudo -n /usr/bin/systemctl start motion")
     else: bot.send_message(chat_id, f"Tu ID no está autorizado para realizar esta acción")

bot.message_handler(commands=['photo'])
def handle_command(message):
    chat_id = message.chat.id
    FotoAlChat(chat_id)

def VideoAlChat(chat_id):
    # Parámetros de grabación
    res = "1280x720"
    fps = 25
    duration = 10

    # Grabar vídeo con la aplicación ffmpeg
    fecha = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_video = f"video_{fecha}.mp4"
    ctemporal = "/tmp"
    os.system("sudo -n /usr/bin/systemctl stop motion")
    subprocess.run(f"ffmpeg -f v4l2 -framerate {fps} -video_size {res} -i /dev/video0 -t {duration} -c:v libx264 -crf 23 -pix_fmt yuv420p {ctemporal}/{nombre_video}", shell=True)

    # Enviar el archivo MP4 al chat de Telegram desde la carpeta temporal
    with open(f"{ctemporal}/{nombre_video}", "rb") as video_cam:
        bot.send_video(chat_id, video_cam)
        
    to_nextcloud(None, f"{ctemporal}/{nombre_video}",chat_id)

    # Eliminar el archivo temporal
    os.remove(f"{ctemporal}/{nombre_video}")
    os.system("sudo -n /usr/bin/systemctl start motion")


#Stream
def StreamAlChat(chat_id):
      if OnlyMe(chat_id):
         stream_link = "https://stream.gcruzz.com"
         bot.send_message(chat_id, f"Ver stream en servidor web: {stream_link}")
      else: bot.send_message(chat_id, f"Tu ID no está autorizado para realizar esta acción")


#Iniciar bot
bot.delete_webhook()
bot.polling()
