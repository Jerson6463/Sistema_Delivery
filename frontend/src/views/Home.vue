<script setup>
import { RouterLink } from 'vue-router'

const features = [
  {
    title: 'Para Clientes',
    description:
      'Encuentra restaurantes activos, compra en minutos y sigue tus pedidos con rastreo GPS en tiempo real.',
  },
  {
    title: 'Para Negocios',
    description:
      'Administra tu menu, recibe ordenes y amplia tu alcance operativo desde un panel claro y centralizado.',
  },
  {
    title: 'Para Repartidores',
    description:
      'Gestiona entregas asignadas, actualiza estados y trabaja con mayor flexibilidad en tu zona de cobertura.',
  },
]
</script>

<template>
  <section class="hero-section">
    <div class="hero-inner">
      <div class="hero-content">
        <span class="eyebrow">Plataforma integral de delivery</span>
        <h1>Gestion Logistica y Delivery de Alto Nivel</h1>
        <p>
          Conectamos clientes, negocios y repartidores en una experiencia formal, rapida y
          trazable para operar pedidos con precision desde el catalogo hasta la entrega final.
        </p>

        <div class="hero-actions">
          <RouterLink class="btn btn-primary btn-large" :to="{ name: 'catalogo' }">
            Explorar Restaurantes
          </RouterLink>
          <RouterLink class="btn btn-secondary btn-large" :to="{ name: 'registro-repartidor' }">
            Unete como Repartidor
          </RouterLink>
        </div>
      </div>

      <div class="hero-panel" aria-label="Resumen operativo">
        <div class="panel-header">
          <span>Operacion en curso</span>
          <strong>98%</strong>
        </div>
        <div class="delivery-card">
          <span class="status-dot"></span>
          <div>
            <strong>Pedido #2481</strong>
            <p>En camino hacia Av. Principal 120</p>
          </div>
        </div>
        <div class="metric-grid">
          <div>
            <strong>24 min</strong>
            <span>Promedio entrega</span>
          </div>
          <div>
            <strong>126</strong>
            <span>Ordenes hoy</span>
          </div>
        </div>
      </div>
    </div>
  </section>

  <section class="features-section" aria-labelledby="features-title">
    <div class="section-heading">
      <span class="eyebrow">Beneficios por rol</span>
      <h2 id="features-title">Una plataforma preparada para cada operacion</h2>
    </div>

    <div class="features-grid">
      <article v-for="feature in features" :key="feature.title" class="feature-card">
        <div class="feature-icon" aria-hidden="true"></div>
        <h3>{{ feature.title }}</h3>
        <p>{{ feature.description }}</p>
      </article>
    </div>
  </section>
</template>

<style scoped>
.hero-section {
  background:
    linear-gradient(135deg, rgba(232, 243, 245, 0.9), rgba(247, 249, 252, 0.94)),
    #f7f9fc;
  border-bottom: 1px solid #dce4ee;
}

.hero-inner {
  display: grid;
  width: min(1180px, calc(100% - 40px));
  margin: 0 auto;
  grid-template-columns: minmax(0, 1.12fr) minmax(320px, 0.88fr);
  gap: 56px;
  align-items: center;
  padding: 86px 0 78px;
}

.hero-content {
  max-width: 680px;
}

.eyebrow {
  display: inline-flex;
  margin-bottom: 18px;
  color: #0f4c5c;
  font-size: 0.82rem;
  font-weight: 800;
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
  max-width: 760px;
  color: #102033;
  font-size: clamp(2.45rem, 6vw, 4.9rem);
  font-weight: 850;
  letter-spacing: 0;
  line-height: 1.02;
}

.hero-content p {
  max-width: 620px;
  margin-top: 24px;
  color: #607086;
  font-size: 1.12rem;
  line-height: 1.8;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 34px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid transparent;
  border-radius: 10px;
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

.btn-large {
  min-height: 54px;
  padding: 0 24px;
  font-size: 1rem;
}

.btn-primary {
  background: #0f4c5c;
  box-shadow: 0 16px 30px rgba(15, 76, 92, 0.24);
  color: #ffffff;
}

.btn-primary:hover {
  background: #0a3d4b;
  box-shadow: 0 20px 38px rgba(15, 76, 92, 0.3);
}

.btn-secondary {
  border-color: #c8d5e2;
  background: rgba(255, 255, 255, 0.82);
  color: #102033;
}

.btn-secondary:hover {
  border-color: #0f4c5c;
  color: #0f4c5c;
}

.hero-panel {
  display: grid;
  gap: 18px;
  border: 1px solid rgba(220, 228, 238, 0.92);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 24px 60px rgba(16, 32, 51, 0.12);
  padding: 24px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #607086;
  font-weight: 700;
}

.panel-header strong {
  color: #0f4c5c;
  font-size: 2.4rem;
  font-weight: 850;
}

.delivery-card {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  border: 1px solid #dce4ee;
  border-radius: 14px;
  background: #ffffff;
  padding: 18px;
}

.status-dot {
  width: 12px;
  height: 12px;
  flex: 0 0 auto;
  border-radius: 999px;
  margin-top: 7px;
  background: #16845f;
  box-shadow: 0 0 0 6px rgba(22, 132, 95, 0.12);
}

.delivery-card strong,
.metric-grid strong {
  display: block;
  color: #102033;
  font-weight: 850;
}

.delivery-card p {
  margin-top: 4px;
  color: #607086;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.metric-grid div {
  border-radius: 14px;
  background: #eef3f8;
  padding: 18px;
}

.metric-grid strong {
  font-size: 1.45rem;
}

.metric-grid span {
  display: block;
  margin-top: 5px;
  color: #607086;
  font-size: 0.9rem;
}

.features-section {
  width: min(1180px, calc(100% - 40px));
  margin: 0 auto;
  padding: 82px 0 92px;
}

.section-heading {
  max-width: 660px;
  margin-bottom: 34px;
}

h2 {
  color: #102033;
  font-size: clamp(2rem, 4vw, 3rem);
  font-weight: 850;
  letter-spacing: 0;
  line-height: 1.1;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 22px;
}

.feature-card {
  border: 1px solid #dce4ee;
  border-radius: 16px;
  background: #ffffff;
  box-shadow: 0 16px 40px rgba(16, 32, 51, 0.07);
  padding: 28px;
  transition:
    transform 180ms ease,
    box-shadow 180ms ease,
    border-color 180ms ease;
}

.feature-card:hover {
  transform: translateY(-4px);
  border-color: #b9ccd9;
  box-shadow: 0 22px 52px rgba(16, 32, 51, 0.1);
}

.feature-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  margin-bottom: 22px;
  background:
    linear-gradient(135deg, rgba(15, 76, 92, 0.92), rgba(22, 132, 95, 0.9)),
    #0f4c5c;
}

h3 {
  color: #102033;
  font-size: 1.22rem;
  font-weight: 850;
}

.feature-card p {
  margin-top: 12px;
  color: #607086;
  line-height: 1.75;
}

@media (max-width: 900px) {
  .hero-inner {
    grid-template-columns: 1fr;
    padding: 64px 0;
  }

  .hero-panel {
    max-width: 520px;
  }

  .features-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .hero-inner,
  .features-section {
    width: min(100% - 28px, 1180px);
  }

  .hero-actions {
    flex-direction: column;
  }

  .btn-large {
    width: 100%;
  }

  .metric-grid {
    grid-template-columns: 1fr;
  }
}
</style>
