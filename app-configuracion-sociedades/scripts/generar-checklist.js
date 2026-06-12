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

/* Recolecta transacciones y la actividad representativa de una pregunta */
function infoPregunta(p) {
  const trans = new Set();
  const actividades = new Set();
  const tablas = new Set();
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

/* Decisión que el negocio debe definir, según el tipo de pregunta */
function definicionRequerida(p) {
  if (p.tipo === "catalogo" || p.tipo === "catalogo_multiple") {
    const cat = (config.catalogos || []).find(c => c.id === p.catalogoId);
    return `Seleccionar valor(es) del catálogo${cat ? " «" + cat.nombre + "»" : ""}.`;
  }
  if (p.tipo === "texto") return "Proporcionar el dato solicitado.";
  if (p.tipo === "si_no") return "Decidir Sí / No y, si aplica, su alcance.";
  const ops = (p.opciones || []).map(o => o.texto).join(" | ");
  return "Elegir una opción: " + ops;
}

/* ===================== HOJA 1: CHECKLIST DE CONFIGURACIÓN ===================== */
const H = (v, s) => ({ v, s });
const cab = ["#", "Módulo / Sección", "Tema (pregunta a definir)", "Definición requerida del negocio",
  "Actividad de configuración SAP", "Transacción(es)", "Tabla / Campo",
  "Área responsable (negocio)", "Responsable técnico (SAP)", "Estado", "Observaciones"];

const filas1 = [cab.map(c => H(c, 1))];
let n = 0, secActual = null;
for (const sec of seccionesOrden) {
  const pregs = config.preguntas.filter(p => p.seccion === sec.id).sort((a, b) => a.orden - b.orden);
  if (!pregs.length) continue;
  // fila de sección
  filas1.push([H(nombreSec[sec.id], 3), ...Array(cab.length - 1).fill(H("", 3))]);
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
  autofiltroRef: "A1:" + "K1"
};

/* ===================== HOJA 2: DATOS MAESTROS ===================== */
const cab2 = ["#", "Objeto de dato maestro", "Descripción / alcance", "Transacción / App",
  "Área que DEFINE el dato", "Área que CREA/CARGA", "Área que APRUEBA", "Estado", "Observaciones"];
const datosMaestros = [
  ["Plan de cuentas / Cuentas de mayor", "Definición de cuentas, grupos y segmentos de sociedad", "FS00 / OB_GLACC11 / MDG-F", "Contabilidad General", "Consultor FI / Equipo MDG", "Gerencia de Contabilidad", "Considerar número de cuenta alternativo (plan local)."],
  ["Business Partner – Proveedores", "Datos generales, rol FLVN00/FLVN01, datos de sociedad y compras", "BP / MDG-S", "Cuentas por Pagar / Compras", "Equipo de Datos Maestros", "Cuentas por Pagar", "CVI activo: integra proveedor FI y MM."],
  ["Business Partner – Clientes", "Datos generales, rol FLCU00/FLCU01, datos de sociedad y ventas", "BP / MDG-C", "Cartera / Comercial", "Equipo de Datos Maestros", "Crédito y Cartera", "Asignar procedimiento de reclamación y datos de crédito."],
  ["Maestro de Bancos propios y Casa de bancos", "Claves de banco, cuentas bancarias (BAM)", "FI01 / FI12 / App Gestionar cuentas de banco", "Tesorería", "Consultor FI / Tesorería", "Gerencia de Tesorería", "Definir cuentas de mayor por banco y transitorias."],
  ["Maestro de Materiales", "Vistas básicas, contabilidad, compras, ventas; tipo y grupo de materiales", "MM01 / MDG-M", "Compras / Logística", "Equipo de Datos Maestros", "Logística / Costos", "Solo si la sociedad usa MM. Definir control de precio (S/V)."],
  ["Maestro de Activos Fijos", "Altas por clase de activo, datos de valoración y amortización", "AS01 / AS91 (saldos iniciales)", "Contabilidad de Activos Fijos", "Consultor FI-AA", "Gerencia de Contabilidad", "AS91 para migración de saldos de activos."],
  ["Centros de coste y Jerarquía estándar", "Estructura organizativa de costos y responsables", "KS01 / OKEON", "Costos / Planeación", "Consultor CO", "Gerencia de Planeación", "Solicitar listado con responsables por centro."],
  ["Clases de coste (primarias/secundarias)", "En S/4HANA son cuentas de mayor tipo coste", "FS00 (tipo de cuenta)", "Costos / Contabilidad", "Consultor CO / FI", "Gerencia de Contabilidad", "Integradas al ledger universal."],
  ["Centros gestores y Posiciones presupuestarias", "Datos maestros de Funds Management", "FMSA / FMCIA", "Presupuesto", "Consultor FM", "Gerencia Financiera", "Solo si hay control presupuestal (FM)."],
  ["Maestro de Proyectos / PEP", "Definiciones de proyecto y elementos PEP", "CJ20N / CJ01", "Gerencia de Proyectos", "Consultor PS", "PMO", "Solo si la sociedad usa PS."],
  ["Tipos de cambio (cotizaciones)", "Tasas por tipo de cotización y moneda", "OB08 / TCURR", "Tesorería / Contabilidad", "Consultor FI / Tesorería", "Gerencia de Tesorería", "Mantener para todas las monedas paralelas/operativas."],
  ["Condiciones de pago", "Términos de pago de clientes y proveedores", "OBB8", "Tesorería / Cartera", "Consultor FI", "Gerencia Financiera", "Compartidas entre AP y AR."],
  ["Indicadores e impuestos / Retenciones", "Códigos de IVA y de retención y sus cuentas", "FTXP / tablas T059", "Área Tributaria", "Consultor FI (Tax)", "Gerencia de Impuestos", "Levantar matriz tributaria del país."],
  ["Empleados / Usuarios y autorizaciones", "Roles y autorizaciones por área", "SU01 / PFCG", "Seguridad / RRHH", "Equipo de Seguridad (BASIS/GRC)", "Dueños de proceso", "Definir matriz de segregación de funciones (SoD)."]
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
  cols: [4, 32, 40, 28, 26, 26, 24, 12, 38],
  filas: filas2,
  autofiltroRef: "A1:I1"
};

/* ===================== HOJA 3: ÁREAS Y RESPONSABILIDADES ===================== */
const cab3 = ["Área / Rol", "Tipo", "Responsabilidad principal en la creación de la sociedad"];
const areas = [
  ["PMO / Líder de Finanzas", "Negocio", "Coordina el levantamiento, valida alcance y aprueba definiciones generales."],
  ["Contabilidad General", "Negocio", "Define plan de cuentas, estructura de balance, períodos, validaciones y cierre."],
  ["Área Tributaria / Impuestos", "Negocio", "Define matriz de IVA, retenciones, lugares comerciales y facturación electrónica."],
  ["Cuentas por Pagar", "Negocio", "Define proveedores, condiciones de pago, programa de pagos y anticipos."],
  ["Cartera / Crédito y Cobranza", "Negocio", "Define clientes, gestión de crédito, reclamaciones y anticipos."],
  ["Contabilidad de Activos Fijos", "Negocio", "Define clases de activos, vidas útiles y plan de valoración."],
  ["Costos / Planeación", "Negocio", "Define centros de coste, órdenes internas y modelo de costeo."],
  ["Presupuesto / Planeación Financiera", "Negocio", "Define estructura presupuestal, control de disponibilidad y CAPEX/OPEX."],
  ["Gerencia de Proyectos / PMO", "Negocio", "Define estructura de proyectos y capitalización de inversiones."],
  ["Tesorería", "Negocio", "Define bancos, medios de pago, conciliación, liquidez e instrumentos financieros."],
  ["Comercial / Facturación", "Negocio", "Define estructura de ventas, precios y facturación."],
  ["Compras / Logística", "Negocio", "Define centros, almacenes, valoración de inventarios y tolerancias."],
  ["Mantenimiento", "Negocio", "Define centros de planificación y órdenes de mantenimiento."],
  ["Equipo de Datos Maestros / MDG", "Negocio/TI", "Gobierna creación y calidad de BP, materiales y cuentas centralizadas."],
  ["Consultores funcionales SAP (por módulo)", "Técnico", "Ejecutan la parametrización en SPRO y validan con el negocio."],
  ["Equipo de Migración de Datos", "Técnico", "Ejecuta cargas (Migration Cockpit), concilia saldos y datos maestros."],
  ["Seguridad / BASIS / GRC", "Técnico", "Crea usuarios, roles y la matriz de segregación de funciones."]
];
const filas3 = [cab3.map(c => H(c, 1))];
areas.forEach(a => filas3.push([H(a[0], 2), H(a[1], 2), H(a[2], 2)]));
const hoja3 = {
  nombre: "Áreas y Responsabilidades",
  cols: [38, 14, 70],
  filas: filas3,
  autofiltroRef: "A1:C1"
};

/* ===================== HOJA 4: INSTRUCCIONES ===================== */
const filas4 = [
  [H("Checklist de configuración — Nueva sociedad SAP S/4HANA", 4)],
  [H("", 0)],
  [H("Generado automáticamente desde el catálogo de preguntas de la app low-code (" + config.preguntas.length + " preguntas, " + config.secciones.length + " módulos/secciones).", 0)],
  [H("", 0)],
  [H("Cómo usar este archivo:", 1)],
  [H("1. Hoja «Checklist Configuración»: una fila por cada definición requerida, con la actividad SAP, la transacción y el área responsable. Use la columna Estado (Pendiente / En proceso / Listo / N/A) para hacer seguimiento.", 2)],
  [H("2. Hoja «Datos Maestros»: objetos de datos maestros a definir y cargar, con el área que define, crea y aprueba cada uno.", 2)],
  [H("3. Hoja «Áreas y Responsabilidades»: glosario de áreas de negocio y técnicas involucradas.", 2)],
  [H("", 0)],
  [H("Notas:", 1)],
  [H("• Las filas se generan a partir de las preguntas vigentes; si agrega o edita preguntas en la app, vuelva a generar el checklist con: node scripts/generar-checklist.js", 2)],
  [H("• Los nombres de áreas son una propuesta estándar; ajústelos a la estructura organizacional de su compañía.", 2)],
  [H("• La parametrización debe ejecutarse y validarse en SAP por personal funcional, siguiendo la estrategia de transportes del proyecto.", 2)]
];
const hoja4 = { nombre: "Instrucciones", cols: [120], filas: filas4 };

/* ===================== GENERAR ===================== */
const salida = path.join(ROOT, "checklist", "Checklist_Configuracion_Sociedad_SAP.xlsx");
fs.mkdirSync(path.dirname(salida), { recursive: true });
construirXLSX([hoja4, hoja1, hoja2, hoja3], salida);
console.log("Checklist generado:", salida);
console.log("Hoja Checklist:", filas1.length - 1, "filas |", n, "tareas de configuración");
console.log("Hoja Datos Maestros:", datosMaestros.length, "objetos");
console.log("Hoja Áreas:", areas.length, "áreas/roles");
