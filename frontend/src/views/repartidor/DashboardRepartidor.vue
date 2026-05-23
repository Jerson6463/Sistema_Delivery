<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const ESTADOS_ACTIVOS = ['LISTO_PARA_RECOJO', 'EN_CAMINO']

const router = useRouter()
const authStore = useAuthStore()

const pedidoActivo = ref(null)
const isLoading = ref(true)
const isUpdating = ref(false)
const errorMessage = ref('')

const estadoActualLabel = computed(() => {
  if (!pedidoActivo.value) return ''
  return pedidoActivo.value.estado_display || formatEstado(pedidoActivo.value.estado)
})

const resumenPedido = computed(() => {
  const detalles = pedidoActivo.value?.detalles || []

  if (!detalles.length) return 'Resumen no disponible'

  return detalles
    .map((detalle) => `${detalle.cantidad}x ${detalle.nombre_producto || 'Producto'}`)
    .join(', ')
})

onMounted(() => {
  cargarPedidoActivo()
})

async function cargarPedidoActivo() {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const { data } = await api.get('pedidos/')
    pedidoActivo.value = data.find((pedido) => ESTADOS_ACTIVOS.includes(pedido.estado)) || null
  } catch {
    errorMessage.value = 'No pudimos cargar tus pedidos asignados. Intenta nuevamente.'
  } finally {
    isLoading.value = false
  }
}

async function actualizarEstado(nuevoEstado) {
  if (!pedidoActivo.value || isUpdating.value) return

  isUpdating.value = true
  errorMessage.value = ''

  try {
    await api.post(`pedidos/${pedidoActivo.value.id}/transicion/`, {
      nuevo_estado: nuevoEstado,
    })

    if (nuevoEstado === 'ENTREGADO') {
      pedidoActivo.value = null
      return
    }

    pedidoActivo.value = {
      ...pedidoActivo.value,
      estado: nuevoEstado,
      estado_display: formatEstado(nuevoEstado),
    }
  } catch (error) {
    errorMessage.value =
      error.response?.data?.error ||
      error.response?.data?.detail ||
      'No pudimos actualizar el estado del pedido.'
  } finally {
    isUpdating.value = false
  }
}

function logout() {
  authStore.logout()
  router.push({ name: 'login' })
}

function formatEstado(estado) {
  return estado
    .toLowerCase()
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}
</script>

<template>
  <main class="driver-dashboard">
    <header class="dashboard-header">
      <div>
        <span class="eyebrow">Panel de repartidor</span>
        <h1>Mi Ruta Actual</h1>
      </div>

      <button class="logout-button" type="button" @click="logout">Cerrar Sesion</button>
    </header>

    <section class="dashboard-content">
      <div v-if="isLoading" class="state-card">
        <div class="loader" aria-hidden="true"></div>
        <p>Buscando pedidos...</p>
      </div>

      <div v-else-if="errorMessage" class="state-card error-card" role="alert">
        <p>{{ errorMessage }}</p>
        <button class="secondary-button" type="button" @click="cargarPedidoActivo">
          Reintentar
        </button>
      </div>

      <article v-else-if="pedidoActivo" class="order-card">
        <div class="order-header">
          <div>
            <span class="eyebrow">Pedido activo</span>
            <h2>Pedido #{{ pedidoActivo.id }}</h2>
          </div>

          <span class="status-badge" :class="pedidoActivo.estado.toLowerCase()">
            {{ estadoActualLabel }}
          </span>
        </div>

        <div class="route-grid">
          <section class="route-block">
            <span class="route-label">Origen</span>
            <h3>{{ pedidoActivo.nombre_negocio || 'Negocio asignado' }}</h3>
            <p>{{ pedidoActivo.direccion_negocio || 'Direccion del negocio no disponible' }}</p>
          </section>

          <section class="route-block">
            <span class="route-label">Destino</span>
            <h3>{{ pedidoActivo.nombre_cliente || 'Cliente' }}</h3>
            <p>{{ pedidoActivo.direccion_entrega }}</p>
          </section>
        </div>

        <section class="details-card">
          <div>
            <span class="route-label">Detalles</span>
            <p>{{ resumenPedido }}</p>
          </div>
          <strong>S/ {{ pedidoActivo.total }}</strong>
        </section>

        <div class="actions">
          <button
            v-if="pedidoActivo.estado === 'LISTO_PARA_RECOJO'"
            class="primary-button"
            :disabled="isUpdating"
            type="button"
            @click="actualizarEstado('EN_CAMINO')"
          >
            {{ isUpdating ? 'Actualizando...' : 'Recoger y poner En Camino' }}
          </button>

          <button
            v-if="pedidoActivo.estado === 'EN_CAMINO'"
            class="success-button"
            :disabled="isUpdating"
            type="button"
            @click="actualizarEstado('ENTREGADO')"
          >
            {{ isUpdating ? 'Actualizando...' : 'Marcar como Entregado' }}
          </button>
        </div>
      </article>

      <div v-else class="state-card empty-card">
        <h2>No tienes pedidos activos</h2>
        <p>Cuando tengas una entrega lista para recojo, aparecera en esta pantalla.</p>
        <button class="secondary-button" type="button" @click="cargarPedidoActivo">
          Actualizar
        </button>
      </div>
    </section>
  </main>
</template>

<style scoped>
.driver-dashboard {
  min-height: 100vh;
  background: #f8fafc;
  color: #102033;
}

.dashboard-header {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  border-bottom: 1px solid #dce4ee;
  background: rgba(255, 255, 255, 0.94);
  padding: 16px;
  backdrop-filter: blur(14px);
}

.eyebrow {
  display: block;
  color: #0f4c5c;
  font-size: 0.72rem;
  font-weight: 850;
  letter-spacing: 0.08em;
  line-height: 1.2;
  text-transform: uppercase;
}

h1,
h2,
h3,
p {
  margin: 0;
}

h1 {
  margin-top: 4px;
  color: #102033;
  font-size: 1.35rem;
  font-weight: 850;
  letter-spacing: 0;
  line-height: 1.15;
}

.logout-button,
.primary-button,
.success-button,
.secondary-button {
  display: inline-flex;
  min-height: 50px;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 800;
  transition:
    transform 180ms ease,
    box-shadow 180ms ease,
    background-color 180ms ease,
    border-color 180ms ease,
    opacity 180ms ease;
}

.logout-button {
  min-height: 44px;
  border: 1px solid #cfd9e6;
  background: #ffffff;
  color: #102033;
  padding: 0 14px;
  white-space: nowrap;
}

.logout-button:hover {
  border-color: #0f4c5c;
  color: #0f4c5c;
}

.dashboard-content {
  width: 100%;
  padding: 18px 16px 28px;
}

.order-card,
.state-card {
  width: 100%;
  border: 1px solid #dce4ee;
  border-radius: 18px;
  background: #ffffff;
  box-shadow: 0 14px 34px rgba(16, 32, 51, 0.07);
  padding: 20px;
}

.order-header {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 20px;
}

h2 {
  margin-top: 4px;
  color: #102033;
  font-size: 1.55rem;
  font-weight: 850;
  letter-spacing: 0;
  line-height: 1.15;
}

.status-badge {
  display: inline-flex;
  width: fit-content;
  align-items: center;
  border-radius: 999px;
  background: #e8f3f5;
  color: #0f4c5c;
  font-size: 0.82rem;
  font-weight: 850;
  padding: 8px 12px;
}

.status-badge.en_camino {
  background: #ecfdf5;
  color: #16704f;
}

.route-grid {
  display: grid;
  gap: 14px;
}

.route-block,
.details-card {
  border: 1px solid #dce4ee;
  border-radius: 14px;
  background: #f8fafc;
  padding: 16px;
}

.route-label {
  display: block;
  color: #607086;
  font-size: 0.78rem;
  font-weight: 850;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

h3 {
  margin-top: 8px;
  color: #102033;
  font-size: 1.05rem;
  font-weight: 850;
  line-height: 1.25;
}

.route-block p,
.details-card p,
.state-card p {
  margin-top: 8px;
  color: #607086;
  line-height: 1.6;
}

.details-card {
  display: grid;
  gap: 14px;
  margin-top: 14px;
  background: #ffffff;
}

.details-card strong {
  color: #102033;
  font-size: 1.35rem;
  font-weight: 850;
}

.actions {
  margin-top: 18px;
}

.primary-button,
.success-button,
.secondary-button {
  width: 100%;
  border: 0;
  color: #ffffff;
  padding: 0 18px;
}

.primary-button {
  background: #0f4c5c;
  box-shadow: 0 14px 28px rgba(15, 76, 92, 0.22);
}

.success-button {
  background: #16845f;
  box-shadow: 0 14px 28px rgba(22, 132, 95, 0.22);
}

.secondary-button {
  border: 1px solid #cfd9e6;
  background: #ffffff;
  color: #102033;
}

.primary-button:hover:not(:disabled),
.success-button:hover:not(:disabled),
.secondary-button:hover:not(:disabled),
.logout-button:hover {
  transform: translateY(-1px);
}

.primary-button:hover:not(:disabled) {
  background: #0a3d4b;
}

.success-button:hover:not(:disabled) {
  background: #116b4d;
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.72;
}

.state-card {
  display: grid;
  justify-items: center;
  gap: 14px;
  text-align: center;
}

.state-card h2 {
  margin: 0;
}

.error-card {
  border-color: #f1b9b9;
  background: #fffafa;
}

.error-card p {
  color: #b42318;
  font-weight: 650;
}

.loader {
  width: 34px;
  height: 34px;
  border: 4px solid #dce4ee;
  border-top-color: #0f4c5c;
  border-radius: 999px;
  animation: spin 800ms linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (min-width: 768px) {
  .dashboard-header {
    padding: 18px calc((100% - 800px) / 2);
  }

  .dashboard-content {
    max-width: 800px;
    margin: 0 auto;
    padding: 34px 24px 48px;
  }

  .order-card,
  .state-card {
    box-shadow: 0 24px 60px rgba(16, 32, 51, 0.1);
    padding: 28px;
  }

  .order-header {
    flex-direction: row;
    align-items: flex-start;
    justify-content: space-between;
  }

  .route-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .details-card {
    grid-template-columns: 1fr auto;
    align-items: start;
  }
}

@media (min-width: 1024px) {
  .dashboard-content {
    max-width: 900px;
  }
}
</style>
