---
title: "Configuración de cámaras IMX519 en una Raspberry Pi 5"
url: "/guia/instalacion/pi5-imx519/"
translationKey: "docs-deployment-pi5-imx519"
linkTitle: "Configuración del equipo: Raspberry Pi 5 con cámaras IMX519"
docs_section: "deployment"
source: "docs/developers/device_setup_pi5_imx519.qmd"
---

***

Esta guía explica cómo conectar y configurar la cámara **Arducam IMX519** en la **Raspberry Pi 5** y cómo probar la captura de fotografías con scripts de shell.

## Hardware probado {#tested-hardware}

- Raspberry Pi 5 con 8 GB de RAM.
- Dos módulos de cámara Arducam IMX519, SKU B0371.
- Dos cables planos CSI de **22 a 22 pines** (recomendamos 15 o 20 cm).
- Fuente de alimentación oficial de Raspberry Pi, de 5 V/3 A o superior (recomendamos la fuente de 27 W).
- Tarjeta microSD de 16 GB con Raspberry Pi OS Lite de 64 bits instalado.

Consulta los pasos iniciales de instalación de Raspberry Pi OS en la [documentación de Raspberry Pi](https://www.raspberrypi.com/documentation/computers/getting-started.html).

---

## 1. Conexión del hardware {#hardware-connection}

Para conectar las cámaras seguimos la [guía de inicio rápido de Arducam para la configuración del hardware](https://docs.arducam.com/Raspberry-Pi-Camera/Native-camera/Quick-Start-Guide/#step-3-connect-to-raspberry-pi).

### Conexión de la cámara {#camera-connection}

Esta fotografía muestra la conexión de la cámara:

{{< media id="imx519-ribbon-connection" >}}

Antes de cerrar la pestaña de sujeción, comprueba que el cable plano quede completamente insertado y alineado en el conector. Ambos puertos de la Pi requieren la misma orientación: los **contactos metálicos del cable deben mirar hacia el puerto Ethernet** y el refuerzo azul hacia el borde frontal de la placa, del lado de HDMI y USB-C. Consulta la fotografía de las dos cámaras más abajo.

### Conexión de dos cámaras a la Raspberry Pi 5 {#dual-camera-connection-on-raspberry-pi-5}

La Raspberry Pi 5 tiene dos conectores CSI, **CAM0** y **CAM1**. Conecta una cámara a cada puerto con cables planos de 22 pines.

> En ambos puertos, los contactos metálicos del cable deben mirar hacia el puerto Ethernet.

{{< media id="rpi5-camera-ribbon-connection" >}}

### Montaje final {#final-assembly}

Después de conectar las cámaras, comprueba que todo esté firme. Instala los disipadores u otros sistemas de refrigeración necesarios e inserta la tarjeta microSD con Raspberry Pi OS instalado. Por último, conecta la fuente de alimentación para encender la Raspberry Pi 5. Conecta el teclado, el ratón y el monitor, o configura SSH para manejarla sin pantalla.

{{< media id="rpi5-imx519-b0371-setup" >}}

---

## 2. Configuración del software {#software-setup}

Para este paso seguimos la [guía de Arducam para configurar el software de IMX519](https://docs.arducam.com/Raspberry-Pi-Camera/Native-camera/16MP-IMX519/), en concreto las instrucciones para Raspberry Pi Bullseye OS 6.1.21 y versiones posteriores, y Bookworm OS.

> **Nota sobre las herramientas de cámara:** Por lo general, las herramientas oficiales `rpicam-apps` de Raspberry Pi son la opción preferida para la Pi 5, pero en nuestras pruebas **no detectaron las IMX519**. El método que describimos a continuación, con los paquetes de Arducam, funcionó de forma fiable. Otras configuraciones podrían funcionar con `rpicam-apps`; esta guía documenta el método que probamos.

**Paso 1: descargar el script de Bash**

```bash
wget -O install_pivariety_pkgs.sh https://github.com/ArduCAM/Arducam-Pivariety-V4L2-Driver/releases/download/install_script/install_pivariety_pkgs.sh

chmod +x install_pivariety_pkgs.sh
```

**Paso 2: instalar `libcamera`**

```bash
./install_pivariety_pkgs.sh -p libcamera_dev
```

**Paso 3: instalar libcamera-apps**

```bash
./install_pivariety_pkgs.sh -p libcamera_apps
```

**Paso 4: modificar la configuración de arranque**

```bash
sudo nano /boot/firmware/config.txt
```

Añade o modifica lo siguiente:

```ini
# Desactiva la detección automática: no detecta con fiabilidad los sensores de otros fabricantes
camera_auto_detect=0

[all]
dtoverlay=imx519,cam0
dtoverlay=imx519
```

> La primera línea (`imx519,cam0`) habilita CAM0 de forma explícita. La segunda (`imx519`) permite que el kernel detecte CAM1 automáticamente. Necesitas ambas líneas para usar dos cámaras.

Opcional: habilita los registros de depuración:

```ini
dtdebug=1
```

Guarda los cambios y reinicia:

```bash
sudo reboot
```

---

## 3. Verificar la detección de cámaras {#verify-camera-detection}

Después de reiniciar:

```bash
rpicam-hello --list-cameras
```

Resultado esperado con dos cámaras IMX519:

```less
Available cameras
-----------------
0 : imx519 [4656x3496 …] (/base/axi/pcie@…/i2c@88000/imx519@1a)
1 : imx519 [4656x3496 …] (/base/axi/pcie@…/i2c@80000/imx519@1a)
```

Si quieres comprobar el grafo de dispositivos multimedia:

```bash
v4l2-ctl --list-devices
media-ctl -p
```

---

## 4. Probar las cámaras {#test-cameras}

**Vista previa de cada cámara**

```bash
rpicam-hello --camera 0 -t 5000
rpicam-hello --camera 1 -t 5000
```

**Capturar una fotografía**

```bash
rpicam-jpeg --camera 0 -o cam0.jpg
rpicam-jpeg --camera 1 -o cam1.jpg
```

**Grabar un video corto**

```bash
rpicam-vid --camera 0 -t 10000 -o cam0.h264
rpicam-vid --camera 1 -t 10000 -o cam1.h264
```

---

## 5. Solución de problemas {#troubleshooting}

**`Error -5: failed to read chip id`**

El sensor no responde por I²C. Vuelve a conectar el cable plano y verifica la orientación. Comprueba que la pestaña esté completamente cerrada. Prueba a intercambiar CAM0 y CAM1.

**Solo aparece una cámara**

Comprueba que figuren ambas líneas `dtoverlay`. Intercambia los módulos y los cables para localizar la falla.

**No existe `/dev/video0`**

El controlador no estableció la conexión con el sensor. Revisa los registros:

```bash
dmesg | grep imx
```

**Comprobar la alimentación**

```bash
vcgencmd get_throttled
```

Un valor de `0x0` indica que el comando no registra ninguna de las condiciones que supervisa. Un valor distinto de cero puede indicar voltaje insuficiente, limitación por temperatura o reducción de frecuencia, actuales o anteriores. Consulta los bits del resultado en la [documentación de Raspberry Pi](https://www.raspberrypi.com/documentation/computers/os.html#get_throttled) para identificar la causa. Si indica voltaje insuficiente, usa la fuente oficial.

**Consultar los registros de depuración**

Si configuraste `dtdebug=1`:

```bash
dmesg | grep -i imx
sudo vcdbg log msg
```

---
