Attribute VB_Name = "HojaFormulario"
' ============================================================
' CÓDIGO DEL MÓDULO DE LA HOJA "Formulario"
'
' INSTRUCCIONES:
'   1. En el editor VBA (Alt+F11), en el panel izquierdo
'      hacer doble clic en "Formulario" (dentro de "Hojas")
'   2. Pegar este código en la ventana que aparece
'   3. Guardar
'
' Este código actualiza el estado (Pendiente / Completado)
' automáticamente cada vez que el usuario llena una celda.
' ============================================================

Option Explicit

' Actualización automática al cambiar cualquier respuesta
Private Sub Worksheet_Change(ByVal Target As Range)
    ' Solo actuar sobre el rango de respuestas (E4:E32)
    If Not Intersect(Target, Me.Range("E4:E32")) Is Nothing Then
        Application.EnableEvents = False
        Me.Unprotect Password:=""

        Call RefrescarEstadosHoja(Me)

        Me.Protect Password:="", DrawingObjects:=False, _
                    Contents:=True, Scenarios:=True
        Application.EnableEvents = True
    End If
End Sub

' Recorre las filas y actualiza la columna F (Estado)
Private Sub RefrescarEstadosHoja(ws As Worksheet)
    Dim f As Integer
    For f = 4 To 32
        Dim v As String
        v = Trim(CStr(ws.Cells(f, 5).Value))

        With ws.Cells(f, 6)
            .Locked = True
            If v = "" Then
                .Value = "Pendiente"
                .Font.Color = RGB(150, 150, 150)
                .Font.Bold = False
                .Interior.Color = RGB(255, 242, 242)
            Else
                .Value = "Completado"
                .Font.Color = RGB(0, 128, 0)
                .Font.Bold = True
                .Interior.Color = RGB(235, 250, 235)
            End If
        End With
    Next f
End Sub
