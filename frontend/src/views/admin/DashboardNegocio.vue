<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const pedidos = ref([])
const isOpen = ref(true)
const isLoading = ref(true)
const isRefreshing = ref(false)
const errorMessage = ref('')
const updatingIds = ref(new Set())

let pollingId = null

const pedidosNuevos = computed(() => pedidos.value.filter((pedido) => pedido.estado === 'RECIBIDO'))

const pedidosPreparando = computed(() =>
  pedidos.value.filter((pedido) => ['CONFIRMADO', 'EN_PREPARACION'].includes(pedido.estado)),
)

const pedidosListos = computed(() =>
  pedidos.value.filter((pedido) => pedido.estado === 'LISTO_PARA_RECOJO'),
)

const columns = computed(() => [
  {
    key: 'nuevos',
    title: 'Nuevos',
    subtitle: 'Recibidos',
    pedidos: pedidosNuevos.value,
  },
  {
    key: 'preparando',
    title: 'En Preparacion',
    subtitle: 'Confirmados / Preparando',
    pedidos: pedidosPreparando.value,
  },
  {
    key: 'listos',
    title: 'Listos',
    subtitle: 'Esperando repartidor',
    pedidos: pedidosListos.value,
  },
])

onMounted(async () => {
  await cargarPedidos()
  pollingId = window.setInterval(cargarPedidos, 10000)
})

onUnmounted(() => {
  if (pollingId) {
    window.clearInterval(pollingId)
  }
})

async function cargarPedidos() {
  if (isRefreshing.value) return

  isRefreshing.value = true
  errorMessage.value = ''

  try {
    const { data } = await api.get('pedidos/')
    pedidos.value = data
  } catch {
    errorMessage.value = 'No pudimos cargar los pedidos del negocio.'
  } finally {
    isLoading.value = false
    isRefreshing.value = false
  }
}

async function avanzarPedido(id, nuevoEstado) {
  if (updatingIds.value.has(id)) return

  updatingIds.value = new Set([...updatingIds.value, id])
  errorMessage.value = ''

  try {
    await api.post(`pedidos/${id}/transicion/`, {
      nuevo_estado: nuevoEstado,
    })

    pedidos.value = pedidos.value.map((pedido) =>
      pedido.id === id
        ? {
            ...pedido,
            estado: nuevoEstado,
            estado_display: formatEstado(nuevoEstado),
          }
        : pedido,
    )
  } catch (error) {
    errorMessage.value =
      error.response?.data?.error ||
      error.response?.data?.detail ||
      'No pudimos actualizar el estado del pedido.'
  } finally {
    const nextIds = new Set(updatingIds.value)
    nextIds.delete(id)
    updatingIds.value = nextIds
  }
}

function logout() {
  authStore.logout()
  router.push({ name: 'login' })
}

function isUpdating(id) {
  return updatingIds.value.has(id)
}

function actionForPedido(pedido) {
  const actions = {
    RECIBIDO: {
      label: 'Confirmar Orden',
      nextState: 'CONFIRMADO',
      type: 'primary',
    },
    CONFIRMADO: {
      label: 'Iniciar Cocina',
      nextState: 'EN_PREPARACION',
      type: 'warning',
    },
    EN_PREPARACION: {
      label: 'Marcar Listo',
      nextState: 'LISTO_PARA_RECOJO',
      type: 'success',
    },
  }

  return actions[pedido.estado] || null
}

function elapsedTime(createdAt) {
  const diffMs = Date.now() - new Date(createdAt).getTime()
  const minutes = Math.max(1, Math.floor(diffMs / 60000))

  if (minutes < 60) return `Hace ${minutes} min`

  const hours = Math.floor(minutes / 60)
  return `Hace ${hours} h ${minutes % 60} min`
}

function formatEstado(estado) {
  return estado
    .toLowerCase()
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function formatMoney(value) {
  return `S/ ${Number(value).toFixed(2)}`
}
</script>

<template>
  <main class="business-dashboard">
    <header class="operation-header">
      <div class="restaurant-title">
        <span>Panel operativo</span>
        <h1>Panel del Restaurante</h1>
        <p>{{ authStore.user?.username || 'Administrador' }}</p>
      </div>

      <div class="header-actions">
        <button
          class="toggle-button"
          :class="{ active: isOpen }"
          type="button"
          @click="isOpen = !isOpen"
        >
          <span class="toggle-track">
            <span class="toggle-thumb"></span>
          </span>
          {{ isOpen ? 'Abierto' : 'Cerrado' }}
        </button>

        <button class="logout-button" type="button" @click="logout">Cerrar Sesion</button>
      </div>
    </header>

    <section class="board-shell">
      <p v-if="errorMessage" class="error-banner" role="alert">
        {{ errorMessage }}
      </p>

      <div v-if="isLoading" class="loading-card">Cargando pedidos...</div>

      <section v-else class="kanban-board" aria-label="Tablero de pedidos">
        <section v-for="column in columns" :key="column.key" class="kanban-column">
          <header class="column-header">
            <div>
              <h2>{{ column.title }}</h2>
              <p>{{ column.subtitle }}</p>
            </div>
            <strong>{{ column.pedidos.length }}</strong>
          </header>

          <div class="ticket-list">
            <article v-for="pedido in column.pedidos" :key="pedido.id" class="order-ticket">
              <header class="ticket-header">
                <strong>#{{ pedido.id }}</strong>
                <span>{{ elapsedTime(pedido.creado_en) }}</span>
              </header>

              <ul class="items-list">
                <li v-for="detalle in pedido.detalles" :key="detalle.id">
                  <strong>{{ detalle.cantidad }}x</strong>
                  <span>{{ detalle.nombre_producto }}</span>
                </li>
              </ul>

              <div class="ticket-meta">
                <span>Total</span>
                <strong>{{ formatMoney(pedido.total) }}</strong>
              </div>

              <button
                v-if="actionForPedido(pedido)"
                class="action-button"
                :class="actionForPedido(pedido).type"
                :disabled="isUpdating(pedido.id)"
                type="button"
                @click="avanzarPedido(pedido.id, actionForPedido(pedido).nextState)"
              >
                {{ isUpdating(pedido.id) ? 'Actualizando...' : actionForPedido(pedido).label }}
              </button>

              <span v-else class="waiting-label">Esperando repartidor</span>
            </article>

            <div v-if="!column.pedidos.length" class="empty-column">
              Sin pedidos en esta etapa.
            </div>
          </div>
        </section>
      </section>
    </section>
  </main>
</template>

<style scoped>
.business-dashboard {
  min-height: 100vh;
  background: #f8fafc;
  color: #102033;
}

.operation-header {
  position: sticky;
  top: 0;
  z-index: 20;
  display: grid;
  gap: 14px;
  border-bottom: 1px solid #dce4ee;
  background: rgba(255, 255, 255, 0.94);
  padding: 16px;
  backdrop-filter: blur(14px);
}

.restaurant-title span {
  color: #0f4c5c;
  font-size: 0.75rem;
  font-weight: 850;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

h1,
h2,
p {
  margin: 0;
}

h1 {
  margin-top: 4px;
  color: #102033;
  font-size: 1.45rem;
  font-weight: 850;
  letter-spacing: 0;
  line-height: 1.15;
}

.restaurant-title p {
  margin-top: 4px;
  color: #607086;
  font-weight: 700;
}

.header-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.toggle-button,
.logout-button,
.action-button {
  display: inline-flex;
  min-height: 48px;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 850;
  transition:
    transform 180ms ease,
    background-color 180ms ease,
    border-color 180ms ease,
    box-shadow 180ms ease,
    opacity 180ms ease;
}

.toggle-button {
  gap: 10px;
  border: 1px solid #d6dee8;
  background: #ffffff;
  color: #607086;
}

.toggle-button.active {
  border-color: #16845f;
  color: #16704f;
}

.toggle-track {
  position: relative;
  width: 42px;
  height: 24px;
  border-radius: 999px;
  background: #cfd9e6;
  transition: background-color 180ms ease;
}

.toggle-button.active .toggle-track {
  background: #16845f;
}

.toggle-thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 18px;
  height: 18px;
  border-radius: 999px;
  background: #ffffff;
  transition: transform 180ms ease;
}

.toggle-button.active .toggle-thumb {
  transform: translateX(18px);
}

.logout-button {
  border: 1px solid #d6dee8;
  background: #ffffff;
  color: #102033;
}

.board-shell {
  padding: 16px;
}

.error-banner,
.loading-card {
  border: 1px solid #f1b9b9;
  border-radius: 14px;
  background: #fff5f5;
  color: #b42318;
  font-weight: 750;
  margin-bottom: 14px;
  padding: 14px 16px;
}

.loading-card {
  border-color: #dce4ee;
  background: #ffffff;
  color: #607086;
}

.kanban-board {
  display: grid;
  gap: 16px;
}

.kanban-column {
  border: 1px solid #dce4ee;
  border-radius: 18px;
  background: #eef3f8;
  padding: 14px;
}

.column-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 4px 2px 14px;
}

.column-header h2 {
  color: #102033;
  font-size: 1.1rem;
  font-weight: 850;
}

.column-header p {
  margin-top: 3px;
  color: #607086;
  font-size: 0.88rem;
  font-weight: 700;
}

.column-header strong {
  display: inline-grid;
  min-width: 34px;
  height: 34px;
  place-items: center;
  border-radius: 999px;
  background: #0f4c5c;
  color: #ffffff;
  font-weight: 850;
}

.ticket-list {
  display: grid;
  gap: 12px;
}

.order-ticket {
  display: grid;
  gap: 14px;
  border: 1px solid #e7dca9;
  border-radius: 14px;
  background: #fffdf3;
  box-shadow: 0 14px 28px rgba(16, 32, 51, 0.08);
  padding: 16px;
}

.ticket-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  border-bottom: 1px dashed #d9c983;
  padding-bottom: 10px;
}

.ticket-header strong {
  color: #102033;
  font-size: 1.75rem;
  font-weight: 900;
  letter-spacing: 0;
}

.ticket-header span {
  color: #8a6d1f;
  font-size: 0.9rem;
  font-weight: 850;
}

.items-list {
  display: grid;
  gap: 8px;
  list-style: none;
  margin: 0;
  padding: 0;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
}

.items-list li {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 8px;
  color: #102033;
}

.items-list strong {
  font-weight: 900;
}

.ticket-meta {
  display: flex;
  justify-content: space-between;
  border-top: 1px dashed #d9c983;
  color: #607086;
  padding-top: 10px;
}

.ticket-meta strong {
  color: #102033;
}

.action-button {
  width: 100%;
  border: 0;
  color: #ffffff;
  padding: 0 16px;
}

.action-button.primary {
  background: #0f4c5c;
  box-shadow: 0 12px 24px rgba(15, 76, 92, 0.2);
}

.action-button.warning {
  background: #b45309;
  box-shadow: 0 12px 24px rgba(180, 83, 9, 0.18);
}

.action-button.success {
  background: #16845f;
  box-shadow: 0 12px 24px rgba(22, 132, 95, 0.2);
}

.action-button:hover:not(:disabled),
.logout-button:hover,
.toggle-button:hover {
  transform: translateY(-1px);
}

.action-button:disabled {
  cursor: not-allowed;
  opacity: 0.72;
}

.waiting-label,
.empty-column {
  display: block;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.68);
  color: #607086;
  font-weight: 800;
  padding: 12px;
  text-align: center;
}

.empty-column {
  border: 1px dashed #c5d0dc;
}

@media (min-width: 768px) {
  .operation-header {
    grid-template-columns: 1fr auto;
    align-items: center;
    padding: 16px 24px;
  }

  .header-actions {
    grid-template-columns: auto auto;
  }

  .toggle-button,
  .logout-button {
    padding: 0 16px;
  }

  .board-shell {
    padding: 22px 24px;
  }

  .kanban-board {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    min-height: calc(100vh - 112px);
  }

  .kanban-column {
    display: flex;
    min-height: calc(100vh - 128px);
    flex-direction: column;
  }

  .ticket-list {
    flex: 1;
    overflow-y: auto;
    padding-right: 4px;
  }
}

@media (min-width: 1200px) {
  .board-shell {
    padding: 24px 32px;
  }
}
</style>
