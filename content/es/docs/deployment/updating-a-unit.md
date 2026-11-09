---
title: "Actualizar un equipo a 0.1.0"
url: /guia/instalacion/actualizar-un-equipo/
translationKey: docs-deployment-updating-a-unit
docs_section: deployment
source: docs/developers/updating_a_unit.qmd
---

***

Esta guía está dirigida a quien administra un equipo. Explica cómo actualizar un equipo que ya está en uso a la versión 0.1.0 y recoge los pasos que debes realizar una sola vez, en el orden necesario. Al final encontrarás una versión breve para un equipo nuevo.

Los comandos suponen una instalación con la configuración que incluye `scripts/dtk.service`: el repositorio está en `/home/pi/dtk` y el servicio usa la cuenta `pi`. Ejecútalos por SSH como `pi`.

---

## 1. Antes de actualizar {#before-the-update}

### 1.1 Anotar la revisión actual {#note-the-current-revision}

```bash
git -C /home/pi/dtk rev-parse HEAD
git -C /home/pi/dtk submodule status
sudo cat /var/lib/dtk/backups/last-deployed-SHA
```

`update.sh` registra como destino para la reversión el commit indicado en `last-deployed-SHA` y vuelve a él si la actualización falla. Con `--no-pull`, que usa la instalación de 0.1.0 (2.1), el script no inicia ni modifica nada si ese archivo no existe, está vacío o indica un commit que no está en el repositorio local. El repositorio ya contiene el código nuevo y no puede sustituir ese registro. En ese caso, antes del paso 2.1, escribe el commit que imprimió el primer comando:

```bash
echo <commit> | sudo tee /var/lib/dtk/backups/last-deployed-SHA
```

El directorio `/var/lib/dtk/backups/` es exclusivo de `root`, con permisos 0700. Necesitas `sudo` para leer su contenido.

### 1.2 Comprobar el espacio libre {#check-free-space}

```bash
df -h / /var/lib/dtk
```

`update.sh` vuelve a compilar la imagen del frontend, reinstala el entorno del backend y guarda una copia comprimida de la base de datos en `/var/lib/dtk/backups/`. Conserva las cinco copias más recientes y elimina las anteriores.

### 1.3 La copia de seguridad de la base de datos {#the-database-backup}

No necesitas crear una copia manualmente. `update.sh` genera dos copias con `pg_dump` en `/var/lib/dtk/backups/pre-update-<YYYYmmdd-HHMMSS>.sql.gz`. La primera es una prueba mientras el equipo todavía presta servicio: comprueba `pg_dump` y el espacio libre antes de interrumpir el funcionamiento.

El script genera la segunda después de detener el backend, de modo que incluya todos los datos guardados antes de la detención. Cuando verifica la segunda copia, elimina la de prueba. El script rechaza cualquier copia de menos de 100 bytes.

Las copias contienen los hashes de contraseña de todas las cuentas, así que el script las escribe con permisos 0600 en un directorio exclusivo de `root`. Para ver las copias que ya tiene el equipo:

```bash
sudo ls -lt /var/lib/dtk/backups/
```

### 1.4 Detener cualquier temporizador provisional de carga {#stop-any-interim-upload-timer}

Algunos equipos tienen un temporizador de carga que alguien instaló manualmente antes de que el backend pudiera subir archivos. Estos temporizadores dependen de cada equipo y no forman parte del software.

En el equipo de Rionegro, el temporizador `b2push-interim` ejecuta `/home/pi/b2push.sh`. Ese script sube al bucket las imágenes y la copia diaria del catálogo que genera con `pg_dumpall`. Busca el temporizador y detenlo para que, después de actualizar, solo el backend escriba en el bucket:

```bash
systemctl list-timers --all
sudo systemctl disable --now b2push-interim.timer
```

Usa el nombre que muestre `list-timers` en tu equipo. No tenemos registrado el nombre del servicio que inicia el temporizador; `systemctl list-timers` lo muestra en la columna `ACTIVATES`. Si el servicio está en ejecución, espera a que termine antes del paso 2.

Si abandonas la actualización antes del paso 3, habilita de nuevo el temporizador para que el equipo siga subiendo archivos como antes:

```bash
sudo systemctl enable --now b2push-interim.timer
```

### 1.5 Fijar el nombre de Tailscale del equipo {#pin-the-units-tailscale-name}

La actualización cambia el nombre del equipo de `digitool` a `captua` (2.6) cuando apt puede acceder a sus repositorios. El alias que permite seguir usando `digitool.local` necesita `avahi-utils`, que instala la actualización. Si el equipo no tiene acceso a apt, conserva su nombre hasta una actualización que sí tenga acceso.

Tailscale toma el nombre del equipo del hostname, salvo que hayas fijado otro nombre. Si accedes al equipo con `ssh pi-dtk` o con su nombre de Tailscale, el cambio de hostname también cambiaría su nombre en la red de Tailscale. Antes de actualizar, fija explícitamente el nombre que tiene ahora en esa red:

```bash
tailscale status --self
sudo tailscale set --hostname=<the unit's current Tailscale name>
```

El software no modifica Tailscale. Omite este paso si el equipo no usa Tailscale.

---

## 2. Ejecutar la actualización {#run-the-update}

### 2.1 Descargar primero el código de 0.1.0 {#put-the-0.1.0-code-on-disk-first}

Para instalar 0.1.0, descarga el código nuevo y selecciona su revisión manualmente. Solo después ejecuta `update.sh` con `--no-pull`. Todos los equipos deben seguir este procedimiento para esta instalación. Bash lee el script del disco mientras lo ejecuta. Si `update.sh` descarga su propia actualización, esa ejecución conserva el manejo de errores de la copia anterior y no cuenta con ninguna de las protecciones del script nuevo.

Los equipos usan `main`, que solo cambia con las publicaciones de nuevas versiones. Si un equipo usa `dev`, cámbialo a `main` aquí, una sola vez. En el momento de redactar la guía, ese era el caso del equipo de pruebas y del equipo de Rionegro. Como `pi`, ejecuta:

```bash
git -C /home/pi/dtk fetch origin
git -C /home/pi/dtk rev-parse --verify --quiet refs/heads/main
```

Comprueba que el commit de `last-deployed-SHA` (1.1) forme parte del historial de la versión:

```bash
git -C /home/pi/dtk merge-base --is-ancestor "$(sudo cat /var/lib/dtk/backups/last-deployed-SHA)" origin/main && echo ok
```

El comando debe imprimir `ok`. Si no lo hace, el equipo tiene código posterior a la versión publicada o código que esa versión no contiene. Detente y decide qué hacer con ese código antes de continuar. `update.sh --no-pull` comprueba que la revisión seleccionada descienda de `last-deployed-SHA`; no hace esa comprobación sobre `origin/main` (2.2).

Si el segundo comando del primer bloque no imprime nada, todavía no existe una rama `main` local. Créala con `origin/main` como rama remota de seguimiento:

```bash
git -C /home/pi/dtk checkout --track origin/main
```

Si imprime un commit, la rama `main` local ya existe. Selecciónala, actualízala hasta `origin/main` y configura su rama remota de seguimiento:

```bash
git -C /home/pi/dtk checkout main
git -C /home/pi/dtk merge --ff-only origin/main
git -C /home/pi/dtk branch --set-upstream-to=origin/main
```

Después, en ambos casos:

```bash
git -C /home/pi/dtk rev-parse --abbrev-ref --symbolic-full-name '@{u}'
git -C /home/pi/dtk submodule update --init --recursive
git -C /home/pi/dtk submodule status
git -C /home/pi/dtk status --porcelain --untracked-files=no
git -C /home/pi/dtk submodule foreach --quiet --recursive 'git status --porcelain --untracked-files=no'
```

- El primer comando debe imprimir `origin/main`. Las siguientes ejecuciones de `update.sh` descargan desde esa rama y rechazan la descarga si no hay una rama remota de seguimiento.
- Cada línea de `submodule status` debe empezar con un espacio: esto indica que cada submódulo está en la revisión fijada por el proyecto.
- Los dos últimos comandos no deben imprimir nada. Si la actualización falla, `update.sh` no restaura un repositorio que tenga archivos versionados modificados, y `rollback-update.sh` tampoco acepta uno. Por eso el árbol de trabajo debe estar limpio antes del paso 2.2.

Comprueba también que ningún archivo versionado tenga los indicadores `assume-unchanged` o `skip-worktree`, que ocultan cambios a `git status`. Ninguno de estos comandos debe imprimir nada:

```bash
git -C /home/pi/dtk ls-files -v | grep '^[a-zS] '
git -C /home/pi/dtk submodule foreach --quiet --recursive 'git ls-files -v | grep "^[a-zS] " || true'
```

`update.sh --no-pull` comprueba por su cuenta las revisiones fijadas de los submódulos, los indicadores, los archivos versionados modificados y la ascendencia. Si detecta un problema, rechaza la ejecución sin modificar nada (2.2). No comprueba la rama ni su rama remota de seguimiento. Las comprobaciones anteriores te permiten preparar el repositorio antes de ejecutarlo.

`checkout` rechaza una operación que sobrescribiría cambios locales. Guarda esos cambios aparte manualmente antes de continuar: `update.sh` solo lo hace cuando descarga código.

**Después de volver a una versión anterior a 0.1.0:** la reversión restaura el `update.sh` de esa versión anterior. La próxima actualización debe seguir de nuevo este procedimiento: descarga el código, selecciona la revisión manualmente y ejecuta el nuevo `update.sh` con `--no-pull` (8.4). El procedimiento de "Actualizaciones posteriores" que aparece más abajo ejecutaría el script antiguo.

### 2.2 Ejecutar `update.sh` fuera de la sesión SSH {#run-update.sh-outside-the-ssh-session}

Comprueba que nadie capture imágenes mientras `update.sh` esté en ejecución: el script detiene el servicio durante el proceso. Solo puede haber una actualización o reversión en curso. Ambos scripts toman el bloqueo `/run/dtk-update.lock` y rechazan una segunda ejecución, indicando el identificador del proceso que tiene el bloqueo.

```bash
sudo systemd-run --unit=dtk-deploy --collect /home/pi/dtk/scripts/update.sh --yes --no-pull
```

`--no-pull` indica que descargaste el código manualmente. La actualización todavía necesita acceso a apt para instalar `avahi-utils` y cambiar el nombre del equipo (2.6). Si el equipo no tiene ninguna conexión de red, añade `--offline`; el cambio de nombre quedará pendiente.

Nunca ejecutes `update.sh` directamente dentro de una sesión SSH. Si pierdes la conexión, el shell envía SIGHUP al script y lo interrumpe a mitad del proceso. Con `systemd-run`, el script funciona en una unidad transitoria propia y continúa aunque pierdas la conexión.

Aquí necesitas `--yes`. `update.sh` pide confirmación cuando la actualización puede necesitar acceso a internet. Sin terminal y sin `--yes`, el script cancela la ejecución.

#### Cuando `--no-pull` rechaza la ejecución {#when---no-pull-refuses}

Con `--no-pull`, `update.sh` instala el código que tienes seleccionado en el repositorio, así que primero comprueba su estado. Cada rechazo ocurre antes de que el script modifique nada. Cada mensaje termina con los comandos para consultar y corregir el problema.

| El mensaje empieza por | Significado | Solución |
|---|---|---|
| `✗ --no-pull: a submodule is not on the commit HEAD records (<commit>),` / `or its staged pointer differs from it (or this could not be read).` | La revisión seleccionada de un submódulo, o su referencia en el área de preparación del superproyecto, no coincide con la referencia gitlink que registra `HEAD`. | Si la referencia está en el área de preparación, ejecuta `git -C /home/pi/dtk reset -q -- <submodule path>`. Después ejecuta `git -C /home/pi/dtk submodule update --init --recursive`. |
| `✗ --no-pull: tracked files are marked assume-unchanged or skip-worktree` | Un archivo versionado del superproyecto o de un submódulo tiene un indicador que oculta sus cambios. El mensaje enumera los archivos. | En el repositorio al que pertenezca cada archivo —el superproyecto o el submódulo con cuyo nombre empieza la ruta indicada—, ejecuta `git -C <repository> update-index --no-assume-unchanged --no-skip-worktree <file>`. Usa la ruta del archivo dentro de ese repositorio. Después revisa `git status --short`. |
| `✗ --no-pull: the checkout has modified tracked files (changed or staged),` | Hay un archivo versionado modificado o en el área de preparación, en el superproyecto o en un submódulo. | Guarda aparte lo que quieras conservar, crea un commit con esos cambios o descártalos. El mensaje incluye comandos `reset --hard HEAD` que descartan todos los cambios locales de archivos versionados. |
| `✗ --no-pull: the code checked out (<commit>) does not descend from the version` / `this unit last deployed (<commit>).`, or `✗ --no-pull: could not check whether the code checked out (<commit>)` / `descends from the version this unit last deployed (<commit>).` | La revisión seleccionada no desciende del commit de `last-deployed-SHA`, o Git no pudo comprobarlo. Instalarla podría poner código incompatible con las migraciones que ya tiene la base de datos de la versión desplegada. | Para volver a una versión anterior, usa el procedimiento de reversión del paso 8. Para instalar una versión nueva, selecciona un commit cuyo historial contenga el commit desplegado. |

Todos los rechazos incluyen `Nothing has been changed.` El script muestra sus comandos de Git con el prefijo `sudo -u pi`; si ya usas la cuenta `pi`, omite ese prefijo. El cuarto rechazo muestra `sudo /home/pi/dtk/scripts/rollback-update.sh`.

**Actualizaciones posteriores, desde 0.1.x**

Una vez instalado 0.1.0, el disco ya contiene el script nuevo. Entonces puedes usar el procedimiento habitual: `sudo systemd-run --unit=dtk-deploy --collect /home/pi/dtk/scripts/update.sh --yes`.

El script descarga `main` y la actualiza mediante un avance directo (fast-forward). Esto solo vale mientras el repositorio tenga 0.1.0 o una versión posterior. Si vuelves a una versión anterior a 0.1.0, el disco vuelve a contener el script antiguo y la siguiente actualización debe seguir el paso 2.1: descarga y selecciona el código manualmente, y después ejecuta el nuevo `update.sh` con `--no-pull` (8.4).

### 2.3 Qué hace `update.sh` {#what-update.sh-does}

En este orden:

1. Registra la versión en ejecución: el último commit desplegado, la imagen del frontend, que conserva con una etiqueta `pre-update-<timestamp>`, y el archivo `pixi.lock` del backend. Si la actualización falla, restaura esos componentes.
2. Solo cuando no usas `--no-pull`, en actualizaciones posteriores: descarga la rama remota de seguimiento, actualiza la rama local mediante un avance directo y sincroniza los submódulos. Rechaza una rama que no admita ese avance directo. Antes de restablecer archivos versionados con cambios locales, guarda una copia en `/var/lib/dtk/local-mods-<timestamp>/`. Nunca elimina archivos sin seguimiento.
3. Vuelve a compilar la imagen del frontend y ejecuta `pixi install --locked` para el backend. Los contenedores y el backend siguen funcionando, aunque el disco ya contiene el código y el entorno de pixi nuevos.
4. Ejecuta `provision-chdk-usb.sh`, `provision-rclone.sh --advisory` y `provision-hostname.sh --prepare --advisory`. El segundo instala la versión fijada de rclone si hace falta y conserva lo que ya registra `offsite.env`. Con `--advisory` nunca escribe una clave de lectura. El tercero instala lo necesario para cambiar el nombre del equipo (2.6).
5. Genera la copia de prueba de la base de datos mientras el equipo presta servicio (1.3) y registra el destino de reversión en `/var/lib/dtk/backups/pre-update-SHA`.
6. Detiene `dtk`, comprueba que no quede ningún proceso del backend y cambia el nombre de un equipo `digitool` a `captua` (2.6).
7. Inicia solo la base de datos y genera la copia con el backend detenido.
8. Escribe el registro sin resolver (7.3), aplica las migraciones con `pixi run db-upgrade` y detiene la base de datos.
9. Inicia `dtk` y espera hasta 300 segundos a que el backend responda a `/health`.
10. Escribe el commit nuevo en `last-deployed-SHA`, elimina el registro sin resolver y vuelve a iniciar el quiosco (2.6).

El paso 7 explica qué hace `update.sh` si alguno de estos pasos falla.

### 2.4 Seguir el progreso {#follow-it}

```bash
journalctl -u dtk-deploy -f
```

El script ha terminado cuando imprime `Update complete!` o uno de sus mensajes de error. Con `--collect`, systemd elimina la unidad transitoria al terminar el script; aun así, `journalctl -u dtk-deploy` permite leer su registro.

El script solo imprime `Update complete!` después de que el backend haya respondido a `/health`, en el paso 9 anterior. Revisa también los mensajes de arranque:

```bash
curl -s http://localhost:8000/health
journalctl -u dtk --since "15 min ago" | grep -E "Volume layout:|Cannot start|Traceback"
```

`/health` responde `{"status":"ok"}` solo cuando el backend ha terminado de arrancar. A través de nginx, la misma ruta es `http://localhost/api/health`. Los mensajes `Cannot start: database schema is out of date` o `Cannot start: the database is unreachable` indican que el backend rechazó el inicio del servicio. Para las líneas `Volume layout:`, consulta 3.4.

### 2.5 Comprobar que todavía no haya cargas {#check-that-nothing-uploads-yet}

Al arrancar, el backend solo activa sus tareas programadas de carga cuando tiene tanto `DTK_OFFSITE_REMOTE` como un `DTK_OFFSITE_TENANT` válido. Un equipo que aún no has preparado para 0.1.0 no tiene tenant y, por tanto, no sube nada. Compruébalo antes del paso 3 con la solicitud de 6.3: `images.enabled` debe ser `false`.

Si es `true`, el proceso de carga usa el nombre del archivo en el disco como clave de cada objeto. Una imagen que ya copiaste al bucket con un nombre del contrato tendría otra carga bajo una segunda clave; después, `adopt-map` rechazaría su entrada con `key_differs`. Si `offsite.env` ya registra un destino remoto y un tenant, crea el archivo de suspensión de cargas (4.0) antes del paso 2. Así, el backend mantendrá suspendidas las cargas desde el reinicio de la actualización:

```bash
sudo grep -E '^DTK_OFFSITE_(REMOTE|TENANT)=' /var/lib/dtk/offsite.env
```

### 2.6 El nombre del equipo: de digitool a captua {#the-unit-name-digitool-becomes-captua}

Desde 0.1.0, todos los equipos tienen el nombre `captua` y responden en `http://captua.local`. El navegador llama a la API en `/api`, en el mismo origen que la página, a través de nginx. Por eso también puedes abrir el equipo por su dirección IP o por cualquier otro nombre que apunte a él. El quiosco abre `http://localhost` en lugar de `http://localhost:3000`.

`update.sh` solo cambia el nombre si el hostname es exactamente `digitool` y `.env` contiene `HOST_IP=digitool.local`. Si alguien asignó otro nombre manualmente, el script lo conserva. `scripts/provision-hostname.sh` realiza el trabajo en dos llamadas:

- Antes de detener el servicio, con `--prepare`: instala `avahi-utils` mediante apt si falta, el script de alias `/usr/local/sbin/dtk-mdns-alias`, su unidad `dtk-mdns-alias.service`, el script de respuesta a eventos de NetworkManager `/etc/NetworkManager/dispatcher.d/90-dtk-mdns-alias` y el archivo adicional de configuración `/etc/systemd/system/dtk.service.d/hostname-repair.conf`. También intenta usar apt con `--no-pull`, así que la instalación de 0.1.0 (2.1) cambia el nombre si el equipo tiene acceso a apt. Solo `update.sh --no-pull --offline` omite apt. Si no puede instalar `avahi-utils`, el registro indica `The rename to captua waits for avahi-utils`: el equipo conserva `digitool` hasta una actualización con acceso a apt y la actualización continúa.
- Con `dtk` detenido, con `--switch`: escribe `127.0.1.1 captua digitool` en `/etc/hosts`, ejecuta `hostnamectl set-hostname captua`, reinicia `avahi-daemon` e inicia `dtk-mdns-alias`, que mantiene la respuesta de `digitool.local` durante la serie 0.1.x. Después comprueba que `captua.local` y `digitool.local` resuelvan a una dirección del propio equipo. Si alguno no responde o apunta a otro dispositivo, restaura el nombre, `/etc/hosts`, avahi y el alias, y conserva `.env` sin cambios. Si ambos apuntan al equipo, establece `HOST_IP=captua.local` en `.env` y añade `http://captua.local` a `CORS_ORIGINS`, conservando `http://digitool.local`.

Ninguna de las dos llamadas puede hacer fallar la actualización. Si el cambio de nombre no termina, el script imprime `⚠ The rename to captua did not finish` y el equipo sigue funcionando como `digitool`.

Si un corte de corriente interrumpe el cambio de nombre, el siguiente arranque de `dtk` ejecuta `provision-hostname.sh --repair` mediante el archivo adicional de configuración. Si el hostname ya había cambiado, el script vuelve a escribir `127.0.1.1 captua digitool`, inicia el alias y comprueba ambos nombres. Si ambos apuntan al equipo, termina de actualizar `.env` y registra el cambio como completo. Si `captua.local` apunta a otro dispositivo, deshace el cambio. Si los nombres aún no responden, por ejemplo porque no hay red al arrancar, termina de actualizar `.env` y deja el registro pendiente para el próximo arranque.

Si el hostname sigue siendo `digitool`, el script deshace el cambio. Si alguien asignó otro nombre manualmente con `--name`, conserva ese nombre y elimina el registro. Al deshacer el cambio, solo restaura `/etc/hosts` cuando el hostname vuelve a ser `digitool`; si `hostnamectl` falla, conserva el estado para que el siguiente arranque vuelva a intentarlo. El script también termina de reparar un equipo llamado `captua` cuyo `.env` aún contiene `HOST_IP=digitool.local`, independientemente del estado del registro. La reparación elimina además los archivos temporales que un corte de corriente puede dejar junto a `.env`, `/etc/hosts` y el registro.

Una actualización fallida y una reversión restauran el código, pero conservan el nombre. El código anterior a 0.1.0 funciona con él: su frontend llama a `http://${HOST_IP}/api`, ahora `http://captua.local/api`, y `CORS_ORIGINS` incluye ambos nombres. Así, una página abierta en `digitool.local` puede llamar a la API.

Cuando la versión nueva responde a `/health`, `update.sh` termina el proceso `cage` del quiosco, únicamente el de `pi`, y el inicio automático de sesión de tty1 vuelve a lanzarlo con el `start-kiosk.sh` nuevo en `http://localhost`. Ese es un origen nuevo para el navegador, así que el quiosco pide iniciar sesión una vez. `update.sh --resolve-forward` (7.4) vuelve a lanzar el quiosco del mismo modo después de iniciar `dtk`; una reversión lo abre en la dirección de la versión restaurada.

El bloqueo del perfil de Chromium, `~/.config/chromium/SingletonLock`, registra el hostname con el que Chromium lo creó, y Chromium rechaza un perfil bloqueado con otro nombre. El cambio de nombre actualiza el bloqueo del quiosco en ejecución a `captua`; si deshace el cambio, lo devuelve a `digitool`. Así, el siguiente Chromium puede usar el perfil con el `start-kiosk.sh` que haya en el disco después de una actualización, restauración o reversión. El script obtiene el usuario del quiosco del inicio automático de sesión de tty1 que configura `install-kiosk-service.sh`. Antes de iniciar Chromium, el `start-kiosk.sh` de 0.1.0 también elimina `SingletonLock`, `SingletonCookie` y `SingletonSocket`, salvo que siga activo un Chromium de `pi`.

Dos equipos de la misma red llamados `digitool` no pueden adoptar ambos el nombre `captua`: la comprobación del segundo detecta que el primero responde como `captua.local` y deshace el cambio. Asigna al segundo un nombre propio manualmente, como explica la solución de problemas de [Preparación y distribución de tarjetas SD](/guia/instalacion/tarjetas-sd/). La actualización conservará ese nombre.

---

## 3. Asignar a cada volumen su prefijo de nombre de archivo y reiniciar {#give-each-volume-its-stem-then-restart}

### 3.1 Asignar los prefijos {#set-the-stems}

En la interfaz, abre el proyecto, edita cada volumen con **Edit Volume** y completa **FILE NAME STEM**. Estas son las reglas:

- Letras minúsculas y dígitos unidos por guiones simples, con un máximo de 27 caracteres.
- El prefijo debe coincidir con el código de referencia del volumen en Fisqua. El backend rechaza un prefijo distinto del código registrado. En **Edit Volume**, el mensaje es `The stem has to be the volume's Fisqua reference code, "<code>"; "<stem>" is different. Use "<code>" as the stem.` Una solicitud `PATCH` al volumen recibe `409` con `The reference code '<code>' is not the file name stem '<stem>'; a volume's reference code is its file name stem.` Una importación rechaza ese elemento con `filename_stem_differs_from_reference_code` ("The filenameStem is not the same as the referenceCode.") y continúa con el resto.
- Debe ser único en el equipo y no coincidir con el nombre del directorio de un proyecto.
- El backend lo rechaza mientras `<projects root>/<stem>/` contenga archivos ajenos al volumen.
- Puedes asignar un prefijo a un volumen sin prefijo en cualquier momento, incluso después de capturar imágenes. Una vez que el volumen tiene prefijo y capturas, no puedes cambiarlo ni borrarlo.

En un volumen que ya tiene imágenes, el prefijo queda fijo en cuanto lo guardas. Antes de guardar, compara cada prefijo con el código de referencia del volumen en Fisqua.

Asignar un prefijo no mueve ningún archivo. El backend escribe inmediatamente las capturas nuevas de ese volumen en `<stem>/captures/`. No captures en un volumen con mapa de nombres hasta completar sus operaciones `adopt-map` y `raise-capture-counter` (5.1, 5.3): antes de ellas, el backend podría asignar a una captura un número que ya existe en el bucket.

### 3.2 Previsualizar el traslado, opcional {#preview-the-move-optional}

`python -m app.core.volume_layout --dry-run` imprime en JSON qué movería el siguiente arranque, sin escribir nada. Necesita la base de datos activa y el backend detenido. Detén `dtk`, inicia solo la base de datos, ejecuta el comando y vuelve a detener la base de datos. Comprueba este procedimiento en el equipo de pruebas:

```bash
sudo systemctl stop dtk
sudo docker compose -f /home/pi/dtk/docker-compose.yml -f /home/pi/dtk/docker-compose.pi.yml up -d db
sudo docker compose -f /home/pi/dtk/docker-compose.yml -f /home/pi/dtk/docker-compose.pi.yml exec -T db pg_isready
cd /home/pi/dtk/backend
pixi run python -m app.core.volume_layout --dry-run > ~/volume-layout-dry-run.json
sudo docker compose -f /home/pi/dtk/docker-compose.yml -f /home/pi/dtk/docker-compose.pi.yml down --remove-orphans
```

Repite `pg_isready` hasta que indique que el servidor acepta conexiones. El comando de simulación termina con `1` si `failed` no está vacío y con `2` si rechaza la operación porque hay un diario de operaciones que no puede completar. No vuelvas a iniciar `dtk` aquí; lo harás en 3.3.

### 3.3 Reiniciar para que el backend mueva los archivos {#restart-so-the-backend-moves-the-files}

```bash
sudo systemctl restart dtk
```

No reinicies hasta comprobar todos los prefijos. A partir de este arranque, los archivos de cada volumen con prefijo estarán en `<stem>/`, y una reversión ya no devolverá el equipo a un estado utilizable (8.3).

En cada arranque, antes de prestar servicio, el backend mueve los archivos existentes de cada volumen con prefijo desde la estructura basada en nombres a `<stem>/captures/`, `<stem>/previews/` y `<stem>/thumbnails/`. Trabaja un volumen a la vez, mediante un diario de operaciones en `/var/lib/dtk/volume-layout.journal`, y completa cualquier lote interrumpido en el siguiente arranque. Una vez que todos los volúmenes con prefijo están en su lugar, no mueve nada.

Si un volumen ya tenía prefijo antes de la actualización, el backend ya movió sus archivos cuando `update.sh` lo inició.

### 3.4 Leer las líneas `Volume layout:` {#read-the-volume-layout-lines}

```bash
journalctl -u dtk --since "15 min ago" | grep "Volume layout:"
```

El backend solo escribe la línea de resumen cuando movió o adoptó archivos, o completó una operación pendiente. Si reinicias después de asignar prefijos a volúmenes con archivos y no aparece esa línea, revisa el resultado.

| Línea | Significado |
|---|---|
| `moved N image(s) and pointed M row(s) at files already in volume directories under <root>` | El resumen. `M` cuenta las filas cuya ruta anterior ya no existía y cuyo archivo apareció en `captures/` con el sha256 registrado al capturar. |
| `image N not moved, left at <path>: <error>` | El backend no pudo mover el archivo. Conservó el archivo y su fila sin cambios y continuó con la siguiente imagen. La fila sigue fuera de lugar, así que volverá a intentarlo en el próximo arranque. |
| `image N not moved (<reason>): <path>` | El plan omitió la imagen. Los motivos aparecen más abajo. |
| `<dir> already holds what is not volume N's, so its files are not moved there: [...]` | `<stem>/` contiene entradas ajenas a todas las imágenes del volumen. El backend no mueve ningún archivo del volumen hasta que retires esas entradas. |
| `<root>/<stem> or one of its directories resolves outside the projects root <root>; ...` | Un enlace dentro de `<stem>/` apunta fuera del directorio raíz de proyectos. El backend no mueve nada de ese volumen. |
| `sidecar not yet beside its master, still at <path>` | El backend movió el original RAW, pero no su vista previa. Vuelve a intentar moverla en cada arranque. |
| `file no record references, left where it is: <path>` | Ninguna fila hace referencia a ese archivo, que está en un directorio de volumen o en uno del que el backend retiró archivos. Ningún proceso lo elimina. Dentro de `<stem>/`, bloquea traslados posteriores del volumen con `stem_dir_occupied` hasta que lo retires. |
| `temporary file of an interrupted write, left where it is: <path>` | El backend deja el archivo en su lugar; no bloquea el traslado. |
| `generated thumbnail no row references, left where it is: <path>` | El backend deja la miniatura en su lugar; no bloquea el traslado. |
| `no capture checksum is held for image N at <path>; no relocation record is written for its move to <path>` | El backend movió el archivo, pero el manifiesto no contiene su suma de comprobación, así que no registra allí el cambio de nombre. |
| `no manifest holds a capture record for capture(s) [...] of volume N` | El manifiesto del volumen carece de registros de captura que tampoco figuran en otros manifiestos. |
| `copied N missing record(s) into volume N's manifest` | El backend copió desde otros manifiestos los registros de captura que faltaban. |
| `completing the interrupted batch of volume N` | El backend completó un lote interrumpido por un fallo o un corte de corriente. |
| `not run, the projects root is not usable: ...` | El backend no movió nada y sigue prestando servicio. |
| `refusing to serve` | El diario de operaciones indica otro directorio raíz de proyectos, o el backend no puede leer el diario o la lista de archivos auxiliares. El backend no inicia el servicio hasta que resuelvas el problema. Si indica otro directorio raíz, vuelve a activar ese almacenamiento y reinicia. |
| `failed` | Un error inesperado. El backend presta servicio salvo que el fallo haya dejado un diario de operaciones pendiente. |

Motivos para omitir una imagen:

| Motivo | Significado |
|---|---|
| `stem_dir_occupied` | `<stem>/` contiene archivos ajenos al volumen; consulta la tabla anterior. |
| `stem_dir_is_project_tree` | `<stem>/` es un directorio de proyecto activo. |
| `stem_dir_outside_projects_root` | `<stem>/` apunta fuera del directorio raíz de proyectos. |
| `no_stem` | El prefijo guardado no es válido. |
| `outside_storage`, `outside_projects_root` | La ruta de la fila está fuera del directorio raíz de proyectos activo. Los archivos cargados antes de esta estructura en `/var/lib/dtk/uploads/` permanecen allí y reciben estos motivos. |
| `missing` | El archivo de la fila no existe y ningún archivo de `captures/` coincide con el sha256 registrado al capturar. |
| `row_changed` | La fila cambió mientras el backend preparaba el traslado. |

El registro de systemd también contiene mensajes de nivel INFO, como el de archivos liberados cuyas referencias ahora apuntan a sus nombres nuevos. Desde el backend `aa0a10a` (#134), el backend envía a stderr los mensajes INFO de sus registradores `app.*` y `capture.*`; systemd los registra con el formato `<LEVEL> <logger>: <message>` (`app/core/logging_setup.py`). `DTK_LOG_LEVEL` establece el nivel, con `INFO` como valor predeterminado.

---

## 4. Preparar la copia remota sin reiniciar {#provision-the-offsite-copy-without-restarting}

### 4.0 Crear el archivo de suspensión de cargas {#create-the-upload-hold}

Mientras exista `/var/lib/dtk/offsite-hold`, el equipo no envía nada a la copia remota:

- El backend no sube ni enumera imágenes. Si ya hay una carga en curso, la detiene después del objeto que está procesando.
- El backend no genera copias del catálogo.
- El backend rechaza la liberación de un volumen de la tarjeta. La simulación de liberación y la restauración siguen disponibles.

El backend comprueba la existencia del archivo al empezar cada ejecución. Crearlo o eliminarlo afecta a la siguiente ejecución sin necesidad de reiniciar. La suspensión también continúa después de reinicios por fallos, reinicios del equipo o cortes de corriente. Los comandos del paso 5 no consultan ese archivo. Solo importa que exista. Puedes cambiar su ruta con `DTK_OFFSITE_HOLD_FILE`. `GET /system/catalogue-backup` informa de él mediante `held` y `hold_file`. La suspensión también afecta al envío a Fisqua y a la consulta de su estado: ambos responden "held" al empezar, sin llamar a Fisqua ni crear un manifiesto (9.3).

Crea el archivo antes de preparar la copia remota, o antes del paso 2 si `offsite.env` ya registra un destino remoto y un tenant (2.5):

```bash
sudo touch /var/lib/dtk/offsite-hold
```

Elimínalo como último paso, en 6.2.

### 4.1 El archivo de claves {#the-key-file}

Usa un editor para guardar las credenciales del equipo en un archivo que solo pueda leer `root`:

```bash
sudo install -m 0600 /dev/null /root/dtk-offsite-key
sudo nano /root/dtk-offsite-key
```

Incluye estas líneas:

```text
KEY_ID=...
APP_KEY=...
BUCKET=...
READ_KEY_ID=...
READ_APP_KEY=...
```

`provision-rclone.sh` muestra el mismo archivo como un heredoc (`sudo sh -c 'cat > /root/dtk-offsite-key' <<'END'`). Si lo escribes en un shell interactivo, el historial guarda las líneas del heredoc, incluidas las claves. Usar un editor evita incluirlas en el historial.

| Clave | Qué contiene |
|---|---|
| `KEY_ID`, `APP_KEY` | La clave de escritura del equipo, `captua-<unit>-write`, con `listBuckets`, `listFiles` y `writeFiles`. No tiene `readFiles` ni `deleteFiles`, así que alguien que robe el equipo no puede descargar ni borrar el archivo remoto. |
| `BUCKET` | El bucket del equipo; consulta la tabla siguiente. |
| `READ_KEY_ID`, `READ_APP_KEY` | Opcionales. La clave de lectura del equipo, `captua-<unit>-read`, con `listBuckets`, `listFiles` y `readFiles`. Debe ser distinta de la clave de escritura. Sin ella, no puedes restaurar un volumen liberado. |

Ambas claves limitan el acceso al bucket del equipo y al prefijo de su tenant. `provision-rclone.sh` solo exige `writeFiles` y `listFiles` para la clave de escritura, y `listFiles` y `readFiles` para la de lectura. Las claves emitidas para 0.1.0 también incluyen `listBuckets`, como la clave provisional de Rionegro. Probamos cada clave de 0.1.0 desde una estación de trabajo con la herramienta `b2`: permitió la autenticación y la consulta de su prefijo de tenant, y rechazó el acceso fuera de él. Todavía no hemos usado esas claves con rclone en un equipo ni probado una clave sin `listBuckets`. Falta comprobar si rclone necesita ese permiso. El archivo tiene permisos 0600 y pertenece a `root`.

Para la conexión con Fisqua, el mismo archivo contiene `FISQUA_TOKEN=<token>`, el token que Fisqua emitió para este equipo: exactamente 64 caracteres hexadecimales en minúsculas (9.2).

#### Equipos y tenants {#units-and-tenants}

| Equipo | Tenant (`--tenant`) | Bucket (`BUCKET`) | Claves |
|---|---|---|---|
| rionegro | `ahr` | `neogranadina-masters` | `captua-rionegro-write`, `captua-rionegro-read` |
| lab | `ampl` | `ampl-masters` | `captua-lab-write`, `captua-lab-read` |
| sbmal | `sbmal` | `ampl-masters` | `captua-sbmal-write`, `captua-sbmal-read` |
| cobos (solo staging) | `cobos` | `ampl-masters` | `captua-cobos-write`, `captua-cobos-read` |

Nunca incluyas un identificador de clave ni una clave de aplicación en un registro, una incidencia o esta guía.

Nunca pases una clave como asignación delante de `sudo`: formará parte de la línea de comandos de sudo, que cualquier usuario local puede leer en `/proc/<pid>/cmdline`.

### 4.2 Ejecutar el script de preparación {#run-the-provisioning-script}

```bash
sudo DTK_OFFSITE_KEY_FILE=/root/dtk-offsite-key \
    /home/pi/dtk/scripts/provision-rclone.sh \
    --tenant <tenant> \
    --dump-recipient age172wkzadqepd565chppztfw8jefpcga8s7t6eqrfhnxnv2nlfkdrqygrl3m
```

- `--tenant` es el prefijo de las claves de todos los objetos del equipo y su identificador en la URL de Fisqua. El script exige entre 1 y 63 caracteres: letras minúsculas, dígitos y guiones simples. Debe empezar por una letra y no terminar con un guion. Rechaza `platform`, `www`, `api`, `admin` y `app`. Para reemplazar un tenant ya registrado, también necesitas `--change-tenant`.
- `--dump-recipient` es la clave pública de age para cifrar las copias del catálogo. La del ejemplo es el destinatario de todos los equipos. El script rechaza una clave privada. Nunca guardes la clave privada en el equipo.
- `--fisqua-env production` o `--fisqua-env staging` activa la conexión con Fisqua, con `FISQUA_TOKEN` en el archivo de claves (9.2).
- En ejecuciones posteriores que no indiquen esos valores, el script conserva el tenant, el destinatario de las copias, el entorno de Fisqua y su token. Esto incluye la ejecución de cada actualización.

Antes de probar el bucket, el script comprueba que `api.backblazeb2.com` responda. Cuenta cualquier respuesta HTTP, incluso un estado de error. Solo omite las pruebas cuando no puede establecer la conexión, y entonces lo indica. Las pruebas verifican las credenciales: el script enumera el prefijo del tenant una vez con la clave de escritura y, si esta ejecución escribió una clave de lectura, otra vez con ella. Una consulta fallida imprime una advertencia y no detiene la ejecución. Sin tenant registrado, la prueba de escritura enumera el bucket y el script omite la de lectura.

El script escribe la configuración de rclone en `/var/lib/dtk/rclone.conf`, con el destino remoto de carga y `[b2read]` cuando proporcionas una clave de lectura, y escribe completo `/var/lib/dtk/offsite.env`. Ambos archivos tienen permisos 0600 y pertenecen a `pi`. Nunca reemplaza una credencial existente. No inicia, detiene ni reinicia `dtk`.

Si indica `/var/lib/dtk/rclone.conf already exists and was NOT replaced`, el script no usó las credenciales ni escribió `offsite.env`. No registró nada, incluidos el tenant y el destinatario. Resuélvelo antes del paso 5: el script muestra el comando para mover el archivo aparte. Después vuelve a ejecutar el comando de 4.2 con `--tenant` y `--dump-recipient`. La línea de repetición que muestra el script omite ambos valores, y todavía no están registrados.

Cuando la ejecución termine correctamente, elimina el archivo de claves:

```bash
sudo rm /root/dtk-offsite-key
```

### 4.3 Comprobar los valores registrados {#check-what-was-recorded}

```bash
sudo sed 's/^DTK_FISQUA_TOKEN=.*/DTK_FISQUA_TOKEN=(not shown)/' /var/lib/dtk/offsite.env
```

`sed` imprime el archivo con el token de Fisqua reemplazado para que no aparezca en pantalla. El archivo contiene `DTK_RCLONE_BIN`, `DTK_OFFSITE_REMOTE`, `DTK_OFFSITE_TENANT` y `DTK_OFFSITE_DUMP_RECIPIENT`; `DTK_OFFSITE_READ_REMOTE` si proporcionaste una clave de lectura; `DTK_RCLONE_CONFIG` si la ejecución estableció la ruta de configuración de rclone; y `DTK_FISQUA_TOKEN` y `DTK_FISQUA_ENV` si el equipo tiene conexión con Fisqua (9.2).

### 4.4 Por qué todavía no hay cargas {#why-nothing-uploads-yet}

El backend lee `.env` y `/var/lib/dtk/offsite.env` una sola vez, al crear su configuración durante la importación. Un valor de `offsite.env` tiene prioridad sobre el mismo valor de `.env`. El backend inicia las tareas programadas de cargas y copias al arrancar. Por eso el proceso activo conserva la configuración con la que arrancó, todavía sin tenant, y no sube nada hasta el reinicio del paso 6.

Cada comando del paso 5 es un proceso nuevo que crea su configuración al empezar y lee el `offsite.env` nuevo. Por eso el paso 5 puede consultar el bucket y registrar claves antes de la primera carga.

Si un fallo, un reinicio o un corte de corriente reinicia el backend antes del paso 6, el proceso nuevo lee el tenant. El archivo de suspensión (4.0) impide que suba archivos en ese caso.

### 4.5 Ancho de banda para la copia remota {#offsite-bandwidth}

El backend aplica un único límite de ancho de banda a las cargas de imágenes, las cargas de copias del catálogo y la restauración de archivos liberados: `DTK_OFFSITE_BWLIMIT`, que pasa a rclone como `--bwlimit`. No limita las consultas del bucket ni las llamadas a Fisqua. El valor predeterminado es `750k`, aproximadamente 750 KB/s; falta comprobar la unidad que interpreta rclone. Ese es el valor que ha usado el equipo de Rionegro con su conexión de unos 12 Mbit/s. Para otro lugar, mide la velocidad de subida en Mbit/s, divide entre 8 para obtener MB/s y usa aproximadamente la mitad. El equipo de pruebas usó el valor predeterminado hasta la ejecución `cobos-bench-005` (9.3). Después lo configuramos en `1.5M`, a partir de una conexión doméstica de unos 25 Mbit/s medida el 25 de octubre de 2026.

Configúralo en `/home/pi/dtk/.env`; `provision-rclone.sh` no escribe ese valor:

```bash
DTK_OFFSITE_BWLIMIT=1.5M
```

El backend lo lee al arrancar. Durante una actualización, configúralo antes del paso 6; el reinicio de 6.1 lo aplicará. Fuera de una actualización, reinicia `dtk` con `sudo systemctl restart dtk`.

---

## 5. Comandos que debes ejecutar una sola vez {#one-time-commands}

Ejecuta cada comando primero sin `--apply`: así no escribe nada y muestra el informe en JSON. Después ejecútalo con `--apply`. Usa la cuenta `pi` y ejecútalos desde `backend/`, donde el backend encuentra `../.env`:

```bash
cd /home/pi/dtk/backend
pixi run python -m app.core.image_upload <command> ... [--apply]
```

Códigos de salida: `0` con el informe; `2` con `error: <reason>`, o con las instrucciones de uso si escribiste mal el comando; `1` con un traceback de Python para cualquier otro fallo. La base de datos debe estar en funcionamiento, así que deja `dtk` en ejecución.

Los informes pueden ser largos. Envía cada uno a un archivo y léelo allí:

```bash
pixi run python -m app.core.image_upload adopt-map /path/to/map.json > ~/adopt-map-<stem>-dry.json
```

`adopt`, `adopt-map` y `backfill-preview-digests` calculan los hashes de los archivos de la tarjeta tanto en la simulación como con `--apply`. Por eso ambas ejecuciones tardan si el volumen es grande, y una desconexión de SSH las interrumpe. Con `systemd-run` continúan aunque pierdas la conexión. Envía el informe a un archivo cuyo contenido cada ejecución reemplaza, y los errores al registro de systemd (comprueba esta forma de ejecución en el equipo de pruebas):

```bash
sudo systemd-run --unit=dtk-adopt --collect --uid=pi \
    --working-directory=/home/pi/dtk/backend \
    --property=StandardOutput=truncate:/home/pi/adopt-map-<stem>.json \
    --property=StandardError=journal \
    /home/pi/.pixi/bin/pixi run python -m app.core.image_upload adopt-map /path/to/map.json --apply
journalctl -u dtk-adopt -f
```

### 5.1 `adopt-map`, una vez por cada mapa de cambio de nombres {#adopt-map-once-per-rename-map}

Solo si alguien copió las imágenes del archivo al bucket con los nombres del contrato. El mapa de cambio de nombres es el archivo JSON del contrato 1.1 que enumera, para un volumen, la clave de destino de cada captura y vista previa copiada.

```bash
pixi run python -m app.core.image_upload adopt-map /path/to/map.json
pixi run python -m app.core.image_upload adopt-map /path/to/map.json --apply
```

El comando registra cada entrada que supera todas las comprobaciones como la clave fija y verificada de su imagen, sin subir ningún archivo, tanto si el archivo todavía está en la tarjeta como si no. Si una entrada falla alguna comprobación, el comando la incluye en `refused` con el motivo y no registra nada para ella.

El comando rechaza todo el mapa, muestra `error: <reason>` y no escribe nada cuando:

- no puede leer el archivo, o el archivo no es JSON, o no contiene un objeto JSON;
- los valores de `contract`, `version` o `kind` no son, respectivamente, `fisqua-captua-exchange`, `1.1` y `rename-map`;
- falta el objeto `volume` o `destination`, o `entries` no es una lista;
- ningún volumen del equipo coincide tanto con `volume.captuaCollectionId` como con `volume.stem` del mapa;
- `DTK_OFFSITE_REMOTE` no tiene un valor definido, no tiene el formato `<remote>:<bucket>` o su bucket no coincide con `destination.bucket`;
- `destination.root` no es un prefijo de clave;
- `DTK_OFFSITE_TENANT` no tiene un valor definido, tiene un valor inválido o no coincide con el primer segmento de `destination.root`;
- la solicitud para listar el bucket no obtiene respuesta.

Lee `refused` y `refused_counts` en la simulación. Resuelve cada entrada rechazada cuya imagen todavía esté en la tarjeta antes de que el backend empiece a subir archivos en el paso 6: de lo contrario, el componente de carga subiría ese archivo con una segunda clave, su nombre en el disco. Aplica todos los mapas antes del paso 5.2 para que `adopt` no registre una clave a la que un mapa da otro nombre.

### 5.2 `adopt <prefix>`, para objetos que no figuran en un mapa {#adopt-prefix-for-objects-not-in-a-map}

```bash
pixi run python -m app.core.image_upload adopt <prefix>
pixi run python -m app.core.image_upload adopt <prefix> --apply
```

`<prefix>` es relativo a `DTK_OFFSITE_REMOTE`. El comando lista ese prefijo, calcula el hash de cada imagen que aún no tiene clave y pertenece a un volumen con prefijo de nombre de archivo, y registra un objeto de la lista como clave de la imagen cuando exactamente un objeto tiene el mismo SHA1. El comando informa de las coincidencias ambiguas y las claves que ya tienen asignación, sin registrarlas. Solo busca coincidencias para archivos que todavía están en la tarjeta.

El comando no comprueba el tenant, pero debes darle un prefijo dentro del tenant (`<tenant>/...`). Al liberar espacio, el backend lista el directorio de cada clave y no lista nada fuera del prefijo del tenant. Por eso nunca puedes liberar un volumen con una clave adoptada fuera de ese prefijo.

### 5.3 `raise-capture-counter <stem> <counterAfter>` {#raise-capture-counter-stem-counterafter}

Para cada volumen cuyo mapa haya asignado números de captura fuera del equipo, aumenta el contador hasta el valor `volume.counterAfter` del mapa. Así la próxima captura usa el número siguiente:

```bash
pixi run python -m app.core.image_upload raise-capture-counter <stem> <counterAfter>
pixi run python -m app.core.image_upload raise-capture-counter <stem> <counterAfter> --apply
```

El contador nunca disminuye: el comando rechaza cualquier valor inferior al actual.

### 5.4 `mark-freed <stem>` {#mark-freed-stem}

Para cada volumen cuyos archivos hayas retirado de la tarjeta manualmente:

```bash
pixi run python -m app.core.image_upload mark-freed <stem>
pixi run python -m app.core.image_upload mark-freed <stem> --apply
```

El comando marca como liberado cada archivo ausente cuyo objeto verificado aparece con el mismo SHA1 en una lista nueva del bucket. No borra nada. Si el archivo está ausente y el bucket no permite comprobar su existencia, el comando lo incluye en `unaccounted` y no lo marca.

Ejecuta el comando solo con el almacenamiento del volumen montado en la raíz activa de proyectos. El comando considera ausente un archivo cuando no está en su ruta. Por eso interpreta como completamente ausente un volumen de una unidad externa que no está montada.

### 5.5 `backfill-preview-digests <stem>` {#backfill-preview-digests-stem}

Para cada volumen con archivos maestros RAW:

```bash
pixi run python -m app.core.image_upload backfill-preview-digests <stem>
pixi run python -m app.core.image_upload backfill-preview-digests <stem> --apply
```

El comando registra el sha256 de cada vista previa RAW capturada antes de que el registro de captura incluyera las vistas previas. Para ello, añade un registro `preview_digest` al archivo `metadata/manifest.jsonl` del volumen. Al liberar espacio, el backend rechaza una vista previa sin hash (`no_preview_digest`), así que ejecuta este comando antes de liberar espacio por primera vez. El comando calcula el hash a partir del archivo de la tarjeta: si retiraste una vista previa antes de registrar su hash, el comando la muestra como `missing` (o `freed`) y no puede completar ese registro.

---

## 6. Reiniciar y comprobar {#restart-and-check}

### 6.1 Reiniciar {#restart}

```bash
sudo systemctl restart dtk
```

El backend ahora lee el tenant e inicia las dos tareas programadas. Ejecuta cada una por primera vez `DTK_OFFSITE_BACKUP_DELAY` segundos después del inicio (300 de forma predeterminada), y de nuevo `DTK_OFFSITE_BACKUP_INTERVAL` segundos después de que termine cada ejecución (1800 de forma predeterminada).

### 6.2 Retirar la suspensión {#remove-the-hold}

Como último paso, retira la suspensión que creaste en 4.0:

```bash
sudo rm /var/lib/dtk/offsite-hold
```

El backend empieza a subir archivos en la siguiente ejecución programada, sin necesidad de reiniciarlo.

### 6.3 Comprobar {#check}

- **El indicador de recepción de cada volumen.** En la página del volumen, la línea de copia remota muestra `Uploading: N of M files verified, P pending` durante la carga, y `Stored offsite: N of N files verified` cuando el backend ha verificado todos los objetos. `N files need attention` indica que el backend rechazó objetos: el bucket contiene un archivo diferente en esa clave (`remote_differs`), o el sha256 del archivo no coincide con el de su registro de captura (`fixity`). El backend no vuelve a intentar la carga de un objeto rechazado. `GET /collections/{id}/offsite` devuelve los mismos recuentos.
- **El estado de la copia remota del equipo.** La sección **Offsite copy** de la página de configuración y el indicador de la página de resumen consultan `GET /system/catalogue-backup`. Desde el equipo:

  ```bash
  read -rs -p "Password: " PW; echo
  TOKEN=$(PW="$PW" python3 -c 'import json,os; print(json.dumps({"username": "<admin>", "password": os.environ["PW"]}))' \
    | curl -s -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d @- \
    | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
  unset PW
  curl -s http://localhost:8000/system/catalogue-backup -H "Authorization: Bearer $TOKEN"
  ```

  `read -rs` evita que la contraseña aparezca en la pantalla y en el historial del shell. El cuerpo de la solicitud pasa por una tubería, así que la contraseña nunca aparece en una línea de comandos.

  `held` tiene el valor `false`; `enabled` e `images.enabled` tienen el valor `true`; `images.misconfigured` tiene el valor `null`; el backend completa `last_verified_at` después de verificar la primera copia de la base de datos. Esta respuesta no indica si falta el destinatario de cifrado de esa copia o si es inválido: `enabled` conserva el valor `true` y `last_verified_at` no avanza, y cada ejecución escribe `catalogue_backup_failed` en el registro del sistema.

### 6.4 Liberar primero un solo volumen {#free-one-volume-first}

No liberes nada hasta que el backend haya verificado una copia del catálogo: `last_verified_at` en 6.3 debe tener un valor distinto de `null`. Después elige un volumen cuya línea de copia remota muestre `Stored offsite`. Con una cuenta de administrador, ábrelo, elige **Space on the SD card** y luego **Free space on the SD card**. Captua primero solicita al backend la simulación (`GET /collections/{id}/offsite/free`) y enumera en el cuadro de diálogo lo que liberaría y cada archivo que dejaría en la tarjeta, con el motivo. La simulación no modifica nada. Confirma con **Free space** solo cuando esa lista corresponda a lo que esperas.

Antes de retirar cualquier archivo, el backend vuelve a calcular el SHA1 de cada uno y después vuelve a listar el bucket, una vez por cada directorio de clave. El backend deja en la tarjeta cualquier archivo que falle una de las dos comprobaciones y lo incluye en la lista con un motivo. Las miniaturas permanecen, así que puedes seguir explorando el volumen. Un administrador puede recuperar un archivo liberado con **Restore to the SD card**; para ello necesita la clave de lectura de 4.1.

---


## 7. Si `update.sh` falla {#if-update.sh-fails}

### 7.1 Qué hace `update.sh` cuando ocurre un fallo {#what-update.sh-does-on-a-failure}

- **Antes de detener el servicio.** El script restaura el código del repositorio, los submódulos, la imagen del frontend y el entorno de pixi a la versión que todavía está en ejecución, y no reinicia el servicio. El script aún no ha modificado la base de datos.
- **Después de detener el servicio, antes de iniciar la versión nueva.** El script restaura el código y las revisiones fijadas de los submódulos, la imagen del frontend y el entorno de pixi. Si había empezado una migración, restaura la base de datos exclusivamente a partir de la copia que creó con el backend detenido. Después inicia la versión anterior y solo informa que está en funcionamiento cuando el backend responde en `/health`. Cuando ninguna rama remota contiene el commit nuevo, el script lo conserva en una rama local `failed-update/<timestamp>`.
- **Después de iniciar la versión nueva.** El script no restaura nada automáticamente: la versión nueva puede haber guardado datos. El script detiene `dtk`, deja el equipo detenido con el código nuevo y la base de datos migrada, escribe el registro sin resolver y muestra el comando de reversión con la advertencia de que esa operación descarta todo lo escrito después de la copia.

Para reinstalar el entorno anterior de pixi, el equipo necesita acceso al registro de conda si la actualización cambió `pixi.lock`, salvo que la caché de pixi todavía contenga todos los paquetes. El script avisa cuando no puede reinstalarlo.

Después de una restauración, la rama local apunta al commit anterior y los submódulos tienen las revisiones fijadas por ese commit. En la instalación de 0.1.0, esto deja `main` apuntando al commit que el equipo usaba antes. Antes de volver a intentarlo, haz que apunte otra vez a `origin/main` y selecciona las revisiones de los submódulos que fija ese commit, porque `update.sh --no-pull` no las sincroniza:

```bash
git -C /home/pi/dtk checkout -B main origin/main
git -C /home/pi/dtk submodule update --init --recursive
git -C /home/pi/dtk submodule status
```

Cada línea de `submodule status` debe empezar con un espacio. Después comprueba el árbol de trabajo como indica 2.1 antes de ejecutar otra vez el paso 2.2.

### 7.2 Una instalación fallida de 0.1.0 {#a-failed-0.1.0-install}

`update.sh` puede dejar un registro sin resolver (7.3) aunque el disco ya tenga el código anterior: cuando no pudo restaurar la base de datos, rechazó la restauración o solo restauró parte del código. Si el `update.sh` del disco es anterior al mecanismo de ese registro, como ocurre con la versión anterior a 0.1.0, no rechazaría la ejecución. En ese caso, y solo en ese caso, el script muestra `DO NOT RUN scripts/update.sh ON THIS UNIT UNTIL THE ROLLBACK HAS SUCCEEDED`. Ejecuta únicamente el comando de reversión registrado, mediante `systemd-run` como indica 7.3.

### 7.3 El registro sin resolver {#the-unresolved-record}

Cuando una actualización no puede dejar el código y la base de datos en estados compatibles, `update.sh` escribe `/var/lib/dtk/backups/unresolved-deployment` y crea el archivo indicador `/etc/dtk/unresolved-deployment`. Un archivo de configuración complementaria de systemd, `/etc/systemd/system/dtk.service.d/unresolved.conf`, establece `ConditionPathExists=!/etc/dtk/unresolved-deployment` como condición de inicio de `dtk`. Por eso systemd no inicia `dtk` mientras exista el indicador, tanto al reiniciar el servicio como al reiniciar el equipo. `install-service.sh` instala esa configuración complementaria, y `update.sh` también la instala cada vez que escribe un registro.

Mientras exista el indicador, `sudo systemctl restart dtk` termina con el código `0` y no inicia `dtk`; `systemctl status dtk` muestra la condición de inicio como incumplida.

Mientras exista el registro, `update.sh` rechaza la ejecución. Muestra el registro, su antigüedad y si `dtk` ha arrancado después de que el script escribiera el registro, e indica cómo continuar.

```bash
sudo cat /var/lib/dtk/backups/unresolved-deployment
```

| `kind` | Qué ocurrió | Qué debes hacer |
|---|---|---|
| `started-failed` | `update.sh` inició la versión nueva y después falló. El código corresponde a la versión nueva y la base de datos tiene las migraciones para ella. | Ejecuta el comando de reversión registrado, que devuelve el código y la base de datos a la versión anterior y descarta todo lo escrito después de la copia, o, cuando hayas corregido la causa, ejecuta `update.sh --resolve-forward` (7.4). En la primera instalación de 0.1.0, una vez que el backend ha movido archivos a `<stem>/captures/`, la comprobación de prefijos de nombre de archivo rechaza la reversión (8.0a); usa `--resolve-forward`. |
| `migrated-not-restored` | `update.sh` falló después del inicio de la migración y no restauró el código anterior, o solo restauró una parte. La base de datos puede tener una migración completa o parcial. | Ejecuta el comando de reversión registrado después de resolver lo que impidió restaurar el código; o usa `--resolve-forward` si el código corresponde exactamente al commit fallido y la base de datos está en la última revisión de migraciones de ese código. |
| `restore-failed` | El script eliminó la base de datos para restaurarla, y la carga de la copia falló o sufrió una interrupción. La base de datos puede estar vacía o parcialmente restaurada. Una reversión interrumpida después de eliminar la base de datos también escribe este tipo de registro. | Ejecuta únicamente el comando de reversión registrado. `--resolve-forward` rechaza este tipo. |
| `restore-refused` | `update.sh` falló después de la migración y rechazó la restauración antes de eliminar nada (había un backend en ejecución o el script no pudo instalar la protección de inicio). El código ya corresponde al commit anterior; la base de datos conserva el estado que dejó la migración. | Ejecuta únicamente el comando de reversión registrado. `--resolve-forward` rechaza este tipo. |

El registro indica el comando de reversión en su línea `rollback-command`, que empieza con `sudo`. Ejecútalo mediante `systemd-run`, igual que `update.sh`: omite el `sudo` inicial y añade `sudo systemd-run --unit=dtk-rollback --collect` delante del resto. La reversión solo ignora SIGHUP a partir del paso de la base de datos, así que una desconexión de SSH puede interrumpirla antes. Por ejemplo:

```bash
sudo systemd-run --unit=dtk-rollback --collect \
    /var/lib/dtk/rollback-update.sh --project-root=/home/pi/dtk --yes /var/lib/dtk/backups/pre-update-<YYYYmmdd-HHMMSS>.sql.gz
journalctl -u dtk-rollback -f
```

Una reversión exitosa elimina el registro y el indicador. Si la reversión rechaza la ejecución porque el repositorio tiene archivos modificados, deja primero el árbol de trabajo sin modificaciones.

**Un indicador sin registro.** `update.sh` rechaza la ejecución y `dtk` no arranca. Averigua qué versión tiene el código y si la base de datos corresponde a ella (consulta la salida de la ejecución fallida y `systemctl status dtk`). Cuando ambos coincidan, elimina el indicador: `sudo rm /etc/dtk/unresolved-deployment`.

### 7.4 `update.sh --resolve-forward [--no-start]`

Usa esta opción para conservar la versión que falló cuando hayas corregido la causa y prefieras conservar lo que guardó. Usa la reversión (paso 8) para volver a la versión anterior.

```bash
sudo systemd-run --unit=dtk-deploy --collect /home/pi/dtk/scripts/update.sh --resolve-forward
```

El script no cambia nada hasta que todas las comprobaciones den un resultado correcto:

- `HEAD` coincide exactamente con `failed-commit` del registro;
- ningún archivo versionado tiene modificaciones;
- cada submódulo tiene su revisión fijada, y los commits seleccionados de los submódulos y cualquier referencia en el área de preparación coinciden con las referencias gitlink que registra `HEAD`;
- `dtk` y todos los procesos del backend están detenidos;
- con solo el contenedor de la base de datos en funcionamiento, `alembic_version` de la base de datos coincide con la última revisión de migraciones del código seleccionado del backend.

Después el script escribe el commit en `last-deployed-SHA`, elimina el registro y el indicador, inicia `dtk`, espera la respuesta de `/health` y vuelve a iniciar el quiosco (2.6). Con `--no-start` registra la versión y deja el equipo detenido, para que después puedas instalar un commit corregido mediante una actualización habitual. Rechaza los tipos `restore-failed` y `restore-refused`, y rechaza la ejecución cuando no existe un registro.

---

## 8. Reversión {#rollback}

### 8.0 Antes de volver a una versión anterior {#before-you-roll-back}

Si existe `/var/lib/dtk/backups/unresolved-deployment`, ejecuta el comando de reversión que indica el registro, mediante `systemd-run` como en 7.3: la reversión rechaza cualquier otro commit o copia mientras exista el registro. En caso contrario:

```bash
sudo ls -lt /var/lib/dtk/backups/
sudo cat /var/lib/dtk/backups/pre-update-SHA
journalctl -u dtk-deploy | grep -A1 "Backing up the database with the backend stopped, to:"
```

El último comando muestra la copia que esta actualización creó con el backend detenido. Comprueba que figure en la lista y que `pre-update-SHA` indique el commit que contenía `last-deployed-SHA` en 1.1, o el que escribiste allí en ese paso. Indica esa copia en la línea de comandos en lugar de confiar en que la más reciente sea la correcta:

```bash
sudo systemd-run --unit=dtk-rollback --collect \
    /home/pi/dtk/scripts/rollback-update.sh --yes /var/lib/dtk/backups/pre-update-<YYYYmmdd-HHMMSS>.sql.gz
journalctl -u dtk-rollback -f
```

Necesitas `--yes` por el mismo motivo que en 2.2: sin terminal, el script cancela la ejecución al pedir confirmación. Con `--yes` elimina y restaura la base de datos sin preguntar. La reversión toma el mismo bloqueo que `update.sh` (2.2).

Si una interrupción detiene la reversión a mitad del proceso, vuelve a ejecutarla desde la copia que conserva fuera del repositorio:

```bash
sudo systemd-run --unit=dtk-rollback --collect \
    /var/lib/dtk/rollback-update.sh --project-root=/home/pi/dtk --yes /var/lib/dtk/backups/pre-update-<YYYYmmdd-HHMMSS>.sql.gz
```

En el primer inicio después de una reversión, `start.sh` ejecuta `pixi run start`, que puede reinstalar el entorno de pixi para el archivo de bloqueo restaurado; esto necesita conexión a la red.

### 8.0a La comprobación de prefijos de nombre de archivo {#a-the-stem-guard}

Antes de cambiar nada, el script comprueba si el catálogo restaurado apuntaría a archivos ausentes:

- Lee todas las rutas de imágenes de la copia y busca cada archivo en el disco. Resuelve una ruta relativa a partir de `/home/pi/dtk/backend`, igual que el backend. No cuenta un archivo maestro cuyo espacio ya liberaste gracias a la copia remota. Cualquier volumen con una imagen ausente está en riesgo.
- Consulta en la base de datos actual los volúmenes con prefijo de nombre de archivo y solo cuenta aquellos cuyo directorio con ese prefijo existe. Busca bajo la raíz de proyectos que indica `/var/lib/dtk/storage-override.json` y bajo la raíz predeterminada (`PROJECTS_ROOT`, o `<DTK_DATA_DIR>/projects`); resuelve una raíz relativa a partir de `/home/pi/dtk/backend`, igual que el backend. Un volumen con un directorio de prefijo que no figura en la copia está en riesgo: desaparecería del catálogo y sus archivos quedarían en el directorio.
- Si el script no puede leer las filas de imágenes o registros de la copia, incluye en la lista todos los volúmenes con un directorio de prefijo, y el mensaje aclara que algunos pueden estar a salvo.

Si algún volumen está en riesgo, el script rechaza la ejecución sin cambiar nada y escribe la lista en `/var/lib/dtk/backups/rollback-stems-at-risk`, que pertenece a root y tiene permisos 0600. El archivo empieza con líneas de encabezado `#` (la copia, si aceptaste la pérdida y cómo comprobó el script la copia), seguidas de una tabla separada por tabulaciones con las columnas `id`, `name`, `filename_stem`, `images_missing`, `images_total` y `example`. El mensaje empieza así:

```text
✗ Restoring this backup may cut volumes off from their files:
```

Y termina así:

```text
  Nothing has been changed. To roll back anyway, accepting this, run the
  same command again with --accept-lost-stems.
```

Con `--accept-lost-stems`, el script continúa, registra `accepted: yes` en la lista y añade `lost-stems-accepted:` con la ruta de la lista al registro que escribe antes de eliminar la base de datos.

El propio script inicia el contenedor de la base de datos si no está en funcionamiento. Rechaza la ejecución si ese inicio falla o si falla una consulta: `✗ Could not check the current database for volumes with a stem directory`. Restablece el acceso a la base de datos y vuelve a ejecutarlo: inicia `dtk` o, si el indicador de actualización sin resolver impide iniciar `dtk`, inicia solo el contenedor de la base de datos (`sudo docker compose -f /home/pi/dtk/docker-compose.yml -f /home/pi/dtk/docker-compose.pi.yml up -d db`). Hay tres estados que no causan rechazo: una base de datos inexistente, como la que deja una restauración interrumpida, no contiene ningún volumen; una base de datos sin tabla de volúmenes tampoco contiene ninguno; y un esquema anterior a los prefijos de nombre de archivo no tiene directorios de prefijo. En los tres casos, el script sigue comprobando las imágenes de la propia copia.

**La primera instalación de 0.1.0.** Cuando 0.1.0 ya ha arrancado y ha movido archivos a `<stem>/captures/` (3.3 y, para volúmenes que ya tenían prefijo, el inicio al final de `update.sh`), la copia anterior a la actualización indica las rutas antiguas de esos archivos. Una reversión a esa copia dejaría los volúmenes sin acceso a sus archivos, así que la comprobación rechaza la ejecución. Después de una actualización fallida con un registro de tipo `started-failed`, usa `update.sh --resolve-forward` (7.4) en lugar de una reversión. Un registro de tipo `migrated-not-restored` significa que la versión nueva nunca arrancó, así que no movió ningún archivo. Después de una actualización exitosa, instala una versión corregida mediante una actualización habitual.

Todavía no existe ningún comando para recuperar un volumen después de aceptar su pérdida. Tenemos previsto un comando `restore-stem` para después de 0.1.0.

### 8.1 Qué restaura {#what-it-restores}

1. El script comprueba que el árbol de trabajo esté limpio, que los submódulos tengan sus revisiones fijadas y que el repositorio contenga el commit anterior a la actualización. Si alguna comprobación falla, termina sin detener el equipo. Conserva una copia de sí mismo en `/var/lib/dtk/rollback-update.sh`.
2. Detiene `dtk`.
3. Selecciona el commit de `/var/lib/dtk/backups/pre-update-SHA` y sincroniza los submódulos con las revisiones fijadas por ese commit. Si no hay un commit registrado, deja el código tal como está.
4. Elimina la base de datos y restaura la copia `pre-update-*.sql.gz` más reciente o la que indicaste en la línea de comandos.
5. Restaura la imagen del frontend registrada para la versión restaurada, si el registro la identifica y el equipo todavía la tiene.
6. Elimina el registro y el indicador de actualización sin resolver, inicia `dtk`, vuelve a iniciar el quiosco e informa, componente por componente, si el entorno de pixi y la imagen del frontend corresponden a la versión restaurada. No vuelve a crear el entorno de pixi; el resumen indica el comando necesario.

No modifica `/var/lib/dtk/offsite.env`, la configuración de rclone, los archivos de la tarjeta o del bucket, ni el nombre del equipo (2.6), `.env`, `/etc/hosts` o avahi.

**Aparta `offsite.env` antes de revertir a una versión anterior después del paso 4.** Los backends desde `ba1688e` (16 de octubre de 2026) hasta `2dda6ac` (24 de octubre de 2026), sin incluir este último, leen `offsite.env` pero no cifran la copia del catálogo, así que la suben en texto plano. Ninguna versión publicada tiene este problema (0.0.0-pre.3 es anterior a ese intervalo); sí lo tienen las revisiones del superproyecto en dev desde `60f05b1` (17 de octubre) hasta `f429ef7` (24 de octubre). Si vuelves a una versión de ese intervalo y dejas `offsite.env` en su lugar, el backend sube el catálogo en texto plano:

```bash
sudo mv /var/lib/dtk/offsite.env /var/lib/dtk/offsite.env.aside
```

### 8.2 Qué pierde {#what-it-loses}

Todo lo escrito en la base de datos después de la copia: capturas (sus archivos permanecen en la tarjeta, pero ninguna fila los referencia), prefijos de nombre de archivo asignados en el paso 3, claves registradas por `adopt-map` y `adopt` en el paso 5, aumentos del contador, cargas registradas en el paso 6 y el estado de los archivos liberados.

Nunca vuelvas a una versión anterior después de liberar un volumen. Los archivos liberados ya no están en la tarjeta, la base de datos restaurada los indica como presentes y ya no contiene los registros que permitirían a un administrador recuperarlos desde el bucket.

### 8.3 Cuándo es seguro {#when-it-is-safe}

El momento más sencillo es antes del paso 3. Hasta entonces, el backend solo ha movido archivos de volúmenes que tenían prefijo de nombre de archivo antes de la actualización; en un equipo donde ningún volumen tenía prefijo, no ha movido nada.

No vuelvas a una versión anterior después del reinicio de 3.3. A partir de ese momento, los archivos de cada volumen al que asignaste un prefijo están en `<stem>/` y las filas restauradas indican sus rutas antiguas. La versión anterior no puede encontrar los archivos trasladados y ningún proceso los devuelve a su lugar. La comprobación de prefijos de nombre de archivo (8.0a) rechaza una reversión de ese tipo.

### 8.4 La próxima actualización {#the-next-update}

La reversión escribe el commit restaurado en `last-deployed-SHA` y mueve la rama local a ese commit. El `update.sh` del disco corresponde entonces a la versión restaurada, no a 0.1.0, así que la próxima actualización repite la instalación de 0.1.0:

1. 2.1: devuelve `main` a `origin/main` (`git -C /home/pi/dtk checkout -B main origin/main`), sincroniza los submódulos y comprueba el árbol de trabajo.
2. Si apartaste `offsite.env` (8.1), crea la suspensión y devuelve `offsite.env` a su lugar:

   ```bash
   sudo touch /var/lib/dtk/offsite-hold
   sudo mv /var/lib/dtk/offsite.env.aside /var/lib/dtk/offsite.env
   ```

   Deja `offsite.env` aparte solo mientras esté en ejecución el backend restaurado de una versión del intervalo que sube copias en texto plano.
3. 2.2, con `--no-pull`.
4. Repite los pasos 3 a 6: la reversión descartó todo lo escrito después de la copia (8.2).

Cuando vuelves a actualizar el equipo a 0.1.0, el backend mueve archivos al arrancar:

- Para un volumen cuyo prefijo de nombre de archivo figura en la base de datos restaurada, el backend hace que una fila cuya ruta antigua ya no existe apunte al archivo del mismo nombre en `<stem>/captures/` si el sha256 del archivo coincide con la suma de comprobación registrada durante la captura. Informa de un archivo sin esa suma de comprobación como `missing`.
- La comprobación de prefijos de nombre de archivo (8.0a) rechaza una reversión que dejaría un volumen sin acceso a sus archivos. Después de aceptar una reversión con `--accept-lost-stems`, el backend rechaza una nueva asignación de un prefijo perdido mientras `<stem>/` contenga archivos que ninguna fila del volumen referencia. Todavía no existe ningún comando para recuperar un volumen después de aceptar su pérdida; tenemos previsto `restore-stem` para después de 0.1.0.

---


## 9. Fisqua {#fisqua}

### 9.1 Cuándo está activo el enlace {#when-the-link-is-on}

El backend envía a Fisqua el manifiesto de captura de cada volumen enviado a revisión y consulta a Fisqua el estado del volumen cuando la configuración cumple las tres condiciones siguientes:

- `DTK_FISQUA_ENV` tiene el valor `production` o `staging`. Producción llama a `https://<tenant>.fisqua.org`; staging llama a `https://<tenant>.staging.fisqua.org`.
- `DTK_FISQUA_TOKEN` contiene 64 caracteres hexadecimales en minúsculas.
- `DTK_OFFSITE_TENANT` contiene un tenant válido.

De lo contrario, el backend no pone nada en cola ni envía nada, y al arrancar escribe en el registro `INFO app.core.fisqua_outbox: Fisqua is not configured; no status poll started`.

El backend solo envía manifiestos cuando `DTK_OFFSITE_REMOTE` también tiene un valor definido: el ciclo de envío forma parte de la tarea programada de carga de imágenes, que el backend solo inicia si tiene un destino remoto y un tenant válido. Con tenant pero sin destino remoto, el backend pone manifiestos en cola y nunca los envía.

El backend lee esta configuración al arrancar. Durante una actualización, define los valores antes del paso 6 y el reinicio de 6.1 los aplica; fuera de una actualización, aplica cualquier cambio con `sudo systemctl restart dtk`. Todas las llamadas usan HTTPS y el token del equipo. El backend nunca escribe el token en los registros, lo almacena ni lo devuelve; en el equipo, `offsite.env` lo contiene, y el archivo de claves también lo contiene hasta que lo elimines.

El número de versión está en el archivo `VERSION` de la raíz del repositorio (`0.1.0`). El backend lo envía en cada manifiesto como `systemVersion`: `0.1.0` cuando el repositorio tiene seleccionado el commit con la etiqueta `0.1.0`; en cualquier otro caso, `0.1.0+g<first 12 characters of the backend commit>`. El backend lee la etiqueta de los archivos de Git del superproyecto sin ejecutar git: si solo puede encontrar una etiqueta dentro de un archivo pack, o en `packed-refs` sin la línea que resuelve por completo el destino de la etiqueta, considera que no hay etiqueta y la versión incluye `+g…` incluso en el commit etiquetado (compruébalo en el equipo de pruebas cuando exista la etiqueta).

### 9.2 Preparar la configuración {#provisioning}

Añade el token al archivo de claves de 4.1 e indica el entorno en 4.2:

```text
FISQUA_TOKEN=<64 lowercase hexadecimal characters>
```

```bash
sudo DTK_OFFSITE_KEY_FILE=/root/dtk-offsite-key \
    /home/pi/dtk/scripts/provision-rclone.sh \
    --tenant <tenant> \
    --dump-recipient age172wkzadqepd565chppztfw8jefpcga8s7t6eqrfhnxnv2nlfkdrqygrl3m \
    --fisqua-env production
```

- En un equipo que ya configuraste en 4.2, el archivo de claves puede contener solo la línea `FISQUA_TOKEN`, porque allí eliminaste el original. El script conserva entonces el destino remoto registrado y su credencial, y vuelve a escribir `offsite.env` con el token y el entorno.
- El script lee el token exclusivamente del archivo de claves, rechaza cualquier token que no tenga 64 caracteres hexadecimales en minúsculas sin mostrarlo y lo rechaza cuando no indicas un tenant o un entorno y tampoco hay uno registrado.
- Escribe `DTK_FISQUA_TOKEN` y `DTK_FISQUA_ENV` en `offsite.env`. Conserva ambos valores en las ejecuciones posteriores en las que no los indiques. Si cambias cualquiera de los dos, aplica el cambio y muestra una nota.
- Con `--advisory`, como lo ejecuta `update.sh`, el script no toma el token.
- El script no hace ninguna llamada a Fisqua. El backend detecta un token incorrecto en la primera llamada: Fisqua responde `401` y el backend detiene los envíos y las consultas de estado (9.4). El backend solo hace su primera llamada a Fisqua cuando ha verificado por completo la copia remota del primer volumen enviado a revisión. Por eso un token incorrecto puede pasar inadvertido durante horas o días después de preparar la configuración.

El backend lee `offsite.env` al arrancar. Durante una actualización, ejecuta el script antes del paso 6 y el reinicio de 6.1 aplica los cambios. Fuera de una actualización, reinicia dtk. Elimina el archivo de claves después de ejecutar el script:

```bash
sudo rm /root/dtk-offsite-key
```

Fuera de una actualización, reinicia también dtk:

```bash
sudo systemctl restart dtk
```

### 9.3 Qué ocurre cuando envías un volumen a revisión {#what-a-handover-does}

Cuando una persona operadora envía un volumen a revisión, el backend pone en cola su manifiesto de captura en la misma transacción y después activa la tarea programada de carga de imágenes. Así el backend inicia una carga de inmediato, en lugar de esperar a que termine el intervalo. Después de cada ejecución de carga de imágenes, el backend ejecuta un ciclo de envío:

1. El backend mantiene en cola el manifiesto hasta completar la recepción del volumen: todos los objetos del volumen deben estar verificados en el bucket.
2. Después construye el manifiesto con un identificador fijo y lo envía en ese mismo ciclo.
3. A partir de la respuesta de Fisqua, marca el manifiesto como entregado o rechazado. Tras un fallo transitorio, el siguiente intento queda programado para después de `DTK_FISQUA_RETRY_BASE` segundos (300). La espera duplica su duración con cada fallo posterior, hasta un máximo de `DTK_FISQUA_RETRY_MAX` (6 horas), y nunca termina antes del momento que indique `Retry-After` de Fisqua. El backend envía el manifiesto en el primer ciclo de envío posterior a ese momento. Ejecuta un ciclo de envío después de cada ejecución de carga de imágenes, y ejecuta estas cargas cada `DTK_OFFSITE_BACKUP_INTERVAL` (30 minutos de forma predeterminada), o de inmediato cuando un envío a revisión activa la tarea programada. El backend sigue reintentando sin límite de intentos.

El backend rechaza de inmediato, sin enviarlo, un volumen cuyo código de referencia registrado no coincida con su prefijo de nombre de archivo, con el problema `reference_code_differs`. Si el componente que construye el manifiesto rechaza un volumen, el backend lo rechaza con los problemas que indica ese componente. Al retirar un volumen de revisión, el backend retira sus manifiestos aún no enviados y no envía nada a Fisqua. Un nuevo envío a revisión reemplaza los manifiestos del volumen que aún no ha enviado. Mientras exista la suspensión (4.0), el backend no construye ni envía ningún manifiesto.

En el equipo de pruebas, el 25 de octubre de 2026, con el volumen `cobos-bench-005` y el límite predeterminado de `750k` (4.5): el backend empezó la carga 2 segundos después del envío a revisión, verificó sus 12 objetos en 5 minutos y 43 segundos, y envió el manifiesto 0,08 segundos después de la última verificación. Después de retirar el volumen de revisión y enviarlo de nuevo, Fisqua registró el manifiesto nuevo en menos de 3 segundos.

El backend consulta por primera vez a Fisqua el estado de sus volúmenes `DTK_OFFSITE_BACKUP_DELAY` segundos (300) después del inicio y después cada diez minutos (`DTK_FISQUA_POLL_INTERVAL`, 600). Consulta un volumen mientras Fisqua no haya indicado un estado final para su manifiesto enviado más reciente y mientras Fisqua ofrezca un conjunto de decisiones del volumen que el backend aún no haya leído (9.5). Los estados finales son `published`, `refused` y `superseded`.

### 9.4 La página del volumen {#the-volume-page}

En la barra superior de la vista del volumen, debajo de la línea de copia remota, una línea muestra la entrega a Fisqua del manifiesto más reciente del volumen que no tenga un reemplazo posterior ni haya sido retirado. Cuando hay más información (una detención por configuración, un incidente, problemas, notas o envíos anteriores), puedes seleccionar la línea para abrir un panel. Los textos de la línea son los siguientes:

| Texto | Significado |
|---|---|
| `Not sent to Fisqua yet` | El backend no tiene ningún manifiesto en cola para el volumen, o todos tienen reemplazos posteriores o han sido retirados. |
| `Waiting for the complete offsite copy before sending to Fisqua` | El manifiesto está en cola; el volumen todavía no tiene recepción completa. |
| `Captua is sending the capture manifest to Fisqua` | El manifiesto está construido y espera el siguiente ciclo de envío (`ready`), o el backend lo está enviando (`sending`). Durante una detención por configuración debida a `token`, `not_found` o `redirect`, la línea conserva este texto y el panel muestra la advertencia. |
| `Captua could not send the capture manifest to Fisqua; it will try again <when>` | Ocurrió un fallo transitorio; el backend vuelve a intentar el envío. |
| `Not sent to Fisqua: Captua cannot build the capture manifest` | El equipo rechazó el manifiesto; la lista indica los problemas. |
| `Fisqua refused the capture manifest` | Fisqua rechazó el manifiesto e indicó sus problemas. |
| `Sent to Fisqua; waiting for its status` | El manifiesto está entregado; todavía no hay un estado. |

La lista `Earlier sends (<n>)` del panel muestra los otros manifiestos del volumen con los mismos textos. Dos textos solo aparecen allí: `Not sent: a later send for review replaced it` para un manifiesto con un reemplazo posterior y `Not sent: the volume was withdrawn from review` para uno retirado.

Cuando Fisqua responde, la línea muestra su estado, desde `Fisqua received the volume` hasta `Published in Fisqua`, o `Fisqua does not know this volume yet` (normalmente el manifiesto no llegó; el backend sigue consultando). El panel enumera los problemas y las notas de Fisqua, y antepone `From Fisqua: ` al texto de Fisqua. Captua redacta por su cuenta los textos de cuatro reglas: `unlisted-object` y `missing-object` (cuando Fisqua identifica el objeto), `bad-request` y `payload-too-large`. `Fisqua could not find some files in the offsite copy that Captua had already verified there. This needs investigating: ask whoever manages the scanner to check the offsite copy. The missing files are listed below.` indica un incidente: comprueba en el bucket las claves enumeradas.

**Detenciones por configuración.** El backend detiene los envíos y las consultas de estado de todo el equipo cuando Fisqua responde `401` o `403` (motivo `token`), `404` (`not_found`) o cualquier redirección (`redirect`). Un `404` con la regla `no-decisions` al leer decisiones no causa una detención (9.5). El backend también detiene estas operaciones ante un `400` cuyos problemas indiquen que Fisqua no puede leer los manifiestos que escribe este software (reglas `version`, `envelope` o `shape`, motivo `version`); el rechazo de ese manifiesto es definitivo. El registro muestra:

```text
ERROR app.core.fisqua_outbox: Fisqua answered HTTP <status> (<reason>) for this unit's configuration (fingerprint <8 hex>); sending and polling stop until DTK_FISQUA_ENV, DTK_FISQUA_BASE_URL or DTK_FISQUA_TOKEN is changed
```

Para el motivo `version`, el backend escribe en cambio esta línea; `<seconds>` es `DTK_FISQUA_RETRY_MAX` (21600 de forma predeterminada):

```text
ERROR app.core.fisqua_outbox: Fisqua answered HTTP 400 (version) for this unit's manifests (fingerprint <8 hex>); sending and polling stop until the software is updated, or until a retest every <seconds> s finds that Fisqua reads its manifests
```

La página del volumen y la página de configuración indican el motivo. Para una detención por token muestran `Fisqua does not accept the token configured on this scanner, so Captua has stopped sending volumes to Fisqua and checking their status. Ask whoever manages the scanner to correct DTK_FISQUA_TOKEN and restart Captua.` Para el motivo `version` muestran `Fisqua does not read the capture manifests this version of Captua writes, so Captua has stopped sending volumes to Fisqua and checking their status. Ask whoever manages the scanner to update Captua or Fisqua.`

El backend conserva la detención en `/var/lib/dtk/fisqua-config-error.json`, incluso después de reiniciar. La elimina cuando cambia el entorno, el tenant (a través de la URL base que construye a partir de él, salvo que `DTK_FISQUA_BASE_URL` tenga un valor definido), `DTK_FISQUA_BASE_URL`, el token o el código instalado; entonces el registro muestra `INFO app.core.fisqua_outbox: The Fisqua configuration was changed since Fisqua refused it; sending resumes`. El backend lee `offsite.env` al arrancar: durante una actualización, el reinicio de 6.1 aplica cualquier cambio de ese archivo; fuera de una actualización, aplícalo con `sudo systemctl restart dtk`. Una actualización que cambie el commit del backend o la versión publicada también elimina una detención por token; si el token sigue siendo incorrecto, la siguiente llamada del backend vuelve a detener estas operaciones en el equipo. El backend también elimina una detención por versión después de una prueba de compatibilidad cuyo manifiesto Fisqua pueda leer (más abajo).

**La detención por versión.** Mientras dure, el backend no construye ningún manifiesto salvo el que envía una prueba de compatibilidad (más abajo). El backend vuelve a poner en espera de construcción los manifiestos que ya había construido, pero no había enviado cuando llegó el rechazo, para construirlos de nuevo con identificadores nuevos. Por eso su línea muestra `Waiting for the complete offsite copy before sending to Fisqua`. Para esta detención, el código instalado consiste en el commit del backend y la versión que indica `VERSION`: una actualización que cambie cualquiera de los dos elimina la detención, y una que no cambie ninguno la conserva. Cuando el backend no puede leer su commit, elimina la detención en cada reinicio. Un cambio de entorno, tenant, URL base o token también la elimina, al igual que una prueba de compatibilidad cuyo manifiesto Fisqua pueda leer (más abajo). Cuando desaparece la detención, el backend vuelve a enviar a revisión cada volumen cuyo manifiesto más reciente tenga un rechazo por versión, con un identificador de manifiesto nuevo, siempre que ninguno de sus registros esté en estado `captured`, y escribe `INFO app.core.fisqua_outbox: Volume <id> handed to Fisqua again under a new manifest id after a version refusal`.

**La prueba de compatibilidad.** Mientras dure una detención por versión, el backend envía un manifiesto cada `DTK_FISQUA_RETRY_MAX` segundos (21600, seis horas), contados desde el momento en que registró la detención o desde la última prueba, el que sea posterior. Envía la primera prueba seis horas después de registrar la detención. Envía la prueba en el primer ciclo de envío posterior a ese momento y ejecuta un ciclo de envío después de cada ejecución de carga de imágenes (9.3). La prueba necesita un volumen enviado a revisión y con recepción completa de la copia remota: el backend toma, del más antiguo al más reciente, un manifiesto pendiente de construcción o construido pero nunca enviado, o un volumen cuyo manifiesto más reciente tenga un rechazo por versión y ninguno de cuyos registros esté en estado `captured`; en este último caso, vuelve a enviarlo a revisión con un identificador de manifiesto nuevo. Si no hay un volumen así o no quedan llamadas en el límite por minuto, el backend no envía nada y vuelve a intentarlo en el siguiente ciclo de envío. La acción posterior del backend depende de la respuesta de Fisqua:

- Fisqua acepta el manifiesto o lo rechaza por su contenido en lugar de su versión: el backend elimina la detención. En el mismo ciclo vuelve a enviar a revisión cada volumen cuyo manifiesto más reciente tenga un rechazo por versión, y después construye y envía los manifiestos pendientes, dentro del límite por ciclo.
- Fisqua vuelve a rechazarlo por versión: el backend registra de nuevo la detención con la hora de este rechazo, así que la próxima prueba corresponde a un intervalo después.
- El envío tiene un fallo transitorio: la detención continúa. El backend envía el mismo manifiesto con el mismo identificador en la siguiente prueba, nunca antes del momento que indique `Retry-After` de Fisqua.
- Fisqua responde con un error de configuración (`token`, `not_found` o `redirect`): esa detención reemplaza la detención por versión. El backend no hace pruebas para ella; la conserva hasta que cambie la configuración o el código instalado (más arriba).

Cuando Fisqua admita los manifiestos que escribe este software, el backend reanuda los envíos en un plazo de seis horas más la espera hasta el siguiente ciclo de envío, sin que tengas que intervenir en el equipo, siempre que exista algún volumen enviado a revisión y con recepción completa de la copia remota y ninguno de sus registros esté en estado `captured`. De lo contrario, conserva la detención hasta que exista un volumen así, o hasta que una actualización o un cambio de configuración la elimine. El backend no hace ninguna prueba mientras exista la suspensión de cargas remotas (4.0). No necesitas eliminar `/var/lib/dtk/fisqua-config-error.json` manualmente. Cuando una actualización o un cambio de configuración elimina la detención, el backend vuelve a construir, con el código nuevo y con identificadores de manifiesto nuevos, los manifiestos que construyeron las pruebas y que nunca llegaron a enviar, y el manifiesto de la última prueba cuando el backend perdió su respuesta o su envío falló.

La tarjeta **Offsite copy** de la página de configuración tiene una sección **Fisqua** con el entorno, el último envío y la última consulta de estado. `GET /system/catalogue-backup` devuelve lo mismo dentro de `fisqua`: `configured`, `token_invalid`, `environment`, `config_error`, `held`, `last_send` y `last_poll`.


### 9.5 Las decisiones de Fisqua {#fisquas-decisions}

Cuando Fisqua ha decidido sobre los registros de un volumen, la consulta de estado lee y aplica las decisiones, exclusivamente para el envío a revisión actual del volumen:

- Un registro aprobado pasa a `approved`; un registro rechazado pasa a `rejected`, con el motivo y la nota de Fisqua. El backend registra como revisor en ambos casos `Fisqua: <decidedBy>`, o `Fisqua` cuando Fisqua no identifica a nadie. La decisión de Fisqua reemplaza una decisión local.
- El conjunto de decisiones de Fisqua reemplaza la corrección de rotación de cada imagen actual de un registro al que aplica: si el conjunto no indica una corrección para una imagen, esa imagen pierde cualquier corrección local. El backend no modifica ningún archivo.
- El backend omite los siguientes casos e informa de ellos sin cambiar nada en ese registro: un registro que no pertenece al volumen, un registro en estado `captured` (alguien retiró el volumen de revisión o repitió la captura del registro), un registro cuyas imágenes actuales no coinciden con las que enumeraba el manifiesto objeto de la decisión (`images_changed`), una decisión que no sea de aprobación ni de rechazo, y un rechazo que la ruta local de rechazo no admitiría (`note_too_long`, un motivo que no figure en la lista, `other` sin nota).
- El backend no aplica un conjunto de decisiones de un manifiesto anterior. Deja pendiente un conjunto mientras un envío a revisión más reciente del volumen aún no haya llegado a Fisqua.
- Cuando el estado de Fisqua ofrece un conjunto de decisiones y Fisqua responde a su lectura con `404` y la regla `no-decisions`, el backend no aplica nada, escribe `INFO app.core.fisqua_outbox: Fisqua has no decisions to give for volume <id> yet; read again at the next poll` y vuelve a leer el conjunto en la siguiente consulta de estado. El enlace sigue activo. Cualquier otro `404` causa una detención por configuración (9.4).

### 9.6 Las líneas del registro {#the-journal-lines}

El backend escribe una línea por cada ejecución que haya realizado alguna acción, con el formato `<LEVEL> <logger>: <message>`:

```text
INFO app.core.image_upload: Image upload run done: uploaded=<n> already_present=<n> unverified=<n> refused=<n> conflicts=<n> skipped=<n>
INFO app.core.fisqua_outbox: Fisqua outbox pass done: promoted=<n> not_exportable=<n> delivered=<n> refused=<n> failed=<n> waiting=<n>
INFO app.core.fisqua_outbox: Fisqua accepted manifest <manifest id> of volume <id>: <state>
INFO app.core.fisqua_outbox: Fisqua status poll done: asked=<n> calls=<n> answered=<n> changed=<n> recovered=<n> decisions_fetched=<n> decisions_applied=<n> decisions_stale=<n>
INFO app.core.fisqua_decisions: Fisqua decisions <id> applied to volume <id>: approved=<n> rejected=<n> unchanged=<n> skipped=<n> rotations=<n> rotations_skipped=<n>
INFO app.core.fisqua_outbox: Fisqua has no decisions to give for volume <id> yet; read again at the next poll
```

Durante una detención por versión (9.4), el backend escribe una línea cuando envía cada prueba de compatibilidad y otra para su resultado; `<seconds>` es `DTK_FISQUA_RETRY_MAX`:

```text
INFO app.core.fisqua_outbox: Fisqua version stop retest: sending manifest <manifest id> of volume <id>
INFO app.core.fisqua_outbox: Fisqua version stop retest: manifest <manifest id> accepted; the stop is cleared and sending resumes
INFO app.core.fisqua_outbox: Fisqua version stop retest: manifest <manifest id> refused for its content, not its version; the stop is cleared and sending resumes
INFO app.core.fisqua_outbox: Fisqua version stop retest: manifest <manifest id> refused again for version; the stop holds and the next retest is in <seconds> s
INFO app.core.fisqua_outbox: Fisqua version stop retest: sending manifest <manifest id> failed; the stop holds and the next retest is in <seconds> s
INFO app.core.fisqua_outbox: Fisqua version stop retest: manifest <manifest id> was answered with a configuration error (<reason>); that stop replaces the version stop
INFO app.core.fisqua_outbox: Fisqua retest manifest of outbox row <row id> is built again under the updated software
```

Antes de la línea de una prueba que Fisqua vuelve a rechazar por versión, el backend también escribe `Fisqua refused manifest <id> of volume <id>` y la línea `ERROR` de la detención por versión (9.4); antes de la línea de una prueba fallida, escribe `Sending manifest <id> of volume <id> to Fisqua failed (attempt <n>): <error>`. Después de un envío fallido, la siguiente prueba espera hasta el momento que indique `Retry-After` de Fisqua si es posterior a `<seconds>`. El backend escribe la última línea en el primer ciclo de envío posterior a que una actualización o un cambio de configuración haya eliminado la detención, para el manifiesto de la última prueba cuando el backend perdió su respuesta o su envío falló.

La línea de aceptación termina con `no state given` cuando la respuesta de Fisqua no indica ningún estado.

La palabra que sigue a `run`, `pass` o `poll` indica cómo terminó la ejecución. Los niveles son los siguientes:

- El backend registra una ejecución de carga de imágenes con nivel `WARNING` cuando rechazó un objeto o terminó en `aborted` o `failed`; conserva el nivel `INFO` para `done`, `stopped` y `held`.
- Registra un ciclo de envío con nivel `WARNING` cuando rechazó un manifiesto o falló su envío, o cuando terminó en `error` o `config_error`; conserva el nivel `INFO` para `done`, `stopped` y `rate_limited`. Un ciclo que encuentra una detención ya registrada no escribe una línea de resumen, salvo que una prueba lleve al backend a eliminar una detención por versión durante ese ciclo; el backend escribe las líneas propias de la prueba.
- Registra una consulta de estado con nivel `WARNING` cuando terminó en `error`, o en `cooling_down` después de un `Retry-After` al leer decisiones; conserva el nivel `INFO` para `done` y `rate_limited`. Una consulta que encuentra un error de configuración, o un `Retry-After` al leer el estado, no escribe una línea de resumen.

Los fallos tienen sus propias líneas: `Sending manifest <id> of volume <id> to Fisqua failed (attempt <n>): <error>`, `Fisqua refused manifest <id> of volume <id>`, `Fisqua manifest <id> for volume <id> is not exportable: <rules>`, `Asking Fisqua for the status of <n> volume(s) failed: <error>`, `Reading Fisqua's decisions for volume <id> failed: <error>`.

### 9.7 Cuando no llega nada a Fisqua {#when-nothing-arrives-in-fisqua}

1. `GET /system/catalogue-backup` (6.3): `fisqua.configured` debe tener el valor `true`. Si `token_invalid` tiene el valor `true`, el token no contiene 64 caracteres hexadecimales en minúsculas. Si `configured` tiene el valor `false` y `token_invalid` tiene el valor `false`, comprueba que `DTK_FISQUA_TOKEN` tenga un valor (el comando de 4.3 lo muestra como `(not shown)`), y comprueba `DTK_FISQUA_ENV` y `DTK_OFFSITE_TENANT`. Durante una actualización, introduce cualquier cambio antes del paso 6 y el reinicio de 6.1 lo aplica; fuera de una actualización, reinicia dtk con `sudo systemctl restart dtk`. Si `config_error` tiene un valor, consulta las detenciones por configuración de 9.4. Para el motivo `version`, el backend hace una prueba de compatibilidad cada seis horas sin que tengas que intervenir en el equipo, siempre que exista algún volumen enviado a revisión y con recepción completa de la copia remota y ninguno de sus registros esté en estado `captured`; de lo contrario, conserva la detención hasta que exista un volumen así, o hasta que una actualización o un cambio de configuración la elimine. El backend no hace ninguna prueba mientras exista la suspensión. `config_error.at` es la hora en que el backend registró la detención por última vez; una prueba que Fisqua rechaza por versión renueva esa hora. `config_error.retest_at` es la hora de la última prueba cuyo envío falló (`null` en cualquier otro caso). Ambas horas corresponden a UTC y aparecen sin desplazamiento horario. La siguiente prueba corresponde a seis horas después de la más reciente de las dos. Si `held` tiene el valor `true` y ya terminaste el paso 5, retira la suspensión (6.2); durante una actualización, déjala.
2. La línea del volumen en 9.4. `Waiting for the complete offsite copy…` (el inicio del texto) indica que la carga aún no ha verificado todos los objetos: lee la línea de copia remota del volumen y las líneas `Image upload run`.
3. El registro: `journalctl -u dtk --since "1 hour ago" | grep -E "Fisqua|Image upload run"`.
4. El backend vuelve a consultar cada diez minutos un volumen entregado para el que Fisqua responde `Fisqua does not know this volume yet`, y no reenvía nada por su cuenta. Para enviarlo de nuevo, retira el volumen de revisión y vuelve a enviarlo a revisión: el backend pone en cola un manifiesto nuevo con un identificador nuevo y lo envía cuando el volumen tiene recepción completa. El backend solo pone en cola un manifiesto nuevo mientras algunos registros del volumen estén en revisión; al retirar el volumen de revisión, devuelve únicamente esos registros al estado `captured`, y no pone nada en cola para un envío a revisión que no tenga ningún registro en estado `captured`.

## 10. Comprobaciones después de una actualización {#checks-after-an-update}

Ejecuta estas comprobaciones en el equipo de pruebas después de cada actualización y en un equipo en uso después de actualizarlo:

```bash
curl -s http://localhost:8000/health
sudo cat /var/lib/dtk/backups/last-deployed-SHA
git -C /home/pi/dtk rev-parse HEAD
cat /home/pi/dtk/VERSION
git -C /home/pi/dtk submodule status
sudo ls /var/lib/dtk/backups/unresolved-deployment /etc/dtk/unresolved-deployment
systemctl cat dtk | grep ConditionPathExists
sudo /home/pi/dtk/scripts/check-stack-health.sh
journalctl -u dtk --since "15 min ago" | grep -E "Volume layout:|Cannot start|Traceback|offsite uploads are on hold|Fisqua"
hostname
getent hosts captua.local digitool.local
grep -E '^(HOST_IP|CORS_ORIGINS)=' /home/pi/dtk/.env
systemctl is-enabled dtk-mdns-alias; systemctl is-active dtk-mdns-alias
sudo cat /etc/dtk/hostname-switch
```

- `/health` responde `{"status":"ok"}`.
- `VERSION` indica la versión instalada. `last-deployed-SHA` y `HEAD` indican el mismo commit, y cada línea de `submodule status` empieza con un espacio (en su revisión fijada).
- No existe ninguno de los dos archivos de actualización sin resolver (`ls` informa de que ambos están ausentes).
- La salida incluye `ConditionPathExists=!/etc/dtk/unresolved-deployment` de la configuración complementaria.
- `check-stack-health.sh` informa de que la base de datos funciona correctamente y el puerto 5432 escucha en el equipo, en cualquier dirección, y de que el frontend y nginx están en ejecución.
- El registro no contiene `Cannot start` ni `Traceback`; interpreta cualquier línea `Volume layout:` como indica 3.4. `offsite uploads are on hold` aparece en cada ejecución mientras exista la suspensión.
- `GET /system/catalogue-backup` (6.3) indica para `held` el valor esperado según el punto del procedimiento y, en un equipo con el enlace, `fisqua.configured` tiene el valor `true` y no hay `config_error`.
- En un equipo con el enlace, el registro no contiene ninguna línea `Fisqua answered HTTP` desde el reinicio. La línea `Fisqua accepted manifest` (9.6) solo aparece después de que un volumen enviado a revisión tenga recepción completa de su copia remota; una línea `Fisqua outbox pass` también puede informar de un volumen rechazado por no ser exportable. Ninguna de las dos aparece mientras exista la suspensión.
- En un volumen enviado a revisión después de la actualización, la línea de Fisqua debajo de la línea de copia remota muestra `Sent to Fisqua; waiting for its status` o un estado de Fisqua (9.4).
- En un equipo cuyo nombre cambió desde `digitool`: `hostname` imprime `captua`; `getent` imprime una dirección para ambos nombres; `HOST_IP=captua.local` y `CORS_ORIGINS` incluye `http://captua.local` y `http://digitool.local`; `dtk-mdns-alias` tiene los estados `enabled` y `active`; `/etc/dtk/hostname-switch` contiene `state=done`. Desde otra computadora de la misma red, `http://captua.local`, `http://digitool.local` y la dirección IP del equipo permiten abrir la aplicación e iniciar sesión. En un equipo que conservó su nombre, el registro de la actualización indica el motivo (2.6).

---

## Un equipo nuevo {#a-new-unit}

1. Prepara la tarjeta con `sudo ./scripts/setup.sh`, que asigna el nombre `captua` (`sudo DTK_HOSTNAME=captua-2 ./scripts/setup.sh` para un segundo equipo en un mismo lugar), y después con `sudo ./scripts/install-service.sh`, que también instala la configuración complementaria para las actualizaciones sin resolver (consulta [Preparación y distribución de tarjetas SD](/guia/instalacion/tarjetas-sd/)).
2. Escribe el archivo de claves y ejecuta `provision-rclone.sh` con `--tenant` y `--dump-recipient` como indica el paso 4. Para un equipo con el enlace a Fisqua, añade `--fisqua-env` y una línea `FISQUA_TOKEN` en el archivo de claves (9.2).
3. Inicia o reinicia `dtk` y comprueba el resultado como indica 6.3.

Debes asignar el prefijo de nombre de archivo a un volumen nuevo al crearlo, así que el paso 3 no corresponde. Como el bucket no contiene nada anterior al equipo, el paso 5 tampoco corresponde.
