<script setup>
import { reactive, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import api from '@/services/api'

const router = useRouter()
const route = useRoute()

const selectedRole = ref(route.name === 'registro-repartidor' ? 'repartidor' : 'cliente')
const zonas = ref([])
const vehiculos = ref([])
const hasLoadedDeliveryCatalogs = ref(false)
const isLoading = ref(false)
const isCatalogLoading = ref(false)
const errorMessage = ref('')

const formData = reactive({
  first_name: '',
  last_name: '',
  username: '',
  email: '',
  password: '',
  telefono: '',
  direccion_principal: '',
  tipo_vehiculo_id: '',
  zona_cobertura_id: '',
})

watch(
  selectedRole,
  async (role) => {
    errorMessage.value = ''

    if (role === 'repartidor') {
      await loadDeliveryCatalogs()
    }
  },
  { immediate: true },
)

watch(
  () => route.name,
  (routeName) => {
    selectedRole.value = routeName === 'registro-repartidor' ? 'repartidor' : 'cliente'
  },
)

async function loadDeliveryCatalogs() {
  if (hasLoadedDeliveryCatalogs.value || isCatalogLoading.value) return

  isCatalogLoading.value = true

  try {
    const [zonasResponse, vehiculosResponse] = await Promise.all([
      api.get('catalogo/zonas/'),
      api.get('catalogo/vehiculos/'),
    ])

    zonas.value = zonasResponse.data
    vehiculos.value = vehiculosResponse.data
    hasLoadedDeliveryCatalogs.value = true
  } catch {
    errorMessage.value = 'No pudimos cargar las zonas y vehiculos. Intenta nuevamente.'
  } finally {
    isCatalogLoading.value = false
  }
}

async function handleSubmit() {
  errorMessage.value = ''
  isLoading.value = true

  try {
    const endpoint =
      selectedRole.value === 'cliente'
        ? 'usuarios/registro/cliente/'
        : 'usuarios/registro/repartidor/'

    const payload =
      selectedRole.value === 'cliente'
        ? buildClientePayload()
        : buildRepartidorPayload()

    await api.post(endpoint, payload)
    router.push({ name: 'login', query: { registered: '1' } })
  } catch (error) {
    errorMessage.value = getErrorMessage(error)
  } finally {
    isLoading.value = false
  }
}

function buildClientePayload() {
  return {
    username: formData.username,
    email: formData.email,
    password: formData.password,
    first_name: formData.first_name,
    last_name: formData.last_name,
    telefono: formData.telefono,
    direccion_principal: formData.direccion_principal,
  }
}

function buildRepartidorPayload() {
  return {
    username: formData.username,
    email: formData.email,
    password: formData.password,
    first_name: formData.first_name,
    last_name: formData.last_name,
    tipo_vehiculo_id: formData.tipo_vehiculo_id,
    zona_cobertura_id: formData.zona_cobertura_id,
  }
}

function getErrorMessage(error) {
  const data = error.response?.data

  if (typeof data === 'string') return data
  if (data?.detail) return data.detail
  if (data && typeof data === 'object') {
    const firstField = Object.keys(data)[0]
    const firstValue = data[firstField]

    if (Array.isArray(firstValue)) return firstValue[0]
    if (typeof firstValue === 'string') return firstValue
  }

  return 'No pudimos crear tu cuenta. Revisa los datos e intenta nuevamente.'
}
</script>

<template>
  <main class="register-container">
    <section class="register-card" aria-labelledby="register-title">
      <header class="register-header">
        <RouterLink class="brand" :to="{ name: 'home' }">
          <span class="brand-mark">D</span>
          <span class="brand-name">DeliveryPro</span>
        </RouterLink>

        <h1 id="register-title">Crea tu cuenta</h1>
        <p>Elige el tipo de cuenta y completa tus datos para empezar a usar la plataforma.</p>
      </header>

      <div class="role-tabs" aria-label="Tipo de cuenta">
        <button
          class="role-tab"
          :class="{ active: selectedRole === 'cliente' }"
          type="button"
          @click="selectedRole = 'cliente'"
        >
          <strong>Quiero pedir comida</strong>
          <span>Cliente</span>
        </button>
        <button
          class="role-tab"
          :class="{ active: selectedRole === 'repartidor' }"
          type="button"
          @click="selectedRole = 'repartidor'"
        >
          <strong>Quiero ser repartidor</strong>
          <span>Repartidor</span>
        </button>
      </div>

      <form class="register-form" @submit.prevent="handleSubmit">
        <div class="form-row">
          <div class="form-group">
            <label for="first_name">Nombre</label>
            <input id="first_name" v-model.trim="formData.first_name" required type="text" />
          </div>

          <div class="form-group">
            <label for="last_name">Apellido</label>
            <input id="last_name" v-model.trim="formData.last_name" required type="text" />
          </div>
        </div>

        <div class="form-group">
          <label for="username">Usuario</label>
          <input
            id="username"
            v-model.trim="formData.username"
            autocomplete="username"
            required
            type="text"
          />
        </div>

        <div class="form-group">
          <label for="email">Correo</label>
          <input
            id="email"
            v-model.trim="formData.email"
            autocomplete="email"
            required
            type="email"
          />
        </div>

        <div class="form-group">
          <label for="password">Contraseña</label>
          <input
            id="password"
            v-model="formData.password"
            autocomplete="new-password"
            required
            type="password"
          />
        </div>

        <template v-if="selectedRole === 'cliente'">
          <div class="form-group">
            <label for="telefono">Telefono</label>
            <input id="telefono" v-model.trim="formData.telefono" required type="tel" />
          </div>

          <div class="form-group">
            <label for="direccion_principal">Direccion Principal</label>
            <input
              id="direccion_principal"
              v-model.trim="formData.direccion_principal"
              required
              type="text"
            />
          </div>
        </template>

        <template v-else>
          <div class="form-group">
            <label for="tipo_vehiculo_id">Tipo de Vehiculo</label>
            <select
              id="tipo_vehiculo_id"
              v-model="formData.tipo_vehiculo_id"
              :disabled="isCatalogLoading"
              required
            >
              <option disabled value="">
                {{ isCatalogLoading ? 'Cargando vehiculos...' : 'Selecciona un vehiculo' }}
              </option>
              <option v-for="vehiculo in vehiculos" :key="vehiculo.id" :value="vehiculo.id">
                {{ vehiculo.nombre }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label for="zona_cobertura_id">Zona de Cobertura</label>
            <select
              id="zona_cobertura_id"
              v-model="formData.zona_cobertura_id"
              :disabled="isCatalogLoading"
              required
            >
              <option disabled value="">
                {{ isCatalogLoading ? 'Cargando zonas...' : 'Selecciona una zona' }}
              </option>
              <option v-for="zona in zonas" :key="zona.id" :value="zona.id">
                {{ zona.nombre }}
              </option>
            </select>
          </div>
        </template>

        <p v-if="errorMessage" class="error-message" role="alert">
          {{ errorMessage }}
        </p>

        <button class="btn-primary" :disabled="isLoading || isCatalogLoading" type="submit">
          {{ isLoading ? 'Creando cuenta...' : 'Crear cuenta' }}
        </button>
      </form>

      <p class="login-link">
        ¿Ya tienes cuenta?
        <RouterLink :to="{ name: 'login' }">Inicia sesion</RouterLink>
      </p>
    </section>
  </main>
</template>

<style scoped>
.register-container {
  display: grid;
  min-height: 100vh;
  place-items: center;
  background:
    linear-gradient(135deg, rgba(232, 243, 245, 0.62), rgba(248, 250, 252, 0.95)),
    #f8fafc;
  padding: 34px 18px;
  color: #102033;
}

.register-card {
  width: 100%;
  max-width: 500px;
  border: 1px solid #dce4ee;
  border-radius: 18px;
  background: #ffffff;
  box-shadow: 0 24px 60px rgba(16, 32, 51, 0.1);
  padding: 34px;
}

.register-header {
  margin-bottom: 24px;
  text-align: center;
}

.brand {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 22px;
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
  font-size: 1.85rem;
  font-weight: 850;
  letter-spacing: 0;
  line-height: 1.15;
}

.register-header p {
  margin-top: 12px;
  color: #607086;
  font-size: 0.96rem;
  line-height: 1.6;
}

.role-tabs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  border-radius: 14px;
  background: #f3f6fa;
  padding: 6px;
  margin-bottom: 24px;
}

.role-tab {
  min-height: 72px;
  border: 1px solid transparent;
  border-radius: 11px;
  background: transparent;
  color: #102033;
  cursor: pointer;
  padding: 12px;
  text-align: left;
  transition:
    transform 180ms ease,
    background-color 180ms ease,
    border-color 180ms ease,
    box-shadow 180ms ease,
    color 180ms ease;
}

.role-tab:hover {
  transform: translateY(-1px);
  border-color: #c8d5e2;
  background: #ffffff;
}

.role-tab.active {
  border-color: #0f4c5c;
  background: #0f4c5c;
  box-shadow: 0 12px 24px rgba(15, 76, 92, 0.22);
  color: #ffffff;
}

.role-tab strong,
.role-tab span {
  display: block;
}

.role-tab strong {
  font-size: 0.9rem;
  font-weight: 800;
  line-height: 1.25;
}

.role-tab span {
  margin-top: 5px;
  font-size: 0.82rem;
  font-weight: 650;
  opacity: 0.78;
}

.register-form {
  display: grid;
  gap: 16px;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
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

input,
select {
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

select {
  cursor: pointer;
}

select:disabled {
  cursor: not-allowed;
  background: #f3f6fa;
  color: #7c8ca0;
}

input:focus,
select:focus {
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

.login-link {
  margin-top: 24px;
  color: #607086;
  font-size: 0.95rem;
  text-align: center;
}

.login-link a {
  color: #0f4c5c;
  font-weight: 800;
  transition: color 180ms ease;
}

.login-link a:hover {
  color: #0a3d4b;
}

@media (max-width: 560px) {
  .register-card {
    padding: 28px 20px;
  }

  .role-tabs,
  .form-row {
    grid-template-columns: 1fr;
  }

  h1 {
    font-size: 1.58rem;
  }
}
</style>
