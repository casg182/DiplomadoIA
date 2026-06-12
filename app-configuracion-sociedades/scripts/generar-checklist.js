"use strict";
/* Genera el checklist en Excel a partir del catálogo de preguntas.
   Uso: node scripts/generar-checklist.js */
const fs = require("fs");
const path = require("path");
const { construirXLSX } = require("./xlsx-lite");

const ROOT = path.join(__dirname, "..");
const config = JSON.parse(fs.readFileSync(path.join(ROOT, "data/configuracion-default.json"), "utf8"));

/* Áreas responsables por sección/módulo: [responsable funcional de negocio, responsable técnico SAP] */
const AREAS = {
  general:     ["PMO / Líder de Finanzas", "Consultor FI / Líder funcional"],
  contable:    ["Contabilidad General", "Consultor FI-GL"],
  impuestos:   ["Área Tributaria / Impuestos", "Consultor FI (Tax)"],
  ap:          ["Cuentas por Pagar", "Consultor FI-AP"],
  ar:          ["Cartera / Crédito y Cobranza", "Consultor FI-AR"],
  aa:          ["Contabilidad de Activos Fijos", "Consultor FI-AA"],
  controlling: ["Costos / Planeación", "Consultor CO"],
  fm:          ["Presupuesto / Planeación Financiera", "Consultor FM"],
  ps:          ["Gerencia de Proyectos / PMO", "Consultor PS"],
  tr:          ["Tesorería", "Consultor TR / TRM"],
  sd:          ["Comercial / Facturación", "Consultor SD"],
  mm:          ["Compras / Logística", "Consultor MM"],
  pm:          ["Mantenimiento", "Consultor PM"],
  documentos:  ["Contabilidad General", "Consultor FI"]
};

const nombreSec = {};
config.secciones.forEach(s => nombreSec[s.id] = s.nombre);
const seccionesOrden = [...config.secciones].sort((a, b) => a.orden - b.orden);
const H = (v, s) => ({ v, s });

/* Recolecta transacciones y la actividad representativa de una pregunta */
function infoPregunta(p) {
  const trans = new Set(), actividades = new Set(), tablas = new Set();
  const recoger = m => {
    if (!m) return;
    if (m.transaccion && m.transaccion !== "-") m.transaccion.split(/[\/+]/).forEach(t => { const x = t.trim(); if (x && x !== "-") trans.add(x); });
    if (m.descripcionConfig && !/^sin /i.test(m.descripcionConfig)) actividades.add(m.descripcionConfig);
    if (m.tablaCampo && m.tablaCampo !== "-") tablas.add(m.tablaCampo);
  };
  if (p.mapeoDirecto) recoger(p.mapeoDirecto);
  (p.opciones || []).forEach(o => recoger(o.mapeo));
  return {
    transacciones: [...trans].join(", ") || "-",
    actividades: [...actividades].join("; ") || "-",
    tablas: [...tablas].join(", ") || "-"
  };
}

function definicionRequerida(p) {
  if (p.tipo === "catalogo" || p.tipo === "catalogo_multiple") {
    const cat = (config.catalogos || []).find(c => c.id === p.catalogoId);
    return `Seleccionar valor(es) del catálogo${cat ? " «" + cat.nombre + "»" : ""}.`;
  }
  if (p.tipo === "texto") return "Proporcionar el dato solicitado.";
  if (p.tipo === "si_no") return "Decidir Sí / No y, si aplica, su alcance.";
  return "Elegir una opción: " + (p.opciones || []).map(o => o.texto).join(" | ");
}

/* ===================== HOJA: CHECKLIST DE CONFIGURACIÓN ===================== */
const cab1 = ["#", "Módulo / Sección", "Tema (pregunta a definir)", "Definición requerida del negocio",
  "Actividad de configuración SAP", "Transacción(es)", "Tabla / Campo",
  "Área responsable (negocio)", "Responsable técnico (SAP)", "Estado", "Observaciones"];
const filas1 = [cab1.map(c => H(c, 1))];
let n = 0;
for (const sec of seccionesOrden) {
  const pregs = config.preguntas.filter(p => p.seccion === sec.id).sort((a, b) => a.orden - b.orden);
  if (!pregs.length) continue;
  filas1.push([H(nombreSec[sec.id], 3), ...Array(cab1.length - 1).fill(H("", 3))]);
  const [areaNeg, areaTec] = AREAS[sec.id] || ["", ""];
  for (const p of pregs) {
    n++;
    const info = infoPregunta(p);
    filas1.push([
      H(String(n), 2), H(nombreSec[sec.id], 2), H(p.texto, 2), H(definicionRequerida(p), 2),
      H(info.actividades, 2), H(info.transacciones, 2), H(info.tablas, 2),
      H(areaNeg, 2), H(areaTec, 2), H("Pendiente", 2), H(p.ayuda || "", 2)
    ]);
  }
}
const hoja1 = {
  nombre: "Checklist Configuración",
  cols: [4, 26, 40, 34, 40, 22, 20, 26, 22, 12, 34],
  filas: filas1,
  autofiltroRef: "A1:K1"
};

/* ===================== HOJA: DETALLE DATOS MAESTROS =====================
   Nivel de campo/decisión por objeto: lo que debe estar DEFINIDO y CARGADO
   para que la sociedad pueda contabilizar. */
const cabD = ["#", "Objeto", "Definición de detalle requerida", "Información que debe entregar el negocio",
  "Transacción / App", "Área que DEFINE", "Área que CREA/CARGA", "Estado", "Observaciones"];

/* [objeto, definición, info a entregar, transacción, define, carga, observaciones] */
const detalle = [
  /* ---------- CECO: Centros de coste ---------- */
  ["CECO – Centros de coste", "Máscara y rango de codificación de CECOs", "Estándar de codificación (longitud, prefijo por sociedad/área, ej. C001-1010)", "Definición de proyecto", "Costos / Planeación", "Consultor CO", "Debe ser coherente entre todas las sociedades del grupo."],
  ["CECO – Centros de coste", "Jerarquía estándar (nodos por gerencia / vicepresidencia / área)", "Organigrama vigente con niveles de agregación para reportes", "OKEON", "Costos / Planeación", "Consultor CO", "La jerarquía estándar es obligatoria antes de crear el primer CECO."],
  ["CECO – Centros de coste", "Listado de CECOs con datos completos por centro", "Por cada CECO: código, denominación, responsable (nombre/usuario), clase de centro (producción, administración, ventas, servicios), área funcional, moneda, CeBe asignado, fecha de validez", "KS01 / KS02 (masivo: app Fiori o LTMC)", "Costos / Planeación", "Consultor CO / Datos Maestros", "Sin CeBe asignado en el maestro, la derivación CECO→CeBe falla al contabilizar."],
  ["CECO – Centros de coste", "Grupos alternativos de CECOs para reportes y autorizaciones", "Agrupaciones por gerencia, proyecto o naturaleza para reporting y roles", "KSH1", "Costos / Planeación", "Consultor CO", "Opcional pero recomendado para reportes y restricción de autorizaciones."],
  ["CECO – Centros de coste", "Bloqueos y restricciones por CECO", "Qué CECOs aceptan imputaciones primarias, secundarias, ingresos o compromisos", "KS02 (pestaña Control)", "Costos / Planeación", "Consultor CO", "Evita imputaciones erradas (ej. ingresos en centros administrativos)."],
  ["CECO – Centros de coste", "Ciclos de distribución / subreparto (si aplica)", "Reglas de reparto de costes indirectos: emisores, receptores, criterios (%/estadísticos)", "KSV1 / KSU1", "Costos / Planeación", "Consultor CO", "Definir si el modelo de costeo lo requiere desde el arranque."],

  /* ---------- CEBE: Centros de beneficio ---------- */
  ["CEBE – Centros de beneficio", "Máscara y rango de codificación de CEBEs", "Estándar de codificación por línea/unidad de negocio o región", "Definición de proyecto", "Costos / Planeación", "Consultor CO/FI", "Coherente con el modelo de rentabilidad del grupo."],
  ["CEBE – Centros de beneficio", "Jerarquía estándar de CEBEs", "Estructura de líneas/unidades de negocio con niveles de agregación", "KCH1 / KCH5N", "Costos / Planeación", "Consultor CO/FI", "Asignada en la sociedad CO (0KE5)."],
  ["CEBE – Centros de beneficio", "Listado de CEBEs con datos completos", "Por cada CeBe: código, denominación, responsable, segmento asignado, sociedad(es) válida(s), fecha de validez", "KE51 / KE52", "Costos / Planeación", "Consultor CO/FI", "El segmento se deriva del CeBe: si falta, el desglose por segmento falla."],
  ["CEBE – Centros de beneficio", "CeBe dummy / por defecto", "CeBe a usar cuando ninguna regla deriva un valor (ej. código de la sociedad)", "KE51 + FAGL3KEH", "Costos / Planeación", "Consultor CO/FI", "Obligatorio si el desglose exige CeBe en toda partida."],
  ["CEBE – Centros de beneficio", "Reglas de derivación de CeBe", "Matriz: CECO→CeBe (maestro KS02), material/centro→CeBe (maestro MM), cuenta→CeBe por defecto (FAGL3KEH), orden CO→CeBe", "KS02 / MM02 / FAGL3KEH", "Costos / Planeación", "Consultor CO/FI", "Probar con asientos de cada proceso (compras, ventas, nómina, manual)."],

  /* ---------- BP: Business Partners ---------- */
  ["BP – General", "Agrupaciones de BP y rangos de números", "Agrupaciones (proveedor nacional, exterior, empleado, cliente nacional, exterior, ICO) y si la numeración es interna o externa", "BUCF + customizing BP", "Datos Maestros / Finanzas", "Consultor FI / MDG", "La agrupación determina el rango y los campos obligatorios."],
  ["BP – General", "Sincronización BP ↔ proveedor/cliente (CVI)", "Verificar que la integración CVI esté activa y los rangos enlazados", "Customizing CVI", "TI / Datos Maestros", "Consultor técnico", "En S/4HANA es obligatorio operar vía BP, no FK01/FD01."],
  ["BP – Proveedores", "Datos generales por proveedor", "Razón social, identificación fiscal (NIT/RFC/RUC con dígito de verificación), tipo de identificación, dirección completa, contacto, idioma", "BP (rol 000000)", "Cuentas por Pagar / Compras", "Datos Maestros", "La identificación fiscal alimenta reportes legales (medios magnéticos, DIOT, etc.)."],
  ["BP – Proveedores", "Rol FI (FLVN00): datos de sociedad", "Por proveedor y sociedad: cuenta asociada, condiciones de pago, vías de pago permitidas, banco propio por defecto, datos bancarios del proveedor (banco, cuenta, IBAN), indicadores de retención aplicables, bloqueos", "BP (rol FLVN00)", "Cuentas por Pagar", "Datos Maestros", "Sin cuenta asociada NO se puede contabilizar ninguna factura al proveedor."],
  ["BP – Proveedores", "Rol Compras (FLVN01): datos de organización de compras", "Org. de compras, moneda de pedido, condiciones de pago de compras, incoterms, verificación de factura basada en EM", "BP (rol FLVN01)", "Compras", "Datos Maestros", "Solo si la sociedad usa MM."],
  ["BP – Clientes", "Datos generales por cliente", "Razón social, identificación fiscal, dirección fiscal y de entrega, contactos, clasificación fiscal", "BP (rol 000000)", "Cartera / Comercial", "Datos Maestros", "La clasificación fiscal determina el IVA en ventas."],
  ["BP – Clientes", "Rol FI (FLCU00): datos de sociedad", "Cuenta asociada, condiciones de pago, procedimiento de reclamación (dunning), persona de cobranza, bloqueos", "BP (rol FLCU00)", "Cartera", "Datos Maestros", "Sin cuenta asociada NO se puede facturar ni contabilizar al cliente."],
  ["BP – Clientes", "Rol Ventas (FLCU01): datos de área de ventas", "Org. de ventas/canal/sector, zona de ventas, grupo de precios, condiciones de expedición, clasificación fiscal por categoría", "BP (rol FLCU01)", "Comercial", "Datos Maestros", "Solo si la sociedad usa SD."],
  ["BP – Clientes", "Datos de crédito (FSCM)", "Segmento de crédito, límite de crédito, clase de riesgo, reglas de verificación", "BP (rol UKM000) / UKM_MY_DCDS", "Crédito y Cobranza", "Consultor FI-AR", "Solo si se activó gestión de crédito."],

  /* ---------- Cuentas de mayor ---------- */
  ["Cuentas de mayor", "Segmento de sociedad por cada cuenta del plan", "Por cuenta: moneda, gestión de partidas abiertas/visualización individual, grupo de status de campo, clave de clasificación (sort key), relevancia de flujo de caja, indicador de impuestos permitido", "FS00 / OB_GLACC11 (masivo)", "Contabilidad General", "Consultor FI-GL", "Una cuenta sin segmento de sociedad bloquea cualquier asiento que la use."],
  ["Cuentas de mayor", "Cuentas asociadas (reconciliation accounts)", "Cuentas de deudores, acreedores y activos fijos por tipo (nacional, exterior, ICO, anticipos CME)", "FS00 (tipo cuenta asociada) + OBYR/OBXR", "Contabilidad General", "Consultor FI", "Definirlas ANTES de crear BPs: el BP exige la cuenta asociada."],
  ["Cuentas de mayor", "Cuentas técnicas y de operación obligatorias", "Retención de beneficios (OB53), diferencias de cambio realizadas/no realizadas (OBA1), redondeo, compensación EM/RF (WRX/GR-IR), diferencias menores, cuentas puente de migración, bancos transitorias", "OB53 / OBA1 / OBYC / FS00", "Contabilidad General", "Consultor FI", "Sin OB53 no se puede cerrar el primer ejercicio; sin OBA1 no compensan partidas en moneda extranjera."],
  ["Cuentas de mayor", "Clasificación de cuentas para el desglose de documentos", "Categoría de posición por rango de cuentas (deudores, acreedores, impuestos, bancos, materiales, PyG)", "SPRO (desglose) ", "Contabilidad General", "Consultor FI-GL", "Solo si hay document splitting: una cuenta sin clasificar bloquea el asiento."],

  /* ---------- Activos fijos ---------- */
  ["Activos fijos", "Intervalos de numeración por clase de activo", "Rango de números interno por cada clase (terrenos, edificios, maquinaria, vehículos, cómputo, AeC...)", "AS08", "Contab. Activos Fijos", "Consultor FI-AA", "Los rangos no se transportan."],
  ["Activos fijos", "Determinación de cuentas por clase", "Cuentas de coste de adquisición, amortización acumulada, gasto de amortización, bajas, utilidad/pérdida en venta", "AO90", "Contab. Activos Fijos", "Consultor FI-AA", "Una clase sin determinación de cuentas impide capitalizar."],
  ["Activos fijos", "Matriz de vidas útiles y claves de amortización", "Por clase y por área de valoración (local/NIIF/fiscal): método, vida útil, valor residual, inicio de amortización", "AFAMA + maestro AS01", "Contab. Activos Fijos", "Consultor FI-AA", "Validar con políticas contables y normativa fiscal del país."],

  /* ---------- Bancos ---------- */
  ["Bancos", "Claves de banco del país", "Catálogo de bancos con código ACH/ABA/SWIFT según el país", "FI01 (o carga del directorio bancario)", "Tesorería", "Consultor FI / Basis", "Puede cargarse el directorio bancario oficial del país."],
  ["Bancos", "Bancos propios y cuentas bancarias (BAM)", "Por cuenta: banco, número de cuenta/IBAN, moneda, descripción, firmantes/aprobadores, cuenta de mayor principal", "FI12 / App Gestionar cuentas de banco", "Tesorería", "Consultor TR", "En S/4HANA las cuentas son datos maestros con flujo de aprobación (BAM)."],
  ["Bancos", "Cuentas contables transitorias por vía de pago", "Estructura de cuentas: principal + transitorias (cheques emitidos, transferencias salientes, entradas) por banco", "FS00 + FBZP", "Tesorería / Contabilidad", "Consultor TR/FI", "Necesarias para conciliación automática del extracto."],

  /* ---------- Parametrizaciones operativas para poder contabilizar ---------- */
  ["Operación contable", "Grupos de tolerancia de empleados y asignación de usuarios", "Importe máximo por documento, por partida y % de descuento permitido por grupo de usuarios; asignar usuarios a grupos", "OBA4 + OB57", "Contabilidad General", "Consultor FI", "SIN GRUPO DE TOLERANCIA NADIE PUEDE CONTABILIZAR. Definir grupo en blanco o por usuario."],
  ["Operación contable", "Tolerancias de compensación para BPs", "Diferencias permitidas al compensar partidas de clientes/proveedores", "OBA3", "Contabilidad General", "Consultor FI", "Requerida para compensaciones (F-32/F-44) y pagos."],
  ["Operación contable", "Clases de documento y claves de contabilización", "Verificar clases estándar (SA, KR, KZ, DR, DZ, AB...) y claves (40/50, 31/21, 01/11...) o definir propias", "OBA7 / OB41", "Contabilidad General", "Consultor FI", "Cada clase debe tener rango de números asignado en la sociedad."],
  ["Operación contable", "Indicadores de impuestos por defecto para cuentas sin impuesto", "Indicadores de entrada/salida 0% para operaciones no gravadas", "OBCL", "Área Tributaria", "Consultor FI", "Sin esto fallan asientos en cuentas marcadas como relevantes de impuesto."],
  ["Operación contable", "Tipos de cambio y cotizaciones iniciales", "Tipos de cotización (M, compra, venta, cierre) y tasas vigentes para todas las monedas operativas", "OB08 / TCURR", "Tesorería", "Consultor FI", "Definir responsable y frecuencia de actualización (manual o interfaz)."],
  ["Operación contable", "Apertura de períodos contables y de CO", "Período actual abierto para todas las clases de cuenta (+, A, D, K, M, S) y períodos CO", "OB52 + OKP1", "Contabilidad General", "Consultor FI/CO", "Definir gobierno mensual de apertura/cierre."]
];

const filasD = [cabD.map(c => H(c, 1))];
let objActual = null, nd = 0;
for (const d of detalle) {
  if (d[0] !== objActual) {
    objActual = d[0];
    filasD.push([H(objActual, 3), ...Array(cabD.length - 1).fill(H("", 3))]);
  }
  nd++;
  filasD.push([
    H(String(nd), 2), H(d[0], 2), H(d[1], 2), H(d[2], 2), H(d[3], 2),
    H(d[4], 2), H(d[5], 2), H("Pendiente", 2), H(d[6], 2)
  ]);
}
const hojaD = {
  nombre: "Detalle Datos Maestros",
  cols: [4, 24, 36, 52, 24, 22, 22, 12, 42],
  filas: filasD,
  autofiltroRef: "A1:I1"
};

/* ===================== HOJA: ARRANQUE 1ER ASIENTO =====================
   Secuencia ordenada de verificación: todo lo que debe estar listo para
   que la sociedad contabilice su primer documento. */
const cabA = ["Paso", "Verificación (criterio de aceptación)", "Transacción / Evidencia", "Responsable", "Bloqueante", "Estado"];
const arranque = [
  ["Sociedad creada con datos completos (razón social, dirección, país, moneda, idioma)", "OX02 — T001 completa", "Consultor FI", "Sí"],
  ["Asignaciones organizativas: plan de cuentas, variante ejercicio, variante períodos, variante status campo, sociedad CO", "OB62 / OB37 / OBBP / OBC5 / OX19", "Consultor FI", "Sí"],
  ["Ledgers y monedas (10/30) verificados ANTES de cualquier asiento", "FINSC_LEDGER — revisar parametrización de moneda", "Consultor FI-GL", "Sí"],
  ["Desglose de documentos decidido y, si aplica, configurado y probado (CeBe/segmento, saldo cero)", "SPRO desglose — asiento de prueba con verificación de FAGL_SPLINFO", "Consultor FI-GL", "Sí"],
  ["Períodos contables abiertos (FI todas las clases de cuenta) y períodos CO", "OB52 / OKP1", "Contabilidad General", "Sí"],
  ["Rangos de números de documento creados para el ejercicio actual y siguiente", "FBN1 / OBH1 — verificar clases SA, KR, KZ, DR, DZ, AB", "Consultor FI", "Sí"],
  ["Clases de documento y claves de contabilización verificadas", "OBA7 / OB41", "Consultor FI", "Sí"],
  ["Cuentas de mayor creadas con segmento de sociedad (plan completo)", "FS00 / OB_GLACC11 — comparar contra plan corporativo", "Consultor FI-GL", "Sí"],
  ["Cuentas de retención de beneficios definidas", "OB53", "Consultor FI-GL", "Sí"],
  ["Cuentas de diferencia de cambio y tasas iniciales cargadas", "OBA1 + OB08", "Consultor FI / Tesorería", "Sí"],
  ["Esquema de impuestos asignado al país, indicadores IVA creados con sus cuentas", "OBBG / FTXP / OB40 — asiento de prueba con IVA", "Consultor FI (Tax)", "Sí"],
  ["Indicadores 0% por defecto para cuentas no gravadas", "OBCL", "Consultor FI (Tax)", "Sí"],
  ["Retenciones: tipos/indicadores configurados, cuentas asignadas y sociedad activada", "SPRO retención ampliada + OB_WT — simulación de factura con retención", "Consultor FI (Tax)", "Sí (si aplica)"],
  ["Grupos de tolerancia de empleados creados y usuarios asignados", "OBA4 + OB57", "Consultor FI", "Sí"],
  ["Tolerancias de compensación de BPs definidas", "OBA3", "Consultor FI", "Sí"],
  ["Jerarquía estándar y CECOs creados, con responsable y CeBe asignado", "OKEON / KS03 — muestreo de centros", "Consultor CO", "Sí (si usa CO)"],
  ["Jerarquía, CEBEs, CeBe dummy y reglas de derivación probadas", "KCH3 / KE53 / FAGL3KEH — asiento de prueba y revisión de CeBe derivado", "Consultor CO/FI", "Sí (si aplica)"],
  ["Segmentos definidos y asignados en maestros de CeBe", "Maestro KE53 campo Segmento", "Consultor FI-GL", "Sí (si aplica)"],
  ["Cuentas asociadas de deudores/acreedores/activos y CME de anticipos configuradas", "FS00 / OBYR / OBXR", "Consultor FI", "Sí"],
  ["BPs proveedores y clientes creados/extendidos a la sociedad con cuenta asociada, condiciones y vía de pago", "BP — muestreo por agrupación", "Datos Maestros", "Sí"],
  ["Bancos propios, cuentas bancarias (BAM) y cuentas contables transitorias creadas", "FI01 / FI12 / FS00", "Tesorería / Consultor TR", "Sí"],
  ["Programa de pagos configurado y probado con pago de prueba", "FBZP + F110 en QA", "Consultor FI-AP", "Sí (si aplica)"],
  ["Clases de activos, determinación de cuentas y claves de amortización listas", "OAOA / AO90 / AFAMA — alta de activo de prueba AS01", "Consultor FI-AA", "Sí (si usa AA)"],
  ["Lugares comerciales / numeración fiscal / facturación electrónica activos", "SPRO localización + EDOC_COCKPIT — documento de prueba", "Consultor FI (Tax) / SD", "Sí (si aplica)"],
  ["Saldos iniciales y partidas abiertas migrados y conciliados (cuentas puente en cero)", "LTMC + reporte de conciliación firmado", "Equipo de Migración", "Sí (si hay migración)"],
  ["Usuarios creados con roles asignados y matriz SoD validada", "SU01 / PFCG", "Seguridad (BASIS/GRC)", "Sí"],
  ["Prueba integral en QA: factura proveedor (FB60), factura cliente (FB70), asiento manual (FB50), pago (F110), extracto (FF_5), cierre de período de prueba", "Plan de pruebas firmado por el negocio", "Líder funcional + Negocio", "Sí"],
  ["Acta de aprobación de arranque (go-live) firmada por las áreas responsables", "Documento de cut-over", "PMO", "Sí"]
];
const filasA = [cabA.map(c => H(c, 1))];
arranque.forEach((a, i) => {
  filasA.push([H(String(i + 1), 2), H(a[0], 2), H(a[1], 2), H(a[2], 2), H(a[3], 5), H("Pendiente", 2)]);
});
const hojaA = {
  nombre: "Arranque 1er Asiento",
  cols: [6, 62, 38, 24, 14, 12],
  filas: filasA,
  autofiltroRef: "A1:F1"
};

/* ===================== HOJA: DATOS MAESTROS (RESUMEN) ===================== */
const cab2 = ["#", "Objeto de dato maestro", "Descripción / alcance", "Transacción / App",
  "Área que DEFINE el dato", "Área que CREA/CARGA", "Área que APRUEBA", "Estado", "Observaciones"];
const datosMaestros = [
  ["Plan de cuentas / Cuentas de mayor", "Definición de cuentas, grupos y segmentos de sociedad", "FS00 / OB_GLACC11 / MDG-F", "Contabilidad General", "Consultor FI / Equipo MDG", "Gerencia de Contabilidad", "Ver hoja «Detalle Datos Maestros» para el nivel de campo."],
  ["CECO – Centros de coste", "Jerarquía estándar, centros con responsable y CeBe, grupos alternativos", "OKEON / KS01 / KSH1", "Costos / Planeación", "Consultor CO", "Gerencia de Planeación", "Ver detalle: codificación, clases de centro, bloqueos, ciclos."],
  ["CEBE – Centros de beneficio", "Jerarquía estándar, CEBEs por línea de negocio, dummy y derivación", "KCH1 / KE51 / FAGL3KEH", "Costos / Planeación", "Consultor CO/FI", "Gerencia Financiera", "Ver detalle: segmentos asignados y reglas de derivación."],
  ["Segmentos (NIIF 8)", "Segmentos reportables asignados a los CEBEs", "SPRO (Definir segmento)", "Contabilidad / Consolidación", "Consultor FI-GL", "Gerencia de Contabilidad", "Requiere desglose de documentos para balances por segmento."],
  ["Business Partner – Proveedores", "Agrupaciones, roles 000000/FLVN00/FLVN01, datos fiscales, bancarios y de retención", "BP / MDG-S", "Cuentas por Pagar / Compras", "Equipo de Datos Maestros", "Cuentas por Pagar", "Ver detalle por rol. CVI activo obligatorio en S/4HANA."],
  ["Business Partner – Clientes", "Agrupaciones, roles 000000/FLCU00/FLCU01, crédito y reclamación", "BP / MDG-C", "Cartera / Comercial", "Equipo de Datos Maestros", "Crédito y Cartera", "Ver detalle por rol: cuenta asociada, dunning, datos de ventas."],
  ["Maestro de Bancos y cuentas (BAM)", "Claves de banco, bancos propios, cuentas con firmantes y cuentas GL vinculadas", "FI01 / FI12 / App BAM", "Tesorería", "Consultor TR / Tesorería", "Gerencia de Tesorería", "Incluye transitorias por vía de pago para conciliación."],
  ["Maestro de Materiales", "Vistas básicas, contabilidad (control de precio), compras y ventas", "MM01 / MDG-M", "Compras / Logística", "Equipo de Datos Maestros", "Logística / Costos", "Solo si la sociedad usa MM."],
  ["Maestro de Activos Fijos", "Altas por clase, valoración y amortización; saldos iniciales con AS91", "AS01 / AS91", "Contab. Activos Fijos", "Consultor FI-AA", "Gerencia de Contabilidad", "Ver detalle: intervalos, determinación de cuentas, vidas útiles."],
  ["Centros gestores y Posiciones presupuestarias", "Datos maestros de FM con jerarquías", "FMSA / FMCIA", "Presupuesto", "Consultor FM", "Gerencia Financiera", "Solo si hay control presupuestal."],
  ["Maestro de Proyectos / PEP", "Definiciones de proyecto y elementos PEP", "CJ20N / CJ01", "Gerencia de Proyectos", "Consultor PS", "PMO", "Solo si la sociedad usa PS."],
  ["Tipos de cambio", "Cotizaciones por tipo y moneda con responsable de actualización", "OB08 / TCURR", "Tesorería / Contabilidad", "Consultor FI / Tesorería", "Gerencia de Tesorería", "Para todas las monedas paralelas y operativas."],
  ["Condiciones de pago", "Términos de pago de clientes y proveedores", "OBB8", "Tesorería / Cartera", "Consultor FI", "Gerencia Financiera", "Compartidas entre AP y AR."],
  ["Indicadores de impuestos / Retenciones", "Códigos de IVA y retención con cuentas asignadas", "FTXP / OB40 / T059", "Área Tributaria", "Consultor FI (Tax)", "Gerencia de Impuestos", "Levantar matriz tributaria del país."],
  ["Usuarios y autorizaciones", "Usuarios, roles por área y matriz SoD; grupos de tolerancia asignados", "SU01 / PFCG / OB57", "Seguridad / Dueños de proceso", "Equipo de Seguridad (BASIS/GRC)", "Dueños de proceso", "Sin grupo de tolerancia el usuario no puede contabilizar."]
];
const filas2 = [cab2.map(c => H(c, 1))];
datosMaestros.forEach((d, i) => {
  filas2.push([
    H(String(i + 1), 2), H(d[0], 2), H(d[1], 2), H(d[2], 2),
    H(d[3], 2), H(d[4], 2), H(d[5], 2), H("Pendiente", 2), H(d[6], 2)
  ]);
});
const hoja2 = {
  nombre: "Datos Maestros",
  cols: [4, 32, 42, 26, 26, 26, 24, 12, 40],
  filas: filas2,
  autofiltroRef: "A1:I1"
};

/* ===================== HOJA: ÁREAS Y RESPONSABILIDADES ===================== */
const cab3 = ["Área / Rol", "Tipo", "Responsabilidad principal en la creación de la sociedad"];
const areas = [
  ["PMO / Líder de Finanzas", "Negocio", "Coordina el levantamiento, valida alcance y aprueba definiciones generales y el go-live."],
  ["Contabilidad General", "Negocio", "Define plan de cuentas, estructura de balance, períodos, validaciones, tolerancias, desglose y cierre."],
  ["Área Tributaria / Impuestos", "Negocio", "Define matriz de IVA, retenciones, lugares comerciales y facturación electrónica."],
  ["Cuentas por Pagar", "Negocio", "Define proveedores (datos FI), condiciones de pago, programa de pagos y anticipos."],
  ["Cartera / Crédito y Cobranza", "Negocio", "Define clientes (datos FI), gestión de crédito, reclamaciones y anticipos."],
  ["Contabilidad de Activos Fijos", "Negocio", "Define clases de activos, vidas útiles, plan de valoración y saldos iniciales de activos."],
  ["Costos / Planeación", "Negocio", "Define CECOs, CEBEs, jerarquías, derivaciones, órdenes internas y modelo de costeo."],
  ["Presupuesto / Planeación Financiera", "Negocio", "Define estructura presupuestal, control de disponibilidad y CAPEX/OPEX."],
  ["Gerencia de Proyectos / PMO", "Negocio", "Define estructura de proyectos y capitalización de inversiones."],
  ["Tesorería", "Negocio", "Define bancos, cuentas bancarias, medios de pago, conciliación, tipos de cambio, liquidez e instrumentos."],
  ["Comercial / Facturación", "Negocio", "Define estructura de ventas, datos de ventas de clientes, precios y facturación."],
  ["Compras / Logística", "Negocio", "Define centros, almacenes, datos de compras de proveedores, valoración y tolerancias."],
  ["Mantenimiento", "Negocio", "Define centros de planificación y órdenes de mantenimiento."],
  ["Consolidación / Reportes corporativos", "Negocio", "Define segmentos NIIF 8, CeBe corporativos y requerimientos de reporting del grupo."],
  ["Equipo de Datos Maestros / MDG", "Negocio/TI", "Gobierna creación, extensión y calidad de BP, materiales y cuentas; ejecuta cargas masivas."],
  ["Consultores funcionales SAP (por módulo)", "Técnico", "Ejecutan la parametrización en SPRO, documentan y validan con el negocio."],
  ["Equipo de Migración de Datos", "Técnico", "Ejecuta cargas (Migration Cockpit), concilia saldos y deja cuentas puente en cero."],
  ["Seguridad / BASIS / GRC", "Técnico", "Crea usuarios, roles, grupos de tolerancia y la matriz de segregación de funciones."]
];
const filas3 = [cab3.map(c => H(c, 1))];
areas.forEach(a => filas3.push([H(a[0], 2), H(a[1], 2), H(a[2], 2)]));
const hoja3 = {
  nombre: "Áreas y Responsabilidades",
  cols: [38, 14, 75],
  filas: filas3,
  autofiltroRef: "A1:C1"
};

/* ===================== HOJA: INSTRUCCIONES ===================== */
const filas4 = [
  [H("Checklist de configuración — Nueva sociedad SAP S/4HANA", 4)],
  [H("", 0)],
  [H("Generado automáticamente desde el catálogo de preguntas de la app low-code (" + config.preguntas.length + " preguntas, " + config.secciones.length + " módulos/secciones).", 0)],
  [H("", 0)],
  [H("Hojas de este libro:", 1)],
  [H("1. «Checklist Configuración»: una fila por cada definición del cuestionario, con actividad SAP, transacción y áreas responsables. Use la columna Estado (Pendiente / En proceso / Listo / N/A).", 2)],
  [H("2. «Datos Maestros»: resumen de los objetos de datos maestros con quién define, crea/carga y aprueba cada uno.", 2)],
  [H("3. «Detalle Datos Maestros»: nivel de campo y decisión por objeto — CECOs, CEBEs, BPs (por rol), cuentas, activos, bancos y parametrizaciones operativas (tolerancias, clases de documento, tipos de cambio).", 2)],
  [H("4. «Arranque 1er Asiento»: secuencia ordenada de verificación con criterios de aceptación; todos los pasos bloqueantes deben estar en «Listo» antes de contabilizar el primer documento.", 2)],
  [H("5. «Áreas y Responsabilidades»: glosario de áreas de negocio y técnicas involucradas.", 2)],
  [H("", 0)],
  [H("Notas:", 1)],
  [H("• Las filas del checklist se generan desde las preguntas vigentes; si edita preguntas en la app, regenere con: node scripts/generar-checklist.js", 2)],
  [H("• Los nombres de áreas son una propuesta estándar; ajústelos a la estructura organizacional de su compañía.", 2)],
  [H("• La parametrización debe ejecutarse y validarse en SAP por personal funcional, siguiendo la estrategia de transportes del proyecto.", 2)]
];
const hoja4 = { nombre: "Instrucciones", cols: [130], filas: filas4 };

/* ===================== GENERAR ===================== */
const salida = path.join(ROOT, "checklist", "Checklist_Configuracion_Sociedad_SAP.xlsx");
fs.mkdirSync(path.dirname(salida), { recursive: true });
construirXLSX([hoja4, hoja1, hoja2, hojaD, hojaA, hoja3], salida);
console.log("Checklist generado:", salida);
console.log("Checklist Configuración:", n, "tareas | Detalle Datos Maestros:", nd, "definiciones | Arranque:", arranque.length, "pasos | Áreas:", areas.length);
