Attribute VB_Name = "modNuevaSociedad"
' ============================================================
' MACRO: NUEVA SOCIEDAD - Formulario Dinámico
' Versión: 1.0
' Descripción: Formulario de diligenciamiento para nuevas
'              sociedades con habilitación dinámica de hojas
'              según las respuestas del usuario.
'
' INSTRUCCIONES DE INSTALACIÓN:
'   1. Abrir Excel y crear un libro nuevo (.xlsm)
'   2. Presionar Alt+F11 para abrir el editor VBA
'   3. Ir a Insertar > Módulo
'   4. Pegar todo este código
'   5. Cerrar el editor y ejecutar: Herramientas > Macros > InicializarFormulario
' ============================================================

Option Explicit

' ---- CONSTANTES DE CONFIGURACIÓN ----
Private Const PASS_FORMULARIO As String = ""   ' Contraseña de protección (dejar vacío = sin contraseña)
Private Const FILA_INICIO     As Integer = 4   ' Primera fila de preguntas
Private Const FILA_FIN        As Integer = 32  ' Última fila de preguntas (29 preguntas)
Private Const COL_RESPUESTA   As Integer = 5   ' Columna E = respuestas

' ============================================================
' PUNTO DE ENTRADA PRINCIPAL
' Ejecutar esta macro para inicializar todo el libro
' ============================================================
Sub InicializarFormulario()
    Application.ScreenUpdating = False
    Application.DisplayAlerts = False

    Dim wb As Workbook
    Set wb = ThisWorkbook

    ' Orden de creación importante
    Call EliminarHojasAnteriores(wb)
    Call CrearHojaBaseDatos(wb)
    Call CrearHojaFormulario(wb)
    Call CrearTodasLasHojasModulo(wb)

    ' Ir al formulario al terminar
    wb.Sheets("Formulario").Activate
    wb.Sheets("Formulario").Range("E4").Select

    Application.ScreenUpdating = True
    Application.DisplayAlerts = True

    MsgBox "¡Formulario de Nueva Sociedad creado exitosamente!" & Chr(13) & Chr(13) & _
           "Complete las preguntas en la hoja 'Formulario'." & Chr(13) & _
           "Las hojas de configuración se habilitarán automáticamente.", _
           vbInformation, "Nueva Sociedad - Listo"
End Sub

' ============================================================
' ELIMINAR HOJAS PREVIAS (permite re-ejecutar limpiamente)
' ============================================================
Private Sub EliminarHojasAnteriores(wb As Workbook)
    Dim nombresAEliminar As Variant
    nombresAEliminar = Array("Formulario", "BaseDatos", "GL - Contabilidad", _
                             "AP - Ctas por Pagar", "AR - Ctas por Cobrar", _
                             "AA - Activos Fijos", "FM - Presupuesto", _
                             "FI - Config. Financiera", "CO-GL - Lugares", _
                             "ICO - Intercompanía", "SD - Facturación", _
                             "Tesorería", "Tes. Avanzada", "CO - Centros Costo")

    Dim nombre As Variant
    Dim ws As Worksheet
    For Each nombre In nombresAEliminar
        On Error Resume Next
        Set ws = wb.Sheets(CStr(nombre))
        If Not ws Is Nothing Then
            ws.Visible = xlSheetVisible
            ws.Delete
            Set ws = Nothing
        End If
        On Error GoTo 0
    Next nombre

    ' Si el libro quedó sin hojas, agregar una temporal
    If wb.Sheets.Count = 0 Then
        wb.Sheets.Add
    End If
End Sub

' ============================================================
' CREAR HOJA BASE DE DATOS
' ============================================================
Private Sub CrearHojaBaseDatos(wb As Workbook)
    Dim ws As Worksheet
    Set ws = wb.Sheets.Add(After:=wb.Sheets(wb.Sheets.Count))
    ws.Name = "BaseDatos"

    ' Título
    With ws.Range("A1:I1")
        .Merge
        .Value = "BASE DE DATOS - OPCIONES CONFIGURABLES"
        .Font.Bold = True
        .Font.Size = 13
        .Font.Color = RGB(255, 255, 255)
        .Interior.Color = RGB(68, 114, 196)
        .HorizontalAlignment = xlCenter
        .RowHeight = 32
    End With

    ' Definir categorías con sus valores
    Dim categorias(7) As String
    Dim valores(7) As Variant

    categorias(0) = "Países / Domicilios"
    valores(0) = Array("Colombia", "México", "Panamá", "España", "Estados Unidos", "Chile", "Perú", "Ecuador", "Costa Rica")

    categorias(1) = "Planes de Cuentas"
    valores(1) = Array("Plan General CO01", "Plan Especial CO02", "Plan NIIF Plenas", "Plan NIIF Pymes", "Plan Local")

    categorias(2) = "Monedas"
    valores(2) = Array("COP - Peso Colombiano", "USD - Dólar Americano", "EUR - Euro", "MXN - Peso Mexicano", "PEN - Sol Peruano", "CLP - Peso Chileno", "PAB - Balboa Panameño")

    categorias(3) = "Variante de Ejercicio"
    valores(3) = Array("K4 - Año fiscal estándar (12 períodos)", "V3 - Períodos especiales (16)", "01 - Enero a Diciembre", "V6 - Semestral")

    categorias(4) = "Clases de Activos Fijos"
    valores(4) = Array("1000 - Terrenos", "1100 - Edificaciones", "1200 - Maquinaria y Equipo", "1300 - Equipos de Cómputo", "1400 - Vehículos", "1500 - Muebles y Enseres", "1600 - Intangibles", "1700 - Activos en Leasing")

    categorias(5) = "Impuestos Aplicables"
    valores(5) = Array("IVA 19%", "IVA 5%", "IVA 0% - Excluido", "INC 8%", "INC 16%", "IVA Descontable", "IVA Generado")

    categorias(6) = "Retenciones Aplicables"
    valores(6) = Array("ReteFuente - Honorarios 11%", "ReteFuente - Servicios 4%", "ReteFuente - Compras 2.5%", "ReteICA", "ReteIVA 15%", "AutoRetención")

    categorias(7) = "Bancos"
    valores(7) = Array("Bancolombia", "Davivienda", "BBVA Colombia", "Banco de Bogotá", "Banco Popular", "Colpatria", "Citibank", "Banco Agrario", "Scotiabank Colpatria")

    ' Escribir categorías y valores
    Dim col As Integer
    Dim i As Integer, j As Integer

    For i = 0 To 7
        col = i + 1
        With ws.Cells(2, col)
            .Value = categorias(i)
            .Font.Bold = True
            .Font.Color = RGB(255, 255, 255)
            .Interior.Color = RGB(31, 73, 125)
            .HorizontalAlignment = xlCenter
            .WrapText = True
            ws.Rows(2).RowHeight = 40
        End With

        Dim vals As Variant
        vals = valores(i)
        For j = 0 To UBound(vals)
            With ws.Cells(3 + j, col)
                .Value = vals(j)
                If j Mod 2 = 0 Then
                    .Interior.Color = RGB(242, 242, 242)
                End If
            End With
        Next j

        ws.Columns(col).AutoFit
        If ws.Columns(col).ColumnWidth < 18 Then ws.Columns(col).ColumnWidth = 18
    Next i

    ' Nota al pie
    Dim ultimaFila As Integer
    ultimaFila = 14
    With ws.Range("A" & ultimaFila & ":I" & ultimaFila)
        .Merge
        .Value = "NOTA: Agregue o modifique opciones en esta hoja. Los cambios se reflejarán en los desplegables del formulario."
        .Font.Italic = True
        .Font.Color = RGB(128, 128, 128)
        .Font.Size = 9
        .HorizontalAlignment = xlCenter
    End With
End Sub

' ============================================================
' CREAR HOJA FORMULARIO PRINCIPAL
' ============================================================
Private Sub CrearHojaFormulario(wb As Workbook)
    Dim ws As Worksheet
    Set ws = wb.Sheets.Add(Before:=wb.Sheets(1))
    ws.Name = "Formulario"

    ' === ENCABEZADO ===
    With ws.Range("A1:G1")
        .Merge
        .Value = "CUESTIONARIO DE NUEVAS SOCIEDADES"
        .Font.Bold = True
        .Font.Size = 18
        .Font.Color = RGB(255, 255, 255)
        .Interior.Color = RGB(31, 73, 125)
        .HorizontalAlignment = xlCenter
        .VerticalAlignment = xlCenter
        .RowHeight = 45
    End With

    With ws.Range("A2:G2")
        .Merge
        .Value = "Complete el formulario. Las hojas de configuración se habilitarán automáticamente según sus respuestas."
        .Font.Size = 10
        .Font.Italic = True
        .Font.Color = RGB(31, 73, 125)
        .Interior.Color = RGB(189, 215, 238)
        .HorizontalAlignment = xlCenter
        .VerticalAlignment = xlCenter
        .RowHeight = 28
    End With

    ' === ENCABEZADOS DE COLUMNA ===
    Dim hdrs As Variant
    hdrs = Array("#", "Frente", "Módulo", "Pregunta", "Respuesta", "Estado", "Hoja habilitada")
    Dim h As Integer
    For h = 0 To 6
        With ws.Cells(3, h + 1)
            .Value = hdrs(h)
            .Font.Bold = True
            .Font.Color = RGB(255, 255, 255)
            .Interior.Color = RGB(31, 73, 125)
            .HorizontalAlignment = xlCenter
            .VerticalAlignment = xlCenter
        End With
    Next h
    ws.Rows(3).RowHeight = 28

    ' === DEFINICIÓN DE PREGUNTAS ===
    ' Formato: Número, Frente, Módulo, Pregunta, TipoRespuesta, HojaAsociada
    ' TipoRespuesta: TEXTO | NUMERO | SINO | LISTA_CONFIG | SINO_LISTA
    Dim preguntas(28, 5) As String

    preguntas(0, 0) = "1"   : preguntas(0, 1) = "Transversal" : preguntas(0, 2) = "Proyecto"
    preguntas(0, 3) = "Nombre del proyecto"
    preguntas(0, 4) = "TEXTO" : preguntas(0, 5) = ""

    preguntas(1, 0) = "2"   : preguntas(1, 1) = "Finanzas" : preguntas(1, 2) = "GL"
    preguntas(1, 3) = "¿Cuántas sociedades son?"
    preguntas(1, 4) = "NUMERO" : preguntas(1, 5) = "GL - Contabilidad"

    preguntas(2, 0) = "3"   : preguntas(2, 1) = "Finanzas" : preguntas(2, 2) = "GL"
    preguntas(2, 3) = "¿Dónde estarán domiciliadas?"
    preguntas(2, 4) = "LISTA_CONFIG" : preguntas(2, 5) = "GL - Contabilidad"

    preguntas(3, 0) = "4"   : preguntas(3, 1) = "Finanzas" : preguntas(3, 2) = "GL"
    preguntas(3, 3) = "¿Qué plan de cuentas usarán? ¿El modelo general que tenemos o uno especial?"
    preguntas(3, 4) = "LISTA_CONFIG" : preguntas(3, 5) = "GL - Contabilidad"

    preguntas(4, 0) = "5"   : preguntas(4, 1) = "Finanzas" : preguntas(4, 2) = "GL"
    preguntas(4, 3) = "¿Qué monedas manejan?"
    preguntas(4, 4) = "LISTA_CONFIG" : preguntas(4, 5) = "GL - Contabilidad"

    preguntas(5, 0) = "6"   : preguntas(5, 1) = "Finanzas" : preguntas(5, 2) = "GL"
    preguntas(5, 3) = "¿Va a tener migración de datos?"
    preguntas(5, 4) = "SINO" : preguntas(5, 5) = "GL - Contabilidad"

    preguntas(6, 0) = "7"   : preguntas(6, 1) = "Finanzas" : preguntas(6, 2) = "GL"
    preguntas(6, 3) = "Variante de ejercicio"
    preguntas(6, 4) = "LISTA_CONFIG" : preguntas(6, 5) = "GL - Contabilidad"

    preguntas(7, 0) = "8"   : preguntas(7, 1) = "Finanzas" : preguntas(7, 2) = "AP"
    preguntas(7, 3) = "¿Gestionarán cuentas por pagar?"
    preguntas(7, 4) = "SINO" : preguntas(7, 5) = "AP - Ctas por Pagar"

    preguntas(8, 0) = "9"   : preguntas(8, 1) = "Finanzas" : preguntas(8, 2) = "AR"
    preguntas(8, 3) = "¿Gestionarán cuentas por cobrar?"
    preguntas(8, 4) = "SINO" : preguntas(8, 5) = "AR - Ctas por Cobrar"

    preguntas(9, 0) = "10"  : preguntas(9, 1) = "Finanzas" : preguntas(9, 2) = "AA"
    preguntas(9, 3) = "¿Gestionarán activos fijos?"
    preguntas(9, 4) = "SINO" : preguntas(9, 5) = "AA - Activos Fijos"

    preguntas(10, 0) = "11" : preguntas(10, 1) = "Finanzas" : preguntas(10, 2) = "AA"
    preguntas(10, 3) = "¿Qué clases de activos fijos se tendrán?"
    preguntas(10, 4) = "LISTA_CONFIG" : preguntas(10, 5) = "AA - Activos Fijos"

    preguntas(11, 0) = "12" : preguntas(11, 1) = "Finanzas" : preguntas(11, 2) = "AA"
    preguntas(11, 3) = "¿Se tendrá el mismo plan de valoración de alguna otra sociedad?"
    preguntas(11, 4) = "SINO_LISTA" : preguntas(11, 5) = "AA - Activos Fijos"

    preguntas(12, 0) = "13" : preguntas(12, 1) = "Finanzas" : preguntas(12, 2) = "FM"
    preguntas(12, 3) = "¿Habrá control presupuestal?"
    preguntas(12, 4) = "SINO" : preguntas(12, 5) = "FM - Presupuesto"

    preguntas(13, 0) = "14" : preguntas(13, 1) = "Finanzas" : preguntas(13, 2) = "FM"
    preguntas(13, 3) = "¿Se necesitará control de imputación para ejecuciones de proyectos (CAPEX | OPEX)?"
    preguntas(13, 4) = "SINO" : preguntas(13, 5) = "FM - Presupuesto"

    preguntas(14, 0) = "15" : preguntas(14, 1) = "Finanzas" : preguntas(14, 2) = "FI"
    preguntas(14, 3) = "¿Se acoge al manejo de datos maestros centralizado?"
    preguntas(14, 4) = "SINO" : preguntas(14, 5) = "FI - Config. Financiera"

    preguntas(15, 0) = "16" : preguntas(15, 1) = "Finanzas" : preguntas(15, 2) = "FI"
    preguntas(15, 3) = "¿El proceso de contabilización a nivel de GL deberá pasar por una validación preliminar?"
    preguntas(15, 4) = "SINO" : preguntas(15, 5) = "FI - Config. Financiera"

    preguntas(16, 0) = "17" : preguntas(16, 1) = "Finanzas" : preguntas(16, 2) = "CO-GL"
    preguntas(16, 3) = "Definición de lugares comerciales (matriz y sucursales)"
    preguntas(16, 4) = "SINO_LISTA" : preguntas(16, 5) = "CO-GL - Lugares"

    preguntas(17, 0) = "18" : preguntas(17, 1) = "Finanzas" : preguntas(17, 2) = "GL"
    preguntas(17, 3) = "Definición de impuestos aplicables"
    preguntas(17, 4) = "LISTA_CONFIG" : preguntas(17, 5) = "GL - Contabilidad"

    preguntas(18, 0) = "19" : preguntas(18, 1) = "Finanzas" : preguntas(18, 2) = "GL"
    preguntas(18, 3) = "Definición de retenciones aplicables"
    preguntas(18, 4) = "LISTA_CONFIG" : preguntas(18, 5) = "GL - Contabilidad"

    preguntas(19, 0) = "20" : preguntas(19, 1) = "Finanzas" : preguntas(19, 2) = "ICO"
    preguntas(19, 3) = "Definición de operaciones multisociedades (ICO)"
    preguntas(19, 4) = "LISTA_CONFIG" : preguntas(19, 5) = "ICO - Intercompañía"

    preguntas(20, 0) = "21" : preguntas(20, 1) = "Finanzas" : preguntas(20, 2) = "GL"
    preguntas(20, 3) = "Revaluación de monedas"
    preguntas(20, 4) = "SINO" : preguntas(20, 5) = "GL - Contabilidad"

    preguntas(21, 0) = "22" : preguntas(21, 1) = "Finanzas" : preguntas(21, 2) = "GL"
    preguntas(21, 3) = "Definición de estructura de balance"
    preguntas(21, 4) = "SINO" : preguntas(21, 5) = "GL - Contabilidad"

    preguntas(22, 0) = "23" : preguntas(22, 1) = "Finanzas" : preguntas(22, 2) = "SD"
    preguntas(22, 3) = "Gestión de facturación de venta"
    preguntas(22, 4) = "SINO" : preguntas(22, 5) = "SD - Facturación"

    preguntas(23, 0) = "24" : preguntas(23, 1) = "Finanzas" : preguntas(23, 2) = "Tesorería"
    preguntas(23, 3) = "Cuentas bancarias: ¿cuántas, en qué bancos, países y monedas?"
    preguntas(23, 4) = "LISTA_CONFIG" : preguntas(23, 5) = "Tesorería"

    preguntas(24, 0) = "25" : preguntas(24, 1) = "Finanzas" : preguntas(24, 2) = "Tesorería"
    preguntas(24, 3) = "Cajas menores: ¿cuántas, en qué sitios y monedas?"
    preguntas(24, 4) = "LISTA_CONFIG" : preguntas(24, 5) = "Tesorería"

    preguntas(25, 0) = "26" : preguntas(25, 1) = "Finanzas" : preguntas(25, 2) = "Tes. Avanzada"
    preguntas(25, 3) = "¿Gestionarán deudas? ¿De qué tipo? ¿Cuántas?"
    preguntas(25, 4) = "SINO" : preguntas(25, 5) = "Tes. Avanzada"

    preguntas(26, 0) = "27" : preguntas(26, 1) = "Finanzas" : preguntas(26, 2) = "Tes. Avanzada"
    preguntas(26, 3) = "¿Gestionarán inversiones? ¿De qué tipo? ¿Cuántas?"
    preguntas(26, 4) = "SINO" : preguntas(26, 5) = "Tes. Avanzada"

    preguntas(27, 0) = "28" : preguntas(27, 1) = "Finanzas" : preguntas(27, 2) = "CO"
    preguntas(27, 3) = "Asignación de gastos por centros de costos"
    preguntas(27, 4) = "LISTA_CONFIG" : preguntas(27, 5) = "CO - Centros Costo"

    preguntas(28, 0) = "29" : preguntas(28, 1) = "Finanzas" : preguntas(28, 2) = "Transversal"
    preguntas(28, 3) = "¿Se configurará con copia de la Sociedad CO01?"
    preguntas(28, 4) = "LISTA_CONFIG" : preguntas(28, 5) = ""

    ' === COLORES POR MÓDULO ===
    ' Se definen en la función ObtenerColorModulo()

    ' === ESCRIBIR FILAS DE PREGUNTAS ===
    Dim fila As Integer
    fila = FILA_INICIO
    Dim p As Integer

    For p = 0 To 28
        ' Columna A - Número
        With ws.Cells(fila, 1)
            .Value = CInt(preguntas(p, 0))
            .Font.Bold = True
            .HorizontalAlignment = xlCenter
            .VerticalAlignment = xlCenter
        End With

        ' Columna B - Frente
        With ws.Cells(fila, 2)
            .Value = preguntas(p, 1)
            .HorizontalAlignment = xlCenter
            .VerticalAlignment = xlCenter
        End With

        ' Columna C - Módulo (con color)
        With ws.Cells(fila, 3)
            .Value = preguntas(p, 2)
            .HorizontalAlignment = xlCenter
            .VerticalAlignment = xlCenter
            .Font.Bold = True
            .Font.Color = RGB(255, 255, 255)
            .Interior.Color = ObtenerColorModulo(preguntas(p, 2))
        End With

        ' Columna D - Pregunta
        With ws.Cells(fila, 4)
            .Value = preguntas(p, 3)
            .WrapText = True
            .VerticalAlignment = xlCenter
        End With

        ' Columna E - Respuesta (con validación según tipo)
        Call AgregarValidacion(ws, fila, preguntas(p, 4), wb)

        ' Columna F - Estado
        With ws.Cells(fila, 6)
            .Value = "Pendiente"
            .HorizontalAlignment = xlCenter
            .Font.Color = RGB(128, 128, 128)
            .Font.Size = 9
            .VerticalAlignment = xlCenter
        End With

        ' Columna G - Hoja habilitada
        With ws.Cells(fila, 7)
            .Value = preguntas(p, 5)
            .Font.Italic = True
            .Font.Size = 8
            .Font.Color = RGB(89, 89, 89)
            .HorizontalAlignment = xlCenter
            .VerticalAlignment = xlCenter
        End With

        ' Color de fila alternado (solo columnas A, B, D)
        If p Mod 2 = 0 Then
            ws.Range(ws.Cells(fila, 1), ws.Cells(fila, 1)).Interior.Color = RGB(235, 241, 251)
            ws.Range(ws.Cells(fila, 2), ws.Cells(fila, 2)).Interior.Color = RGB(235, 241, 251)
            ws.Range(ws.Cells(fila, 4), ws.Cells(fila, 4)).Interior.Color = RGB(235, 241, 251)
            ws.Range(ws.Cells(fila, 6), ws.Cells(fila, 6)).Interior.Color = RGB(235, 241, 251)
            ws.Range(ws.Cells(fila, 7), ws.Cells(fila, 7)).Interior.Color = RGB(235, 241, 251)
        Else
            ws.Range(ws.Cells(fila, 1), ws.Cells(fila, 1)).Interior.Color = RGB(255, 255, 255)
            ws.Range(ws.Cells(fila, 2), ws.Cells(fila, 2)).Interior.Color = RGB(255, 255, 255)
            ws.Range(ws.Cells(fila, 4), ws.Cells(fila, 4)).Interior.Color = RGB(255, 255, 255)
            ws.Range(ws.Cells(fila, 6), ws.Cells(fila, 6)).Interior.Color = RGB(255, 255, 255)
            ws.Range(ws.Cells(fila, 7), ws.Cells(fila, 7)).Interior.Color = RGB(255, 255, 255)
        End If

        ws.Rows(fila).RowHeight = 32
        fila = fila + 1
    Next p

    ' === BOTÓN ACTUALIZAR HOJAS ===
    Dim filaBton As Integer
    filaBton = fila + 1

    Dim btn As Object
    Set btn = ws.Buttons.Add( _
        ws.Cells(filaBton, 4).Left, _
        ws.Cells(filaBton, 4).Top + 4, _
        ws.Range(ws.Cells(filaBton, 4), ws.Cells(filaBton, 5)).Width, _
        30)
    btn.OnAction = "ActualizarHojas"
    btn.Caption = "  ACTUALIZAR HOJAS DE CONFIGURACION  "
    btn.Font.Bold = True
    btn.Font.Size = 11

    ws.Rows(filaBton).RowHeight = 38

    ' === AJUSTAR ANCHOS ===
    ws.Columns("A").ColumnWidth = 5
    ws.Columns("B").ColumnWidth = 12
    ws.Columns("C").ColumnWidth = 14
    ws.Columns("D").ColumnWidth = 58
    ws.Columns("E").ColumnWidth = 30
    ws.Columns("F").ColumnWidth = 14
    ws.Columns("G").ColumnWidth = 20

    ' === PROTEGER HOJA (solo col E editable) ===
    ws.Cells.Locked = True
    ws.Range("E" & FILA_INICIO & ":E" & FILA_FIN).Locked = False
    ws.Protect Password:=PASS_FORMULARIO, DrawingObjects:=False, Contents:=True, Scenarios:=True

    ' Congelar encabezados
    ws.Activate
    ws.Range("A4").Select
    ActiveWindow.FreezePanes = True
End Sub

' ============================================================
' AGREGAR VALIDACIÓN SEGÚN TIPO DE RESPUESTA
' ============================================================
Private Sub AgregarValidacion(ws As Worksheet, fila As Integer, tipo As String, wb As Workbook)
    Dim celda As Range
    Set celda = ws.Cells(fila, COL_RESPUESTA)

    celda.Validation.Delete

    Select Case tipo
        Case "TEXTO"
            celda.Interior.Color = RGB(255, 255, 204)  ' Amarillo claro
            celda.HorizontalAlignment = xlLeft
            celda.VerticalAlignment = xlCenter

        Case "NUMERO"
            With celda.Validation
                .Add Type:=xlValidateWholeNumber, AlertStyle:=xlValidAlertStop, _
                     Operator:=xlGreater, Formula1:="0"
                .ErrorTitle = "Valor inválido"
                .ErrorMessage = "Ingrese un número entero mayor a cero."
                .ShowError = True
            End With
            celda.Interior.Color = RGB(255, 255, 204)
            celda.HorizontalAlignment = xlCenter
            celda.NumberFormat = "0"

        Case "SINO"
            With celda.Validation
                .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, _
                     Operator:=xlBetween, Formula1:="Sí,No"
                .ErrorTitle = "Selección inválida"
                .ErrorMessage = "Seleccione Sí o No de la lista desplegable."
                .ShowError = True
                .ShowDropDown = False
            End With
            celda.Interior.Color = RGB(204, 255, 204)  ' Verde claro
            celda.HorizontalAlignment = xlCenter

        Case "LISTA_CONFIG"
            ' Para listas configurables se deja como texto libre con color diferente
            ' (el usuario consulta la hoja BaseDatos)
            celda.Interior.Color = RGB(204, 229, 255)  ' Azul claro
            celda.HorizontalAlignment = xlLeft
            With celda.Comment
                ' Limpiar comentario anterior
            End With
            On Error Resume Next
            celda.Comment.Delete
            On Error GoTo 0
            celda.AddComment "Consulte la hoja 'BaseDatos' para ver las opciones disponibles. " & _
                             "Puede escribir múltiples valores separados por coma."
            celda.Comment.Visible = False

        Case "SINO_LISTA"
            ' Sí/No primero, si es Sí se espera detalle adicional
            With celda.Validation
                .Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, _
                     Operator:=xlBetween, Formula1:="Sí,No,Sí - ver detalle"
                .ShowDropDown = False
            End With
            celda.Interior.Color = RGB(255, 229, 204)  ' Naranja claro
            celda.HorizontalAlignment = xlCenter
    End Select

    celda.VerticalAlignment = xlCenter
End Sub

' ============================================================
' OBTENER COLOR POR MÓDULO
' ============================================================
Private Function ObtenerColorModulo(modulo As String) As Long
    Select Case modulo
        Case "Proyecto"       : ObtenerColorModulo = RGB(237, 125, 49)
        Case "GL"             : ObtenerColorModulo = RGB(68, 114, 196)
        Case "AP"             : ObtenerColorModulo = RGB(84, 130, 53)
        Case "AR"             : ObtenerColorModulo = RGB(197, 90, 17)
        Case "AA"             : ObtenerColorModulo = RGB(91, 155, 213)
        Case "FM"             : ObtenerColorModulo = RGB(192, 0, 0)
        Case "FI"             : ObtenerColorModulo = RGB(0, 128, 0)
        Case "CO-GL"          : ObtenerColorModulo = RGB(255, 153, 0)
        Case "ICO"            : ObtenerColorModulo = RGB(0, 112, 192)
        Case "SD"             : ObtenerColorModulo = RGB(112, 48, 160)
        Case "Tesorería"      : ObtenerColorModulo = RGB(0, 176, 80)
        Case "Tes. Avanzada"  : ObtenerColorModulo = RGB(0, 140, 140)
        Case "CO"             : ObtenerColorModulo = RGB(150, 0, 0)
        Case "Transversal"    : ObtenerColorModulo = RGB(89, 89, 89)
        Case Else             : ObtenerColorModulo = RGB(31, 73, 125)
    End Select
End Function

' ============================================================
' CREAR TODAS LAS HOJAS DE MÓDULO (ocultas inicialmente)
' ============================================================
Private Sub CrearTodasLasHojasModulo(wb As Workbook)
    ' Definición de módulos: Nombre hoja, Módulo, Preguntas relevantes
    Dim modulos(11, 2) As String

    modulos(0, 0) = "GL - Contabilidad"
    modulos(0, 1) = "GL - Contabilidad General"
    modulos(0, 2) = "3,4,5,6,7,18,19,21,22"

    modulos(1, 0) = "AP - Ctas por Pagar"
    modulos(1, 1) = "AP - Cuentas por Pagar"
    modulos(1, 2) = "8"

    modulos(2, 0) = "AR - Ctas por Cobrar"
    modulos(2, 1) = "AR - Cuentas por Cobrar"
    modulos(2, 2) = "9"

    modulos(3, 0) = "AA - Activos Fijos"
    modulos(3, 1) = "AA - Activos Fijos"
    modulos(3, 2) = "10,11,12"

    modulos(4, 0) = "FM - Presupuesto"
    modulos(4, 1) = "FM - Gestión Financiera / Presupuesto"
    modulos(4, 2) = "13,14"

    modulos(5, 0) = "FI - Config. Financiera"
    modulos(5, 1) = "FI - Configuración Financiera"
    modulos(5, 2) = "15,16"

    modulos(6, 0) = "CO-GL - Lugares"
    modulos(6, 1) = "CO-GL - Lugares Comerciales"
    modulos(6, 2) = "17"

    modulos(7, 0) = "ICO - Intercompañía"
    modulos(7, 1) = "ICO - Operaciones Intercompañía"
    modulos(7, 2) = "20"

    modulos(8, 0) = "SD - Facturación"
    modulos(8, 1) = "SD - Facturación / Ventas"
    modulos(8, 2) = "23"

    modulos(9, 0) = "Tesorería"
    modulos(9, 1) = "Tesorería"
    modulos(9, 2) = "24,25"

    modulos(10, 0) = "Tes. Avanzada"
    modulos(10, 1) = "Tesorería Avanzada"
    modulos(10, 2) = "26,27"

    modulos(11, 0) = "CO - Centros Costo"
    modulos(11, 1) = "CO - Centros de Costo"
    modulos(11, 2) = "28"

    Dim i As Integer
    For i = 0 To 11
        Call CrearHojaModulo(wb, modulos(i, 0), modulos(i, 1), modulos(i, 2))
    Next i
End Sub

' ============================================================
' CREAR UNA HOJA DE MÓDULO
' ============================================================
Private Sub CrearHojaModulo(wb As Workbook, nombreHoja As String, titulo As String, preguntasRef As String)
    Dim ws As Worksheet
    Set ws = wb.Sheets.Add(After:=wb.Sheets(wb.Sheets.Count))
    ws.Name = nombreHoja

    Dim colorHoja As Long
    colorHoja = ObtenerColorModulo(Split(nombreHoja, " ")(0))

    ' Encabezado
    With ws.Range("A1:G1")
        .Merge
        .Value = "CONFIGURACIÓN: " & UCase(titulo)
        .Font.Bold = True
        .Font.Size = 14
        .Font.Color = RGB(255, 255, 255)
        .Interior.Color = colorHoja
        .HorizontalAlignment = xlCenter
        .VerticalAlignment = xlCenter
        .RowHeight = 38
    End With

    ' Info del proyecto (referenciada del formulario)
    With ws.Range("A2:G2")
        .Merge
        .Formula = "=""Proyecto: "" & Formulario!E4"
        .Font.Bold = True
        .Font.Size = 11
        .Font.Color = colorHoja
        .Interior.Color = RGB(242, 242, 242)
        .HorizontalAlignment = xlCenter
        .VerticalAlignment = xlCenter
        .RowHeight = 26
    End With

    ' Nota de preguntas relacionadas
    With ws.Range("A3:G3")
        .Merge
        .Value = "Esta sección se habilitó en respuesta a las preguntas: " & preguntasRef & " del formulario principal."
        .Font.Italic = True
        .Font.Size = 9
        .Font.Color = RGB(128, 128, 128)
        .Interior.Color = RGB(252, 252, 252)
        .HorizontalAlignment = xlCenter
        .RowHeight = 22
    End With

    ' Encabezados de la tabla de configuración
    Dim hdrs As Variant
    hdrs = Array("Parámetro de Configuración", "Valor Formulario", "Valor en BD", "¿Coincide?", "Observaciones", "Responsable", "Fecha")
    Dim colWidths As Variant
    colWidths = Array(35, 28, 28, 12, 30, 15, 12)

    Dim h As Integer
    For h = 0 To 6
        With ws.Cells(4, h + 1)
            .Value = hdrs(h)
            .Font.Bold = True
            .Font.Color = RGB(255, 255, 255)
            .Interior.Color = colorHoja
            .HorizontalAlignment = xlCenter
            .VerticalAlignment = xlCenter
            .WrapText = True
        End With
        ws.Columns(h + 1).ColumnWidth = colWidths(h)
    Next h
    ws.Rows(4).RowHeight = 32

    ' Filas de ejemplo (5 parámetros vacíos para diligenciar)
    Dim r As Integer
    For r = 5 To 14
        ws.Cells(r, 1).Interior.Color = IIf(r Mod 2 = 0, RGB(242, 242, 242), RGB(255, 255, 255))
        ws.Cells(r, 2).Interior.Color = RGB(255, 255, 204)  ' Valor formulario
        ws.Cells(r, 3).Interior.Color = RGB(204, 229, 255)  ' Valor BD
        ws.Cells(r, 5).Interior.Color = RGB(252, 252, 252)  ' Observaciones
        ws.Rows(r).RowHeight = 26

        ' Fórmula en col D: ¿Coincide?
        ws.Cells(r, 4).Formula = "=IF(AND(B" & r & "<>"""",C" & r & "<>""""),IF(B" & r & "=C" & r & ",""✅ Sí"",""❌ No""),"""")"
        ws.Cells(r, 4).HorizontalAlignment = xlCenter
        ws.Cells(r, 7).NumberFormat = "dd/mm/yyyy"
    Next r

    ' Botón volver al formulario
    Dim btn As Object
    Set btn = ws.Buttons.Add(ws.Cells(1, 1).Left, ws.Cells(1, 1).Top, 160, 22)
    btn.OnAction = "IrAlFormulario"
    btn.Caption = "< Volver al Formulario"
    btn.Font.Size = 9

    ' Ocultar la hoja (se mostrará con ActualizarHojas)
    ws.Visible = xlSheetVeryHidden
End Sub

' ============================================================
' ACTUALIZAR HOJAS SEGÚN RESPUESTAS (llamado por el botón)
' ============================================================
Sub ActualizarHojas()
    Dim wb As Workbook
    Set wb = ThisWorkbook

    Dim wsForm As Worksheet
    Set wsForm = wb.Sheets("Formulario")

    ' Desproteger para actualizar estados
    wsForm.Unprotect Password:=PASS_FORMULARIO

    ' Leer respuestas clave
    ' Nota: fila = FILA_INICIO - 1 + número de pregunta
    '       Q1=fila4, Q2=fila5, ..., Q29=fila32
    Dim r8  As String : r8  = Trim(CStr(wsForm.Cells(FILA_INICIO + 7,  COL_RESPUESTA).Value)) ' Q8  AP
    Dim r9  As String : r9  = Trim(CStr(wsForm.Cells(FILA_INICIO + 8,  COL_RESPUESTA).Value)) ' Q9  AR
    Dim r10 As String : r10 = Trim(CStr(wsForm.Cells(FILA_INICIO + 9,  COL_RESPUESTA).Value)) ' Q10 AA
    Dim r13 As String : r13 = Trim(CStr(wsForm.Cells(FILA_INICIO + 12, COL_RESPUESTA).Value)) ' Q13 FM
    Dim r15 As String : r15 = Trim(CStr(wsForm.Cells(FILA_INICIO + 14, COL_RESPUESTA).Value)) ' Q15 FI
    Dim r17 As String : r17 = Trim(CStr(wsForm.Cells(FILA_INICIO + 16, COL_RESPUESTA).Value)) ' Q17 CO-GL
    Dim r20 As String : r20 = Trim(CStr(wsForm.Cells(FILA_INICIO + 19, COL_RESPUESTA).Value)) ' Q20 ICO
    Dim r23 As String : r23 = Trim(CStr(wsForm.Cells(FILA_INICIO + 22, COL_RESPUESTA).Value)) ' Q23 SD
    Dim r24 As String : r24 = Trim(CStr(wsForm.Cells(FILA_INICIO + 23, COL_RESPUESTA).Value)) ' Q24 Tesorería
    Dim r26 As String : r26 = Trim(CStr(wsForm.Cells(FILA_INICIO + 25, COL_RESPUESTA).Value)) ' Q26 Tes.Av
    Dim r28 As String : r28 = Trim(CStr(wsForm.Cells(FILA_INICIO + 27, COL_RESPUESTA).Value)) ' Q28 CO

    ' Actualizar indicadores de estado en col F
    Call RefrescarEstados(wsForm)

    ' GL - Siempre visible (contiene preguntas base)
    Call ToggleHoja(wb, "GL - Contabilidad", True)

    ' FI - Siempre visible
    Call ToggleHoja(wb, "FI - Config. Financiera", True)

    ' AP: solo si Q8 = Sí
    Call ToggleHoja(wb, "AP - Ctas por Pagar", (r8 = "Sí"))

    ' AR: solo si Q9 = Sí
    Call ToggleHoja(wb, "AR - Ctas por Cobrar", (r9 = "Sí"))

    ' AA: solo si Q10 = Sí
    Call ToggleHoja(wb, "AA - Activos Fijos", (r10 = "Sí"))

    ' FM: solo si Q13 = Sí
    Call ToggleHoja(wb, "FM - Presupuesto", (r13 = "Sí"))

    ' CO-GL: solo si Q17 empieza con "Sí"
    Call ToggleHoja(wb, "CO-GL - Lugares", (Left(r17, 2) = "Sí"))

    ' ICO: si Q20 tiene algún valor
    Call ToggleHoja(wb, "ICO - Intercompañía", (r20 <> ""))

    ' SD: solo si Q23 = Sí
    Call ToggleHoja(wb, "SD - Facturación", (r23 = "Sí"))

    ' Tesorería: si Q24 tiene valor
    Call ToggleHoja(wb, "Tesorería", (r24 <> ""))

    ' Tes. Avanzada: si Q26 = Sí
    Call ToggleHoja(wb, "Tes. Avanzada", (r26 = "Sí"))

    ' CO: si Q28 tiene valor
    Call ToggleHoja(wb, "CO - Centros Costo", (r28 <> ""))

    ' Volver a proteger
    wsForm.Protect Password:=PASS_FORMULARIO, DrawingObjects:=False, Contents:=True, Scenarios:=True

    ' Resumen de hojas habilitadas
    Dim resumen As String
    resumen = "Hojas habilitadas:" & Chr(13)
    resumen = resumen & " GL - Contabilidad (siempre activa)" & Chr(13)
    resumen = resumen & " FI - Config. Financiera (siempre activa)" & Chr(13)
    If r8 = "Sí"         Then resumen = resumen & " AP - Cuentas por Pagar" & Chr(13)
    If r9 = "Sí"         Then resumen = resumen & " AR - Cuentas por Cobrar" & Chr(13)
    If r10 = "Sí"        Then resumen = resumen & " AA - Activos Fijos" & Chr(13)
    If r13 = "Sí"        Then resumen = resumen & " FM - Presupuesto" & Chr(13)
    If Left(r17, 2) = "Sí" Then resumen = resumen & " CO-GL - Lugares Comerciales" & Chr(13)
    If r20 <> ""         Then resumen = resumen & " ICO - Intercompañía" & Chr(13)
    If r23 = "Sí"        Then resumen = resumen & " SD - Facturación" & Chr(13)
    If r24 <> ""         Then resumen = resumen & " Tesorería" & Chr(13)
    If r26 = "Sí"        Then resumen = resumen & " Tes. Avanzada" & Chr(13)
    If r28 <> ""         Then resumen = resumen & " CO - Centros de Costo" & Chr(13)

    MsgBox resumen, vbInformation, "Hojas Actualizadas"

    wsForm.Activate
End Sub

' ============================================================
' MOSTRAR / OCULTAR HOJA
' ============================================================
Private Sub ToggleHoja(wb As Workbook, nombre As String, mostrar As Boolean)
    On Error Resume Next
    Dim ws As Worksheet
    Set ws = wb.Sheets(nombre)
    If Not ws Is Nothing Then
        ws.Visible = IIf(mostrar, xlSheetVisible, xlSheetVeryHidden)
    End If
    On Error GoTo 0
End Sub

' ============================================================
' REFRESCAR INDICADORES DE ESTADO EN COLUMNA F
' ============================================================
Private Sub RefrescarEstados(wsForm As Worksheet)
    Dim f As Integer
    For f = FILA_INICIO To FILA_FIN
        Dim val As String
        val = Trim(CStr(wsForm.Cells(f, COL_RESPUESTA).Value))
        With wsForm.Cells(f, 6)
            If val = "" Then
                .Value = "Pendiente"
                .Font.Color = RGB(128, 128, 128)
                .Interior.Color = RGB(255, 242, 242)
            Else
                .Value = "Completado"
                .Font.Color = RGB(0, 128, 0)
                .Interior.Color = RGB(235, 250, 235)
                .Font.Bold = False
            End If
        End With
    Next f
End Sub

' ============================================================
' BOTÓN VOLVER AL FORMULARIO (usado desde hojas de módulo)
' ============================================================
Sub IrAlFormulario()
    On Error Resume Next
    ThisWorkbook.Sheets("Formulario").Activate
    On Error GoTo 0
End Sub

' ============================================================
' EVENTO CHANGE - Pegar este código en el módulo de la hoja
' "Formulario" (doble clic sobre la pestaña en el editor VBA)
'
'   Private Sub Worksheet_Change(ByVal Target As Range)
'       If Not Intersect(Target, Me.Range("E4:E32")) Is Nothing Then
'           Me.Unprotect Password:=""
'           Call RefrescarEstadosHoja(Me)
'           Me.Protect Password:="", DrawingObjects:=False, _
'                       Contents:=True, Scenarios:=True
'       End If
'   End Sub
'
'   Private Sub RefrescarEstadosHoja(ws As Worksheet)
'       Dim f As Integer
'       For f = 4 To 32
'           Dim v As String
'           v = Trim(CStr(ws.Cells(f, 5).Value))
'           With ws.Cells(f, 6)
'               If v = "" Then
'                   .Value = "Pendiente"
'                   .Font.Color = RGB(128, 128, 128)
'                   .Interior.Color = RGB(255, 242, 242)
'               Else
'                   .Value = "Completado"
'                   .Font.Color = RGB(0, 128, 0)
'                   .Interior.Color = RGB(235, 250, 235)
'               End If
'           End With
'       Next f
'   End Sub
' ============================================================
