import { defineStore } from 'pinia'

const DELIVERY_FEE = 5

export const useCartStore = defineStore('cart', {
  state: () => ({
    negocioId: null,
    negocioNombre: '',
    items: [],
  }),

  getters: {
    isEmpty: (state) => state.items.length === 0,
    subtotal: (state) =>
      state.items.reduce((total, item) => total + Number(item.precio) * item.cantidad, 0),
    deliveryFee: (state) => (state.items.length > 0 ? DELIVERY_FEE : 0),
    total() {
      return this.subtotal + this.deliveryFee
    },
    totalItems: (state) => state.items.reduce((total, item) => total + item.cantidad, 0),
  },

  actions: {
    addProduct(producto, negocio) {
      if (!producto || !negocio) return { ok: false, message: 'Producto invalido.' }
      if (producto.stock_disponible <= 0) {
        return { ok: false, message: 'Este producto no tiene stock disponible.' }
      }

      if (this.negocioId && this.negocioId !== negocio.id) {
        const shouldClear = window.confirm(
          'Tu carrito contiene productos de otro negocio. ¿Quieres limpiarlo y empezar uno nuevo?',
        )

        if (!shouldClear) return { ok: false, message: 'Se mantuvo el carrito anterior.' }
        this.clearCart()
      }

      this.negocioId = negocio.id
      this.negocioNombre = negocio.nombre

      const existingItem = this.items.find((item) => item.productoId === producto.id)

      if (existingItem) {
        if (existingItem.cantidad >= producto.stock_disponible) {
          return { ok: false, message: 'No puedes agregar mas unidades que el stock disponible.' }
        }

        existingItem.cantidad += 1
        return { ok: true }
      }

      this.items.push({
        productoId: producto.id,
        negocioId: negocio.id,
        nombre: producto.nombre,
        precio: Number(producto.precio),
        stockDisponible: producto.stock_disponible,
        cantidad: 1,
      })

      return { ok: true }
    },

    increment(productoId) {
      const item = this.items.find((cartItem) => cartItem.productoId === productoId)
      if (!item) return
      if (item.cantidad >= item.stockDisponible) return
      item.cantidad += 1
    },

    decrement(productoId) {
      const item = this.items.find((cartItem) => cartItem.productoId === productoId)
      if (!item) return

      if (item.cantidad <= 1) {
        this.removeItem(productoId)
        return
      }

      item.cantidad -= 1
    },

    removeItem(productoId) {
      this.items = this.items.filter((item) => item.productoId !== productoId)

      if (this.items.length === 0) {
        this.negocioId = null
        this.negocioNombre = ''
      }
    },

    clearCart() {
      this.negocioId = null
      this.negocioNombre = ''
      this.items = []
    },
  },
})
