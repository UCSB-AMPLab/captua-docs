---
title: "Almacenamiento externo"
url: "/guia/operacion/almacenamiento-externo/"
translationKey: "docs-operators-external-storage"
docs_section: "operators"
source: "docs/users/external-storage.qmd"
---

Digitization Toolkit puede guardar las imágenes capturadas en una unidad USB externa o en una tarjeta SD, en lugar de usar el almacenamiento interno del equipo. Esta opción resulta útil al digitalizar fondos grandes que superan la capacidad de la tarjeta microSD interna.

{{< callout type="warning" title="Función experimental" >}}
Esta función depende de las operaciones que realiza el sistema operativo sobre los discos. La compatibilidad varía según el formato de la unidad y el hardware. Consulta **[Formatos compatibles](#supported-formats)** más abajo. No uses una unidad externa como **única** copia del material digitalizado: conserva siempre una copia de respaldo.
{{< /callout >}}

---

## Cómo funciona {#how-it-works}

Cuando activas una unidad externa, Captua guarda los proyectos nuevos en una carpeta `dtk-projects/` de esa unidad. Los proyectos que ya guardaste en la tarjeta interna no cambian y siguen disponibles. Solo puedes tener una ubicación externa activa a la vez.

---

## Preparar la unidad {#supported-formats}

### Formato recomendado: exFAT {#recommended-format-exfat}

Recomendamos **exFAT** para las unidades externas que uses con Captua:

- Es compatible con Linux, Windows y macOS, sin instalar controladores adicionales.
- Admite archivos de más de 4 GB, algo importante para conjuntos de imágenes de alta resolución.
- Raspberry Pi OS ofrece buen soporte para este formato.

### Cómo formatear una unidad como exFAT {#how-to-format-a-drive-as-exfat}

#### Linux / Raspberry Pi {#linux-raspberry-pi}

```bash
# Instala las herramientas de exFAT si aún no las tienes
sudo apt install exfatprogs

# Identifica la unidad (busca tu dispositivo USB, por ejemplo, /dev/sda2)
lsblk

# Formatea la partición (reemplaza /dev/sdXN por la partición correcta)
sudo mkfs.exfat /dev/sdXN
```

{{< callout type="caution" >}}
Verifica dos veces la ruta del dispositivo con `lsblk` antes de ejecutar `mkfs`. Si formateas la partición equivocada, borrarás todo su contenido de forma permanente.
{{< /callout >}}

#### Windows {#windows}

1. Abre el **Explorador de archivos** y haz clic derecho en la unidad → **Formatear…**
2. En **Sistema de archivos**, selecciona `exFAT`.
3. Haz clic en **Iniciar**.

#### macOS {#macos}

1. Abre **Utilidad de Discos** (Aplicaciones → Utilidades → Utilidad de Discos).
2. Selecciona la unidad en el panel izquierdo.
3. Haz clic en **Borrar**, selecciona `ExFAT` en **Formato** y vuelve a hacer clic en **Borrar**.

### Resumen de compatibilidad de formatos {#format-compatibility-summary}

| Formato | Funciona con DTK | Notas |
|---|---|---|
| **exFAT** | ✅ Recomendado | La mejor opción para usar en varios sistemas operativos |
| **ext4** | ✅ Compatible | Solo Linux; algo más rápido |
| **FAT32 (vfat)** | ✅ Compatible | Límite de 4 GB por archivo |
| NTFS | ⚠️ Podría funcionar | Requiere `ntfs-3g`; sin garantía de compatibilidad |
| APFS | ❌ No compatible | Sistema de archivos exclusivo de macOS |
| HFS+ | ❌ No compatible | Sistema de archivos exclusivo de macOS |

---

## Usar almacenamiento externo desde la interfaz {#using-external-storage-in-the-ui}

Ve a **Configuración** (el ícono del engranaje en la barra lateral) y despliega la sección **Unidad de almacenamiento**.

### Paso 1: conectar la unidad {#step-1-connect-the-drive}

Conecta la unidad USB o la tarjeta SD a la Raspberry Pi. No necesitas montar la unidad de antemano.

### Paso 2: montar la unidad {#step-2-mount-the-drive}

La lista de dispositivos muestra todas las particiones detectadas. Las particiones sin montar tienen un botón **Montar**.

1. Busca en la lista la partición que quieras usar.
2. Presiona **Montar**.
3. Captua monta la unidad y el botón cambia a **Activar**.

### Paso 3: activar la unidad {#step-3-activate-the-drive}

Presiona **Activar** junto a la partición montada. Captua:

1. Crea un directorio `dtk-projects/` en la unidad, si aún no existe.
2. Usa ese directorio como ubicación activa de los proyectos.
3. Muestra una etiqueta verde con la palabra **activo** en la fila del dispositivo y un aviso que confirma la ruta activa.

Captua guarda en la unidad externa los proyectos que crees a partir de este momento.

### Desactivar la unidad y volver al almacenamiento interno {#deactivating-reverting-to-internal-storage}

Presiona **Restaurar predeterminado** en el aviso que indica la ubicación activa para volver al almacenamiento interno. Captua no desmonta la unidad externa: los proyectos que contiene permanecen intactos y disponibles.

### Retirar la unidad de forma segura {#safely-removing-the-drive}

Antes de desconectar la unidad:

1. Si es la ubicación de almacenamiento activa, presiona primero **Restaurar predeterminado**.
2. Presiona **Desmontar** junto a la partición.
3. Espera el mensaje de confirmación.
4. Desconecta la unidad.

{{< callout type="important" >}}
Presiona siempre **Desmontar** antes de desconectar la unidad. Si retiras una unidad montada, puedes dañar el sistema de archivos y perder datos.
{{< /callout >}}

---

## Solución de problemas {#troubleshooting}

**La unidad no aparece en la lista**
: Captua solo muestra las particiones de dispositivos extraíbles que no forman parte del sistema operativo. Prueba a presionar **Actualizar lista**. Si la unidad sigue sin aparecer, comprueba la conexión y verifica que el sistema operativo la reconozca (ejecuta `lsblk` en una terminal).

**"Montar" devuelve un error**
: Puede que la unidad use un formato incompatible (APFS, HFS+) o que necesite módulos adicionales del kernel (NTFS). Formatea la unidad como exFAT y vuelve a intentarlo.

**"Activar" falla por un error de permisos**
: Esto puede ocurrir en unidades ext4 recién formateadas, cuando `root` es el propietario del directorio raíz del sistema de archivos. Captua intenta completar la operación con permisos elevados. Si vuelve a fallar, formatea la unidad como exFAT.

**Unidad montada en modo de solo lectura**
: Algunas unidades imponen el modo de solo lectura cuando están casi llenas o cuando el sistema de archivos tiene errores. Comprueba el espacio disponible y ejecuta `sudo fsck /dev/sdXN` con la unidad desmontada para reparar los errores del sistema de archivos.
