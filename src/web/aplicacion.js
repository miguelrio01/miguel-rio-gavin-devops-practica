"use strict";

const estado = { usuarios: [], productos: [], pedidos: [] };
const $ = (id) => document.getElementById(id);
const euros = new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR" });
const escapar = (valor) => String(valor ?? "").replace(/[&<>"']/g, (caracter) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
})[caracter]);

async function peticion(ruta, opciones = {}) {
  const respuesta = await fetch(ruta, opciones);
  if (!respuesta.ok) {
    let mensaje = `Error ${respuesta.status}`;
    try {
      const error = await respuesta.json();
      if (typeof error.detail === "string") mensaje = error.detail;
      else if (Array.isArray(error.detail)) mensaje = error.detail.map((detalle) => detalle.msg).join("; ");
    } catch (_) { /* En algunos errores no hay respuesta JSON. */ }
    throw new Error(mensaje);
  }
  return respuesta.status === 204 ? null : respuesta.json();
}

function notificar(mensaje, error = false) {
  const aviso = $("aviso");
  aviso.textContent = mensaje;
  aviso.classList.toggle("error", error);
  aviso.hidden = false;
  clearTimeout(notificar.temporizador);
  notificar.temporizador = setTimeout(() => { aviso.hidden = true; }, 4300);
}

function cambiarVista(vista) {
  const titulos = {
    inicio: ["Resumen", "Consulta el estado de la tienda."],
    usuarios: ["Usuarios", "Gestiona los usuarios registrados."],
    productos: ["Productos", "Controla el catálogo y las existencias."],
    pedidos: ["Pedidos", "Registra compras y consulta el historial."]
  };
  document.querySelectorAll(".vista").forEach((seccion) => {
    seccion.hidden = seccion.id !== `vista-${vista}`;
  });
  document.querySelectorAll("[data-vista]").forEach((boton) => {
    const activo = boton.dataset.vista === vista;
    boton.classList.toggle("activo", activo);
    if (activo) boton.setAttribute("aria-current", "page");
    else boton.removeAttribute("aria-current");
  });
  $("titulo-vista").textContent = titulos[vista][0];
  $("subtitulo-vista").textContent = titulos[vista][1];
  if (vista === "pedidos") mostrarHistorial();
}

async function actualizarDatos() {
  const [usuarios, productos] = await Promise.all([peticion("/usuarios"), peticion("/productos")]);
  estado.usuarios = usuarios;
  estado.productos = productos;
  pintarUsuarios();
  pintarProductos();
  pintarResumen();
  actualizarSelectores();
  actualizarLineas();
  await actualizarCantidadPedidos();
}

async function actualizarCantidadPedidos() {
  const clientes = estado.usuarios.filter((u) => !u.es_admin);
  if (!clientes.length) { $("stat-pedidos").textContent = "0"; return; }
  try {
    const listas = await Promise.all(clientes.map((u) => peticion(`/usuarios/${encodeURIComponent(u.id)}/pedidos`)));
    $("stat-pedidos").textContent = listas.reduce((n, pedidos) => n + pedidos.length, 0);
  } catch (_) {
    $("stat-pedidos").textContent = "—";
  }
}

function pintarResumen() {
  $("stat-usuarios").textContent = estado.usuarios.length;
  $("stat-productos").textContent = estado.productos.length;
  $("stat-unidades").textContent = estado.productos.reduce((total, p) => total + p.stock, 0);
  const recientes = estado.productos.slice(-4).reverse();
  $("resumen-productos").innerHTML = recientes.length
    ? recientes.map((p) => `<div class="resumen-elemento"><span><strong>${escapar(p.nombre)}</strong><small>${escapar(nombreTipo(p.tipo))} · ${p.stock} uds.</small></span><span class="importe">${euros.format(p.precio)}</span></div>`).join("")
    : '<p class="estado-vacio">Todavía no hay productos.</p>';
}

function nombreTipo(tipo) {
  return ({ generico: "Genérico", electronico: "Electrónico", ropa: "Ropa" })[tipo] || tipo;
}

function pintarUsuarios() {
  $("conteo-usuarios").textContent = estado.usuarios.length;
  $("tabla-usuarios").innerHTML = estado.usuarios.length
    ? estado.usuarios.map((u) => `<tr><td><strong>${escapar(u.nombre)}</strong><small title="${escapar(u.id)}">ID: ${escapar(u.id.slice(0, 8))}...</small></td><td>${escapar(u.email)}</td><td><span class="pill ${u.es_admin ? "admin" : ""}">${u.es_admin ? "Administrador" : "Cliente"}</span></td></tr>`).join("")
    : '<tr><td colspan="3" class="estado-vacio">No hay usuarios registrados.</td></tr>';
}

function pintarProductos() {
  const busqueda = $("buscar-producto").value.toLocaleLowerCase("es").trim();
  const filtrados = estado.productos.filter((p) => p.nombre.toLocaleLowerCase("es").includes(busqueda));
  $("conteo-productos").textContent = estado.productos.length;
  $("tabla-productos").innerHTML = filtrados.length
    ? filtrados.map((p) => `<tr><td><strong>${escapar(p.nombre)}</strong><small>${escapar(nombreTipo(p.tipo))}${p.tipo === "electronico" ? ` · ${p.meses_garantia} meses de garantía` : ""}${p.tipo === "ropa" ? ` · ${escapar(p.talla)} / ${escapar(p.color)}` : ""}</small></td><td>${euros.format(p.precio)}</td><td><span class="pill ${p.stock ? "ok" : "bajo"}">${p.stock}</span></td><td><button class="boton-borrar" type="button" data-borrar="${escapar(p.id)}">Eliminar</button></td></tr>`).join("")
    : `<tr><td colspan="4" class="estado-vacio">${busqueda ? "No se encontraron productos." : "No hay productos en el catálogo."}</td></tr>`;
}

function rellenarClientes(select) {
  const seleccionado = select.value;
  const opciones = estado.usuarios.filter((u) => !u.es_admin).map((u) => `<option value="${escapar(u.id)}">${escapar(u.nombre)} (${escapar(u.email)})</option>`).join("");
  select.innerHTML = '<option value="">Selecciona un cliente</option>' + opciones;
  if ([...select.options].some((opcion) => opcion.value === seleccionado)) select.value = seleccionado;
}

function actualizarSelectores() {
  rellenarClientes($("cliente-pedido"));
  rellenarClientes($("cliente-historial"));
}

function opcionesProductos(seleccionado = "") {
  return '<option value="">Selecciona un producto</option>' + estado.productos.map((p) =>
    `<option value="${escapar(p.id)}" ${p.id === seleccionado ? "selected" : ""}>${escapar(p.nombre)} · ${euros.format(p.precio)} (stock: ${p.stock})</option>`
  ).join("");
}

function añadirLinea() {
  const contenedor = document.createElement("div");
  contenedor.className = "linea-pedido";
  contenedor.innerHTML = `<label>Producto<select class="linea-producto" required>${opcionesProductos()}</select></label><label>Cantidad<input class="linea-cantidad" type="number" min="1" step="1" value="1" required></label><button type="button" class="quitar-linea" aria-label="Quitar producto" title="Quitar línea">×</button>`;
  $("lineas-pedido").appendChild(contenedor);
}

function actualizarLineas() {
  document.querySelectorAll(".linea-producto").forEach((select) => {
    const seleccionado = select.value;
    select.innerHTML = opcionesProductos(seleccionado);
    select.value = estado.productos.some((p) => p.id === seleccionado) ? seleccionado : "";
  });
}

async function mostrarHistorial() {
  const id = $("cliente-historial").value;
  if (!id) {
    $("lista-pedidos").innerHTML = '<p class="estado-vacio">Selecciona un cliente para ver su historial.</p>';
    return;
  }
  $("lista-pedidos").innerHTML = '<p class="estado-vacio">Cargando pedidos...</p>';
  try {
    const pedidos = await peticion(`/usuarios/${encodeURIComponent(id)}/pedidos`);
    if (id !== $("cliente-historial").value) return;
    $("lista-pedidos").innerHTML = pedidos.length ? [...pedidos].reverse().map((pedido) => {
      const articulos = pedido.items.map((item) => `<p><span>${escapar(item.nombre_producto)} × ${item.cantidad}</span><span>${euros.format(item.subtotal)}</span></p>`).join("");
      return `<div class="tarjeta-pedido"><div class="pedido-cabecera"><div><strong>Pedido ${escapar(pedido.id.slice(0, 8))}</strong><small>${escapar(new Date(pedido.fecha).toLocaleString("es-ES"))}</small></div><span class="pedido-total">${euros.format(pedido.total)}</span></div><div class="pedido-detalle">${articulos}</div></div>`;
    }).join("") : '<p class="estado-vacio">Este cliente todavía no tiene pedidos.</p>';
  } catch (error) {
    $("lista-pedidos").innerHTML = '<p class="estado-vacio">No se ha podido cargar el historial.</p>';
    notificar(error.message, true);
  }
}

function actualizarCamposUsuario() {
  const esCliente = $("tipo-usuario").value === "cliente";
  $("campo-direccion").hidden = !esCliente;
  $("form-usuario").elements.direccion.required = esCliente;
}

function actualizarCamposProducto() {
  const tipo = $("tipo-producto").value;
  $("campos-electronico").hidden = tipo !== "electronico";
  $("campos-ropa").hidden = tipo !== "ropa";
  const formulario = $("form-producto");
  formulario.elements.meses_garantia.required = tipo === "electronico";
  formulario.elements.talla.required = tipo === "ropa";
  formulario.elements.color.required = tipo === "ropa";
}

async function enviarFormulario(evento, trabajo) {
  evento.preventDefault();
  const boton = evento.currentTarget.querySelector('[type="submit"]');
  boton.disabled = true;
  try { await trabajo(evento.currentTarget); }
  catch (error) { notificar(error.message, true); }
  finally { boton.disabled = false; }
}

$("form-usuario").addEventListener("submit", (evento) => enviarFormulario(evento, async (formulario) => {
  const datos = {
    tipo: formulario.elements.tipo.value,
    nombre: formulario.elements.nombre.value.trim(),
    email: formulario.elements.email.value.trim()
  };
  if (datos.tipo === "cliente") datos.direccion = formulario.elements.direccion.value.trim();
  await peticion("/usuarios", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(datos) });
  formulario.reset();
  actualizarCamposUsuario();
  await actualizarDatos();
  notificar("Usuario registrado correctamente.");
}));

$("form-producto").addEventListener("submit", (evento) => enviarFormulario(evento, async (formulario) => {
  const tipo = formulario.elements.tipo.value;
  const datos = {
    tipo, nombre: formulario.elements.nombre.value.trim(),
    precio: Number(formulario.elements.precio.value),
    stock: Number(formulario.elements.stock.value)
  };
  if (tipo === "electronico") datos.meses_garantia = Number(formulario.elements.meses_garantia.value);
  if (tipo === "ropa") {
    datos.talla = formulario.elements.talla.value.trim();
    datos.color = formulario.elements.color.value.trim();
  }
  await peticion("/productos", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(datos) });
  formulario.reset();
  actualizarCamposProducto();
  await actualizarDatos();
  notificar("Producto añadido correctamente.");
}));

$("form-pedido").addEventListener("submit", (evento) => enviarFormulario(evento, async (formulario) => {
  const cliente_id = formulario.elements.cliente_id.value;
  const items = [...$("lineas-pedido").querySelectorAll(".linea-pedido")].map((linea) => ({
    producto_id: linea.querySelector(".linea-producto").value,
    cantidad: Number(linea.querySelector(".linea-cantidad").value)
  }));
  if (!cliente_id) throw new Error("Selecciona un cliente.");
  if (!items.length || items.some((item) => !item.producto_id)) throw new Error("Selecciona los productos del pedido.");
  if (new Set(items.map((item) => item.producto_id)).size !== items.length) throw new Error("No repitas un producto en el mismo pedido.");
  await peticion("/pedidos", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ cliente_id, items }) });
  $("lineas-pedido").innerHTML = "";
  añadirLinea();
  await actualizarDatos();
  $("cliente-historial").value = cliente_id;
  await mostrarHistorial();
  notificar("Pedido registrado correctamente.");
}));

$("tabla-productos").addEventListener("click", async (evento) => {
  const boton = evento.target.closest("[data-borrar]");
  if (!boton) return;
  const producto = estado.productos.find((p) => p.id === boton.dataset.borrar);
  if (!producto || !confirm(`¿Quieres eliminar el producto «${producto.nombre}»?`)) return;
  boton.disabled = true;
  try {
    await peticion(`/productos/${encodeURIComponent(producto.id)}`, { method: "DELETE" });
    await actualizarDatos();
    notificar("Producto eliminado.");
  } catch (error) { notificar(error.message, true); boton.disabled = false; }
});

$("lineas-pedido").addEventListener("click", (evento) => {
  if (!evento.target.closest(".quitar-linea")) return;
  const lineas = $("lineas-pedido");
  if (lineas.children.length > 1) evento.target.closest(".linea-pedido").remove();
  else notificar("El pedido necesita al menos un producto.", true);
});

$("tipo-usuario").addEventListener("change", actualizarCamposUsuario);
$("tipo-producto").addEventListener("change", actualizarCamposProducto);
$("buscar-producto").addEventListener("input", pintarProductos);
$("cliente-historial").addEventListener("change", mostrarHistorial);
$("anadir-linea").addEventListener("click", añadirLinea);
document.querySelectorAll("[data-vista]").forEach((boton) => boton.addEventListener("click", () => cambiarVista(boton.dataset.vista)));
document.querySelectorAll("[data-ir]").forEach((boton) => boton.addEventListener("click", () => cambiarVista(boton.dataset.ir)));

actualizarCamposUsuario();
actualizarCamposProducto();
añadirLinea();
actualizarDatos().catch((error) => notificar(`No se ha podido conectar con la tienda: ${error.message}`, true));
