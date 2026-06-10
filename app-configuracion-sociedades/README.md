# 🏢 Configurador de Sociedades — SAP S/4HANA (App Low-Code Local)

Aplicación low-code para facilitar el **diligenciamiento de los datos principales para la configuración de sociedades nuevas en SAP S/4HANA**. A partir de las respuestas a un cuestionario guiado, la app **determina automáticamente el plan de configuración** que se deberá ejecutar en el sistema: actividades, transacciones, rutas IMG (SPRO), tablas/campos afectados y valores propuestos.

## ✨ Características

- **📝 Cuestionario guiado por secciones** (datos generales, FI, CO, impuestos, documentos y crédito), con preguntas obligatorias, textos de ayuda, preguntas condicionales (se muestran según respuestas previas) y barra de progreso.
- **📋 Plan de configuración SAP automático**: cada respuesta se traduce en una actividad de configuración con transacción, ruta IMG, tabla/campo y valor propuesto. Exportable a CSV, JSON o PDF (imprimir).
- **⚙️ Módulo de administración**: crear, editar, ordenar y eliminar preguntas; definir sus posibles respuestas; y configurar cómo cada respuesta se traduce en configuración SAP (incluido el marcador `{respuesta}` para insertar el valor digitado). Importación/exportación del catálogo completo en JSON.
- **🔒 100% local, sin nube y sin API keys**: es un único archivo HTML que se ejecuta en el navegador. Los datos se guardan en `localStorage` del navegador; nada sale de su computador.
- **📱 Compatible con Microsoft Power Apps**: exporta el catálogo como tres tablas CSV normalizadas (Preguntas, Opciones, MapeoSAP) listas para usarse como origen de datos de una canvas app con conectores estándar (sin licencias premium). Ver [`powerapps/GUIA_POWERAPPS.md`](powerapps/GUIA_POWERAPPS.md).

## 🚀 Cómo ejecutar

1. Descargue o clone esta carpeta.
2. Haga **doble clic en `index.html`** (o ábralo con Chrome/Edge). No requiere instalación, servidor ni conexión a internet.

## 🗂️ Estructura del proyecto

```
app-configuracion-sociedades/
├── index.html                      ← La aplicación completa (HTML+CSS+JS, sin dependencias)
├── README.md
├── data/
│   └── configuracion-default.json  ← Catálogo por defecto (preguntas/respuestas/mapeo SAP)
└── powerapps/
    ├── GUIA_POWERAPPS.md           ← Guía paso a paso para replicar la app en Power Apps
    ├── Preguntas.csv               ← Tabla de preguntas (catálogo por defecto)
    ├── Opciones.csv                ← Tabla de posibles respuestas
    └── MapeoSAP.csv                ← Tabla de traducción respuesta → configuración SAP
```

## 🧠 Modelo de datos (cómo una respuesta se vuelve configuración)

```json
{
  "id": "p_plan_cuentas",
  "texto": "¿La sociedad utilizará el plan de cuentas corporativo existente o uno nuevo?",
  "tipo": "unica",
  "opciones": [
    {
      "texto": "Plan de cuentas corporativo existente",
      "mapeo": {
        "descripcionConfig": "Asignar sociedad al plan de cuentas existente",
        "transaccion": "OB62",
        "rutaIMG": "Gestión financiera > Contabilidad principal > ... > Asignar sociedad a plan de cuentas",
        "tablaCampo": "T001-KTOPL",
        "valorPropuesto": "Plan corporativo (ej. PCGC)",
        "notas": "Crear los segmentos de sociedad de las cuentas con FS00."
      }
    }
  ]
}
```

- Preguntas de **selección única / Sí-No**: cada opción tiene su propio mapeo SAP (las respuestas sin acción usan transacción `-` y no generan actividad en el plan).
- Preguntas de **texto libre**: usan un `mapeoDirecto` cuyo `valorPropuesto` admite el marcador `{respuesta}` (ej. el código de sociedad digitado se propone como valor de `T001-BUKRS`).
- Preguntas **condicionales**: `dependeDe` indica de qué pregunta dependen y con qué respuestas se muestran (ej. las preguntas de CO solo aparecen si la sociedad usará Controlling).

## 📦 Catálogo por defecto incluido

17 preguntas que cubren el alcance típico de la creación de una sociedad en S/4HANA:

| Sección | Temas y transacciones cubiertas |
|---|---|
| Datos generales | Código y razón social (OX02/EC01), país y esquema de impuestos (OBBG), moneda local, idioma |
| Estructura contable (FI) | Plan de cuentas (OB13/OB62), variante de ejercicio (OB29/OB37), períodos contables (OBBO/OBBP/OB52), monedas paralelas (OB22/FINSC_LEDGER), variante de status de campo (OBC4/OBC5) |
| Controlling (CO) | Sociedad CO (OKKP/OX19), jerarquía y centros de coste (OKEON/KS01) |
| Impuestos | Retención ampliada (extended withholding tax), indicadores de IVA (FTXP/OB40) |
| Documentos y crédito | Rangos de números de documento (FBN1/OBH1), gestión de crédito FSCM (OB38/UKM) |

Todo el catálogo es editable desde la pestaña **⚙️ Administración** sin tocar código.

## ⚠️ Alcance

El plan generado es una **guía de configuración para el consultor**: estandariza el levantamiento de información y la determinación de actividades, pero la parametrización debe ejecutarse y validarse en el sistema SAP por personal funcional, siguiendo la estrategia de transportes del proyecto.
