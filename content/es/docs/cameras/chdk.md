---
title: "Configuración de cámaras CHDK"
url: /guia/camaras/chdk/
translationKey: docs-cameras-chdk
docs_section: cameras
source: docs/users/setting-up-chdk-cams.qmd
---

## Qué es CHDK {#what-chdk-is}

[CHDK](https://chdk.fandom.com/wiki/CHDK) es un firmware que permite controlar una cámara compacta Canon por USB. En este equipo, el backend CHDK del equipo controla dos cámaras Canon A2500 mediante PTP/USB y la biblioteca `pychdk`.

CHDK no sustituye el firmware de la cámara. La cámara lo carga desde una tarjeta SD preparada para ello: la tarjeta contiene los archivos de arranque de CHDK, y la herramienta modifica su sector de arranque para que la cámara la reconozca como arrancable. Si insertas una tarjeta corriente, sin preparar, la cámara inicia su firmware habitual y no carga CHDK.

## Qué necesitas {#what-you-need}

- **Dos cámaras Canon A2500.** La herramienta de preparación de tarjetas (`tools/flash_chdk.py`) descarga e instala CHDK 1.6.1-6315 específicamente para la A2500 con firmware 1.00A. No es un instalador general de CHDK para otros modelos Canon.
- **Dos tarjetas SD**, una por cámara, preparadas según las instrucciones de esta guía.
- **Un Mac** con una copia del repositorio [`pychdk`](https://github.com/UCSB-AMPLab/pychdk) en la etiqueta `v0.1.2`, para preparar las tarjetas. Esa es la versión que usa el backend, fijada en `backend/requirements.txt` y `backend/pixi.toml`. El repositorio de Digitization Toolkit no incluye `pychdk`. Instalarlo como paquete de Python, como hace el backend, tampoco incluye la herramienta de preparación: esta solo está en `tools/` dentro del repositorio y no forma parte del paquete. `tools/flash_chdk.py` solo funciona en macOS; usa `diskutil` del Mac para formatear y escribir la tarjeta.
- **Un cable USB** por cámara para conectarla al equipo.

{{< callout type="important" title="Todavía no hemos comprobado la captura por USB en estas cámaras" >}}
El equipo captura la fotografía por el cable USB: la cámara envía la imagen directamente por el cable y nunca la escribe en su propia tarjeta SD. La adaptación de CHDK para la A2500 está en fase alfa, y la documentación de `pychdk` señala que esta transmisión puede fallar en la A2500 con el error PTP `0x2002`. Ni `pychdk` v0.1.2 ni este backend intentan guardar la imagen en la tarjeta como alternativa. Si aparece ese error, la captura falla por completo, sin crear un archivo en otro lugar. El backend también cierra la sesión de esa cámara y la retira de la lista de dispositivos; en la siguiente búsqueda tiene que abrirla de nuevo. Tampoco hemos comprobado si esa reconexión funciona sin problemas ni si la vista previa sigue funcionando después. Una misma prueba permitiría resolver esas dudas. El registro del backend indica el error.

No sabemos todavía si estas cámaras concretas presentan ese problema: aún no hemos ejecutado la prueba con ellas. Todavía tenemos pendiente esa prueba con las cámaras. Hasta completarla, considera que la captura en la A2500 está sin comprobar y no organices una jornada de digitalización que dependa de ella.
{{< /callout >}}

## Seleccionar el backend CHDK {#selecting-the-chdk-backend}

Esta página corresponde a la versión que actualiza la referencia del backend en el superproyecto a una revisión posterior a NEH-231, y a las versiones siguientes. Un equipo con un backend anterior no tiene ni el código del backend CHDK ni la dependencia `pychdk`, por lo que `CAMERA_BACKEND=chdk` todavía no puede funcionar allí.

{{< callout type="warning" appearance="simple" >}}
Debes indicar al equipo que use el backend CHDK para estas cámaras. La configuración predeterminada del backend usa otro sistema de cámaras, y la instalación del equipo no cambia esa elección automáticamente. Aunque prepares bien las dos tarjetas y conectes dos cámaras que funcionen, el equipo puede no mostrar nada porque está buscando otro tipo de cámara.
{{< /callout >}}

Antes de conectar una cámara CHDK, comprueba que el archivo `.env` del equipo, en la raíz del proyecto, incluya:

```
CAMERA_BACKEND=chdk
```

Luego reinicia el servicio del backend para aplicar el cambio:

```bash
sudo systemctl restart dtk
```

Si no preparaste tú el equipo, consulta con quien lo hizo: quizá ya tenga esta configuración, o quizá use otro backend para otro par de cámaras.

## Preparar una tarjeta SD {#preparing-an-sd-card}

Prepara las tarjetas en un Mac con `tools/flash_chdk.py`, desde una copia del propio repositorio `pychdk`. La herramienta no está en el repositorio de Digitization Toolkit ni en la instalación de la dependencia de Python que usa el backend:

```bash
git clone https://github.com/UCSB-AMPLab/pychdk.git
cd pychdk
git checkout v0.1.2
python3 tools/flash_chdk.py
```

{{< callout type="warning" appearance="simple" >}}
Preparar una tarjeta **borra su contenido**. La herramienta solo muestra la confirmación "This will ERASE the disk. Continue?" cuando el Mac detecta **exactamente un disco extraíble en total**, no una sola tarjeta SD. Si hay otro almacenamiento extraíble conectado, como una unidad USB u otro lector de tarjetas, la herramienta omite la confirmación y borra el disco que elijas por número. Desconecta primero todos los demás dispositivos de almacenamiento extraíble y deja conectada únicamente la tarjeta que quieras preparar.
{{< /callout >}}

La herramienta descarga la versión de CHDK y conserva una copia en caché, formatea la tarjeta, extrae en ella los archivos de arranque de CHDK y modifica el sector de arranque para que la cámara pueda arrancar desde la tarjeta. Después pregunta qué páginas fotografiará esa cámara: impares, pares, o si prefieres omitir la elección. Guarda la respuesta en la tarjeta. Al terminar, **bloquea la tarjeta** con el interruptor de protección contra escritura del borde antes de insertarla en la cámara.

Si vuelves a preparar una tarjeta que ya tenía una cámara asignada, la herramienta conserva la paridad y el identificador que tenía, aunque omitas la pregunta. Más abajo explicamos por qué importa.

## Paridad de las páginas, no posición en la mesa {#page-parity-not-a-side-of-the-table}

{{< callout type="important" appearance="simple" >}}
La tarjeta indica qué **páginas** fotografía la cámara, ODD (impares) o EVEN (pares), y no a qué lado de la mesa está la cámara. Son dos cosas distintas: normalmente EVEN corresponde al índice de cámara 0 y ODD al índice 1. El control para intercambiar las cámaras en la interfaz determina cuál ve la persona operadora a su izquierda; la tarjeta no decide eso. Un libro que lees de derecha a izquierda usa las mismas dos tarjetas: solo cambia la opción de intercambio de la interfaz.
{{< /callout >}}

Por tanto, una tarjeta corresponde a "la cámara que fotografía páginas pares" o a "la cámara que fotografía páginas impares", y no a "la cámara izquierda" o "la cámara derecha".

Una cámara con paridad en su tarjeta conserva el índice de esa paridad mientras ninguna otra cámara conectada declare la misma. Si dos cámaras comparten paridad, no puedes dar por hecho que sus índices sean los esperados y el backend bloquea la captura de ambas hasta que resuelvas el conflicto.

Una cámara sin paridad no tiene un índice propio: recibe el menor índice que ninguna paridad haya reservado. Cuando conectas otra cámara, el backend puede asignarle un índice distinto a la primera aunque funcione bien. Por eso conviene asignar las dos paridades antes de empezar.

Cuando dos cámaras comparten paridad, el backend bloquea ambas para captura. La primera que encuentra en el bus conserva el índice de esa paridad; la otra recibe el menor índice que ninguna paridad esté usando, aunque no corresponda a su tarjeta. No puede capturar desde allí y el backend no archiva imágenes bajo ese índice. El backend solo le asigna esa posición para que puedas dirigirle la reparación que explicamos más abajo. Un conflicto de identificadores sin conflicto de paridad no cambia ningún índice: solo bloquea la captura. Lee la paridad y el identificador reales de cada cámara en la lista de dispositivos, en lugar de deducirlos del índice.

## El identificador de la cámara {#the-cameras-identity}

Algunas de estas cámaras no proporcionan un número de serie USB, así que el equipo no siempre puede distinguir dos cámaras conectadas solo por la conexión USB. Para resolverlo, el archivo de la tarjeta que guarda la paridad también puede guardar un identificador corto: una cadena hexadecimal de 12 caracteres. La herramienta crea ese identificador la primera vez que asignas una paridad, ya sea en el banco de trabajo con `tools/flash_chdk.py` o desde el equipo, como explicamos más abajo. El equipo usa este identificador para reconocer cada cámara después de desconectarla y volver a conectarla, y para recordar su configuración.

Cuando vuelves a preparar una tarjeta, la herramienta conserva el identificador en lugar de reemplazarlo. Por eso el equipo conserva la configuración registrada de la cámara después de volver a grabar la tarjeta.

## Conectar las cámaras {#connecting-the-cameras}

Conecta las dos cámaras al equipo por USB y enciéndelas.

{{< callout type="warning" appearance="simple" >}}
La interfaz web habitual solo muestra el modelo y el índice de cada cámara, y presenta como utilizable cualquier índice de la lista. No muestra la paridad ni los errores que indican que una cámara aún no está lista. No uses esa interfaz para confirmar que las cámaras estén preparadas.
{{< /callout >}}

Consulta la lista de dispositivos con autenticación: `GET /cameras/devices`, la misma llamada que explicamos en "Asignar la paridad de una cámara". Cada cámara conectada debe aparecer con su modelo, su paridad (`odd` o `even`) y sin errores. Una cámara sin número de serie USB ni identificador propio muestra un error que indica que debes asignarle una paridad antes de capturar. Esto ocurre con estas cámaras compactas antes de la primera asignación. Asignar la paridad también crea su identificador.

Si acabas de volver a grabar una tarjeta o de cambiar una paridad manualmente, solicita otra búsqueda con `POST /cameras/rescan`, en lugar de usar el resultado de una consulta anterior. Esa búsqueda vuelve a leer la tarjeta de cada cámara conectada.

## Asignar la paridad de una cámara {#assigning-a-cameras-parity}

La interfaz todavía no tiene un control para esta tarea; esperamos incorporarlo en una versión futura. Por ahora, un administrador debe asignar la paridad directamente mediante la API del equipo.

{{< callout type="warning" appearance="simple" >}}
Iniciar sesión en la interfaz web habitual no autoriza esta operación. Si el navegador ya tiene una sesión en la interfaz web con la misma dirección, por ejemplo el navegador del equipo en `http://localhost`, el explorador interactivo de la API admite consultas de lectura con esa sesión, pero rechaza todos los cambios, incluida la asignación de paridad, con un error 403 y `"Missing X-Requested-With header"`, hasta que inicies sesión dentro del explorador como explicamos a continuación. Tampoco puedes acceder al explorador desde un portátil conectado únicamente a la red local del lugar: el puerto 8000 solo admite conexiones desde el propio equipo o mediante Tailscale.
{{< /callout >}}

1. **Abre el explorador de la API**, en una dirección distinta de la interfaz habitual:
   - En el propio equipo: `http://localhost:8000/docs`.
   - Desde otro equipo mediante Tailscale: usa el nombre o la IP de Tailscale del equipo Captua, el puerto 8000 y la ruta `/docs`. No uses `localhost`: en una computadora remota, ese nombre apunta a esa computadora, no al equipo Captua. Ejemplo: `http://<nombre-o-IP-de-Tailscale-del-equipo>:8000/docs`.
2. **Inicia sesión como administrador dentro del explorador.** Completa todos los pasos. Si omites alguno, el equipo rechaza la asignación del paso 4 con 401 y `"Not authenticated"` si el navegador no tiene sesión, o con 403 y `"Missing X-Requested-With header"` si ya tiene una sesión, ya sea de la interfaz web o del inicio de sesión de este paso. Iniciar sesión aquí también reemplaza la sesión de la interfaz web en ese navegador, que queda abierta como administrador. Al terminar, presiona **Salir**.
   - Despliega `POST /auth/login`, presiona **Try it out**, introduce las credenciales del administrador y presiona **Execute**.
   - Copia el valor `access_token` del cuerpo de la respuesta.
   - Presiona el botón verde **Authorize**, cerca de la parte superior de la página, para abrir el cuadro de diálogo.
   - Pega el token en el campo y presiona **Authorize dentro del cuadro de diálogo** para enviarlo. Pegar el token no basta: debes presionar ese segundo botón para aplicarlo. Cierra el cuadro cuando confirme la autorización.
3. **Consulta la lista actual de dispositivos** con `GET /cameras/devices` e identifica la cámara que quieres cambiar mediante `index`, `hardware_id` y `location`/puerto.
4. **Envía la asignación** a `POST /cameras/side/<camera index>`, con un cuerpo JSON de `{"side": "odd"}` o `{"side": "even"}`. Reemplaza `<camera index>` por el índice actual de la cámara.
5. **Vuelve a leer la respuesta:** contiene una lista completa de dispositivos tras una nueva búsqueda, no una sola fila actualizada. La cámara que acabas de cambiar suele pasar al otro índice. Identifica de nuevo todas las cámaras en esa lista antes de enviar otra asignación. No supongas que una cámara conserva el índice de hace un momento.

Esta operación vuelve a escribir la paridad y el identificador en la tarjeta de la cámara. Conserva el identificador existente, o crea uno si la cámara no tenía ninguno.

El equipo no asigna a una cámara una paridad que otra cámara **conectada en ese momento** ya tenga. Por eso dos cámaras conectadas no pueden intercambiar paridades directamente: cualquier paridad que intentes asignar a una ya pertenece a la otra, y el equipo rechaza la solicitud. Ningún orden de esas solicitudes resuelve el problema. Para intercambiar las paridades:

1. Desconecta una de las dos cámaras.
2. Solicita otra búsqueda para que el equipo deje de contar la cámara desconectada.
3. Asigna la nueva paridad a la cámara que sigue conectada.
4. Vuelve a conectar la otra cámara, solicita otra búsqueda y asígnale la paridad que debe tener.

El equipo actualiza las dos tarjetas y deja una cámara para páginas impares y la otra para páginas pares.

## Solución de problemas {#troubleshooting}

{{< callout type="note" appearance="simple" >}}
Sigue este orden. La lista de cámaras puede mostrar los mismos síntomas para causas distintas, y empezar por la causa equivocada te hará perder tiempo.
{{< /callout >}}

**No aparece ninguna de las dos cámaras**

Confirma que configuraste el backend CHDK y que reiniciaste el servicio después del cambio. Un equipo configurado con `picamera2` no puede detectar estas cámaras USB: solo busca el sensor conectado a la Pi por cable plano. Con gPhoto2 no puedes sacar la misma conclusión, porque usa un protocolo general de fotografía por USB. Que aparezcan cámaras, o que no aparezca ninguna, no basta para identificar el backend. Comprueba el archivo `.env`.

**No aparece una cámara concreta y estás seguro de que preparaste bien su tarjeta**

Confirma que la cámara haya cargado CHDK. Una tarjeta sin preparar o mal preparada no impide que la cámara aparezca por USB; la cámara responde como una compacta Canon corriente, no como una cámara CHDK. El equipo no la reconocerá como CHDK en ninguno de esos casos. Revisa la tarjeta.

**Sigue sin aparecer y no encuentras la causa**

Consulta el registro del backend en `/var/log/dtk/capture_service.log`. El backend omite de la lista las cámaras que no puede usar, sin mostrar allí la causa; el registro es el único lugar que la indica. El backend usa un mismo mensaje para todos los fallos al abrir una cámara. Lee el texto exacto:

- **No pudo abrirla y el mensaje indica un problema de permisos** (`access denied` o similar): revisa la regla udev, como explicamos más abajo.
- **No pudo abrirla y el mensaje indica que el dispositivo está ocupado o que otro proceso ya lo ha reservado:** revisa el proceso que tiene abierta la cámara, como explicamos más abajo.
- **No pudo abrirla y el mensaje indica otra cosa:** suele tratarse de un tiempo de espera agotado. El registro solo confirma el fallo al abrirla, no su causa. Que la cámara aún esté terminando de arrancar es una hipótesis, no un diagnóstico. Espera un momento y solicita otra búsqueda; un segundo intento puede funcionar. No interpretes el mensaje como un problema de permisos o de dispositivo ocupado si no dice eso. Si vuelve a fallar, anota el mensaje exacto y considera la causa pendiente de diagnóstico, en lugar de seguir suponiendo que basta con esperar.
- **Abrió la cámara, pero falló un paso posterior, normalmente la lectura de la tarjeta:** revisa la tarjeta o la conexión, no los permisos. Vuelve a insertar la tarjeta, comprueba que esté bloqueada y que no tenga daños, o prueba otra tarjeta o cable.

**El registro indica un problema de permisos al abrir la cámara y ya comprobaste la tarjeta y el backend**

Revisa la regla udev. Ejecuta `lsusb`: debe mostrar una línea `"Canon, Inc."` por cámara, igual que con gPhoto2. Si `lsusb` la detecta, la conexión física funciona y el problema es de permisos. No vuelvas a ejecutar todo el script de instalación: en un equipo sin conexión útil a la red, ese script detiene los servicios y luego intenta descargar y compilar componentes que necesitan red, aunque el problema solo afecte a las cámaras. Ejecuta `sudo ./scripts/provision-chdk-usb.sh` para instalar únicamente la regla y la pertenencia al grupo. Puedes repetirlo sin alterar otros componentes. Luego reinicia el backend con `sudo systemctl restart dtk`. Al reiniciar el servicio, el backend usa la pertenencia actualizada del usuario del equipo a los grupos; no necesitas reiniciar todo el equipo.

**El registro indica que la cámara está ocupada o reservada**

Reiniciar el backend solo ayuda si el propio backend conserva una reserva de una ejecución anterior que no liberó la cámara correctamente. En ese caso, reiniciar `dtk` la libera. Si otro proceso tiene la cámara, reiniciar `dtk` no lo soluciona: ese proceso conserva la reserva y puede volver a tomar la cámara cuando la reconectes. Busca el proceso que la tiene abierta, por ejemplo comprobando los procesos activos o cuál tiene abierto el nodo del dispositivo, y detén ese proceso concreto.

**La cámara no aparece y `lsusb` tampoco la detecta**

Revisa el cable USB, la conexión y la alimentación de la cámara. El problema no es del software.

**Las dos cámaras rechazan la captura y una o ambas indican un conflicto**

Consulta tanto la paridad como el identificador de cada cámara en la lista de dispositivos. No supongas que el mensaje de error describe el único problema. La lista informa primero del conflicto de identificadores, incluso si la cámara también comparte paridad. Sin embargo, una solicitud de asignación comprueba primero la paridad y rechaza una paridad compartida antes de examinar el identificador. Resuelve primero el conflicto de paridad, aunque el mensaje no lo mencione.

**Paridad compartida, sin identificador compartido**

Asigna a una cámara la paridad que la otra no tiene.

**Paridad e identificador compartidos**

Es habitual tras clonar una tarjeta completa, porque la copia lleva la misma paridad y el mismo identificador. Si intentas asignar a una cámara la paridad que ya tiene, el equipo rechaza la solicitud por el conflicto de paridad antes de comprobar el identificador. Asigna a cualquiera de las dos la paridad contraria, que está libre. Así resuelves el conflicto de paridad y, si ninguna cámara proporciona un número de serie USB, el equipo crea también un identificador nuevo para esa cámara en la misma llamada. Esto resuelve ambos conflictos a la vez.

**Identificador compartido, sin paridad compartida**

Las cámaras tienen paridades distintas o ninguna tiene paridad. La solución depende del origen del identificador:

- **Ninguna cámara tiene número de serie USB:** basta con volver a asignar una paridad a una de ellas para que el equipo cree un identificador nuevo. Si ya tiene paridad, vuelve a asignarle la misma; no necesitas cambiar qué páginas fotografía. Si ninguna tiene paridad, como ocurre al clonar una tarjeta antes de asignarla por primera vez, elige la paridad que quieras para esa cámara. Cualquiera de las dos solicitudes funcionará porque ninguna cámara tiene todavía una paridad reservada.
- **Una cámara tiene número de serie USB y la tarjeta de la otra contiene ese mismo valor:** solo puedes reparar así la cámara cuyo identificador procede de la tarjeta. Al asignarle una paridad, la misma que tenía o una libre si no tenía ninguna, el equipo crea un identificador nuevo. La reasignación no puede reparar la cámara identificada por su número de serie USB: escribir en la tarjeta no cambia el número que proporciona la cámara.
- **Ambas cámaras proporcionan el mismo número de serie USB:** reasignar la paridad no resuelve el problema, porque escribir en una tarjeta no cambia un número de serie USB. Debes retirar una de las dos cámaras del equipo.

El mensaje de error de cada cámara indica a cuáles corresponden estas reparaciones. Sigue esa indicación y comprueba también el otro campo: el error visible puede no describir todos los problemas.
