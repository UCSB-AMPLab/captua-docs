---
title: "Preparación y distribución de tarjetas SD"
url: /guia/instalacion/tarjetas-sd/
translationKey: docs-deployment-sd-card-distribution
docs_section: deployment
source: docs/developers/sd_card_distribution.qmd
---

***

Esta guía explica cómo preparar y distribuir una imagen de tarjeta SD para Raspberry Pi con Captua preinstalado. Quien reciba la tarjeta podrá insertarla y acceder a la aplicación desde cualquier dispositivo de la misma red, sin configurar direcciones IP manualmente.

---

## Cómo funciona {#how-it-works}

La Raspberry Pi anuncia su nombre de equipo en la red local mediante **mDNS**, con el servicio Avahi que Raspberry Pi OS incluye de forma predeterminada. Así, cualquier dispositivo de la misma red puede acceder a la Pi en `http://<hostname>.local` sin conocer su dirección IP. Todos los equipos tienen el nombre `captua` y responden en `http://captua.local`.

El navegador llama a la API en `/api`, en el mismo origen que la página, y Nginx, en el puerto 80, pasa las solicitudes al backend. El nombre solo sirve para encontrar el equipo: puedes abrir la aplicación con su dirección IP o con cualquier otro nombre que apunte a él.

---

## Preparar la imagen maestra {#preparing-the-master-image}

### 0. Instalar Captua en la tarjeta maestra {#install-captua-on-the-master-card}

Graba en la tarjeta **Raspberry Pi OS (Legacy, 64-bit) Lite**, basado en Debian 12 "Bookworm": es el sistema con el que probamos Captua. La opción "Raspberry Pi OS Lite (64-bit)" de Raspberry Pi Imager instala ahora Debian 13 "Trixie", un sistema con el que todavía no hemos validado Captua. En las opciones de personalización de Imager, usa `pi` como nombre de usuario: `scripts/dtk.service` ejecuta el servicio como `pi` desde `/home/pi/dtk`, y el instalador del quiosco espera ese mismo usuario. Configura allí también la red y SSH (consulta [Qué debe hacer quien recibe la tarjeta](#what-the-recipient-needs-to-do)).

Después, en la Pi, con la cuenta `pi` y conexión a internet, ejecuta:

```bash
sudo apt update && sudo apt install -y git
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

Cierra la sesión y vuelve a iniciarla, para que la cuenta `pi` tenga los permisos del grupo `docker`. Después, ejecuta:

```bash
curl -fsSL https://pixi.sh/install.sh | PIXI_VERSION=v0.73.0 bash
git config --global url."https://github.com/".insteadOf "git@github.com:"
git clone --recurse-submodules https://github.com/UCSB-AMPLab/digitization-toolkit-software.git ~/dtk
cd ~/dtk
sudo ./scripts/setup.sh
sudo ./scripts/install-service.sh
sudo systemctl start dtk
curl http://localhost:8000/health   # {"status":"ok"}
curl -I http://localhost            # HTTP 200: la interfaz, a través de nginx
sudo ./scripts/installkb.sh
sudo ./scripts/install-kiosk-service.sh
```

- La línea `git config` va antes de clonar porque `.gitmodules` registra los submódulos con direcciones SSH (`git@github.com:`) y la Pi no tiene una clave SSH para GitHub: con esa línea, git los descarga por HTTPS. Los repositorios son públicos, así que no necesitas ningún token para clonarlos.
- La versión de pixi está fijada en `PIXI_VERSION`, en `scripts/setup.sh`: las versiones anteriores no pueden leer el `pixi.lock` del repositorio.
- `setup.sh` crea `.env` a partir de `.env.example`, construye la imagen del frontend, instala el entorno del backend, asigna el nombre del equipo (paso 1) y aplica las migraciones de la base de datos. Necesita conexión a internet; después, el equipo funciona sin ella.
- `install-service.sh` instala y habilita `dtk.service` y `dtk-secrets.service`, pero no inicia `dtk`; para eso está la línea `systemctl start`. Las dos líneas `curl` comprueban que el backend y la interfaz responden.
- `installkb.sh` e `install-kiosk-service.sh` configuran el quiosco, es decir, el navegador a pantalla completa en el monitor conectado a la Pi.

### 1. Asignar un nombre al equipo {#name-the-unit}

`setup.sh` asigna el nombre `captua` al equipo en el paso 6f, mediante `scripts/provision-hostname.sh`. Configura el nombre del equipo y la línea `127.0.1.1` de `/etc/hosts`, establece `HOST_IP=captua.local` y añade `http://captua.local` a `CORS_ORIGINS` en `.env`. No necesitas editar nada manualmente.

Dos equipos en una misma red no pueden compartir nombre. Si vas a instalar un segundo equipo en el mismo lugar, asígnale otro nombre al ejecutar la instalación:

```bash
sudo CAPTUA_HOSTNAME=captua-2 ./scripts/setup.sh
```

`setup.sh` todavía acepta el nombre anterior, `DTK_HOSTNAME`.

Comprueba el resultado:

```bash
hostname
# captua
grep -E '^(HOST_IP|CORS_ORIGINS)=' /home/pi/dtk/.env
```

### 2. Comprobar que Avahi esté activo {#confirm-avahi-is-running}

Raspberry Pi OS incluye Avahi (mDNS) de forma predeterminada. Comprueba que esté activo:

```bash
systemctl is-enabled avahi-daemon
systemctl is-active avahi-daemon
```

El primer comando debe devolver `enabled` y el segundo `active`. Si no:

```bash
sudo systemctl enable --now avahi-daemon
```

### 3. Verificar el acceso {#verify}

Desde otro dispositivo de la misma red, abre `http://captua.local` y prueba también la dirección IP del equipo. Ambas deben abrir la aplicación.

`HOST_IP` y `CORS_ORIGINS` ya no determinan las rutas de acceso del equipo. El frontend lee `PUBLIC_API_BASE=/api` durante la ejecución (`docker-compose.pi.yml`), y `HOST_IP` solo establece `ORIGIN` de SvelteKit. La configuración conserva los valores correctos de ambas variables por si vuelves a una versión anterior cuyo frontend llama a `http://${HOST_IP}/api`.

### 4. Crear una imagen de la tarjeta SD {#image-the-sd-card}

Cuando el sistema funcione correctamente, apaga la Pi de forma segura y crea una imagen de la tarjeta SD desde otra computadora.

En los ejemplos siguientes, reemplaza `/dev/sdX` o `/dev/diskN` por el dispositivo completo de la tarjeta, no por una partición. Comprueba la ruta antes de continuar.

**Linux**

Identifica la tarjeta con `lsblk` y desmonta las particiones de esa tarjeta que estén montadas. Luego crea la imagen:

```bash
lsblk
sudo dd if=/dev/sdX of=dtk-master.img bs=4M status=progress
```

**macOS**

Identifica la tarjeta con `diskutil list`, desmonta sus volúmenes y crea la imagen:

```bash
diskutil list
diskutil unmountDisk /dev/diskN
sudo dd if=/dev/diskN of=dtk-master.img bs=4m
```

Cuando `dd` termine correctamente, expulsa la tarjeta:

```bash
diskutil eject /dev/diskN
```

**Windows**

Usa [Win32 Disk Imager](https://sourceforge.net/projects/win32diskimager/). Selecciona el dispositivo de la tarjeta, indica `dtk-master.img` como archivo de destino y presiona **Read**. Comprueba que elegiste la tarjeta correcta.

{{< callout type="tip" title="Reduce el tamaño de la imagen antes de comprimirla" >}}
Herramientas como [PiShrink](https://github.com/Drewsif/PiShrink) pueden reducir el archivo `.img` al eliminar de la imagen el espacio que el sistema de archivos no utiliza. Si quieres hacerlo, trabaja sobre la imagen sin comprimir.
{{< /callout >}}

Después de crear la imagen y, si corresponde, reducirla, comprímela:

```bash
gzip dtk-master.img
```

El resultado será `dtk-master.img.gz`. En Windows puedes usar una herramienta de compresión compatible con gzip.

{{< callout type="note" title="Cada equipo genera sus propias claves y contraseñas" >}}
`dtk-secrets.service`, que instala `install-service.sh`, genera de nuevo `SECRET_KEY`, `DATABASE_PASSWORD` y `BOOTSTRAP_TOKEN` (el token para crear la primera cuenta) en cada equipo físico. El servicio registra el número de serie de la Pi en `/var/lib/dtk/secrets-provenance`. Si grabas una copia de la imagen y la arrancas en otra Pi, el servicio detecta el número de serie distinto y genera claves y contraseñas nuevas antes de iniciar el backend. También cambia la contraseña de Postgres dentro del directorio de datos clonado. No necesitas borrar estas claves y contraseñas de la imagen maestra, y puedes arrancar la tarjeta maestra para probarla antes de crear la imagen.
{{< /callout >}}

{{< callout type="warning" title="Nunca añadas credenciales a `.env` manualmente" >}}
La generación por equipo descrita arriba solo cubre `SECRET_KEY`, `DATABASE_PASSWORD` y `BOOTSTRAP_TOKEN`. No cubre lo que añadas tú al preparar una tarjeta: la imagen y todas sus copias incluirán todo lo que contenga `.env` en ese momento. Ya encontramos una tarjeta que tenía en `~/dtk/.env`, en texto plano, un token personal de acceso a GitHub vigente; no lo había añadido el software.

La preparación del equipo no necesita ningún token: los repositorios son públicos, así que los clonas por HTTPS sin token, y `setup.sh` hace que las descargas posteriores de los submódulos también usen HTTPS. Si alguna vez necesitas descargar un repositorio privado, introduce el token en una solicitud interactiva para que nunca aparezca en la línea de comandos y elimina la variable al terminar:

```bash
read -rs -p "Token: " GH_TOKEN && export GH_TOKEN
gh repo clone UCSB-AMPLab/<repo>
unset GH_TOKEN
```

**No** lo pases en la propia línea como `GH_TOKEN=… gh …`: el shell escribe el token completo en `~/.bash_history`, que está en la tarjeta y formará parte de la imagen. Por el mismo motivo, nunca incluyas un token en la URL de un repositorio remoto: Git lo conserva en `.git/config` y la imagen también lo incluirá.

Antes de crear la imagen maestra, compara `.env` con `.env.example`: no debe contener claves que no figuren en la plantilla.
{{< /callout >}}

{{< callout type="warning" title="Prepara la copia externa y las cuentas en cada equipo, no en la tarjeta maestra" >}}
Todo lo demás que contiene la tarjeta maestra queda también en cada tarjeta grabada a partir de ella, y la generación por equipo no lo cambia:

- `/var/lib/dtk/offsite.env` y `/var/lib/dtk/rclone.conf`, que `provision-rclone.sh` escribe cuando recibe la clave de la copia externa o el token de Fisqua de un equipo. `setup.sh` ya ejecuta `provision-rclone.sh` sin claves. En la tarjeta maestra no le pases ninguna clave a `provision-rclone.sh`; prepara la copia externa de cada equipo después de grabar su tarjeta, como indica el [paso 4 de Actualizar un equipo](/guia/instalacion/actualizar-un-equipo/#provision-the-offsite-copy-without-restarting).
- La base de datos, con todas las cuentas que crees al probar la tarjeta. No crees cuentas en la tarjeta maestra.

Desde la versión siguiente a 0.2.0, si arrancaste la tarjeta antes de preparar su copia externa, el backend pone el equipo en el modo "Solo en el escáner", y cada tarjeta grabada a partir de ella arranca en ese mismo modo. Fija el modo en cada equipo cuando su copia externa esté lista ([Actualizar un equipo, 6.2a](/guia/instalacion/actualizar-un-equipo/#set-the-units-mode)).
{{< /callout >}}

---

## Grabar y entregar la imagen {#flashing-and-delivering-the-image}

En Linux, graba la imagen en una tarjeta SD nueva. Comprueba que `/dev/sdX` corresponda a la tarjeta de destino: **este paso borra su contenido**. Desmonta las particiones de la tarjeta de destino que estén montadas.

```bash
gzip -dc dtk-master.img.gz | sudo dd of=/dev/sdX bs=4M status=progress
sync
```

En macOS y Windows, o como alternativa en Linux, abre Raspberry Pi Imager, elige la opción para usar una imagen local y selecciona `dtk-master.img.gz`. Elige la tarjeta de destino y graba la imagen.

---

## Qué debe hacer quien recibe la tarjeta {#what-the-recipient-needs-to-do}

En la mayoría de los casos, solo necesita:

1. Insertar la tarjeta SD y encender la Pi.
2. Conectar la Pi a la red local por Ethernet o mediante una red Wi-Fi configurada antes de crear la imagen.
3. Abrir `http://captua.local` desde cualquier navegador de la misma red.

{{< callout type="note" title="Configurar el Wi-Fi antes del envío" >}}
Si el lugar de destino usa Wi-Fi en lugar de Ethernet, configura las credenciales de la red en la tarjeta SD **antes de enviarla**.

Raspberry Pi OS Bookworm sustituyó `dhcpcd` y `wpa_supplicant` por NetworkManager. Por eso, añadir un archivo `wpa_supplicant.conf` a la partición `/boot` **ya no funciona**: Bookworm ignora ese archivo.

- **Al preparar la tarjeta maestra desde Raspberry Pi OS:** configura el SSID y la contraseña en las opciones de personalización de Raspberry Pi Imager, en **Wi-Fi**. Habilita también SSH en **Remote Access**, preferiblemente con autenticación por clave pública.
- **En una tarjeta ya preparada:** configura el Wi-Fi mediante NetworkManager, por ejemplo con `sudo nmcli device wifi connect "<SSID>" password "<password>"`, o añade un perfil de conexión de NetworkManager en formato keyfile en `/etc/NetworkManager/system-connections/`.

No supongas que Imager puede aplicar las mismas opciones de personalización a una imagen local clonada. Deja la red y SSH configurados en la tarjeta maestra antes de crear la imagen. Sin SSH no puedes preparar el equipo a distancia sin pantalla: una instalación nueva de Raspberry Pi OS Lite tiene SSH deshabilitado de forma predeterminada, y luego solo podrás acceder si conectas un teclado y una pantalla.
{{< /callout >}}

---

## Solución de problemas {#troubleshooting}

**`captua.local` no resuelve a una dirección IP**

- Comprueba que la Pi y la computadora estén en la misma red y que Avahi esté activo en la Pi.
- Prueba `ping captua.local`.
- Si no funciona, busca la dirección IP en la lista de clientes DHCP del router y abre esa dirección: la aplicación también funciona por IP.

**Un equipo instalado antes de 0.1.0-beta responde como `digitool.local`**

Los equipos instalados antes de 0.1.0-beta tenían el nombre `digitool`. `update.sh` cambia su nombre a `captua` y conserva la respuesta de `digitool.local`; la versión 0.2.0 también la conserva. Consulta **[Actualizar un equipo](/guia/instalacion/actualizar-un-equipo/#the-unit-name-digitool-becomes-captua)**.

**Errores CORS en el navegador**

El navegador llama a la API en el mismo origen que la página. La instalación de producción no hace llamadas entre orígenes distintos, así que no debería presentar este error. En el entorno de desarrollo, Vite en `:5173` llama al backend en `:8000`: el origen de la página debe figurar en `CORS_ORIGINS`, en `.env`. Actualiza la lista y reinicia el backend.

La página y la API también deben pertenecer al mismo sitio, porque la cookie de sesión usa `SameSite=Strict`: abre la página en `localhost` si `PUBLIC_API_BASE` usa `localhost`, y en `127.0.0.1` si usa `127.0.0.1`. Si no coinciden, el navegador no muestra un error CORS: el backend responde al inicio de sesión con 200 y rechaza la siguiente solicitud con 401. Consulta la sección **CORS Configuration** de la [referencia de la API (en inglés)](/docs/developers/api-reference/#cors-configuration) para más detalles.

**Dos Raspberry Pi en la misma red**

Cada nombre de equipo mDNS debe ser único en su red. Asigna el nombre de la segunda unidad durante la instalación con `CAPTUA_HOSTNAME=captua-2`, como en el paso 1. En un equipo ya instalado, ejecuta el mismo script manualmente:

```bash
sudo /home/pi/dtk/scripts/provision-hostname.sh --name captua-2
sudo systemctl restart dtk
```
