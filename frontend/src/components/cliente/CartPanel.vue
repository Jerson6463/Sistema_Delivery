<script setup>
import { RouterLink } from 'vue-router'
import { useCartStore } from '@/stores/cart'

const cartStore = useCartStore()

function formatMoney(value) {
  return `S/ ${Number(value).toFixed(2)}`
}
</script>

<template>
  <aside class="cart-panel" aria-label="Carrito de compras">
    <header class="cart-header">
      <div>
        <span>Carrito</span>
        <h2>{{ cartStore.negocioNombre || 'Sin negocio seleccionado' }}</h2>
      </div>
      <strong>{{ cartStore.totalItems }}</strong>
    </header>

    <div v-if="cartStore.isEmpty" class="empty-cart">
      <p>Agrega productos desde el catalogo para preparar tu pedido.</p>
    </div>

    <div v-else class="cart-content">
      <ul class="cart-list">
        <li v-for="item in cartStore.items" :key="item.productoId" class="cart-item">
          <div>
            <h3>{{ item.nombre }}</h3>
            <p>{{ formatMoney(item.precio) }}</p>
          </div>

          <div class="quantity-control">
            <button type="button" @click="cartStore.decrement(item.productoId)">-</button>
            <span>{{ item.cantidad }}</span>
            <button
              type="button"
              :disabled="item.cantidad >= item.stockDisponible"
              @click="cartStore.increment(item.productoId)"
            >
              +
            </button>
          </div>
        </li>
      </ul>

      <div class="totals">
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

      <div class="cart-actions">
        <RouterLink class="checkout-button" :to="{ name: 'checkout' }">
          Continuar pedido
        </RouterLink>
        <button class="clear-button" type="button" @click="cartStore.clearCart">Limpiar</button>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.cart-panel {
  width: 100%;
  border: 1px solid var(--app-border);
  border-radius: 18px;
  background: var(--app-surface);
  box-shadow: var(--app-shadow-soft);
  padding: 18px;
}

.cart-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  border-bottom: 1px solid var(--app-border);
  padding-bottom: 16px;
}

.cart-header span {
  color: var(--app-muted);
  font-size: 0.78rem;
  font-weight: 850;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.cart-header h2,
.cart-item h3,
.empty-cart p {
  margin: 0;
}

.cart-header h2 {
  margin-top: 4px;
  color: var(--app-text);
  font-size: 1rem;
  font-weight: 850;
}

.cart-header strong {
  display: inline-grid;
  min-width: 34px;
  height: 34px;
  place-items: center;
  border-radius: 999px;
  background: var(--app-primary);
  color: #ffffff;
  font-weight: 850;
}

.empty-cart {
  padding: 20px 0 4px;
}

.empty-cart p {
  color: var(--app-muted);
  line-height: 1.6;
}

.cart-content {
  display: grid;
  gap: 18px;
  padding-top: 16px;
}

.cart-list {
  display: grid;
  gap: 14px;
  list-style: none;
  margin: 0;
  padding: 0;
}

.cart-item {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 14px;
  align-items: center;
}

.cart-item h3 {
  color: var(--app-text);
  font-size: 0.98rem;
  font-weight: 800;
}

.cart-item p {
  margin: 4px 0 0;
  color: var(--app-muted);
}

.quantity-control {
  display: inline-grid;
  grid-template-columns: 36px 34px 36px;
  align-items: center;
  border: 1px solid var(--app-border);
  border-radius: 999px;
  overflow: hidden;
}

.quantity-control button {
  min-height: 36px;
  border: 0;
  background: #ffffff;
  color: var(--app-text);
  cursor: pointer;
  font-weight: 850;
}

.quantity-control button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.quantity-control span {
  text-align: center;
  font-weight: 850;
}

.totals {
  display: grid;
  gap: 10px;
  border-top: 1px solid var(--app-border);
  padding-top: 16px;
}

.totals div {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  color: var(--app-muted);
}

.totals strong {
  color: var(--app-text);
}

.grand-total {
  font-size: 1.14rem;
  font-weight: 850;
}

.grand-total span,
.grand-total strong {
  color: var(--app-text);
  font-weight: 850;
}

.cart-actions {
  display: grid;
  gap: 10px;
}

.checkout-button,
.clear-button {
  display: inline-flex;
  min-height: 48px;
  align-items: center;
  justify-content: center;
  border-radius: 11px;
  cursor: pointer;
  font-weight: 850;
  transition:
    transform 180ms ease,
    background-color 180ms ease,
    box-shadow 180ms ease;
}

.checkout-button {
  background: var(--app-primary);
  box-shadow: 0 14px 28px rgba(15, 76, 92, 0.2);
  color: #ffffff;
}

.clear-button {
  border: 1px solid var(--app-border);
  background: #ffffff;
  color: var(--app-text);
}

.checkout-button:hover,
.clear-button:hover {
  transform: translateY(-1px);
}

.checkout-button:hover {
  background: var(--app-primary-hover);
}
</style>
