import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    component: () => import('@/components/layout/MainLayout.vue'),
    children: [
      {
        path: '',
        name: 'home',
        component: () => import('@/views/Home.vue'),
      },
      {
        path: 'catalogo',
        name: 'catalogo',
        component: () => import('@/views/cliente/Catalogo.vue'),
      },
    ],
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { guestOnly: true },
  },
  {
    path: '/registro',
    name: 'registro',
    component: () => import('@/views/auth/Register.vue'),
    meta: { guestOnly: true },
  },
  {
    path: '/registro/cliente',
    name: 'registro-cliente',
    component: () => import('@/views/auth/Register.vue'),
    meta: { guestOnly: true },
  },
  {
    path: '/registro/empresa',
    name: 'registro-empresa',
    component: () => import('@/views/auth/RegisterEmpresaView.vue'),
    meta: { guestOnly: true },
  },
  {
    path: '/registro/repartidor',
    name: 'registro-repartidor',
    component: () => import('@/views/auth/Register.vue'),
    meta: { guestOnly: true },
  },
  {
    path: '/negocios/:id',
    name: 'negocio-detalle',
    component: () => import('@/views/catalogo/NegocioDetalleView.vue'),
    props: true,
  },

  {
    path: '/cliente/inicio',
    name: 'cliente-inicio',
    component: () => import('@/views/cliente/InicioCliente.vue'),
    meta: { requiresAuth: true, roles: ['CLIENTE'] },
  },

  {
    path: '/checkout',
    name: 'checkout',
    component: () => import('@/views/cliente/Confirmacion.vue'),
    meta: { requiresAuth: true, roles: ['CLIENTE'] },
  },
  {
    path: '/mis-pedidos',
    name: 'mis-pedidos',
    component: () => import('@/views/cliente/MisPedidos.vue'),
    meta: { requiresAuth: true, roles: ['CLIENTE'] },
  },
  {
    path: '/admin/menu',
    name: 'admin-menu',
    component: () => import('@/views/admin/MenuView.vue'),
    meta: { requiresAuth: true, roles: ['ADMIN'] },
  },
  {
    path: '/admin/pedidos',
    name: 'admin-pedidos',
    component: () => import('@/views/admin/DashboardNegocio.vue'),
    meta: { requiresAuth: true, roles: ['ADMIN'] },
  },
  {
    path: '/repartidor/entregas',
    name: 'repartidor-entregas',
    component: () => import('@/views/repartidor/DashboardRepartidor.vue'),
    meta: { requiresAuth: true, roles: ['REPARTIDOR'] },
  },
  {
    path: '/403',
    name: 'forbidden',
    component: () => import('@/views/errors/ForbiddenView.vue'),
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/errors/NotFoundView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()

  if (authStore.accessToken && !authStore.user) {
    await authStore.bootstrapSession()
  }

  if (to.meta.guestOnly && authStore.isAuthenticated) {
    return { name: getDefaultRouteByRole(authStore.role) }
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.roles?.length && !to.meta.roles.includes(authStore.role)) {
    return { name: 'forbidden' }
  }

  return true
})

function getDefaultRouteByRole(role) {
  const routesByRole = {
    CLIENTE: 'cliente-inicio',
    ADMIN: 'admin-pedidos',
    REPARTIDOR: 'repartidor-entregas',
  }

  return routesByRole[role] || 'home'
}

export default router
