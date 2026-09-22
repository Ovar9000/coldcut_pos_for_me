<script lang="ts">
  import { cart } from '../lib/cart.svelte'
  import { Trash2, Plus, Minus, ShoppingCart, PauseCircle, Ban, Search, Edit3 } from 'lucide-svelte'
  import type { CartItem } from '../types'
  import QuantityModal from './QuantityModal.svelte'

  interface Props {
    onOpenPayment: () => void
    onHoldCart: () => void
    onRequestFocusSearch?: () => void
  }

  let { onOpenPayment, onHoldCart, onRequestFocusSearch }: Props = $props()

  let editingItem = $state<CartItem | null>(null)

  function handleSaveQuantity(newQty: number) {
    if (!editingItem) return
    cart.updateQuantity(editingItem.id, newQty)
    editingItem = null
  }

  function handleRemoveEditingItem() {
    if (!editingItem) return
    cart.removeItem(editingItem.id)
    editingItem = null
  }
</script>

<div class="flex flex-col h-full bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
  <!-- Cart Header -->
  <div class="px-4 py-3 bg-slate-50/90 border-b border-slate-200 flex items-center justify-between flex-shrink-0">
    <div class="flex items-center gap-2">
      <ShoppingCart class="w-4 h-4 text-slate-600" />
      <h2 class="text-xs font-bold uppercase tracking-wider text-slate-700">Current Cart</h2>
      {#if cart.items.length > 0}
        <span class="px-2 py-0.5 rounded-full text-[11px] font-extrabold bg-emerald-100 text-emerald-800">
          {cart.itemCount} items
        </span>
      {/if}
    </div>

    {#if cart.items.length > 0}
      <div class="flex items-center gap-1.5">
        <button
          type="button"
          onclick={onHoldCart}
          class="flex items-center gap-1 px-3 py-1.5 text-xs font-semibold text-amber-800 bg-amber-50 hover:bg-amber-100 active:bg-amber-200 border border-amber-200 rounded-lg transition-all cursor-pointer shadow-2xs"
          title="Hold/Park Cart (F4)"
        >
          <PauseCircle class="w-3.5 h-3.5 text-amber-600" />
          <span>Hold (F4)</span>
        </button>

        <button
          type="button"
          onclick={() => cart.clearCart()}
          class="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 active:bg-rose-100 rounded-lg transition-all cursor-pointer"
          title="Clear Entire Cart"
        >
          <Ban class="w-4 h-4" />
        </button>
      </div>
    {/if}
  </div>

  <!-- Cart Items List -->
  <div class="flex-1 overflow-y-auto divide-y divide-slate-100 p-2 min-h-0">
    {#if cart.items.length === 0}
      <div class="h-full flex flex-col items-center justify-center p-6 text-center text-slate-400">
        <div class="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center mb-3">
          <ShoppingCart class="w-7 h-7 text-slate-300" />
        </div>
        <p class="text-sm font-bold text-slate-600">Cart is Empty</p>
        <p class="text-xs text-slate-400 mt-1 max-w-[220px] leading-relaxed">
          Scan with barcode gun, pick from poultry/staples, or search above.
        </p>
        {#if onRequestFocusSearch}
          <button
            type="button"
            onclick={onRequestFocusSearch}
            class="mt-4 flex items-center gap-1.5 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl transition-all cursor-pointer"
          >
            <Search class="w-3.5 h-3.5" />
            <span>Search Products (F2)</span>
          </button>
        {/if}
      </div>
    {:else}
      {#each cart.items as item (item.id)}
        <div class="py-2.5 px-2.5 flex items-center justify-between gap-2 hover:bg-slate-50 rounded-xl transition-colors">
          <!-- Item Details (Click to open direct edit) -->
          <button
            type="button"
            onclick={() => editingItem = item}
            class="min-w-0 flex-1 text-left cursor-pointer group"
          >
            <div class="flex items-center gap-1.5">
              <p class="text-xs font-bold text-slate-900 truncate leading-snug group-hover:text-emerald-700 transition-colors">
                {item.product_name}
              </p>
              {#if item.pack_label}
                <span class="px-1.5 py-0.2 rounded text-[9px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200 flex-shrink-0">
                  {item.pack_label}
                </span>
              {/if}
            </div>
            <p class="text-[11px] font-mono text-slate-500 mt-0.5 flex items-center gap-1">
              <span>₱{item.unit_price.toFixed(2)} / {item.unit}</span>
              <span class="text-[9px] text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity">
                • Tap to edit
              </span>
            </p>
          </button>

          <!-- Quantity Stepper with Comfortable Touch Targets -->
          <div class="flex items-center gap-1 flex-shrink-0 bg-slate-100 rounded-xl p-1">
            <button
              type="button"
              onclick={() => cart.updateQuantity(item.id, item.unit === 'pc' ? item.quantity - 1 : Number((item.quantity - 0.25).toFixed(3)))}
              class="w-8 h-8 sm:w-8.5 sm:h-8.5 flex items-center justify-center rounded-lg bg-white hover:bg-slate-200 active:bg-slate-300 text-slate-700 font-bold transition-colors shadow-2xs cursor-pointer"
              title="Decrease quantity"
            >
              <Minus class="w-3.5 h-3.5" />
            </button>

            <!-- Clickable Quantity for Direct Numpad Input -->
            <button
              type="button"
              onclick={() => editingItem = item}
              class="min-w-10 px-1 py-1 text-center text-xs font-bold font-mono text-slate-800 hover:text-emerald-700 hover:bg-emerald-50 rounded-md transition-colors cursor-pointer"
              title="Click to directly type quantity"
            >
              {item.unit === 'pc' ? item.quantity : item.quantity.toFixed(3)}
            </button>

            <button
              type="button"
              onclick={() => cart.updateQuantity(item.id, item.unit === 'pc' ? item.quantity + 1 : Number((item.quantity + 0.25).toFixed(3)))}
              class="w-8 h-8 sm:w-8.5 sm:h-8.5 flex items-center justify-center rounded-lg bg-white hover:bg-slate-200 active:bg-slate-300 text-slate-700 font-bold transition-colors shadow-2xs cursor-pointer"
              title="Increase quantity"
            >
              <Plus class="w-3.5 h-3.5" />
            </button>
          </div>

          <!-- Subtotal & Remove -->
          <div class="flex items-center gap-2 flex-shrink-0 text-right">
            <span class="text-xs font-extrabold font-mono text-slate-900 w-16">
              ₱{item.subtotal.toFixed(2)}
            </span>
            <button
              type="button"
              onclick={() => cart.removeItem(item.id)}
              class="w-8 h-8 flex items-center justify-center text-slate-400 hover:text-rose-600 hover:bg-rose-50 active:bg-rose-100 rounded-lg transition-colors cursor-pointer"
              title="Remove item from cart"
            >
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </div>
      {/each}
    {/if}
  </div>

  <!-- Cart Footer / Big Total & Checkout -->
  <div class="p-4 bg-slate-50/90 border-t border-slate-200 flex-shrink-0 space-y-3">
    <div class="flex items-baseline justify-between">
      <span class="text-xs font-bold uppercase tracking-wider text-slate-500">Total Amount:</span>
      <span class="text-3xl font-black font-mono text-slate-900 tracking-tight">
        ₱{cart.subtotal.toFixed(2)}
      </span>
    </div>

    <!-- Big Checkout Button -->
    <button
      type="button"
      onclick={onOpenPayment}
      disabled={cart.items.length === 0}
      class="w-full py-3.5 px-4 bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 disabled:opacity-40 disabled:cursor-not-allowed text-white font-extrabold text-sm rounded-xl shadow-md transition-all flex items-center justify-between cursor-pointer"
    >
      <span class="flex items-center gap-2">
        <span>Proceed to Payment</span>
        <kbd class="px-1.5 py-0.5 text-[10px] font-mono bg-emerald-700/80 rounded">F5</kbd>
      </span>
      <span class="text-base font-mono">₱{cart.subtotal.toFixed(2)}</span>
    </button>
  </div>
</div>

<!-- Quantity Direct Edit Modal -->
{#if editingItem}
  <QuantityModal
    item={editingItem}
    onSave={handleSaveQuantity}
    onRemove={handleRemoveEditingItem}
    onClose={() => editingItem = null}
  />
{/if}
