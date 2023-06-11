import RPi.GPIO as GPIO
import smtplib
from twilio.rest import Client
import pygame
import time
import logging
import os
import subprocess
import datetime
import datetime as dt
from dotenv import load_dotenv
import nextcloud_client


#PIN GPIO
sensor_pin = 4
#Coger variables desde .env(Igual que Telegram)
load_dotenv()
#---------- VARIABLES CORREO ---------------------
remitente = os.getenv('remitente')
contraseña_correo = os.getenv('contraseña_correo')
receptor = os.getenv('receptor')
#------------ VARIABLES TWILIO ---------------------
id_twilio = os.getenv('id_twilio')
token_twilio = os.getenv('token_twilio')
numero_twilio = os.getenv('numero_twilio')
numero_llamada = os.getenv('numero_llamada')
#Audio de alarma y pydub
#audio = '/home/gpena166/alarma.mp3'
#Archivo log y logging
log = '/var/logs/sensor.log'
info='Alguien entró al cortijo'


# GPIO PARA SENSOR
GPIO.setmode(GPIO.BCM)
GPIO.setup(sensor_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# *********** COMIENZO DE FUNCIONES *******************

#Correo

def enviar_correo():

    asunto = 'Se ha activado el script de la alarma'
    mensaje = 'Alguien ha entrado en el cortijo. Revisa las cámaras'
    email = 'Asunto: {}\n\n{}'.format(asunto, mensaje)
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(remitente, contraseña_correo)
    server.sendmail(remitente, receptor, email.encode('utf-8'))
    server.quit()


#Twilio

def llamada_twilio():

    client = Client(id_twilio, token_twilio)
    client.calls.create(
        url='http://demo.twilio.com/docs/voice.xml',
        to=numero_llamada,
        from_=numero_twilio
    )



#Log de apertura

def escribir_log(mensaje):
    with open(log, 'a') as file:
        file.write(f'{datetime.datetime.now()} - {mensaje}\n')

# Sonido de alarma

def audio_alarma():

    os.system('cvlc /home/gpena166/alarma.mp3')
#Subir a nextcloud
instancia_nextcloud = os.getenv('instancia_nextcloud')
usuario_nextcloud = os.getenv('usuario_nextcloud')
password_nextcloud = os.getenv('password_nextcloud')
nxc_fotos = os.getenv('nxc_fotos')
nexc_videos = os.getenv('nxc_videos')


# Video de alarma
def VideoAlarma():
    # Parámetros de grabación
    res = "1280x720"
    fps = 25
    duration = 10

    # Grabar vídeo con la aplicación ffmpeg
    fecha = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_video = f"Alarma_{fecha}.mp4"
    ctemporal = "/TempVideosAlarma"
    os.makedirs(ctemporal, exist_ok=True)
    os.system("sudo -n /usr/bin/systemctl stop motion")
    subprocess.run(f"ffmpeg -f v4l2 -framerate {fps} -video_size {res} -i /dev/video0 -t {duration} {ctemporal}/{nombre_video}", shell=True)

    # Subir a Nextcloud
    carpeta_destino = f"/Alarma/{nombre_video}"
    nc = nextcloud_client.Client(instancia_nextcloud)
    nc.login(usuario_nextcloud, password_nextcloud)
    nc.put_file(f"{carpeta_destino}", f"{ctemporal}/{nombre_video}")

    # Eliminar el archivo temporal
    os.remove(f"{ctemporal}/{nombre_video}")
    os.system("sudo -n /usr/bin/systemctl start motion")




#Accionador de cambio de estado del sensor

try:
    estado_anterior = GPIO.input(sensor_pin)  # Estado inicial del sensor

    # Bucle principal
    while True:
        estado_actual = GPIO.input(sensor_pin)  # Estado actual del sensor

        if estado_actual != estado_anterior:  # Si hay un cambio en el estado del sensor
            if estado_actual == GPIO.LOW:  # Estado actual es bajo (puerta cerrada)
                print('La puerta está cerrada')
            else:  # Estado actual es alto (puerta abierta)
                print('La puerta se ha abierto')
                enviar_correo()
                llamada_twilio()
                audio_alarma()
                VideoAlarma()
                escribir_log(info)

        estado_anterior = estado_actual  # Actualizar el estado anterior

        time.sleep(0.1)

except KeyboardInterrupt:
    # Limpieza de GPIO en caso de interrupción del usuario
    GPIO.cleanup()
