<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '@/services/api'
import CartPanel from '@/components/cliente/CartPanel.vue'
import { useCartStore } from '@/stores/cart'

const cartStore = useCartStore()

const negocios = ref([])
const detallesPorNegocio = ref({})
const selectedNegocioId = ref(null)
const searchTerm = ref('')
const isLoading = ref(true)
const loadingDetailId = ref(null)
const errorMessage = ref('')
const feedbackMessage = ref('')

const filteredNegocios = computed(() => {
  const term = searchTerm.value.trim().toLowerCase()
  if (!term) return negocios.value

  return negocios.value.filter((negocio) =>
    [negocio.nombre, negocio.categoria, negocio.direccion].some((value) =>
      String(value || '')
        .toLowerCase()
        .includes(term),
    ),
  )
})

onMounted(() => {
  cargarNegocios()
})

async function cargarNegocios() {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const { data } = await api.get('catalogo/negocios/')
    negocios.value = data
  } catch {
    errorMessage.value = 'No pudimos cargar el catalogo. Intenta nuevamente.'
  } finally {
    isLoading.value = false
  }
}

async function toggleNegocio(negocio) {
  feedbackMessage.value = ''

  if (selectedNegocioId.value === negocio.id) {
    selectedNegocioId.value = null
    return
  }

  selectedNegocioId.value = negocio.id

  if (detallesPorNegocio.value[negocio.id]) return

  loadingDetailId.value = negocio.id

  try {
    const { data } = await api.get(`catalogo/negocios/${negocio.id}/`)
    detallesPorNegocio.value = {
      ...detallesPorNegocio.value,
      [negocio.id]: data,
    }
  } catch {
    feedbackMessage.value = 'No pudimos cargar el menu de este negocio.'
  } finally {
    loadingDetailId.value = null
  }
}

function addToCart(producto, negocio) {
  const result = cartStore.addProduct(producto, negocio)
  feedbackMessage.value = result.ok ? 'Producto agregado al carrito.' : result.message
}

function productDisabled(producto, negocio) {
  return !negocio.esta_abierto || !producto.disponible || producto.stock_disponible <= 0
}

function formatMoney(value) {
  return `S/ ${Number(value).toFixed(2)}`
}
</script>

<template>
  <main class="catalog-page">
    <section class="catalog-shell">
      <div class="catalog-main">
        <header class="catalog-header">
          <span class="eyebrow">Catalogo de restaurantes</span>
          <h1>Elige tu negocio favorito</h1>
          <p>Explora restaurantes activos, revisa su menu y arma tu pedido en un solo carrito.</p>

          <label class="search-box" for="search">
            <span>Buscar</span>
            <input
              id="search"
              v-model.trim="searchTerm"
              placeholder="Restaurante, categoria o direccion"
              type="search"
            />
          </label>
        </header>

        <p v-if="feedbackMessage" class="feedback-message" role="status">
          {{ feedbackMessage }}
        </p>

        <div v-if="isLoading" class="state-card">Cargando restaurantes...</div>
        <div v-else-if="errorMessage" class="state-card error-card">{{ errorMessage }}</div>

        <section v-else class="business-grid" aria-label="Restaurantes disponibles">
          <article
            v-for="negocio in filteredNegocios"
            :key="negocio.id"
            class="business-card"
            :class="{ closed: !negocio.esta_abierto, expanded: selectedNegocioId === negocio.id }"
          >
            <button class="business-summary" type="button" @click="toggleNegocio(negocio)">
              <div>
                <span class="category">{{ negocio.categoria }}</span>
                <h2>{{ negocio.nombre }}</h2>
                <p>{{ negocio.direccion }}</p>
              </div>

              <div class="business-meta">
                <span class="status-badge" :class="{ open: negocio.esta_abierto }">
                  {{ negocio.esta_abierto ? 'Abierto' : 'Cerrado' }}
                </span>
                <strong>{{ negocio.cantidad_productos }} productos</strong>
              </div>
            </button>

            <div v-if="selectedNegocioId === negocio.id" class="products-panel">
              <div v-if="loadingDetailId === negocio.id" class="products-loading">
                Cargando menu...
              </div>

              <ul v-else class="products-list">
                <li
                  v-for="producto in detallesPorNegocio[negocio.id]?.productos || []"
                  :key="producto.id"
                  class="product-item"
                  :class="{ muted: productDisabled(producto, negocio) }"
                >
                  <div>
                    <h3>{{ producto.nombre }}</h3>
                    <p>Stock disponible: {{ producto.stock_disponible }}</p>
                    <strong>{{ formatMoney(producto.precio) }}</strong>
                  </div>

                  <button
                    class="add-button"
                    :disabled="productDisabled(producto, negocio)"
                    type="button"
                    @click="addToCart(producto, negocio)"
                  >
                    Agregar
                  </button>
                </li>
              </ul>
            </div>
          </article>
        </section>
      </div>

      <CartPanel class="catalog-cart" />
    </section>
  </main>
</template>

<style scoped>
.catalog-page {
  min-height: 100vh;
  background: var(--app-background);
  color: var(--app-text);
  padding: 18px 16px 32px;
}

.catalog-shell {
  display: grid;
  gap: 18px;
  width: 100%;
  max-width: 1180px;
  margin: 0 auto;
}

.catalog-header {
  display: grid;
  gap: 12px;
  margin-bottom: 18px;
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
h3,
p {
  margin: 0;
}

h1 {
  color: var(--app-text);
  font-size: clamp(2rem, 8vw, 3.5rem);
  font-weight: 850;
  letter-spacing: 0;
  line-height: 1.05;
}

.catalog-header p {
  color: var(--app-muted);
  line-height: 1.7;
}

.search-box {
  display: grid;
  gap: 8px;
  margin-top: 10px;
}

.search-box span {
  color: var(--app-text);
  font-weight: 800;
}

.search-box input {
  width: 100%;
  min-height: 52px;
  border: 1px solid var(--app-border);
  border-radius: 12px;
  outline: none;
  padding: 0 16px;
  transition:
    border-color 180ms ease,
    box-shadow 180ms ease;
}

.search-box input:focus {
  border-color: var(--app-primary);
  box-shadow: 0 0 0 4px rgba(15, 76, 92, 0.12);
}

.feedback-message,
.state-card {
  border: 1px solid var(--app-border);
  border-radius: 14px;
  background: var(--app-surface);
  color: var(--app-muted);
  padding: 14px 16px;
}

.feedback-message {
  margin-bottom: 14px;
  color: var(--app-primary);
  font-weight: 750;
}

.error-card {
  border-color: #f1b9b9;
  background: #fff5f5;
  color: #b42318;
}

.business-grid {
  display: grid;
  gap: 16px;
}

.business-card {
  overflow: hidden;
  border: 1px solid var(--app-border);
  border-radius: 18px;
  background: var(--app-surface);
  box-shadow: var(--app-shadow-soft);
  transition:
    transform 180ms ease,
    border-color 180ms ease,
    box-shadow 180ms ease;
}

.business-card:hover {
  transform: translateY(-2px);
  border-color: #b9ccd9;
}

.business-card.closed {
  opacity: 0.72;
}

.business-summary {
  display: grid;
  width: 100%;
  gap: 14px;
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  padding: 18px;
  text-align: left;
}

.category {
  color: var(--app-primary);
  font-size: 0.78rem;
  font-weight: 850;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.business-summary h2 {
  margin-top: 8px;
  color: var(--app-text);
  font-size: 1.28rem;
  font-weight: 850;
}

.business-summary p {
  margin-top: 6px;
  color: var(--app-muted);
  line-height: 1.55;
}

.business-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.business-meta strong {
  color: var(--app-muted);
  font-size: 0.9rem;
}

.status-badge {
  display: inline-flex;
  border-radius: 999px;
  background: #fff5f5;
  color: #b42318;
  font-size: 0.8rem;
  font-weight: 850;
  padding: 7px 10px;
}

.status-badge.open {
  background: #ecfdf5;
  color: #16704f;
}

.products-panel {
  border-top: 1px solid var(--app-border);
  background: #fbfcfe;
  padding: 14px;
}

.products-loading {
  color: var(--app-muted);
  padding: 10px;
}

.products-list {
  display: grid;
  gap: 12px;
  list-style: none;
  margin: 0;
  padding: 0;
}

.product-item {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 14px;
  align-items: center;
  border: 1px solid var(--app-border);
  border-radius: 14px;
  background: #ffffff;
  padding: 14px;
}

.product-item.muted {
  opacity: 0.55;
}

.product-item h3 {
  color: var(--app-text);
  font-size: 1rem;
  font-weight: 850;
}

.product-item p {
  margin-top: 4px;
  color: var(--app-muted);
  font-size: 0.9rem;
}

.product-item strong {
  display: block;
  margin-top: 8px;
  color: var(--app-text);
  font-size: 1.05rem;
}

.add-button {
  min-height: 44px;
  border: 0;
  border-radius: 11px;
  background: var(--app-primary);
  color: #ffffff;
  cursor: pointer;
  font-weight: 850;
  padding: 0 16px;
  transition:
    transform 180ms ease,
    background-color 180ms ease,
    opacity 180ms ease;
}

.add-button:hover:not(:disabled) {
  transform: translateY(-1px);
  background: var(--app-primary-hover);
}

.add-button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

@media (min-width: 768px) {
  .catalog-page {
    padding: 34px 24px 48px;
  }

  .business-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .business-card.expanded {
    grid-column: 1 / -1;
  }

  .business-summary {
    grid-template-columns: 1fr auto;
  }
}

@media (min-width: 1024px) {
  .catalog-shell {
    grid-template-columns: minmax(0, 1fr) 340px;
    align-items: start;
  }

  .catalog-cart {
    position: sticky;
    top: 96px;
  }
}
</style>
