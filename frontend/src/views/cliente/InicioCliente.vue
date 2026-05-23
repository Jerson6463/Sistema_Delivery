<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useCartStore } from '@/stores/cart'

const authStore = useAuthStore()
const cartStore = useCartStore()

const nombreCliente = computed(() => {
  return (
    authStore.user?.first_name ||
    authStore.user?.nombre ||
    authStore.user?.username ||
    'Cliente'
  )
})

const cantidadCarrito = computed(() => {
  return cartStore.items?.length || 0
})

const totalCarrito = computed(() => {
  return Number(cartStore.total || 0).toFixed(2)
})
</script>

<template>
  <main class="client-home">
    <section class="client-shell">
      <section class="welcome-card">
        <div class="welcome-content">
          <span class="eyebrow">Panel del cliente</span>

          <h1>
            Hola, <span>{{ nombreCliente }}</span>
          </h1>

          <p>
            Bienvenido a DeliveryPro. Explora restaurantes, realiza pedidos y sigue tus entregas
            de manera rápida y segura.
          </p>

          <div class="welcome-actions">
            <RouterLink class="btn btn-primary" :to="{ name: 'catalogo' }">
              Explorar restaurantes
            </RouterLink>

            <RouterLink class="btn btn-secondary" :to="{ name: 'mis-pedidos' }">
              Ver mis pedidos
            </RouterLink>
          </div>
        </div>

        <aside class="summary-card" aria-label="Resumen del cliente">
          <div class="summary-header">
            <span>Tu compra actual</span>
          </div>

          <div class="summary-metric">
            <strong>{{ cantidadCarrito }}</strong>
            <p>Productos en carrito</p>
          </div>

          <div class="summary-total">
            <span>Total estimado</span>
            <strong>S/ {{ totalCarrito }}</strong>
          </div>

          <RouterLink
            v-if="cantidadCarrito > 0"
            class="checkout-link"
            :to="{ name: 'checkout' }"
          >
            Continuar con mi pedido
          </RouterLink>

          <p v-else class="empty-cart-text">
            Aún no tienes productos agregados. Empieza explorando el catálogo.
          </p>
        </aside>
      </section>

      <section class="quick-actions-section">
        <header class="section-heading">
          <span class="eyebrow">Accesos rápidos</span>
          <h2>¿Qué deseas hacer hoy?</h2>
        </header>

        <div class="quick-actions-grid">
          <RouterLink class="action-card" :to="{ name: 'catalogo' }">
            <div class="action-icon">🍽️</div>
            <h3>Pedir comida</h3>
            <p>Explora negocios activos y encuentra productos disponibles.</p>
          </RouterLink>

          <RouterLink class="action-card" :to="{ name: 'mis-pedidos' }">
            <div class="action-icon">📦</div>
            <h3>Mis pedidos</h3>
            <p>Consulta el estado de tus pedidos y revisa su seguimiento.</p>
          </RouterLink>

          <RouterLink class="action-card" :to="{ name: 'checkout' }">
            <div class="action-icon">🛒</div>
            <h3>Mi carrito</h3>
            <p>Finaliza tu compra y confirma la dirección de entrega.</p>
          </RouterLink>
        </div>
      </section>

      <section class="process-section">
        <header class="section-heading">
          <span class="eyebrow">Cómo funciona</span>
          <h2>Tu pedido en tres pasos</h2>
        </header>

        <div class="process-grid">
          <article class="process-card">
            <span>01</span>
            <h3>Selecciona</h3>
            <p>Busca un restaurante, revisa su menú y agrega productos al carrito.</p>
          </article>

          <article class="process-card">
            <span>02</span>
            <h3>Confirma</h3>
            <p>Verifica el total, registra tu dirección y confirma tu pedido.</p>
          </article>

          <article class="process-card">
            <span>03</span>
            <h3>Recibe</h3>
            <p>Sigue el estado de tu pedido hasta que llegue a tu ubicación.</p>
          </article>
        </div>
      </section>
    </section>
  </main>
</template>

<style scoped>
.client-home {
  min-height: 100vh;
  background: var(--app-background);
  color: var(--app-text);
  padding: 34px 24px 58px;
}

.client-shell {
  display: grid;
  width: 100%;
  max-width: 1180px;
  margin: 0 auto;
  gap: 46px;
}

.welcome-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 350px;
  gap: 28px;
  align-items: stretch;
  border: 1px solid var(--app-border);
  border-radius: 22px;
  background:
    linear-gradient(135deg, rgba(232, 243, 245, 0.92), rgba(255, 255, 255, 0.96)),
    var(--app-surface);
  box-shadow: var(--app-shadow-soft);
  padding: 34px;
}

.welcome-content {
  display: flex;
  flex-direction: column;
  justify-content: center;
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
  margin-top: 14px;
  color: var(--app-text);
  font-size: clamp(2.2rem, 5vw, 4rem);
  font-weight: 850;
  line-height: 1.05;
}

h1 span {
  color: var(--app-primary);
}

.welcome-content p {
  max-width: 640px;
  margin-top: 18px;
  color: var(--app-muted);
  font-size: 1.05rem;
  line-height: 1.75;
}

.welcome-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 28px;
}

.btn {
  display: inline-flex;
  min-height: 52px;
  align-items: center;
  justify-content: center;
  border: 1px solid transparent;
  border-radius: 12px;
  padding: 0 22px;
  font-weight: 800;
  transition:
    transform 180ms ease,
    box-shadow 180ms ease,
    background-color 180ms ease,
    border-color 180ms ease,
    color 180ms ease;
}

.btn:hover {
  transform: translateY(-2px);
}

.btn-primary {
  background: var(--app-primary);
  box-shadow: 0 14px 28px rgba(15, 76, 92, 0.22);
  color: #ffffff;
}

.btn-primary:hover {
  background: var(--app-primary-hover);
}

.btn-secondary {
  border-color: var(--app-border);
  background: #ffffff;
  color: var(--app-text);
}

.btn-secondary:hover {
  border-color: var(--app-primary);
  color: var(--app-primary);
}

.summary-card {
  display: grid;
  gap: 18px;
  border: 1px solid var(--app-border);
  border-radius: 18px;
  background: #ffffff;
  padding: 24px;
}

.summary-header {
  color: var(--app-muted);
  font-weight: 750;
}

.summary-metric {
  border-radius: 16px;
  background: var(--app-surface-strong);
  padding: 20px;
}

.summary-metric strong {
  display: block;
  color: var(--app-primary);
  font-size: 2.6rem;
  font-weight: 900;
}

.summary-metric p {
  margin-top: 4px;
  color: var(--app-muted);
}

.summary-total {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--app-muted);
  font-weight: 750;
}

.summary-total strong {
  color: var(--app-text);
  font-size: 1.3rem;
  font-weight: 850;
}

.checkout-link {
  display: inline-flex;
  min-height: 48px;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: var(--app-primary);
  color: #ffffff;
  font-weight: 850;
  transition:
    transform 180ms ease,
    background-color 180ms ease;
}

.checkout-link:hover {
  transform: translateY(-1px);
  background: var(--app-primary-hover);
}

.empty-cart-text {
  color: var(--app-muted);
  font-size: 0.94rem;
  line-height: 1.6;
}

.section-heading {
  display: grid;
  gap: 12px;
  max-width: 680px;
}

h2 {
  color: var(--app-text);
  font-size: clamp(1.8rem, 4vw, 2.8rem);
  font-weight: 850;
  line-height: 1.12;
}

.quick-actions-grid,
.process-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
  margin-top: 26px;
}

.action-card,
.process-card {
  border: 1px solid var(--app-border);
  border-radius: 18px;
  background: #ffffff;
  box-shadow: var(--app-shadow-soft);
  padding: 26px;
  transition:
    transform 180ms ease,
    border-color 180ms ease,
    box-shadow 180ms ease;
}

.action-card:hover {
  transform: translateY(-4px);
  border-color: #b9ccd9;
}

.action-icon {
  display: grid;
  width: 54px;
  height: 54px;
  place-items: center;
  border-radius: 16px;
  background: var(--app-primary-soft);
  font-size: 1.6rem;
}

.action-card h3,
.process-card h3 {
  margin-top: 18px;
  color: var(--app-text);
  font-size: 1.18rem;
  font-weight: 850;
}

.action-card p,
.process-card p {
  margin-top: 10px;
  color: var(--app-muted);
  line-height: 1.7;
}

.process-card span {
  display: inline-flex;
  color: var(--app-primary);
  font-size: 0.88rem;
  font-weight: 900;
  letter-spacing: 0.08em;
}

@media (max-width: 960px) {
  .welcome-card {
    grid-template-columns: 1fr;
  }

  .quick-actions-grid,
  .process-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .client-home {
    padding: 24px 16px 42px;
  }

  .welcome-card {
    padding: 24px 20px;
  }

  .welcome-actions {
    flex-direction: column;
  }

  .btn {
    width: 100%;
  }
}
</style>