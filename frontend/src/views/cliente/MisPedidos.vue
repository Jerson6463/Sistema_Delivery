<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import api from '@/services/api'

const pedidos = ref([])
const ubicaciones = reactive({})
const pollingIntervals = new Map()
const isLoading = ref(true)
const errorMessage = ref('')

const pedidosOrdenados = computed(() =>
  [...pedidos.value].sort((a, b) => new Date(b.creado_en) - new Date(a.creado_en)),
)

onMounted(() => {
  cargarPedidos()
})

onBeforeUnmount(() => {
  clearAllPolling()
})

async function cargarPedidos() {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const { data } = await api.get('pedidos/')
    pedidos.value = data
    syncPolling()
  } catch {
    errorMessage.value = 'No pudimos cargar tu historial de pedidos.'
  } finally {
    isLoading.value = false
  }
}

function syncPolling() {
  const enCaminoIds = new Set(
    pedidos.value.filter((pedido) => pedido.estado === 'EN_CAMINO').map((pedido) => pedido.id),
  )

  pedidos.value.forEach((pedido) => {
    if (pedido.estado === 'EN_CAMINO') {
      startPolling(pedido.id)
      return
    }

    if (pedido.estado === 'ENTREGADO') {
      stopPolling(pedido.id)
    }
  })

  pollingIntervals.forEach((_, pedidoId) => {
    if (!enCaminoIds.has(pedidoId)) {
      stopPolling(pedidoId)
    }
  })
}

function startPolling(pedidoId) {
  if (pollingIntervals.has(pedidoId)) return

  rastrearPedido(pedidoId)
  const intervalId = window.setInterval(() => rastrearPedido(pedidoId), 7000)
  pollingIntervals.set(pedidoId, intervalId)
}

function stopPolling(pedidoId) {
  const intervalId = pollingIntervals.get(pedidoId)
  if (!intervalId) return

  window.clearInterval(intervalId)
  pollingIntervals.delete(pedidoId)
}

function clearAllPolling() {
  pollingIntervals.forEach((intervalId) => window.clearInterval(intervalId))
  pollingIntervals.clear()
}

async function rastrearPedido(pedidoId) {
  try {
    const { data } = await api.get(`seguimiento/pedidos/${pedidoId}/rastrear/`)
    ubicaciones[pedidoId] = {
      latitud: data.latitud,
      longitud: data.longitud,
      actualizadoEn: new Date().toLocaleTimeString(),
    }
  } catch {
    ubicaciones[pedidoId] = {
      ...ubicaciones[pedidoId],
      error: 'Esperando ubicacion del repartidor...',
    }
  }
}

function badgeClass(estado) {
  return `status-${String(estado).toLowerCase()}`
}

function formatEstado(estado) {
  return String(estado)
    .toLowerCase()
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function formatDate(value) {
  return new Intl.DateTimeFormat('es-PE', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function formatMoney(value) {
  return `S/ ${Number(value).toFixed(2)}`
}
</script>

<template>
  <main class="orders-page">
    <section class="orders-shell">
      <header class="orders-header">
        <span class="eyebrow">Historial y rastreo</span>
        <h1>Mis Pedidos</h1>
        <p>Consulta el estado de tus compras y sigue al repartidor cuando el pedido este en camino.</p>
      </header>

      <div v-if="isLoading" class="state-card">Cargando pedidos...</div>

      <div v-else-if="errorMessage" class="state-card error-card">
        <p>{{ errorMessage }}</p>
        <button type="button" @click="cargarPedidos">Reintentar</button>
      </div>

      <div v-else-if="!pedidosOrdenados.length" class="state-card">
        <h2>Aun no tienes pedidos</h2>
        <p>Cuando confirmes una compra, aparecera en esta seccion.</p>
      </div>

      <section v-else class="orders-list" aria-label="Lista de pedidos">
        <article v-for="pedido in pedidosOrdenados" :key="pedido.id" class="order-card">
          <div class="order-top">
            <div>
              <span class="order-id">Pedido #{{ pedido.id }}</span>
              <h2>{{ pedido.nombre_negocio || 'Negocio' }}</h2>
              <p>{{ formatDate(pedido.creado_en) }}</p>
            </div>

            <span class="status-badge" :class="badgeClass(pedido.estado)">
              {{ pedido.estado_display || formatEstado(pedido.estado) }}
            </span>
          </div>

          <div class="order-meta">
            <div>
              <span>Total</span>
              <strong>{{ formatMoney(pedido.total) }}</strong>
            </div>
            <div>
              <span>Direccion</span>
              <strong>{{ pedido.direccion_entrega }}</strong>
            </div>
          </div>

          <ul class="details-list">
            <li v-for="detalle in pedido.detalles" :key="detalle.id">
              <span>{{ detalle.cantidad }}x {{ detalle.nombre_producto }}</span>
              <strong>{{ formatMoney(detalle.subtotal) }}</strong>
            </li>
          </ul>

          <section v-if="pedido.estado === 'EN_CAMINO'" class="tracking-card">
            <div>
              <span class="tracking-label">Rastreo activo</span>
              <h3>Ubicacion del repartidor</h3>
            </div>

            <div v-if="ubicaciones[pedido.id]?.latitud" class="coordinates">
              <span>Latitud: {{ ubicaciones[pedido.id].latitud }}</span>
              <span>Longitud: {{ ubicaciones[pedido.id].longitud }}</span>
              <small>Actualizado: {{ ubicaciones[pedido.id].actualizadoEn }}</small>
            </div>

            <p v-else>
              {{ ubicaciones[pedido.id]?.error || 'Obteniendo coordenadas del repartidor...' }}
            </p>
          </section>
        </article>
      </section>
    </section>
  </main>
</template>

<style scoped>
.orders-page {
  min-height: 100vh;
  background: var(--app-background);
  color: var(--app-text);
  padding: 22px 16px 34px;
}

.orders-shell {
  width: 100%;
  max-width: 980px;
  margin: 0 auto;
}

.orders-header {
  margin-bottom: 20px;
}

.eyebrow,
.order-id,
.tracking-label {
  color: var(--app-primary);
  font-size: 0.78rem;
  font-weight: 850;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

h1,
h2,
h3,
p {
  margin: 0;
}

h1 {
  margin-top: 8px;
  color: var(--app-text);
  font-size: clamp(2rem, 8vw, 3.2rem);
  font-weight: 850;
  letter-spacing: 0;
  line-height: 1.08;
}

.orders-header p {
  margin-top: 12px;
  color: var(--app-muted);
  line-height: 1.7;
}

.state-card,
.order-card {
  border: 1px solid var(--app-border);
  border-radius: 18px;
  background: var(--app-surface);
  box-shadow: var(--app-shadow-soft);
  padding: 20px;
}

.state-card {
  display: grid;
  gap: 12px;
  color: var(--app-muted);
  text-align: center;
}

.state-card h2 {
  color: var(--app-text);
  font-weight: 850;
}

.state-card button {
  min-height: 46px;
  border: 0;
  border-radius: 11px;
  background: var(--app-primary);
  color: #ffffff;
  cursor: pointer;
  font-weight: 850;
}

.error-card {
  border-color: #f1b9b9;
  background: #fff5f5;
  color: #b42318;
}

.orders-list {
  display: grid;
  gap: 16px;
}

.order-card {
  display: grid;
  gap: 18px;
}

.order-top {
  display: grid;
  gap: 14px;
}

.order-top h2 {
  margin-top: 6px;
  color: var(--app-text);
  font-size: 1.28rem;
  font-weight: 850;
}

.order-top p {
  margin-top: 4px;
  color: var(--app-muted);
}

.status-badge {
  display: inline-flex;
  width: fit-content;
  border-radius: 999px;
  background: #eef3f8;
  color: var(--app-muted);
  font-size: 0.8rem;
  font-weight: 850;
  padding: 8px 11px;
}

.status-recibido {
  background: #e8f3f5;
  color: var(--app-primary);
}

.status-confirmado,
.status-en_preparacion,
.status-listo_para_recojo {
  background: #fff7ed;
  color: #b45309;
}

.status-en_camino {
  background: #ecfdf5;
  color: #16704f;
}

.status-entregado {
  background: #eef3f8;
  color: #475569;
}

.order-meta {
  display: grid;
  gap: 12px;
  border-radius: 14px;
  background: #f8fafc;
  padding: 14px;
}

.order-meta div {
  display: grid;
  gap: 4px;
}

.order-meta span {
  color: var(--app-muted);
  font-size: 0.82rem;
  font-weight: 800;
}

.order-meta strong {
  color: var(--app-text);
  font-weight: 850;
}

.details-list {
  display: grid;
  gap: 10px;
  list-style: none;
  margin: 0;
  padding: 0;
}

.details-list li {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  color: var(--app-muted);
}

.details-list strong {
  color: var(--app-text);
}

.tracking-card {
  display: grid;
  gap: 12px;
  border: 1px solid #b9decf;
  border-radius: 14px;
  background: #f0fbf6;
  padding: 16px;
}

.tracking-card h3 {
  margin-top: 6px;
  color: var(--app-text);
  font-size: 1.05rem;
  font-weight: 850;
}

.tracking-card p {
  color: #16704f;
  font-weight: 700;
}

.coordinates {
  display: grid;
  gap: 6px;
  color: #16704f;
  font-weight: 800;
}

.coordinates small {
  color: var(--app-muted);
  font-weight: 700;
}

@media (min-width: 768px) {
  .orders-page {
    padding: 42px 24px 56px;
  }

  .state-card,
  .order-card {
    padding: 28px;
    box-shadow: 0 24px 60px rgba(16, 32, 51, 0.1);
  }

  .order-top {
    grid-template-columns: 1fr auto;
    align-items: start;
  }

  .order-meta {
    grid-template-columns: 180px 1fr;
  }
}
</style>
