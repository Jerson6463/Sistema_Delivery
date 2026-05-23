<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="main-layout">
    <header class="site-header">
      <nav class="navbar" aria-label="Navegacion principal">
        <RouterLink class="brand" :to="{ name: 'home' }">
          <span class="brand-mark">D</span>
          <span class="brand-name">DeliveryPro</span>
        </RouterLink>

        <div class="nav-actions">
          <RouterLink class="nav-link" :to="{ name: 'catalogo' }">Explorar Catalogo</RouterLink>
          <RouterLink class="btn btn-ghost" :to="{ name: 'login' }">Iniciar Sesion</RouterLink>
          <RouterLink class="btn btn-primary" :to="{ name: 'registro-cliente' }">Registrarse</RouterLink>
        </div>
      </nav>
    </header>

    <main class="content">
      <RouterView />
    </main>

    <footer class="site-footer">
      <div class="footer-inner">
        <p>© 2026 DeliveryPro. Todos los derechos reservados.</p>

        <div class="footer-links">
          <a href="#">Terminos</a>
          <a href="#">Privacidad</a>
          <a href="#">Contacto</a>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.main-layout {
  --color-page: #ffffff;
  --color-surface: #f7f9fc;
  --color-surface-strong: #eef3f8;
  --color-text: #102033;
  --color-muted: #607086;
  --color-border: #dce4ee;
  --color-primary: #0f4c5c;
  --color-primary-hover: #0a3d4b;
  --color-primary-soft: #e8f3f5;
  --shadow-soft: 0 16px 40px rgba(16, 32, 51, 0.08);

  display: flex;
  min-height: 100vh;
  flex-direction: column;
  background: var(--color-page);
  color: var(--color-text);
}

.site-header {
  position: sticky;
  top: 0;
  z-index: 20;
  border-bottom: 1px solid rgba(220, 228, 238, 0.78);
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(14px);
}

.navbar {
  display: flex;
  width: min(1180px, calc(100% - 40px));
  min-height: 76px;
  margin: 0 auto;
  align-items: center;
  justify-content: space-between;
  gap: 28px;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  color: var(--color-text);
  font-weight: 800;
}

.brand-mark {
  display: inline-grid;
  width: 38px;
  height: 38px;
  place-items: center;
  border-radius: 10px;
  background: var(--color-primary);
  color: #ffffff;
  font-size: 1rem;
  font-weight: 800;
}

.brand-name {
  font-size: 1.08rem;
  font-weight: 800;
  letter-spacing: 0;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-link {
  color: var(--color-muted);
  font-size: 0.95rem;
  font-weight: 650;
  transition:
    color 180ms ease,
    background-color 180ms ease;
}

.nav-link:hover {
  color: var(--color-primary);
}

.btn {
  display: inline-flex;
  min-height: 42px;
  align-items: center;
  justify-content: center;
  border: 1px solid transparent;
  border-radius: 10px;
  padding: 0 18px;
  font-size: 0.94rem;
  font-weight: 700;
  transition:
    transform 180ms ease,
    box-shadow 180ms ease,
    background-color 180ms ease,
    border-color 180ms ease,
    color 180ms ease;
}

.btn:hover {
  transform: translateY(-1px);
}

.btn-ghost {
  border-color: var(--color-border);
  background: #ffffff;
  color: var(--color-text);
}

.btn-ghost:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.btn-primary {
  background: var(--color-primary);
  box-shadow: 0 10px 24px rgba(15, 76, 92, 0.22);
  color: #ffffff;
}

.btn-primary:hover {
  background: var(--color-primary-hover);
  box-shadow: 0 14px 30px rgba(15, 76, 92, 0.28);
}

.content {
  flex: 1;
}

.site-footer {
  border-top: 1px solid var(--color-border);
  background: #ffffff;
}

.footer-inner {
  display: flex;
  width: min(1180px, calc(100% - 40px));
  min-height: 86px;
  margin: 0 auto;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  color: var(--color-muted);
  font-size: 0.92rem;
}

.footer-links {
  display: flex;
  align-items: center;
  gap: 20px;
}

.footer-links a {
  transition: color 180ms ease;
}

.footer-links a:hover {
  color: var(--color-primary);
}

@media (max-width: 760px) {
  .navbar {
    width: min(100% - 28px, 1180px);
    min-height: auto;
    flex-direction: column;
    align-items: stretch;
    padding: 16px 0;
  }

  .brand {
    justify-content: space-between;
  }

  .nav-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }

  .nav-link {
    grid-column: 1 / -1;
    text-align: center;
  }

  .footer-inner {
    width: min(100% - 28px, 1180px);
    flex-direction: column;
    align-items: flex-start;
    padding: 24px 0;
  }
}
</style>
