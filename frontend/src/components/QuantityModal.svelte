<script lang="ts">
  import type { CartItem } from '../types'
  import { Hash, Plus, Minus, Trash2, X, Check } from 'lucide-svelte'
  import { onMount } from 'svelte'

  interface Props {
    item: CartItem
    onSave: (newQuantity: number) => void
    onRemove: () => void
    onClose: () => void
  }

  let { item, onSave, onRemove, onClose }: Props = $props()

  let inputVal = $state<string>('')
  $effect(() => {
    inputVal = item.quantity.toString()
  })
  let inputEl = $state<HTMLInputElement | null>(null)

  let parsedQty = $derived.by(() => {
    const q = parseFloat(inputVal)
    return isNaN(q) || q <= 0 ? 0 : q
  })

  let subtotalPreview = $derived.by(() => {
    return Number((parsedQty * item.unit_price).toFixed(2))
  })

  function appendDigit(digit: string) {
    if (inputVal === '0' && digit !== '.') {
      inputVal = digit
    } else if (digit === '.' && inputVal.includes('.')) {
      // ignore extra decimal
    } else {
      inputVal += digit
    }
  }

  function handleBackspace() {
    inputVal = inputVal.slice(0, -1)
    if (!inputVal) inputVal = '0'
  }

  function handleClear() {
    inputVal = '0'
  }

  function bumpQuantity(amount: number) {
    const cur = parseFloat(inputVal) || 0
    const next = Math.max(1, cur + amount)
    inputVal = item.unit === 'pc' ? Math.round(next).toString() : next.toFixed(3)
  }

  function handleConfirm() {
    if (parsedQty <= 0) {
      onRemove()
    } else {
      onSave(parsedQty)
    }
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleConfirm()
    } else if (e.key === 'Escape') {
      e.preventDefault()
      onClose()
    }
  }

  onMount(() => {
    inputEl?.focus()
    inputEl?.select()
  })
</script>

<div
  class="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4 z-50 animate-in fade-in duration-150 select-none"
  onkeydown={handleKeyDown}
  role="dialog"
  aria-modal="true"
  tabindex="-1"
>
  <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-sm overflow-hidden flex flex-col">
    <!-- Header -->
    <div class="px-5 py-3.5 bg-slate-900 text-white flex items-center justify-between">
      <div class="flex items-center gap-2">
        <Hash class="w-5 h-5 text-emerald-400" />
        <div class="min-w-0">
          <h2 class="text-sm font-bold truncate">{item.product_name}</h2>
          <p class="text-[11px] text-slate-400 font-mono mt-0.5">Rate: ₱{item.unit_price.toFixed(2)} / {item.unit}</p>
        </div>
      </div>
      <button
        type="button"
        onclick={onClose}
        class="text-slate-400 hover:text-white p-1 rounded-lg transition-colors cursor-pointer"
      >
        <X class="w-5 h-5" />
      </button>
    </div>

    <!-- Body -->
    <div class="p-4 space-y-3">
      <!-- Quantity Input Display -->
      <div>
        <label for="qtyInput" class="block text-xs font-bold text-slate-700 mb-1">Enter Quantity ({item.unit}):</label>
        <div class="relative flex items-center">
          <input
            id="qtyInput"
            bind:this={inputEl}
            bind:value={inputVal}
            type="number"
            step="any"
            min="0"
            class="w-full px-4 py-2.5 bg-slate-50 border-2 border-emerald-500 rounded-xl text-2xl font-black font-mono text-slate-900 text-right focus:outline-none focus:bg-white"
          />
          <span class="absolute left-4 text-xs font-bold text-slate-400 uppercase">{item.unit}</span>
        </div>
      </div>

      <!-- Quick Steppers -->
      <div class="grid grid-cols-4 gap-1.5">
        <button
          type="button"
          onclick={() => bumpQuantity(1)}
          class="py-2 bg-slate-100 hover:bg-slate-200 active:bg-slate-300 rounded-lg text-xs font-bold font-mono text-slate-800 transition-colors"
        >
          +1
        </button>
        <button
          type="button"
          onclick={() => bumpQuantity(5)}
          class="py-2 bg-slate-100 hover:bg-slate-200 active:bg-slate-300 rounded-lg text-xs font-bold font-mono text-slate-800 transition-colors"
        >
          +5
        </button>
        <button
          type="button"
          onclick={() => bumpQuantity(10)}
          class="py-2 bg-slate-100 hover:bg-slate-200 active:bg-slate-300 rounded-lg text-xs font-bold font-mono text-slate-800 transition-colors"
        >
          +10
        </button>
        <button
          type="button"
          onclick={() => { inputVal = '1' }}
          class="py-2 bg-slate-200 hover:bg-slate-300 active:bg-slate-400 rounded-lg text-xs font-bold text-slate-800 transition-colors"
        >
          Reset 1
        </button>
      </div>

      <!-- Touch Numpad Grid -->
      <div class="grid grid-cols-3 gap-1.5 pt-1">
        {#each ['1', '2', '3', '4', '5', '6', '7', '8', '9'] as digit}
          <button
            type="button"
            onclick={() => appendDigit(digit)}
            class="h-11 rounded-xl bg-slate-50 hover:bg-slate-100 active:bg-slate-200 border border-slate-200 text-base font-bold font-mono text-slate-800 transition-all flex items-center justify-center cursor-pointer shadow-2xs"
          >
            {digit}
          </button>
        {/each}
        <button
          type="button"
          onclick={() => appendDigit('.')}
          class="h-11 rounded-xl bg-slate-50 hover:bg-slate-100 active:bg-slate-200 border border-slate-200 text-base font-bold font-mono text-slate-800 transition-all flex items-center justify-center cursor-pointer shadow-2xs"
        >
          .
        </button>
        <button
          type="button"
          onclick={() => appendDigit('0')}
          class="h-11 rounded-xl bg-slate-50 hover:bg-slate-100 active:bg-slate-200 border border-slate-200 text-base font-bold font-mono text-slate-800 transition-all flex items-center justify-center cursor-pointer shadow-2xs"
        >
          0
        </button>
        <button
          type="button"
          onclick={handleBackspace}
          class="h-11 rounded-xl bg-slate-100 hover:bg-slate-200 active:bg-slate-300 border border-slate-200 text-xs font-bold text-slate-700 transition-all flex items-center justify-center cursor-pointer shadow-2xs"
        >
          ⌫ Back
        </button>
      </div>

      <!-- Subtotal Preview -->
      <div class="p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-baseline justify-between">
        <span class="text-xs font-bold text-emerald-800 uppercase tracking-wider">Item Subtotal:</span>
        <span class="text-xl font-black font-mono text-emerald-700">₱{subtotalPreview.toFixed(2)}</span>
      </div>
    </div>

    <!-- Actions -->
    <div class="p-3.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between gap-2">
      <button
        type="button"
        onclick={onRemove}
        class="flex items-center gap-1.5 px-3 py-2 text-xs font-bold text-rose-600 hover:bg-rose-50 rounded-xl transition-colors cursor-pointer"
      >
        <Trash2 class="w-4 h-4" />
        <span>Delete Item</span>
      </button>

      <div class="flex items-center gap-2">
        <button
          type="button"
          onclick={onClose}
          class="px-3 py-2 text-xs font-bold text-slate-600 hover:text-slate-800 rounded-xl"
        >
          Cancel
        </button>
        <button
          type="button"
          onclick={handleConfirm}
          class="flex items-center gap-1.5 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white text-xs font-bold rounded-xl shadow-xs transition-all cursor-pointer"
        >
          <Check class="w-4 h-4" />
          <span>Update (Enter)</span>
        </button>
      </div>
    </div>
  </div>
</div>
