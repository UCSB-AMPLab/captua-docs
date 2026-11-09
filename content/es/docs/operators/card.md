---
title: "Captua — Guía rápida de uso"
url: "/guia/operacion/tarjeta/"
translationKey: "docs-operators-card"
linkTitle: "Guía rápida de uso"
docs_section: "operators"
toc: false
---

Guía de una página para quienes operan el equipo de digitalización. Imprímela y déjala junto al equipo.

## Apagar y reiniciar el equipo {#shutting-down-and-restarting-the-scanner}

1. Si hay una captura en curso, espera a que termine.
2. Abre el menú de usuario. En cualquier pantalla con barra lateral, como **Resumen** o **Proyectos**, presiona tu nombre de usuario, abajo en la barra lateral; si la barra está contraída, presiona el cuadro con las dos primeras letras de tu nombre. En la pantalla de captura y en la del volumen, presiona el círculo con esas letras, arriba a la derecha.
3. Presiona "Apagar el equipo" y, en la confirmación, "Sí, apagar".
4. Aparece "Apagando el equipo…". Desconecta la corriente solo cuando la pantalla quede negra.

Para reiniciar, presiona "Reiniciar el equipo" en el mismo menú y luego "Sí, reiniciar". La pantalla queda negra un momento. No desconectes la corriente hasta que vuelva a aparecer la aplicación.

Si eres administrador, también tienes los botones "Apagar" y "Reiniciar" en **Configuración → Energía**.

**Si la pantalla no responde:** presiona una vez el botón de encendido del equipo. Así apagas el equipo de forma segura. Espera a que la pantalla quede negra antes de desconectar la corriente.

**Si el equipo sigue encendido:** presiona **Ctrl+Alt+F2**, escribe `sudo poweroff` y presiona Enter. Espera a que la pantalla quede negra.

{{< callout type="warning" appearance="simple" >}}
**Nunca desconectes la corriente con el equipo encendido:** puedes dañar la tarjeta de memoria y perder información.
{{< /callout >}}

## Cambiar de pantalla {#switching-screens}

- **Ctrl+Alt+F2** → pantalla de texto (recuperación)
- **Ctrl+Alt+F1** → la aplicación

Usa las teclas Ctrl y Alt de la izquierda; las de la derecha no funcionan para estos atajos.

## Cámaras réflex Canon: enfoque al iniciar la jornada {#canon-dslr-cameras-focusing-at-the-start-of-the-day}

1. Pon el interruptor del lente en **AF** en las dos cámaras y toma la primera captura. Las dos cámaras enfocan automáticamente.
2. Pasa el interruptor a **MF**, también **en las dos cámaras**. Así el enfoque queda fijo el resto de la jornada, porque la distancia entre la cámara y el documento no cambia.

Si dejas el interruptor en AF, cada captura tarda unos 12 segundos más y puede quedar bloqueada. En ese caso, la pantalla de captura puede mostrar una advertencia en el panel "Controles de cámara". Antes de empezar a digitalizar, mira el lente de cada cámara y comprueba que el interruptor está en **MF**. Captua intenta desactivar el flash. Comprueba que el flash esté cerrado antes de empezar.

## Enviar un volumen terminado a revisión {#sending-a-finished-volume-for-review}

1. Abre el volumen: **Proyectos →** tu proyecto **→** el volumen. Si el equipo no usa proyectos, abre **Volúmenes →** el volumen.
2. Presiona "Enviar a revisión", en la barra superior. Si ya habías enviado parte del volumen, el botón indica cuántos registros nuevos vas a enviar (por ejemplo, "Enviar 3 registros nuevos"). Si el botón indica cuántas recapturas faltan (por ejemplo, "Faltan 2 recapturas"), todavía no puedes enviar el volumen: termina primero las recapturas.
3. En la confirmación, presiona "Enviar".

Desde ese momento los registros quedan en revisión y no puedes moverlos a otro volumen. Si te equivocaste, presiona "Retirar de revisión" y, en la confirmación, "Retirar". Así retiras solo los registros que todavía están pendientes de revisión: los aprobados y los rechazados quedan como están.

## Si las cámaras no aparecen {#if-the-cameras-dont-appear}

1. Si una cámara se apagó sola, presiona el disparador hasta la mitad para activarla, o vuelve a conectar el cable USB.
2. Presiona "Reconectar cámaras". Está en **Resumen**, en la sección "Probar cámaras", y en la pantalla de captura, en el panel "Controles de cámara" (ábrelo con el ícono del engranaje).
3. Si siguen sin aparecer, presiona "Salir" en el menú de usuario (ver arriba) y vuelve a iniciar sesión.

## Si una cámara deja de responder {#if-a-camera-stops-responding}

1. En las cámaras réflex Canon, revisa que el interruptor del lente esté en **MF** (ver arriba).
2. Apaga esa cámara, vuelve a encenderla y presiona "Reconectar cámaras".
3. Si sigue igual, reinicia el equipo desde el menú de usuario (ver arriba).

## Si la aplicación deja de responder {#if-the-application-freezes}

Presiona **Ctrl+Alt+F2**, escribe `sudo systemctl restart dtk` y presiona Enter. **Durante el reinicio no aparece ningún mensaje: es normal.** Espera hasta que puedas volver a escribir en la terminal (puede tardar un minuto o más) y vuelve a la aplicación con **Ctrl+Alt+F1**.

Si aparece un mensaje que dice que `dtk.service` falló, o si la aplicación sigue sin responder, apaga el equipo con el botón de encendido (ver arriba) y vuelve a encenderlo.
