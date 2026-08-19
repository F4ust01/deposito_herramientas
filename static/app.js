/* Depósito de Herramientas — lógica del front (JS puro, sin dependencias). */

// ─── Utilidades ────────────────────────────────────────────────────────────
const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

async function api(ruta, opciones = {}) {
  const r = await fetch(ruta, {
    headers: { "Content-Type": "application/json" },
    ...opciones,
  });
  const cuerpo = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(cuerpo.detail || "Error de conexión");
  return cuerpo;
}

let temporizadorToast;
function toast(mensaje, tipo = "") {
  const t = $("#toast");
  t.textContent = mensaje;
  t.className = "ver " + tipo;
  clearTimeout(temporizadorToast);
  temporizadorToast = setTimeout(() => (t.className = tipo), 3200);
}

function escapar(s) {
  const d = document.createElement("div");
  d.textContent = s ?? "";
  return d.innerHTML;
}

const hora = (ts) => (ts ? ts.slice(11, 16) : "");
const fecha = (ts) => (ts ? ts.slice(0, 10) : "");

function fechaLinda(f) {
  const hoy = new Date().toISOString().slice(0, 10);
  const ayer = new Date(Date.now() - 864e5).toISOString().slice(0, 10);
  if (f === hoy) return "Hoy";
  if (f === ayer) return "Ayer";
  const [a, m, d] = f.split("-");
  return `${d}/${m}/${a}`;
}

// ─── Navegación ────────────────────────────────────────────────────────────
function irA(vista) {
  $$("nav button").forEach((b) => b.classList.toggle("activo", b.dataset.vista === vista));
  $$(".vista").forEach((s) => s.classList.toggle("activa", s.id === "v-" + vista));
  if (vista === "inicio") cargarInicio();
  if (vista === "inventario") cargarInventario();
  if (vista === "historial") cargarHistorial();
  if (vista === "retiro") reiniciarRetiro();
  if (vista === "devolucion") reiniciarDevolucion();
}

$$("nav button").forEach((b) => b.addEventListener("click", () => irA(b.dataset.vista)));
$$("[data-ir]").forEach((b) => b.addEventListener("click", () => irA(b.dataset.ir)));

// ─── Reloj y estado de conexión ────────────────────────────────────────────
setInterval(() => {
  $("#reloj").textContent = new Date().toLocaleTimeString("es-AR", {
    hour: "2-digit",
    minute: "2-digit",
  });
}, 1000);

// ─── INICIO ────────────────────────────────────────────────────────────────
async function cargarInicio() {
  try {
    const [r, herramientas] = await Promise.all([
      api("/api/resumen"),
      api("/api/herramientas"),
    ]);
    $("#punto").className = "punto";

    $("#stats").innerHTML = `
      <div class="stat naranja"><div class="num">${r.fuera}</div><div class="lbl">Afuera</div></div>
      <div class="stat verde"><div class="num">${r.disponibles}</div><div class="lbl">Disponibles</div></div>
      <div class="stat amarillo"><div class="num">${r.total}</div><div class="lbl">Total unidades</div></div>
      <div class="stat rojo"><div class="num">${r.movimientos_hoy}</div><div class="lbl">Movs. hoy</div></div>`;

    $("#alerta-inicio").innerHTML =
      r.fuera > 0
        ? `<div class="alerta naranja">⚠ ${r.fuera} unidad${r.fuera !== 1 ? "es" : ""} sin devolver</div>`
        : `<div class="alerta verde">✓ Todas las herramientas están en el depósito</div>`;

    const afuera = [];
    for (const h of herramientas) {
      const prestadas = h.cantidad - h.disponibles;
      if (prestadas > 0) {
        const det = await api("/api/herramientas/" + h.codigo);
        det.prestamos.forEach((p) => afuera.push({ herramienta: h.nombre, ...p }));
      }
    }
    $("#afuera-ahora").innerHTML = afuera.length
      ? afuera
          .map(
            (p) => `<div class="mov">
              <div class="ico retiro">↑</div>
              <div class="cuerpo">
                <div class="h">${escapar(p.herramienta)}${p.cantidad > 1 ? ` ×${p.cantidad}` : ""}</div>
                <div class="a">${escapar(p.nombre)} · DNI ${escapar(p.dni)}</div>
              </div>
              <div class="t">${fechaLinda(fecha(p.retiro_ts))}<br>${hora(p.retiro_ts)}</div>
            </div>`
          )
          .join("")
      : `<div class="vacio">Nada afuera. Todo en su lugar.</div>`;
  } catch (e) {
    $("#punto").className = "punto off";
    toast(e.message, "error");
  }
}

// ─── RETIRO ────────────────────────────────────────────────────────────────
let rHerramienta = null;
let rAlumno = null;

function reiniciarRetiro() {
  rHerramienta = null;
  rAlumno = null;
  $("#retiro-form").style.display = "";
  $("#retiro-exito").style.display = "none";
  $("#retiro-h-vacio").style.display = "";
  $("#retiro-h-ok").style.display = "none";
  $("#retiro-a-vacio").style.display = "";
  $("#retiro-a-ok").style.display = "none";
  $("#paso-c").style.display = "none";
  $("#paso-h").classList.remove("hecho");
  $("#paso-a").classList.remove("hecho");
  $("#retiro-codigo").value = "";
  $("#retiro-buscar").value = "";
  $("#retiro-dni").value = "";
  $("#dni-msg").innerHTML = "";
  $("#retiro-cantidad").value = 1;
  $("#retiro-obs").value = "";
  $("#btn-retiro").disabled = true;
  cargarAlumnos("");
  setTimeout(() => $("#retiro-codigo").focus(), 60);
}

async function escanearRetiro(codigo) {
  if (!codigo.trim()) return;
  try {
    const h = await api("/api/herramientas/" + encodeURIComponent(codigo.trim()));
    if (h.disponibles < 1) {
      toast(`No quedan ${h.nombre} disponibles`, "error");
      $("#retiro-codigo").value = "";
      return;
    }
    rHerramienta = h;
    $("#retiro-h-vacio").style.display = "none";
    $("#retiro-h-ok").style.display = "";
    $("#paso-h").classList.add("hecho");
    $("#retiro-h-ok").innerHTML = `
      <div class="elegido">
        <div class="bolita"></div>
        <div style="flex:1">
          <div class="n">${escapar(h.nombre)}</div>
          <div class="m">${h.codigo} · ${escapar(h.categoria)} · ${h.disponibles} de ${h.cantidad} libres</div>
        </div>
        <button class="chico" onclick="reiniciarRetiro()">CAMBIAR</button>
      </div>`;
    $("#retiro-cantidad").max = h.disponibles;
    $("#paso-c").style.display = h.cantidad > 1 ? "" : "none";
    if (!rAlumno) $("#retiro-dni").focus();
    revisarRetiro();
  } catch (e) {
    toast(e.message, "error");
    $("#retiro-codigo").value = "";
  }
}

async function cargarAlumnos(q) {
  try {
    const lista = await api("/api/alumnos?q=" + encodeURIComponent(q));
    $("#retiro-lista").innerHTML = lista.length
      ? lista
          .map(
            (a) => `<div class="item-alumno" data-id="${a.id}" data-nombre="${escapar(a.nombre)}" data-div="${escapar(a.division)}" data-dni="${escapar(a.dni)}">
              <span class="nom">${escapar(a.nombre)}</span>
              <span class="div">${escapar(a.dni)} · ${escapar(a.division)}</span>
            </div>`
          )
          .join("")
      : `<div class="vacio">Sin resultados</div>`;

    $$("#retiro-lista .item-alumno").forEach((el) =>
      el.addEventListener("click", () =>
        fijarAlumno({
          id: +el.dataset.id,
          nombre: el.dataset.nombre,
          division: el.dataset.div,
          dni: el.dataset.dni,
        })
      )
    );
  } catch (e) {
    toast(e.message, "error");
  }
}

function fijarAlumno(a) {
  rAlumno = a;
  $("#retiro-a-vacio").style.display = "none";
  $("#retiro-a-ok").style.display = "";
  $("#paso-a").classList.add("hecho");
  $("#retiro-a-ok").innerHTML = `
    <div class="elegido">
      <div class="bolita"></div>
      <div style="flex:1">
        <div class="n">${escapar(a.nombre)}</div>
        <div class="m">DNI ${escapar(a.dni)} · ${escapar(a.division)}</div>
      </div>
      <button class="chico" onclick="volverAElegirAlumno()">CAMBIAR</button>
    </div>`;
  revisarRetiro();
}

async function buscarPorDni() {
  const dni = $("#retiro-dni").value.replace(/\D/g, "");
  if (dni.length < 7) {
    $("#dni-msg").innerHTML = `<div class="alerta roja" style="margin-top:10px">
      El DNI tiene que tener al menos 7 dígitos</div>`;
    return;
  }
  try {
    const a = await api("/api/alumnos/dni/" + dni);
    $("#dni-msg").innerHTML = "";
    fijarAlumno(a);
  } catch (e) {
    $("#dni-msg").innerHTML = `<div class="alerta roja" style="margin-top:10px">
      ⚠ ${escapar(e.message)}</div>`;
    $("#retiro-dni").select();
  }
}

function volverAElegirAlumno() {
  rAlumno = null;
  $("#retiro-a-vacio").style.display = "";
  $("#retiro-a-ok").style.display = "none";
  $("#paso-a").classList.remove("hecho");
  $("#retiro-buscar").value = "";
  $("#retiro-dni").value = "";
  $("#dni-msg").innerHTML = "";
  cargarAlumnos("");
  $("#retiro-dni").focus();
  revisarRetiro();
}

function revisarRetiro() {
  $("#btn-retiro").disabled = !(rHerramienta && rAlumno);
}

$("#retiro-codigo").addEventListener("keydown", (e) => {
  if (e.key === "Enter") escanearRetiro(e.target.value);
});

$("#btn-dni").addEventListener("click", buscarPorDni);
$("#retiro-dni").addEventListener("keydown", (e) => {
  if (e.key === "Enter") buscarPorDni();
});
$("#retiro-dni").addEventListener("input", (e) => {
  e.target.value = e.target.value.replace(/\D/g, "");
  $("#dni-msg").innerHTML = "";
});

let debounce;
$("#retiro-buscar").addEventListener("input", (e) => {
  clearTimeout(debounce);
  debounce = setTimeout(() => cargarAlumnos(e.target.value), 180);
});

$("#menos").addEventListener("click", () => {
  const i = $("#retiro-cantidad");
  i.value = Math.max(1, +i.value - 1);
});
$("#mas").addEventListener("click", () => {
  const i = $("#retiro-cantidad");
  i.value = Math.min(rHerramienta ? rHerramienta.disponibles : 99, +i.value + 1);
});

$("#btn-retiro").addEventListener("click", async () => {
  $("#btn-retiro").disabled = true;
  try {
    const r = await api("/api/retiros", {
      method: "POST",
      body: JSON.stringify({
        codigo: rHerramienta.codigo,
        alumno_id: rAlumno.id,
        cantidad: +$("#retiro-cantidad").value || 1,
        observacion: $("#retiro-obs").value.trim() || null,
      }),
    });
    $("#retiro-form").style.display = "none";
    $("#retiro-exito").style.display = "";
    $("#retiro-exito").innerHTML = `
      <div class="exito">
        <div class="tick">✓</div>
        <div class="t">RETIRO REGISTRADO</div>
        <div class="d">
          <strong>${escapar(r.herramienta)}</strong>${r.cantidad > 1 ? ` ×${r.cantidad}` : ""}<br>
          ${escapar(r.alumno)}<br>
          <span style="color:var(--dimmer);font-size:12px">Quedan ${r.restantes} disponibles</span>
        </div>
        <button class="chico naranja" style="margin-top:20px;padding:12px 26px" onclick="reiniciarRetiro()">
          REGISTRAR OTRO
        </button>
      </div>`;
    setTimeout(reiniciarRetiro, 4000);
  } catch (e) {
    toast(e.message, "error");
    $("#btn-retiro").disabled = false;
  }
});

// ─── DEVOLUCIÓN ────────────────────────────────────────────────────────────
function reiniciarDevolucion() {
  $("#dev-form").style.display = "";
  $("#dev-exito").style.display = "none";
  $("#dev-h-vacio").style.display = "";
  $("#dev-h-ok").style.display = "none";
  $("#dev-paso-p").style.display = "none";
  $("#dev-codigo").value = "";
  setTimeout(() => $("#dev-codigo").focus(), 60);
}

async function escanearDevolucion(codigo) {
  if (!codigo.trim()) return;
  try {
    const h = await api("/api/herramientas/" + encodeURIComponent(codigo.trim()));
    if (!h.prestamos.length) {
      toast(`${h.nombre} no figura prestada`, "error");
      $("#dev-codigo").value = "";
      return;
    }
    $("#dev-h-vacio").style.display = "none";
    $("#dev-h-ok").style.display = "";
    $("#dev-h-ok").innerHTML = `
      <div class="elegido">
        <div class="bolita"></div>
        <div style="flex:1">
          <div class="n">${escapar(h.nombre)}</div>
          <div class="m">${h.codigo} · ${h.prestamos.length} préstamo(s) abierto(s)</div>
        </div>
        <button class="chico" onclick="reiniciarDevolucion()">CAMBIAR</button>
      </div>`;
    $("#dev-paso-p").style.display = "";
    $("#dev-prestamos").innerHTML = h.prestamos
      .map(
        (p) => `<div class="item-herr">
          <div class="bolita parcial"></div>
          <div class="info">
            <div class="nom">${escapar(p.nombre)}</div>
            <div class="meta">DNI ${escapar(p.dni)} · retiró ${fechaLinda(fecha(p.retiro_ts))} ${hora(p.retiro_ts)}${p.cantidad > 1 ? ` · ×${p.cantidad}` : ""}</div>
          </div>
          <button class="chico naranja" onclick="devolver(${p.id})">DEVOLVER</button>
        </div>`
      )
      .join("");
  } catch (e) {
    toast(e.message, "error");
    $("#dev-codigo").value = "";
  }
}

async function devolver(prestamoId) {
  try {
    const r = await api("/api/devoluciones", {
      method: "POST",
      body: JSON.stringify({ prestamo_id: prestamoId }),
    });
    $("#dev-form").style.display = "none";
    $("#dev-exito").style.display = "";
    $("#dev-exito").innerHTML = `
      <div class="exito">
        <div class="tick">✓</div>
        <div class="t">DEVOLUCIÓN REGISTRADA</div>
        <div class="d">
          <strong>${escapar(r.herramienta)}</strong>${r.cantidad > 1 ? ` ×${r.cantidad}` : ""}<br>
          Devuelta por ${escapar(r.alumno)}
        </div>
        <button class="chico naranja" style="margin-top:20px;padding:12px 26px" onclick="reiniciarDevolucion()">
          REGISTRAR OTRA
        </button>
      </div>`;
    setTimeout(reiniciarDevolucion, 4000);
  } catch (e) {
    toast(e.message, "error");
  }
}

$("#dev-codigo").addEventListener("keydown", (e) => {
  if (e.key === "Enter") escanearDevolucion(e.target.value);
});

// ─── INVENTARIO ────────────────────────────────────────────────────────────
let inventario = [];
let filtroInv = "todas";

async function cargarInventario() {
  try {
    inventario = await api("/api/herramientas");
    const cats = [...new Set(inventario.map((h) => h.categoria))].sort();
    $("#inv-filtros").innerHTML = ["todas", "afuera", "disponibles", ...cats]
      .map(
        (f) =>
          `<button class="filtro ${f === filtroInv ? "activo" : ""}" data-f="${f}">${f}</button>`
      )
      .join("");
    $$("#inv-filtros .filtro").forEach((b) =>
      b.addEventListener("click", () => {
        filtroInv = b.dataset.f;
        cargarInventario();
      })
    );
    const unidades = inventario.reduce((s, h) => s + h.cantidad, 0);
    $("#inv-sub").textContent = `${inventario.length} tipos · ${unidades} unidades en total`;
    pintarInventario();
  } catch (e) {
    toast(e.message, "error");
  }
}

function pintarInventario() {
  const q = $("#inv-buscar").value.toLowerCase();
  const lista = inventario.filter((h) => {
    const prestadas = h.cantidad - h.disponibles;
    const okFiltro =
      filtroInv === "todas" ||
      (filtroInv === "afuera" && prestadas > 0) ||
      (filtroInv === "disponibles" && h.disponibles > 0) ||
      h.categoria === filtroInv;
    const okBusca =
      h.nombre.toLowerCase().includes(q) || h.codigo.toLowerCase().includes(q);
    return okFiltro && okBusca;
  });

  $("#inv-lista").innerHTML = lista.length
    ? lista
        .map((h) => {
          const clase =
            h.disponibles === 0 ? "cero" : h.disponibles < h.cantidad ? "parcial" : "libre";
          const prestadas = h.cantidad - h.disponibles;
          const meta = prestadas
            ? `${prestadas} afuera · último: ${escapar(h.ultimo_usuario || "—")}`
            : h.ultimo_usuario
            ? `Último que la llevó: ${escapar(h.ultimo_usuario)}`
            : "Nunca se prestó";
          return `<div class="item-herr">
            <div class="bolita ${clase}"></div>
            <div class="info">
              <div class="nom">${escapar(h.nombre)}</div>
              <div class="meta">${meta}</div>
            </div>
            <div class="der">
              <div class="cant ${clase}">${h.disponibles}<span style="font-size:14px;color:var(--dimmer)">/${h.cantidad}</span></div>
              <div class="cant-sub">libres</div>
              <div class="cod">${h.codigo}</div>
            </div>
          </div>`;
        })
        .join("")
    : `<div class="vacio">Sin resultados</div>`;
}

$("#inv-buscar").addEventListener("input", pintarInventario);

// ─── HISTORIAL ─────────────────────────────────────────────────────────────
let movimientos = [];

async function cargarHistorial() {
  try {
    const datos = await api("/api/historial");
    movimientos = [];
    datos.forEach((p) => {
      movimientos.push({ ...p, tipo: "retiro", ts: p.retiro_ts });
      if (p.devolucion_ts)
        movimientos.push({ ...p, tipo: "devolucion", ts: p.devolucion_ts });
    });
    movimientos.sort((a, b) => b.ts.localeCompare(a.ts));
    $("#hist-sub").textContent = `${movimientos.length} movimientos registrados`;
    pintarHistorial();
  } catch (e) {
    toast(e.message, "error");
  }
}

function pintarHistorial() {
  const q = $("#hist-buscar").value.toLowerCase();
  const lista = movimientos.filter(
    (m) =>
      m.alumno.toLowerCase().includes(q) || m.herramienta.toLowerCase().includes(q)
  );

  if (!lista.length) {
    $("#hist-lista").innerHTML = `<div class="vacio">Todavía no hay movimientos</div>`;
    return;
  }

  let html = "";
  let ultimaFecha = null;
  lista.forEach((m) => {
    const f = fecha(m.ts);
    if (f !== ultimaFecha) {
      html += `<div class="separador-fecha">— ${fechaLinda(f)}</div>`;
      ultimaFecha = f;
    }
    const verbo = m.tipo === "retiro" ? "Retiró" : "Devolvió";
    const color = m.tipo === "retiro" ? "var(--orange)" : "var(--green)";
    html += `<div class="mov">
      <div class="ico ${m.tipo}">${m.tipo === "retiro" ? "↑" : "↓"}</div>
      <div class="cuerpo">
        <div class="h">${escapar(m.herramienta)}${m.cantidad > 1 ? ` ×${m.cantidad}` : ""}</div>
        <div class="a">${escapar(m.alumno)} · ${escapar(m.division)} ·
          <span style="color:${color};font-weight:600">${verbo}</span></div>
        ${m.observacion && m.tipo === "retiro" ? `<div class="a" style="font-style:italic">"${escapar(m.observacion)}"</div>` : ""}
      </div>
      <div class="t">${hora(m.ts)}</div>
    </div>`;
  });
  $("#hist-lista").innerHTML = html;
}

$("#hist-buscar").addEventListener("input", pintarHistorial);

// ─── AJUSTES ───────────────────────────────────────────────────────────────
$("#btn-nh").addEventListener("click", async () => {
  const nombre = $("#nh-nombre").value.trim();
  if (!nombre) return toast("Escribí el nombre de la herramienta", "error");
  try {
    const r = await api("/api/herramientas", {
      method: "POST",
      body: JSON.stringify({
        nombre,
        categoria: $("#nh-cat").value,
        cantidad: +$("#nh-cant").value || 1,
      }),
    });
    toast(`${r.nombre} agregada con código ${r.codigo}`, "ok");
    $("#nh-nombre").value = "";
    $("#nh-cant").value = 1;
  } catch (e) {
    toast(e.message, "error");
  }
});

$("#btn-na").addEventListener("click", async () => {
  const nombre = $("#na-nombre").value.trim();
  const division = $("#na-div").value.trim();
  const dni = $("#na-dni").value.replace(/\D/g, "");
  if (!nombre || !division || !dni)
    return toast("Completá nombre, división y DNI", "error");
  try {
    await api("/api/alumnos", {
      method: "POST",
      body: JSON.stringify({ nombre, division, dni }),
    });
    toast(`${nombre} agregado`, "ok");
    $("#na-nombre").value = "";
    $("#na-dni").value = "";
  } catch (e) {
    toast(e.message, "error");
  }
});

// ─── Captura del lector de código de barras ────────────────────────────────
// El lector USB actúa como teclado: escribe rápido y manda Enter.
// Si nadie está escribiendo en un campo, redirigimos la lectura al input activo.
let buffer = "";
let ultimaTecla = 0;

document.addEventListener("keydown", (e) => {
  const enCampo = ["INPUT", "SELECT", "TEXTAREA"].includes(document.activeElement.tagName);
  if (enCampo) return;

  const ahora = Date.now();
  if (ahora - ultimaTecla > 120) buffer = "";
  ultimaTecla = ahora;

  if (e.key === "Enter" && buffer.length >= 3) {
    const vista = document.querySelector(".vista.activa").id;
    if (vista === "v-devolucion") escanearDevolucion(buffer);
    else {
      if (vista !== "v-retiro") irA("retiro");
      setTimeout(() => escanearRetiro(buffer), 80);
    }
    buffer = "";
  } else if (e.key.length === 1) {
    buffer += e.key;
  }
});

// ─── Arranque ──────────────────────────────────────────────────────────────
cargarInicio();
setInterval(() => {
  if (document.querySelector(".vista.activa").id === "v-inicio") cargarInicio();
}, 30000);
