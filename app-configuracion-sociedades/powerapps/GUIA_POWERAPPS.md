# Guía: Replicar el Configurador de Sociedades SAP en Microsoft Power Apps

Esta guía explica cómo construir la misma solución como **aplicación de lienzo (canvas app)** en Power Apps, usando como origen de datos las tres tablas que exporta la aplicación local (`index.html` → Administración → "Exportar tablas para Power Apps").

> **Sin API keys ni conectores premium.** La solución usa únicamente conectores estándar (Excel en OneDrive o listas de SharePoint), incluidos en cualquier licencia Microsoft 365 con Power Apps.

---

## 1. Modelo de datos

La aplicación local exporta tres archivos CSV normalizados (también incluidos en esta carpeta con el catálogo por defecto):

| Archivo | Contenido | Columnas clave |
|---|---|---|
| `Preguntas.csv` | Catálogo de preguntas | `PreguntaID`, `Seccion`, `Orden`, `Texto`, `Ayuda`, `Tipo` (texto / unica / si_no), `Obligatoria`, `DependeDePregunta`, `DependeDeValores` |
| `Opciones.csv` | Posibles respuestas de cada pregunta | `OpcionID`, `PreguntaID`, `TextoRespuesta` |
| `MapeoSAP.csv` | Traducción de cada respuesta a configuración SAP | `MapeoID`, `PreguntaID`, `OpcionID`, `ActividadConfiguracion`, `Transaccion`, `RutaIMG`, `TablaCampo`, `ValorPropuesto`, `Notas` |
| `Catalogos.csv` | Bases de valores para preguntas tipo catálogo (monedas, bancos, etc.) | `CatalogoID`, `NombreCatalogo`, `Codigo`, `Texto` |

Para las preguntas con `Tipo = catalogo` o `catalogo_multiple`, la columna `Preguntas.CatalogoID` indica qué subconjunto de `Catalogos.csv` usar como origen del control. En Power Apps use un **ComboBox** con `Items: Filter(colCatalogos, CatalogoID = ThisItem.CatalogoID)`, propiedad `SelectMultiple` según el tipo, y guarde en `colRespuestas` los códigos seleccionados unidos con `Concat(cmbValores.SelectedItems, Codigo, ", ")` — exactamente el mismo formato que usa la app local, de modo que el mapeo con `{respuesta}` funciona igual.

**Relaciones:**
- `Opciones.PreguntaID` → `Preguntas.PreguntaID` (1 pregunta : N opciones)
- `MapeoSAP.OpcionID` → `Opciones.OpcionID` (1 opción : 1 mapeo). Para preguntas de texto libre, `OpcionID` queda vacío y el mapeo aplica directamente a la pregunta; el campo `ValorPropuesto` puede contener el marcador `{respuesta}`, que se sustituye por lo que digite el usuario.

## 2. Preparar el origen de datos

**Opción A — Excel en OneDrive (la más simple):**
1. Abra cada CSV en Excel y conviértalo en tabla (`Ctrl+T`), con nombres `Preguntas`, `Opciones` y `MapeoSAP`.
2. Guarde el libro `ConfiguradorSAP.xlsx` en OneDrive para la Empresa.

**Opción B — Listas de SharePoint (mejor para varios usuarios):**
1. Cree tres listas con las mismas columnas e importe los CSV (SharePoint admite "crear lista desde Excel/CSV").

## 3. Crear la aplicación de lienzo

1. En [make.powerapps.com](https://make.powerapps.com) → **Crear** → **Aplicación de lienzo en blanco** (formato tableta).
2. **Datos** → agregue las tres tablas (conector Excel Online (Business) o SharePoint).
3. En `App.OnStart` cargue colecciones de trabajo:

```powerfx
ClearCollect(colPreguntas, SortByColumns(Preguntas, "Seccion", SortOrder.Ascending, "Orden", SortOrder.Ascending));
ClearCollect(colOpciones, Opciones);
ClearCollect(colMapeo, MapeoSAP);
// Colección donde se guardan las respuestas del usuario
ClearCollect(colRespuestas, Table({PreguntaID: "", Respuesta: ""}));
Clear(colRespuestas)
```

## 4. Pantalla "Cuestionario"

1. Inserte una **galería vertical flexible** `galPreguntas` con `Items`:

```powerfx
Filter(
    colPreguntas,
    // Lógica condicional: mostrar si no depende de otra pregunta,
    // o si la respuesta de la pregunta padre está en la lista DependeDeValores
    IsBlank(DependeDePregunta) ||
    LookUp(colRespuestas, PreguntaID = DependeDePregunta, Respuesta) in Split(DependeDeValores, "|")
)
```

2. Dentro de la plantilla de la galería:
   - **Etiqueta** `lblPregunta`: `ThisItem.Texto & If(ThisItem.Obligatoria = "Si", " *", "")`
   - **Etiqueta** `lblAyuda`: `ThisItem.Ayuda` (tamaño pequeño, gris)
   - **Botones de opción** `radOpciones` (visible cuando `ThisItem.Tipo <> "texto"`):
     - `Items`: `Filter(colOpciones, PreguntaID = ThisItem.PreguntaID).TextoRespuesta`
     - `OnChange`:

```powerfx
RemoveIf(colRespuestas, PreguntaID = ThisItem.PreguntaID);
Collect(colRespuestas, {PreguntaID: ThisItem.PreguntaID, Respuesta: radOpciones.Selected.Value})
```

   - **Entrada de texto** `txtRespuesta` (visible cuando `ThisItem.Tipo = "texto"`), con el mismo patrón en `OnChange` usando `txtRespuesta.Text`.

3. **Botón "Generar plan"** con validación de obligatorias:

```powerfx
If(
    CountRows(
        Filter(
            colPreguntas,
            Obligatoria = "Si" &&
            (IsBlank(DependeDePregunta) ||
             LookUp(colRespuestas, PreguntaID = DependeDePregunta, Respuesta) in Split(DependeDeValores, "|")) &&
            IsBlank(LookUp(colRespuestas, PreguntaID = ThisRecord.PreguntaID, Respuesta))
        )
    ) > 0,
    Notify("Hay preguntas obligatorias sin responder", NotificationType.Error),
    Navigate(PantallaPlan, ScreenTransition.Cover)
)
```

## 5. Pantalla "Plan de configuración"

1. En `PantallaPlan.OnVisible` construya el plan cruzando respuestas → opciones → mapeo:

```powerfx
ClearCollect(
    colPlan,
    ForAll(
        colRespuestas As r,
        With(
            {
                preg: LookUp(colPreguntas, PreguntaID = r.PreguntaID),
                op: LookUp(colOpciones, PreguntaID = r.PreguntaID && TextoRespuesta = r.Respuesta)
            },
            With(
                {
                    map: If(
                        preg.Tipo = "texto",
                        LookUp(colMapeo, PreguntaID = r.PreguntaID && IsBlank(OpcionID)),
                        LookUp(colMapeo, OpcionID = op.OpcionID)
                    )
                },
                {
                    Seccion: preg.Seccion,
                    Pregunta: preg.Texto,
                    Respuesta: r.Respuesta,
                    Actividad: map.ActividadConfiguracion,
                    Transaccion: map.Transaccion,
                    RutaIMG: map.RutaIMG,
                    TablaCampo: map.TablaCampo,
                    ValorPropuesto: Substitute(map.ValorPropuesto, "{respuesta}", r.Respuesta),
                    Notas: map.Notas
                }
            )
        )
    )
);
// Quitar filas sin actividad de configuración (respuestas "No" sin acción)
RemoveIf(colPlan, IsBlank(Actividad) || Actividad = "Sin acción")
```

2. Muestre `colPlan` en una galería o tabla de datos agrupada por `Seccion`.
3. Para entregar el plan: botón que guarde `colPlan` en una lista de SharePoint / tabla de Excel (`Patch` o `Collect` sobre el origen), o un flujo de Power Automate estándar que genere el Excel/correo.

## 6. Pantalla "Administración" (opcional)

Para mantener preguntas/opciones/mapeos desde la propia Power App, cree formularios de edición (`EditForm`) sobre las tres tablas. Al estar el catálogo en Excel/SharePoint, también puede mantenerse directamente allí sin desarrollo adicional: la app lo refleja al recargar.

## 7. Equivalencias entre la app local y la Power App

| Concepto | App local (`index.html`) | Power Apps |
|---|---|---|
| Catálogo de preguntas | `CONFIG_DEFAULT` + localStorage | Tablas Excel/SharePoint |
| Respuestas del usuario | objeto `respuestas` (localStorage) | `colRespuestas` |
| Lógica condicional | `dependeDe {preguntaId, valores}` | columnas `DependeDePregunta` + `DependeDeValores` con `Split(..., "|")` |
| Traducción a SAP | `mapeo` por opción / `mapeoDirecto` | tabla `MapeoSAP` (por `OpcionID` o solo `PreguntaID`) |
| Marcador `{respuesta}` | `replace()` en `construirPlan()` | `Substitute()` en `colPlan` |
| Plan de configuración | vista "Plan" + CSV/JSON/print | `colPlan` + galería + Patch/Power Automate |

Ambas implementaciones comparten exactamente el mismo modelo de datos, por lo que el catálogo mantenido en una puede importarse en la otra en cualquier momento.
