# 🏢 Configurador de Sociedades — SAP S/4HANA (App Low-Code Local)

Aplicación low-code para facilitar el **diligenciamiento de los datos principales para la configuración de sociedades nuevas en SAP S/4HANA**. A partir de las respuestas a un cuestionario guiado, la app **determina automáticamente el plan de configuración** que se deberá ejecutar en el sistema: actividades, transacciones, rutas IMG (SPRO), tablas/campos afectados y valores propuestos.

## ✨ Características

- **📝 Cuestionario guiado por secciones** (datos generales, FI, CO, impuestos, documentos y crédito), con preguntas obligatorias, textos de ayuda, preguntas condicionales (se muestran según respuestas previas) y barra de progreso.
- **📋 Plan de configuración SAP automático**: cada respuesta se traduce en una actividad de configuración con transacción, ruta IMG, tabla/campo y valor propuesto. Exportable a CSV, JSON o PDF (imprimir).
- **⚙️ Módulo de administración**: crear, editar, ordenar y eliminar preguntas; definir sus posibles respuestas; y configurar cómo cada respuesta se traduce en configuración SAP (incluido el marcador `{respuesta}` para insertar el valor digitado). Importación/exportación del catálogo completo en JSON.
- **🗃️ Catálogos de datos por pregunta**: para respuestas amplias (monedas, bancos, países, clases de activos…) las preguntas pueden conectarse a una base de valores con búsqueda incremental, en modo de un valor o de selección múltiple (chips). Los catálogos se cargan masivamente desde archivos CSV o pegando texto, y se administran sin tocar código. Incluye precargados: monedas ISO (44), países (33), idiomas SAP (17), bancos de ejemplo (20) y clases de activos (10).
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

53 preguntas en 14 secciones que cubren el alcance multimódulo de la creación de una sociedad en S/4HANA:

| Sección / Módulo | Temas y transacciones cubiertas |
|---|---|
| Datos generales y alcance | Código y razón social (OX02/EC01), número de sociedades, domicilios/sucursales, país y esquema de impuestos (OBBG), moneda, idioma, migración de datos (LTMC), datos maestros centralizados (MDG) |
| Contabilidad principal (GL) | Plan de cuentas (OB13/OB62), variante de ejercicio (OB29/OB37), períodos (OBBO/OBBP/OB52), monedas paralelas (OB22/FINSC_LEDGER), status de campo (OBC4/OBC5), validaciones (OB28/GGB0), revaluación de monedas (FAGL_FCV/OBA1), estructura de balance (OB58), intercompany (OBYA), lugares comerciales |
| Impuestos y retenciones | Retención ampliada (extended withholding tax), indicadores de IVA (FTXP/OB40) |
| Cuentas por pagar (AP) | Grupos de BP proveedor (OBD3), programa de pagos (FBZP/F110), anticipos (OBYR) |
| Cuentas por cobrar (AR) | Grupos de BP cliente (OBD2), anticipos (OBXR), reclamaciones (FBMP/F150), crédito FSCM (OB38/UKM) |
| Activos fijos (AA) | Plan de valoración (OAOB/EC08/OADB), clases de activos (OAOA/AO90), claves de amortización (AFAMA) |
| Controlling (CO) | Sociedad CO (OKKP/OX19), centros de coste (OKEON/KS01), órdenes internas (KOT2_OPA/OKO7) |
| Control presupuestal (FM) | Entidad CP y BCS (OF18/FMUF), centros gestores/posiciones (FMSA/FMCIA), derivación CAPEX-OPEX y AVC (FMDERIVE/OF39) |
| Proyectos (PS) | Perfil de proyecto y PEP (OPSA/OPSK), capitalización a activos (OITA/OKO7) |
| Tesorería (TR/TRM) | Bancos propios y BAM (FI12), extracto electrónico (OT83/FF_5), Cash Management (FQM), instrumentos financieros TRM (FTR_CREATE) |
| Ventas (SD) | Estructura de ventas (OVX5/OVX3, VKOA), facturación electrónica (EDOC_COCKPIT) |
| Compras e inventarios (MM) | Centros y almacenes (OX10/OX18/OX09), valoración S/V (OMW0/OBYC), tolerancias de facturas (OMR6) |
| Mantenimiento (PM) | Centros de planificación PM, tipos de orden e integración CO (OIOA/OKO7) |
| Documentos contables | Rangos de números de documento (FBN1/OBH1) |

Todo el catálogo es editable desde la pestaña **⚙️ Administración** sin tocar código.

## ⚠️ Alcance

El plan generado es una **guía de configuración para el consultor**: estandariza el levantamiento de información y la determinación de actividades, pero la parametrización debe ejecutarse y validarse en el sistema SAP por personal funcional, siguiendo la estrategia de transportes del proyecto.
