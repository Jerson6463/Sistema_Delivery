<script setup>
import { ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const username = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMessage = ref('')

async function handleLogin() {
  errorMessage.value = ''
  isLoading.value = true

  try {
    await authStore.login({
      username: username.value,
      password: password.value,
    })

    router.push(route.query.redirect?.toString() || { name: getDefaultRouteByRole(authStore.role) })
  } catch {
    errorMessage.value = 'Credenciales invalidas. Por favor, intenta de nuevo.'
  } finally {
    isLoading.value = false
  }
}

function getDefaultRouteByRole(role) {
  const routesByRole = {
    CLIENTE: 'catalogo',
    ADMIN: 'admin-pedidos',
    REPARTIDOR: 'repartidor-entregas',
  }

  return routesByRole[role] || 'home'
}
</script>

<template>
  <main class="login-container">
    <section class="login-card" aria-labelledby="login-title">
      <header class="login-header">
        <RouterLink class="brand" :to="{ name: 'home' }">
          <span class="brand-mark">D</span>
          <span class="brand-name">DeliveryPro</span>
        </RouterLink>

        <h1 id="login-title">Ingresa a tu cuenta</h1>
        <p>Accede para gestionar pedidos, entregas o tu catalogo de negocio.</p>
      </header>

      <p v-if="route.query.registered" class="success-message" role="status">
        Cuenta creada correctamente. Ya puedes iniciar sesion.
      </p>

      <form class="login-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="username">Username</label>
          <input
            id="username"
            v-model.trim="username"
            autocomplete="username"
            name="username"
            placeholder="tu_usuario"
            required
            type="text"
          />
        </div>

        <div class="form-group">
          <label for="password">Contraseña</label>
          <input
            id="password"
            v-model="password"
            autocomplete="current-password"
            name="password"
            placeholder="Ingresa tu contraseña"
            required
            type="password"
          />
        </div>

        <p v-if="errorMessage" class="error-message" role="alert">
          {{ errorMessage }}
        </p>

        <button class="btn-primary" :disabled="isLoading" type="submit">
          {{ isLoading ? 'Ingresando...' : 'Iniciar Sesion' }}
        </button>
      </form>

      <p class="register-link">
        ¿No tienes cuenta?
        <RouterLink :to="{ name: 'registro-cliente' }">Registrate</RouterLink>
      </p>
    </section>
  </main>
</template>

<style scoped>
.login-container {
  display: grid;
  min-height: 100vh;
  place-items: center;
  background:
    linear-gradient(135deg, rgba(232, 243, 245, 0.62), rgba(248, 250, 252, 0.95)),
    #f8fafc;
  padding: 32px 18px;
  color: #102033;
}

.login-card {
  width: 100%;
  max-width: 420px;
  border: 1px solid #dce4ee;
  border-radius: 18px;
  background: #ffffff;
  box-shadow: 0 24px 60px rgba(16, 32, 51, 0.1);
  padding: 34px;
}

.login-header {
  margin-bottom: 30px;
  text-align: center;
}

.brand {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 26px;
  color: #102033;
}

.brand-mark {
  display: inline-grid;
  width: 40px;
  height: 40px;
  place-items: center;
  border-radius: 10px;
  background: #0f4c5c;
  color: #ffffff;
  font-size: 1rem;
  font-weight: 850;
}

.brand-name {
  font-size: 1.12rem;
  font-weight: 850;
  letter-spacing: 0;
}

h1,
p {
  margin: 0;
}

h1 {
  color: #102033;
  font-size: 1.8rem;
  font-weight: 850;
  letter-spacing: 0;
  line-height: 1.15;
}

.login-header p {
  margin-top: 12px;
  color: #607086;
  font-size: 0.96rem;
  line-height: 1.6;
}

.login-form {
  display: grid;
  gap: 18px;
}

.success-message {
  border: 1px solid #b9decf;
  border-radius: 10px;
  background: #f0fbf6;
  color: #16704f;
  font-size: 0.92rem;
  font-weight: 650;
  line-height: 1.5;
  margin-bottom: 18px;
  padding: 12px 14px;
}

.form-group {
  display: grid;
  gap: 8px;
}

label {
  color: #102033;
  font-size: 0.92rem;
  font-weight: 750;
}

input {
  width: 100%;
  min-height: 48px;
  border: 1px solid #cfd9e6;
  border-radius: 10px;
  background: #ffffff;
  color: #102033;
  outline: none;
  padding: 0 14px;
  transition:
    border-color 180ms ease,
    box-shadow 180ms ease,
    background-color 180ms ease;
}

input::placeholder {
  color: #9aa7b6;
}

input:focus {
  border-color: #0f4c5c;
  box-shadow: 0 0 0 4px rgba(15, 76, 92, 0.12);
}

.error-message {
  border: 1px solid #f1b9b9;
  border-radius: 10px;
  background: #fff5f5;
  color: #b42318;
  font-size: 0.92rem;
  font-weight: 650;
  line-height: 1.5;
  padding: 12px 14px;
}

.btn-primary {
  display: inline-flex;
  width: 100%;
  min-height: 50px;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 10px;
  background: #0f4c5c;
  box-shadow: 0 14px 28px rgba(15, 76, 92, 0.22);
  color: #ffffff;
  cursor: pointer;
  font-weight: 800;
  transition:
    transform 180ms ease,
    box-shadow 180ms ease,
    background-color 180ms ease,
    opacity 180ms ease;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  background: #0a3d4b;
  box-shadow: 0 18px 34px rgba(15, 76, 92, 0.28);
}

.btn-primary:disabled {
  cursor: not-allowed;
  opacity: 0.72;
}

.register-link {
  margin-top: 24px;
  color: #607086;
  font-size: 0.95rem;
  text-align: center;
}

.register-link a {
  color: #0f4c5c;
  font-weight: 800;
  transition: color 180ms ease;
}

.register-link a:hover {
  color: #0a3d4b;
}

@media (max-width: 480px) {
  .login-card {
    padding: 28px 20px;
  }

  h1 {
    font-size: 1.55rem;
  }
}
</style>
