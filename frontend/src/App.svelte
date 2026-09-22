<script lang="ts">
  import { onMount } from 'svelte'
  import { cart } from './lib/cart.svelte'
  import { fetchQuickItems } from './lib/api'
  import { setupBarcodeListener } from './lib/scanner'
  import { sound } from './lib/sound'
  import type { Product, TransactionResult } from './types'

  import Header from './components/Header.svelte'
  import SearchBar from './components/SearchBar.svelte'
  import StaplesGrid from './components/StaplesGrid.svelte'
  import CartTable from './components/CartTable.svelte'
  import WeightModal from './components/WeightModal.svelte'
  import PaymentModal from './components/PaymentModal.svelte'
  import ParkedCartsModal from './components/ParkedCartsModal.svelte'
  import ReceiptModal from './components/ReceiptModal.svelte'
  import ShortcutsModal from './components/ShortcutsModal.svelte'
  import GCashModal from './components/GCashModal.svelte'
  import UtangModal from './components/UtangModal.svelte'
  import { ShoppingCart, LayoutGrid, ArrowRight } from 'lucide-svelte'

  let quickItems = $state<Product[]>([])
  let searchBarComponent = $state<any>(null)

  // Responsive tablet / mobile active view: 'catalog' | 'cart'
  let mobileActiveTab = $state<'catalog' | 'cart'>('catalog')

  // Modals state
  let weightModalProduct = $state<Product | null>(null)
  let showPaymentModal = $state(false)
  let showParkedModal = $state(false)
  let showShortcutsModal = $state(false)
  let showGCashModal = $state(false)
  let showUtangModal = $state(false)
  let lastTransaction = $state<TransactionResult | null>(null)

  // Toast Notification state
  let toast = $state<{ show: boolean; message: string; type: 'success' | 'info' | 'error' }>({
    show: false,
    message: '',
    type: 'info'
  })
  let toastTimer: any = null

  function showToast(message: string, type: 'success' | 'info' | 'error' = 'info') {
    clearTimeout(toastTimer)
    toast = { show: true, message, type }
    toastTimer = setTimeout(() => {
      toast.show = false
    }, 2800)
  }

  async function loadInitialData() {
    try {
      quickItems = await fetchQuickItems()
    } catch (e) {
      console.error('Failed to load quick items', e)
    }
  }

  function handleProductSelect(
    product: Product,
    quantity: number = 1.0,
    price?: number,
    label?: string | null
  ) {
    cart.addItem(product, quantity, price, label)
    showToast(`Added ${quantity}${product.unit === 'pc' ? 'x' : product.unit} ${product.name}`, 'success')
  }

  function handleWeightConfirm(quantity: number, subtotal: number, label: string) {
    if (!weightModalProduct) return
    const unitPrice = quantity > 0 ? Number((subtotal / quantity).toFixed(2)) : weightModalProduct.selling_price
    cart.addItem(weightModalProduct, quantity, unitPrice, label)
    sound.playBeep('scan')
    showToast(`Weighed ${quantity}${weightModalProduct.unit} ${weightModalProduct.name} (₱${subtotal.toFixed(2)})`, 'success')
    weightModalProduct = null
  }

  function handleHoldCart() {
    if (cart.items.length === 0) {
      showToast('Cart is already empty', 'info')
      return
    }
    const success = cart.parkCurrentCart()
    if (success) {
      showToast('Cart parked! Screen cleared for next customer.', 'info')
    }
  }

  function handleCheckoutComplete(res: TransactionResult) {
    showPaymentModal = false
    lastTransaction = res
    const changeVal = res.change ?? res.change_amount ?? 0
    showToast(`Sale complete! Sukli: ₱${changeVal.toFixed(2)}`, 'success')
  }

  // Global Keyboard Shortcuts
  function handleGlobalKeyDown(e: KeyboardEvent) {
    if (e.key === 'F2') {
      e.preventDefault()
      mobileActiveTab = 'catalog'
      searchBarComponent?.focusInput()
    } else if (e.key === 'F4') {
      e.preventDefault()
      if (cart.items.length > 0) {
        handleHoldCart()
      } else {
        showParkedModal = true
      }
    } else if (e.key === 'F5') {
      e.preventDefault()
      if (cart.items.length > 0 && !showPaymentModal) {
        showPaymentModal = true
      }
    } else if (e.key === 'F7') {
      e.preventDefault()
      showUtangModal = true
    } else if (e.key === 'Escape') {
      if (weightModalProduct) {
        weightModalProduct = null
      } else if (showPaymentModal) {
        showPaymentModal = false
      } else if (showGCashModal) {
        showGCashModal = false
      } else if (showUtangModal) {
        showUtangModal = false
      } else if (showParkedModal) {
        showParkedModal = false
      } else if (showShortcutsModal) {
        showShortcutsModal = false
      } else if (lastTransaction) {
        lastTransaction = null
      } else {
        searchBarComponent?.clear()
        searchBarComponent?.focusInput()
      }
    }
  }

  onMount(() => {
    loadInitialData()
    window.addEventListener('keydown', handleGlobalKeyDown)

    // Barcode scanner listener
    const cleanupScanner = setupBarcodeListener((barcode) => {
      searchBarComponent?.processBarcodeOrCode(barcode)
    })

    return () => {
      window.removeEventListener('keydown', handleGlobalKeyDown)
      cleanupScanner()
    }
  })
</script>

<div class="h-full flex flex-col bg-slate-100 overflow-hidden text-slate-800 select-none">
  <!-- Top Navigation Header -->
  <Header
    onOpenParked={() => showParkedModal = true}
    onOpenShortcuts={() => showShortcutsModal = true}
    onOpenGCash={() => showGCashModal = true}
    onOpenUtang={() => showUtangModal = true}
  />

  <!-- Mobile / Tablet Screen Tab Switcher (Visible only on < lg screens) -->
  <div class="lg:hidden px-3 pt-2 pb-1 bg-white border-b border-slate-200 flex items-center justify-between gap-2 flex-shrink-0">
    <div class="grid grid-cols-2 gap-1 w-full bg-slate-100 p-1 rounded-xl text-xs font-bold">
      <button
        type="button"
        onclick={() => mobileActiveTab = 'catalog'}
        class="flex items-center justify-center gap-1.5 py-2 rounded-lg transition-all cursor-pointer {mobileActiveTab === 'catalog' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'}"
      >
        <LayoutGrid class="w-4 h-4 text-cyan-600" />
        <span>Staples & Catalog</span>
      </button>

      <button
        type="button"
        onclick={() => mobileActiveTab = 'cart'}
        class="flex items-center justify-center gap-1.5 py-2 rounded-lg transition-all cursor-pointer {mobileActiveTab === 'cart' ? 'bg-white text-emerald-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'}"
      >
        <ShoppingCart class="w-4 h-4 {cart.items.length > 0 ? 'text-emerald-600' : 'text-slate-400'}" />
        <span>Cart ({cart.itemCount}) • ₱{cart.subtotal.toFixed(2)}</span>
      </button>
    </div>
  </div>

  <!-- Main POS Layout -->
  <main class="flex-1 p-2.5 sm:p-3 grid grid-cols-1 lg:grid-cols-12 gap-2.5 sm:gap-3 min-h-0 overflow-hidden relative">
    <!-- Left Column (7 cols): Search + Staples Grid -->
    <div class="lg:col-span-7 flex flex-col gap-2.5 min-h-0 overflow-hidden {mobileActiveTab === 'catalog' ? 'flex' : 'hidden lg:flex'}">
      <!-- Search & Barcode Input -->
      <SearchBar
        bind:this={searchBarComponent}
        onSelectProduct={handleProductSelect}
        onRequestWeightModal={(prod) => weightModalProduct = prod}
      />

      <!-- Fast Action Staples & Tingi Grid -->
      <div class="flex-1 min-h-0 overflow-hidden">
        <StaplesGrid
          {quickItems}
          onSelectProduct={handleProductSelect}
          onRequestWeightModal={(prod) => weightModalProduct = prod}
          onOpenGCash={(type) => showGCashModal = true}
        />
      </div>
    </div>

    <!-- Right Column (5 cols): Live Cart & Checkout Summary -->
    <div class="lg:col-span-5 flex flex-col min-h-0 overflow-hidden {mobileActiveTab === 'cart' ? 'flex' : 'hidden lg:flex'}">
      <CartTable
        onOpenPayment={() => showPaymentModal = true}
        onHoldCart={handleHoldCart}
        onRequestFocusSearch={() => {
          mobileActiveTab = 'catalog'
          searchBarComponent?.focusInput()
        }}
      />
    </div>

    <!-- Mobile/Tablet Floating Bottom Bar (Visible on < lg when viewing catalog with items in cart) -->
    {#if mobileActiveTab === 'catalog' && cart.items.length > 0}
      <div class="lg:hidden absolute bottom-3 left-3 right-3 z-30">
        <button
          type="button"
          onclick={() => mobileActiveTab = 'cart'}
          class="w-full py-3 px-4 bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white rounded-2xl shadow-xl border border-emerald-500 flex items-center justify-between font-bold text-xs cursor-pointer animate-in slide-in-from-bottom-3 duration-150"
        >
          <div class="flex items-center gap-2">
            <span class="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center font-extrabold text-[11px]">
              {cart.itemCount}
            </span>
            <span>View Cart ({cart.itemCount} items)</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-base font-mono font-black">₱{cart.subtotal.toFixed(2)}</span>
            <ArrowRight class="w-4 h-4" />
          </div>
        </button>
      </div>
    {/if}
  </main>

  <!-- Modals -->
  {#if weightModalProduct}
    <WeightModal
      product={weightModalProduct}
      onConfirm={handleWeightConfirm}
      onClose={() => weightModalProduct = null}
    />
  {/if}

  {#if showPaymentModal}
    <PaymentModal
      onComplete={handleCheckoutComplete}
      onClose={() => showPaymentModal = false}
    />
  {/if}

  {#if showParkedModal}
    <ParkedCartsModal
      onClose={() => showParkedModal = false}
    />
  {/if}

  {#if lastTransaction}
    <ReceiptModal
      transaction={lastTransaction}
      onClose={() => lastTransaction = null}
    />
  {/if}

  {#if showGCashModal}
    <GCashModal
      onComplete={(msg) => {
        showGCashModal = false
        showToast(msg, 'success')
      }}
      onClose={() => showGCashModal = false}
    />
  {/if}

  {#if showUtangModal}
    <UtangModal
      onPaymentRecorded={(msg) => showToast(msg, 'success')}
      onClose={() => showUtangModal = false}
    />
  {/if}

  {#if showShortcutsModal}
    <ShortcutsModal
      onClose={() => showShortcutsModal = false}
    />
  {/if}

  <!-- Floating Toast Notification -->
  {#if toast.show}
    <div class="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 px-4 py-2.5 rounded-xl shadow-lg border text-xs font-bold flex items-center gap-2 animate-in fade-in slide-in-from-bottom-2 duration-200 {toast.type === 'success' ? 'bg-emerald-800 text-white border-emerald-700' : 'bg-slate-900 text-white border-slate-800'}">
      <span>{toast.message}</span>
    </div>
  {/if}
</div>
