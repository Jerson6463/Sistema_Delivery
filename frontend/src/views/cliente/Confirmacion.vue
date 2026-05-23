<script setup>
import { computed, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import api from '@/services/api'
import { useCartStore } from '@/stores/cart'

const router = useRouter()
const cartStore = useCartStore()

const direccionEntrega = ref('')
const isLoading = ref(false)
const errorMessage = ref('')

const payload = computed(() => ({
  negocio: cartStore.negocioId,
  direccion_entrega: direccionEntrega.value,
  detalles: cartStore.items.map((item) => ({
    producto: item.productoId,
    cantidad: item.cantidad,
  })),
}))

async function confirmarPedido() {
  if (cartStore.isEmpty) return

  errorMessage.value = ''
  isLoading.value = true

  try {
    await api.post('pedidos/', payload.value)
    cartStore.clearCart()
    router.push({ name: 'mis-pedidos' })
  } catch (error) {
    errorMessage.value = extractDjangoError(error)
  } finally {
    isLoading.value = false
  }
}

function extractDjangoError(error) {
  const data = error.response?.data

  if (typeof data === 'string') return data
  if (Array.isArray(data)) return data[0]
  if (data?.detail) return data.detail
  if (data?.error) return data.error
  if (data?.non_field_errors?.length) return data.non_field_errors[0]

  if (data && typeof data === 'object') {
    const firstKey = Object.keys(data)[0]
    const firstValue = data[firstKey]

    if (Array.isArray(firstValue)) return `${firstKey}: ${firstValue[0]}`
    if (typeof firstValue === 'string') return `${firstKey}: ${firstValue}`
  }

  return 'No pudimos procesar el pedido. Verifica la disponibilidad e intenta nuevamente.'
}

function formatMoney(value) {
  return `S/ ${Number(value).toFixed(2)}`
}
</script>

<template>
  <main class="confirm-page">
    <section class="confirm-shell">
      <header class="confirm-header">
        <span class="eyebrow">Confirmacion de pedido</span>
        <h1>Revisa y confirma tu compra</h1>
        <p>Valida la direccion de entrega antes de enviar el pedido al negocio.</p>
      </header>

      <div v-if="cartStore.isEmpty" class="empty-card">
        <h2>Tu carrito esta vacio</h2>
        <p>Agrega productos desde el catalogo para poder confirmar un pedido.</p>
        <RouterLink class="primary-link" :to="{ name: 'catalogo' }">Ir al catalogo</RouterLink>
      </div>

      <div v-else class="checkout-grid">
        <form class="checkout-card" @submit.prevent="confirmarPedido">
          <div class="form-group">
            <label for="direccion_entrega">Direccion de Entrega</label>
            <textarea
              id="direccion_entrega"
              v-model.trim="direccionEntrega"
              placeholder="Ej. Av. Principal 123, referencia frente al parque"
              required
              rows="4"
            ></textarea>
          </div>

          <p v-if="errorMessage" class="error-alert" role="alert">
            {{ errorMessage }}
          </p>

          <button class="confirm-button" :disabled="isLoading" type="submit">
            {{ isLoading ? 'Procesando pedido...' : 'Confirmar y Pagar Pedido' }}
          </button>
        </form>

        <aside class="summary-card">
          <span class="eyebrow">Resumen final</span>
          <h2>{{ cartStore.negocioNombre }}</h2>

          <ul class="summary-list">
            <li v-for="item in cartStore.items" :key="item.productoId">
              <span>{{ item.cantidad }}x {{ item.nombre }}</span>
              <strong>{{ formatMoney(item.precio * item.cantidad) }}</strong>
            </li>
          </ul>

          <div class="summary-totals">
            <div>
              <span>Subtotal</span>
              <strong>{{ formatMoney(cartStore.subtotal) }}</strong>
            </div>
            <div>
              <span>Envio</span>
              <strong>{{ formatMoney(cartStore.deliveryFee) }}</strong>
            </div>
            <div class="grand-total">
              <span>Total</span>
              <strong>{{ formatMoney(cartStore.total) }}</strong>
            </div>
          </div>
        </aside>
      </div>
    </section>
  </main>
</template>

<style scoped>
.confirm-page {
  min-height: 100vh;
  background: var(--app-background);
  color: var(--app-text);
  padding: 22px 16px 34px;
}

.confirm-shell {
  width: 100%;
  max-width: 980px;
  margin: 0 auto;
}

.confirm-header {
  margin-bottom: 20px;
}

.eyebrow {
  color: var(--app-primary);
  font-size: 0.78rem;
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
  margin-top: 8px;
  color: var(--app-text);
  font-size: clamp(2rem, 8vw, 3.2rem);
  font-weight: 850;
  letter-spacing: 0;
  line-height: 1.08;
}

.confirm-header p {
  margin-top: 12px;
  color: var(--app-muted);
  line-height: 1.7;
}

.checkout-grid {
  display: grid;
  gap: 18px;
}

.checkout-card,
.summary-card,
.empty-card {
  border: 1px solid var(--app-border);
  border-radius: 18px;
  background: var(--app-surface);
  box-shadow: var(--app-shadow-soft);
  padding: 20px;
}

.form-group {
  display: grid;
  gap: 8px;
}

label {
  color: var(--app-text);
  font-weight: 850;
}

textarea {
  width: 100%;
  resize: vertical;
  border: 1px solid var(--app-border);
  border-radius: 12px;
  outline: none;
  padding: 14px;
  transition:
    border-color 180ms ease,
    box-shadow 180ms ease;
}

textarea:focus {
  border-color: var(--app-primary);
  box-shadow: 0 0 0 4px rgba(15, 76, 92, 0.12);
}

.error-alert {
  border: 1px solid #f1b9b9;
  border-radius: 12px;
  background: #fff5f5;
  color: #b42318;
  font-weight: 700;
  line-height: 1.55;
  margin-top: 16px;
  padding: 13px 14px;
}

.confirm-button,
.primary-link {
  display: inline-flex;
  width: 100%;
  min-height: 52px;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 12px;
  background: var(--app-primary);
  box-shadow: 0 14px 28px rgba(15, 76, 92, 0.22);
  color: #ffffff;
  cursor: pointer;
  font-weight: 850;
  margin-top: 18px;
  transition:
    transform 180ms ease,
    background-color 180ms ease,
    box-shadow 180ms ease,
    opacity 180ms ease;
}

.confirm-button:hover:not(:disabled),
.primary-link:hover {
  transform: translateY(-1px);
  background: var(--app-primary-hover);
}

.confirm-button:disabled {
  cursor: not-allowed;
  opacity: 0.72;
}

.summary-card h2 {
  margin-top: 8px;
  color: var(--app-text);
  font-size: 1.35rem;
  font-weight: 850;
}

.summary-list {
  display: grid;
  gap: 12px;
  list-style: none;
  margin: 18px 0;
  padding: 0;
}

.summary-list li,
.summary-totals div {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.summary-list span,
.summary-totals span {
  color: var(--app-muted);
}

.summary-list strong,
.summary-totals strong {
  color: var(--app-text);
}

.summary-totals {
  display: grid;
  gap: 10px;
  border-top: 1px solid var(--app-border);
  padding-top: 16px;
}

.grand-total span,
.grand-total strong {
  color: var(--app-text);
  font-size: 1.16rem;
  font-weight: 850;
}

.empty-card {
  display: grid;
  gap: 12px;
  text-align: center;
}

.empty-card h2 {
  color: var(--app-text);
  font-weight: 850;
}

.empty-card p {
  color: var(--app-muted);
}

@media (min-width: 768px) {
  .confirm-page {
    padding: 42px 24px 56px;
  }

  .checkout-grid {
    grid-template-columns: minmax(0, 1fr) 340px;
    align-items: start;
  }

  .checkout-card,
  .summary-card,
  .empty-card {
    padding: 28px;
    box-shadow: 0 24px 60px rgba(16, 32, 51, 0.1);
  }

  .summary-card {
    position: sticky;
    top: 96px;
  }
}
</style>
