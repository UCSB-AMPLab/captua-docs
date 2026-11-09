---
title: "Configuración de cámaras compatibles con gphoto2"
url: "/guia/camaras/gphoto2/"
translationKey: "docs-cameras-gphoto2"
docs_section: "cameras"
source: "docs/users/setting-up-gphoto2-cams.qmd"
---

{{< callout type="note" title="Lista de cámaras compatibles con gphoto2" appearance="simple" collapse="true" >}}
Consulta la lista completa de cámaras compatibles con gphoto2 en la [página oficial de compatibilidad](http://gphoto.org/proj/libgphoto2/support.php).

Para funcionar plenamente con Digitization Toolkit, las cámaras deben ofrecer todas estas funciones: captura de imágenes (Image Capture), disparo remoto (Trigger Capture), vista en vivo (Live View) y configuración (Configuration).
{{< /callout >}}

## Conectar las cámaras a la Raspberry Pi {#connect-the-cameras-to-the-raspberry-pi}

Requisitos: dos cables USB 2.0 tipo A a mini-B de cinco pines, con transmisión de **datos**.

{{< callout type="warning" appearance="simple" >}}
Muchos cables mini-B actuales solo sirven para cargar y no tienen líneas de datos. Un cable de estos no provoca ninguna reacción visible en la cámara ni genera mensajes en la Pi: la cámara nunca aparece. Dos cables nuevos fallaron así durante las pruebas de hardware (uno produjo un `error -71` intermitente en `dmesg` y luego dejó de emitir señales). Usa cables que hayas comprobado que transmiten datos, conecta bien ambos extremos y verifica la conexión con `lsusb` (más abajo) antes de buscar otra causa.
{{< /callout >}}

Conexiones:

- En la cámara, conecta el cable al puerto central, marcado con el símbolo USB.
- En la Raspberry Pi, conéctalo a cualquier puerto USB-A, preferiblemente uno azul USB 3.0.

{{< media id="cannon-eos-rebelt7-usb4cam" >}}

{{< media id="cannon-eos-rebelt7-usb2rpi" >}}

## Verificar la conexión {#verify-the-connection}

Con ambas cámaras conectadas y **encendidas**, ejecuta en la Pi:

```bash
lsusb                 # Debe aparecer una línea "Canon, Inc." por cámara
gphoto2 --auto-detect  # Deben aparecer ambas cámaras
```

Si falta una cámara, vuelve a conectar ambos extremos del cable, apaga la cámara y vuelve a encenderla. Revisa `dmesg | tail`: un `error -71` repetido indica un cable defectuoso o un conector mal ajustado; si una cámara encendida no produce ninguna señal, el cable podría servir solo para cargar.

## Canon EOS Rebel T7 {#canon-eos-rebel-t7}

- Selecciona el enfoque manual: pon el interruptor del lente en **MF** (Manual Focus).

{{< media id="cannon-eos-rebelt7-lensmf" >}}

- Selecciona el modo manual: gira el dial de modos a **M** (Manual).

{{< media id="cannon-eos-rebelt7-mode" >}}

- Cierra el flash integrado: si la cámara levanta el flash al encenderla, bájalo hasta cerrarlo.

{{< media id="cannon-eos-rebelt7-flash" >}}

- Configura el apagado automático: en el menú de la cámara, busca **Auto power off** y selecciona **15 minutos**.

{{< media id="cannon-eos-rebelt7-config-menu" >}}

{{< callout type="caution" appearance="simple" >}}
El software abre una sesión con la cámara al solicitar la primera vista previa, captura o lectura de configuración después de encenderla. En ese momento intenta desactivar **Auto power off** para impedir que la cámara entre en reposo durante la sesión; el software nunca apaga la cámara. Antes de abrir esa sesión, la cámara aplica su propia configuración: si estuvo inactiva antes de la primera vista previa del día, podría haber abandonado ya el bus USB. Si la Raspberry Pi falla o la apagas durante una sesión, la cámara puede seguir encendida hasta que la apagues manualmente.
{{< /callout >}}

{{< callout type="important" appearance="simple" >}}
Cuando la cámara ejecuta el apagado automático, **abandona por completo el bus USB**: `lsusb` deja de mostrarla y el software no puede reactivarla. La interfaz muestra una cámara en ese estado como desconectada. Para recuperarla, **presiona el disparador hasta la mitad**, espera unos segundos a que vuelva a aparecer en el bus USB y presiona **Reconectar cámaras** en la interfaz, en el panel de cámaras de **Resumen** o en los controles de vista previa. El mismo procedimiento permite recuperar una cámara cuyo cable USB acabas de reconectar. Tenlo en cuenta antes de desconectar componentes o reiniciar servicios.
{{< /callout >}}
