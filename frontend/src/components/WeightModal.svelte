<script lang="ts">
  import type { Product } from '../types'
  import { Scale, Banknote, X, Check, Delete } from 'lucide-svelte'
  import { onMount } from 'svelte'

  interface Props {
    product: Product
    onConfirm: (quantity: number, subtotal: number, label: string) => void
    onClose: () => void
  }

  let { product, onConfirm, onClose }: Props = $props()

  let mode = $state<'weight' | 'peso'>('weight')
  let weightVal = $state<string>('0.5')
  let pesoVal = $state<string>('20')
  let inputWeightEl = $state<HTMLInputElement | null>(null)
  let inputPesoEl = $state<HTMLInputElement | null>(null)

  // Computed values
  let pricePerKg = $derived(product.selling_price || 50)

  let computedSubtotal = $derived.by(() => {
    if (mode === 'weight') {
      const w = parseFloat(weightVal) || 0
      return Number((w * pricePerKg).toFixed(2))
    } else {
      return parseFloat(pesoVal) || 0
    }
  })

  let computedWeight = $derived.by(() => {
    if (mode === 'weight') {
      return parseFloat(weightVal) || 0
    } else {
      const p = parseFloat(pesoVal) || 0
      return pricePerKg > 0 ? Number((p / pricePerKg).toFixed(3)) : 0
    }
  })

  function setPresetWeight(w: number) {
    mode = 'weight'
    weightVal = w.toString()
  }

  function setPresetPeso(p: number) {
    mode = 'peso'
    pesoVal = p.toString()
  }

  function appendNumpad(val: string) {
    if (mode === 'weight') {
      if (weightVal === '0' && val !== '.') {
        weightVal = val
      } else if (val === '.' && weightVal.includes('.')) {
        // ignore duplicate dot
      } else {
        weightVal += val
      }
    } else {
      if (pesoVal === '0' && val !== '.') {
        pesoVal = val
      } else if (val === '.' && pesoVal.includes('.')) {
        // ignore duplicate dot
      } else {
        pesoVal += val
      }
    }
  }

  function handleBackspace() {
    if (mode === 'weight') {
      weightVal = weightVal.slice(0, -1)
      if (!weightVal) weightVal = '0'
    } else {
      pesoVal = pesoVal.slice(0, -1)
      if (!pesoVal) pesoVal = '0'
    }
  }

  function handleClear() {
    if (mode === 'weight') {
      weightVal = '0'
    } else {
      pesoVal = '0'
    }
  }

  function handleSubmit() {
    if (computedWeight <= 0 || computedSubtotal <= 0) return

    const label = mode === 'peso'
      ? `₱${computedSubtotal.toFixed(2)} portion (${computedWeight}kg)`
      : `${computedWeight}kg portion`

    onConfirm(computedWeight, computedSubtotal, label)
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleSubmit()
    } else if (e.key === 'Escape') {
      e.preventDefault()
      onClose()
    } else if ((e.key === 'w' || e.key === 'W') && document.activeElement?.tagName !== 'INPUT') {
      mode = 'weight'
    } else if ((e.key === 'p' || e.key === 'P') && document.activeElement?.tagName !== 'INPUT') {
      mode = 'peso'
    }
  }

  onMount(() => {
    inputWeightEl?.focus()
    inputWeightEl?.select()
  })
</script>

<!-- Backdrop -->
<div
  class="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4 z-50 animate-in fade-in duration-150 select-none"
  onkeydown={handleKeyDown}
  role="dialog"
  aria-modal="true"
  tabindex="-1"
>
  <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-lg overflow-hidden flex flex-col max-h-[95vh]">
    <!-- Header -->
    <div class="px-5 py-3.5 bg-cyan-700 text-white flex items-center justify-between">
      <div class="flex items-center gap-2.5">
        <Scale class="w-5 h-5 text-cyan-200" />
        <div>
          <h2 class="text-sm font-bold tracking-tight leading-tight">{product.name}</h2>
          <p class="text-[11px] text-cyan-100 font-mono mt-0.5">Rate: ₱{pricePerKg.toFixed(2)} / {product.unit}</p>
        </div>
      </div>
      <button
        type="button"
        onclick={onClose}
        class="text-cyan-200 hover:text-white p-1 rounded-lg transition-colors cursor-pointer"
      >
        <X class="w-5 h-5" />
      </button>
    </div>

    <!-- Mode Selector Tabs -->
    <div class="p-4 space-y-3 overflow-y-auto">
      <div class="grid grid-cols-2 gap-2 bg-slate-100 p-1 rounded-xl">
        <button
          type="button"
          onclick={() => { mode = 'weight'; setTimeout(() => inputWeightEl?.focus(), 50) }}
          class="flex items-center justify-center gap-1.5 py-2.5 text-xs font-bold rounded-lg transition-all cursor-pointer {mode === 'weight' ? 'bg-white text-cyan-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'}"
        >
          <Scale class="w-4 h-4" />
          <span>By Weight (kg) <kbd class="text-[10px] opacity-60">W</kbd></span>
        </button>

        <button
          type="button"
          onclick={() => { mode = 'peso'; setTimeout(() => inputPesoEl?.focus(), 50) }}
          class="flex items-center justify-center gap-1.5 py-2.5 text-xs font-bold rounded-lg transition-all cursor-pointer {mode === 'peso' ? 'bg-white text-cyan-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'}"
        >
          <Banknote class="w-4 h-4" />
          <span>By Peso Amount (₱) <kbd class="text-[10px] opacity-60">P</kbd></span>
        </button>
      </div>

      {#if mode === 'weight'}
        <!-- Input by Weight -->
        <div class="space-y-2">
          <label for="weightInput" class="block text-xs font-bold text-slate-700">Enter Weighed Kilograms or Grams:</label>
          <div class="relative flex items-center">
            <input
              id="weightInput"
              bind:this={inputWeightEl}
              bind:value={weightVal}
              type="number"
              step="0.005"
              min="0.001"
              class="w-full px-4 py-2.5 bg-slate-50 border-2 border-cyan-500 rounded-xl text-2xl font-black font-mono text-slate-900 focus:outline-none focus:bg-white text-right"
            />
            <span class="absolute left-4 text-xs font-bold text-slate-400 uppercase">{product.unit}</span>
          </div>

          <!-- Quick Weight Pills for Butcher Cuts -->
          <div class="grid grid-cols-3 sm:grid-cols-6 gap-1.5">
            {#each [0.25, 0.5, 0.75, 1.0, 1.5, 2.0] as w}
              <button
                type="button"
                onclick={() => setPresetWeight(w)}
                class="py-2 text-xs font-bold rounded-lg border transition-all cursor-pointer {parseFloat(weightVal) === w ? 'bg-cyan-600 text-white border-cyan-600 shadow-xs' : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'}"
              >
                {w === 0.25 ? '250g' : w === 0.5 ? '500g' : w === 0.75 ? '750g' : `${w} kg`}
              </button>
            {/each}
          </div>
        </div>
      {:else}
        <!-- Input by Peso -->
        <div class="space-y-2">
          <label for="pesoInput" class="block text-xs font-bold text-slate-700">Customer Buys (e.g. ₱20, ₱50):</label>
          <div class="relative flex items-center">
            <span class="absolute left-4 text-lg font-bold text-slate-400">₱</span>
            <input
              id="pesoInput"
              bind:this={inputPesoEl}
              bind:value={pesoVal}
              type="number"
              step="1"
              min="1"
              class="w-full pl-9 pr-4 py-2.5 bg-slate-50 border-2 border-emerald-500 rounded-xl text-2xl font-bold font-mono text-slate-900 focus:outline-none focus:bg-white text-right"
            />
          </div>

          <!-- Quick Peso Pills -->
          <div class="grid grid-cols-5 gap-1.5">
            {#each [10, 20, 30, 50, 100] as p}
              <button
                type="button"
                onclick={() => setPresetPeso(p)}
                class="py-2 text-xs font-bold rounded-lg border transition-all cursor-pointer {parseFloat(pesoVal) === p ? 'bg-emerald-600 text-white border-emerald-600 shadow-xs' : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'}"
              >
                ₱{p}
              </button>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Built-in Touch Numpad for Kiosks -->
      <div class="grid grid-cols-3 gap-1.5 pt-1">
        {#each ['1', '2', '3', '4', '5', '6', '7', '8', '9'] as digit}
          <button
            type="button"
            onclick={() => appendNumpad(digit)}
            class="h-10 rounded-xl bg-slate-50 hover:bg-slate-100 active:bg-slate-200 border border-slate-200 text-base font-bold font-mono text-slate-800 transition-all flex items-center justify-center cursor-pointer shadow-2xs"
          >
            {digit}
          </button>
        {/each}
        <button
          type="button"
          onclick={() => appendNumpad('.')}
          class="h-10 rounded-xl bg-slate-50 hover:bg-slate-100 active:bg-slate-200 border border-slate-200 text-base font-bold font-mono text-slate-800 transition-all flex items-center justify-center cursor-pointer shadow-2xs"
        >
          .
        </button>
        <button
          type="button"
          onclick={() => appendNumpad('0')}
          class="h-10 rounded-xl bg-slate-50 hover:bg-slate-100 active:bg-slate-200 border border-slate-200 text-base font-bold font-mono text-slate-800 transition-all flex items-center justify-center cursor-pointer shadow-2xs"
        >
          0
        </button>
        <button
          type="button"
          onclick={handleBackspace}
          class="h-10 rounded-xl bg-slate-100 hover:bg-slate-200 active:bg-slate-300 border border-slate-200 text-xs font-bold text-slate-700 transition-all flex items-center justify-center cursor-pointer shadow-2xs"
        >
          ⌫ Back
        </button>
      </div>

      <!-- Result Summary Box -->
      <div class="bg-emerald-50 border border-emerald-200 rounded-xl p-3 flex items-center justify-between">
        <div>
          <p class="text-[10px] font-bold text-emerald-800 uppercase tracking-wider">Calculated Portion</p>
          <p class="text-sm font-extrabold text-emerald-950 font-mono mt-0.5">
            {computedWeight.toFixed(3)} {product.unit}
          </p>
        </div>
        <div class="text-right">
          <p class="text-[10px] font-bold text-emerald-800 uppercase tracking-wider">Charge Amount</p>
          <p class="text-2xl font-black text-emerald-700 font-mono mt-0.5">
            ₱{computedSubtotal.toFixed(2)}
          </p>
        </div>
      </div>
    </div>

    <!-- Actions -->
    <div class="p-3.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between gap-2">
      <button
        type="button"
        onclick={onClose}
        class="px-4 py-2 text-xs font-bold text-slate-600 hover:text-slate-800 rounded-xl cursor-pointer"
      >
        Cancel (Esc)
      </button>

      <button
        type="button"
        onclick={handleSubmit}
        disabled={computedWeight <= 0 || computedSubtotal <= 0}
        class="flex items-center gap-1.5 px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 disabled:opacity-40 text-white text-xs font-bold rounded-xl shadow-xs transition-all cursor-pointer"
      >
        <Check class="w-4 h-4" />
        <span>Add to Cart (Enter)</span>
      </button>
    </div>
  </div>
</div>
