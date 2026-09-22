<script lang="ts">
  import { cart } from '../lib/cart.svelte'
  import { submitCheckout, fetchDebtCustomers } from '../lib/api'
  import type { CustomerDebt, TransactionResult } from '../types'
  import { Banknote, Smartphone, BookOpen, X, Check, Printer, Loader2, AlertCircle } from 'lucide-svelte'
  import { onMount } from 'svelte'

  interface Props {
    onComplete: (res: TransactionResult) => void
    onClose: () => void
  }

  let { onComplete, onClose }: Props = $props()

  let method = $state<'CASH' | 'GCASH' | 'UTANG'>('CASH')
  let amountTendered = $state<string>('')
  let printReceipt = $state(false)
  let isSubmitting = $state(false)
  let errorMessage = $state('')

  // GCash optional logging
  let gcashRef = $state('')
  let gcashCustomerMobile = $state('')

  // Utang fields
  let customerList = $state<CustomerDebt[]>([])
  let selectedCustomerName = $state('')
  let customerPhone = $state('')
  let partialPaidNow = $state<string>('0')
  let utangNotes = $state('')

  let inputTenderedEl = $state<HTMLInputElement | null>(null)

  let totalAmount = $derived(cart.subtotal)

  let numericTendered = $derived(parseFloat(amountTendered) || 0)

  let changeAmount = $derived.by(() => {
    return numericTendered >= totalAmount ? Number((numericTendered - totalAmount).toFixed(2)) : 0
  })

  let shortageAmount = $derived.by(() => {
    return numericTendered < totalAmount ? Number((totalAmount - numericTendered).toFixed(2)) : 0
  })

  let isTenderedSufficient = $derived.by(() => {
    if (method === 'UTANG') return selectedCustomerName.trim().length > 0
    if (method === 'GCASH') return true
    return numericTendered >= totalAmount
  })

  function setExactAmount() {
    amountTendered = totalAmount.toString()
  }

  function setDenomination(denom: number) {
    amountTendered = denom.toString()
  }

  function addDenomination(denom: number) {
    const cur = parseFloat(amountTendered) || 0
    amountTendered = (cur + denom).toString()
  }

  function appendNumpad(val: string) {
    if (amountTendered === '0' && val !== '.') {
      amountTendered = val
    } else if (val === '.' && amountTendered.includes('.')) {
      // ignore
    } else {
      amountTendered += val
    }
  }

  function handleBackspace() {
    amountTendered = amountTendered.slice(0, -1)
    if (!amountTendered) amountTendered = '0'
  }

  function handleClear() {
    amountTendered = '0'
  }

  async function handleCheckout() {
    if (!isTenderedSufficient || isSubmitting) return

    isSubmitting = true
    errorMessage = ''

    try {
      const payload: any = {
        items: cart.items,
        total_amount: totalAmount,
        payment_method: method,
        amount_tendered: method === 'CASH' ? numericTendered : totalAmount,
        print_receipt: printReceipt
      }

      if (method === 'GCASH') {
        if (gcashRef.trim()) payload.reference_number = gcashRef.trim()
        if (gcashCustomerMobile.trim()) payload.phone_number = gcashCustomerMobile.trim()
      } else if (method === 'UTANG') {
        payload.customer_name = selectedCustomerName.trim()
        payload.phone_number = customerPhone.trim() || undefined
        payload.notes = utangNotes.trim() || undefined
        payload.amount_paid_now = parseFloat(partialPaidNow) || 0
      }

      const result = await submitCheckout(payload)
      cart.clearCart()
      onComplete(result)
    } catch (err: any) {
      errorMessage = err.message || 'Payment processing failed'
    } finally {
      isSubmitting = false
    }
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      e.preventDefault()
      onClose()
    } else if (e.key === 'Enter' || e.key === 'F5') {
      e.preventDefault()
      handleCheckout()
    } else if (document.activeElement?.tagName !== 'INPUT') {
      if (e.key === '1') {
        method = 'CASH'
      } else if (e.key === '2') {
        method = 'GCASH'
      } else if (e.key === '3') {
        method = 'UTANG'
      }
    }
  }

  onMount(async () => {
    setExactAmount()
    inputTenderedEl?.focus()
    inputTenderedEl?.select()

    try {
      customerList = await fetchDebtCustomers()
    } catch (e) {
      // quiet
    }
  })
</script>

<div
  class="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4 z-50 animate-in fade-in duration-150 select-none"
  onkeydown={handleKeyDown}
  role="dialog"
  aria-modal="true"
  tabindex="-1"
>
  <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-lg overflow-hidden flex flex-col max-h-[96vh]">
    <!-- Header -->
    <div class="px-5 py-3.5 bg-slate-900 text-white flex items-center justify-between flex-shrink-0">
      <div>
        <h2 class="text-base font-bold tracking-tight">Complete Payment</h2>
        <p class="text-xs text-slate-400 mt-0.5">Total: <span class="text-emerald-400 font-mono font-bold">₱{totalAmount.toFixed(2)}</span> ({cart.itemCount} items)</p>
      </div>
      <button
        type="button"
        onclick={onClose}
        class="text-slate-400 hover:text-white p-1 rounded-lg transition-colors cursor-pointer"
      >
        <X class="w-5 h-5" />
      </button>
    </div>

    <!-- Payment Methods -->
    <div class="p-4 space-y-3.5 overflow-y-auto flex-1">
      <div class="grid grid-cols-3 gap-2 bg-slate-100 p-1 rounded-xl">
        <button
          type="button"
          onclick={() => { method = 'CASH'; setTimeout(() => inputTenderedEl?.focus(), 50) }}
          class="flex items-center justify-center gap-1.5 py-2.5 text-xs font-bold rounded-lg transition-all cursor-pointer {method === 'CASH' ? 'bg-emerald-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'}"
        >
          <Banknote class="w-4 h-4" />
          <span>CASH <kbd class="text-[10px] opacity-70">1</kbd></span>
        </button>

        <button
          type="button"
          onclick={() => method = 'GCASH'}
          class="flex items-center justify-center gap-1.5 py-2.5 text-xs font-bold rounded-lg transition-all cursor-pointer {method === 'GCASH' ? 'bg-blue-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'}"
        >
          <Smartphone class="w-4 h-4" />
          <span>GCASH <kbd class="text-[10px] opacity-70">2</kbd></span>
        </button>

        <button
          type="button"
          onclick={() => method = 'UTANG'}
          class="flex items-center justify-center gap-1.5 py-2.5 text-xs font-bold rounded-lg transition-all cursor-pointer {method === 'UTANG' ? 'bg-amber-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'}"
        >
          <BookOpen class="w-4 h-4" />
          <span>UTANG <kbd class="text-[10px] opacity-70">3</kbd></span>
        </button>
      </div>

      {#if errorMessage}
        <div class="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs font-bold text-rose-700 flex items-center gap-2">
          <AlertCircle class="w-4 h-4 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      {/if}

      <!-- Cash Mode -->
      {#if method === 'CASH'}
        <div class="space-y-3">
          <div>
            <div class="flex items-center justify-between mb-1">
              <label for="cashTendered" class="text-xs font-bold text-slate-700">Amount Tendered (Bayad):</label>
              <button
                type="button"
                onclick={setExactAmount}
                class="text-xs font-bold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 px-2 py-0.5 rounded cursor-pointer"
              >
                Exact (₱{totalAmount.toFixed(2)})
              </button>
            </div>
            <div class="relative flex items-center">
              <span class="absolute left-4 text-xl font-black text-slate-400">₱</span>
              <input
                id="cashTendered"
                bind:this={inputTenderedEl}
                bind:value={amountTendered}
                type="number"
                step="any"
                min="0"
                class="w-full pl-10 pr-4 py-2.5 bg-slate-50 border-2 border-emerald-500 rounded-xl text-2xl font-black font-mono text-slate-900 focus:outline-none focus:bg-white text-right"
              />
            </div>
          </div>

          <!-- Quick Denomination Buttons (+ Additive and Exact Set) -->
          <div class="space-y-1.5">
            <div class="text-[11px] font-bold text-slate-500 flex items-center justify-between">
              <span>Quick Bills:</span>
              <span class="text-[10px] text-slate-400">Tap to set, or hold shift to add</span>
            </div>
            <div class="grid grid-cols-4 sm:grid-cols-6 gap-1.5">
              {#each [20, 50, 100, 200, 500, 1000] as denom}
                <button
                  type="button"
                  onclick={() => setDenomination(denom)}
                  class="py-2 text-xs font-bold font-mono rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-emerald-50 hover:border-emerald-300 hover:text-emerald-800 active:scale-95 transition-all cursor-pointer shadow-2xs"
                >
                  ₱{denom}
                </button>
              {/each}
            </div>
          </div>

          <!-- Touch Numpad for Touchscreen Terminals -->
          <div class="grid grid-cols-4 gap-1.5 pt-1">
            <div class="col-span-3 grid grid-cols-3 gap-1.5">
              {#each ['1', '2', '3', '4', '5', '6', '7', '8', '9'] as digit}
                <button
                  type="button"
                  onclick={() => appendNumpad(digit)}
                  class="h-9.5 rounded-xl bg-slate-50 hover:bg-slate-100 active:bg-slate-200 border border-slate-200 text-sm font-bold font-mono text-slate-800 transition-all flex items-center justify-center cursor-pointer shadow-2xs"
                >
                  {digit}
                </button>
              {/each}
              <button
                type="button"
                onclick={() => appendNumpad('.')}
                class="h-9.5 rounded-xl bg-slate-50 hover:bg-slate-100 active:bg-slate-200 border border-slate-200 text-sm font-bold font-mono text-slate-800 transition-all flex items-center justify-center cursor-pointer shadow-2xs"
              >
                .
              </button>
              <button
                type="button"
                onclick={() => appendNumpad('0')}
                class="h-9.5 rounded-xl bg-slate-50 hover:bg-slate-100 active:bg-slate-200 border border-slate-200 text-sm font-bold font-mono text-slate-800 transition-all flex items-center justify-center cursor-pointer shadow-2xs"
              >
                0
              </button>
              <button
                type="button"
                onclick={handleBackspace}
                class="h-9.5 rounded-xl bg-slate-100 hover:bg-slate-200 active:bg-slate-300 border border-slate-200 text-xs font-bold text-slate-700 transition-all flex items-center justify-center cursor-pointer shadow-2xs"
              >
                ⌫
              </button>
            </div>

            <!-- Additive Bills column -->
            <div class="flex flex-col gap-1.5">
              <button
                type="button"
                onclick={() => addDenomination(20)}
                class="flex-1 py-1 bg-amber-50 hover:bg-amber-100 border border-amber-200 rounded-lg text-[11px] font-bold font-mono text-amber-900 transition-colors cursor-pointer"
              >
                +₱20
              </button>
              <button
                type="button"
                onclick={() => addDenomination(50)}
                class="flex-1 py-1 bg-amber-50 hover:bg-amber-100 border border-amber-200 rounded-lg text-[11px] font-bold font-mono text-amber-900 transition-colors cursor-pointer"
              >
                +₱50
              </button>
              <button
                type="button"
                onclick={() => addDenomination(100)}
                class="flex-1 py-1 bg-amber-50 hover:bg-amber-100 border border-amber-200 rounded-lg text-[11px] font-bold font-mono text-amber-900 transition-colors cursor-pointer"
              >
                +₱100
              </button>
              <button
                type="button"
                onclick={handleClear}
                class="flex-1 py-1 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-lg text-[11px] font-bold transition-colors cursor-pointer"
              >
                Clear
              </button>
            </div>
          </div>

          <!-- Dynamic Sukli vs Kulang Banner -->
          {#if numericTendered >= totalAmount}
            <div class="p-3.5 rounded-xl border bg-emerald-50 border-emerald-300 text-emerald-950 flex items-center justify-between shadow-2xs animate-in fade-in duration-100">
              <span class="text-xs font-extrabold uppercase tracking-wider text-emerald-900">Sukli (Change):</span>
              <span class="text-3xl font-black font-mono text-emerald-700">
                ₱{changeAmount.toFixed(2)}
              </span>
            </div>
          {:else if numericTendered > 0}
            <div class="p-3.5 rounded-xl border bg-rose-50 border-rose-300 text-rose-950 flex items-center justify-between shadow-2xs animate-in fade-in duration-100">
              <span class="text-xs font-extrabold uppercase tracking-wider text-rose-900">⚠️ Kulang pa ng:</span>
              <span class="text-2xl font-black font-mono text-rose-700">
                ₱{shortageAmount.toFixed(2)}
              </span>
            </div>
          {:else}
            <div class="p-3 rounded-xl border bg-slate-50 border-slate-200 text-slate-500 flex items-center justify-between">
              <span class="text-xs font-semibold">Tender required:</span>
              <span class="text-lg font-bold font-mono text-slate-700">₱{totalAmount.toFixed(2)}</span>
            </div>
          {/if}
        </div>

      <!-- GCash Mode -->
      {:else if method === 'GCASH'}
        <div class="space-y-3">
          <div class="p-4 bg-blue-50 border border-blue-200 rounded-xl space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-blue-900">GCash Exact Payment:</span>
              <span class="text-xl font-black font-mono text-blue-800">₱{totalAmount.toFixed(2)}</span>
            </div>
            <p class="text-xs text-blue-700 leading-relaxed">
              Customer scans store QRPh or sends to store GCash number. Please verify receipt SMS or app notification before completing checkout.
            </p>
          </div>

          <!-- Optional Reference Logging -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
            <div>
              <label for="gcashRefNum" class="block text-[11px] font-semibold text-slate-600 mb-1">Reference No. (Optional):</label>
              <input
                id="gcashRefNum"
                bind:value={gcashRef}
                placeholder="e.g. 5042..."
                class="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs font-mono font-semibold text-slate-900"
              />
            </div>
            <div>
              <label for="gcashMobileNum" class="block text-[11px] font-semibold text-slate-600 mb-1">Customer Mobile (Optional):</label>
              <input
                id="gcashMobileNum"
                bind:value={gcashCustomerMobile}
                placeholder="09..."
                class="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs font-mono text-slate-900"
              />
            </div>
          </div>
        </div>

      <!-- Utang / Palista Mode -->
      {:else if method === 'UTANG'}
        <div class="space-y-3">
          <div>
            <label for="customerName" class="block text-xs font-bold text-slate-700 mb-1">Customer Name (Palista kay):</label>
            <input
              id="customerName"
              bind:value={selectedCustomerName}
              list="customerNamesList"
              placeholder="Type or pick customer name..."
              class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-semibold text-slate-900 focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
            <datalist id="customerNamesList">
              {#each customerList as c}
                <option value={c.customer_name}>Current Balance: ₱{c.total_debt.toFixed(2)}</option>
              {/each}
            </datalist>
          </div>

          <div class="grid grid-cols-2 gap-2">
            <div>
              <label for="customerPhone" class="block text-[11px] font-semibold text-slate-600 mb-1">Phone Number:</label>
              <input
                id="customerPhone"
                bind:value={customerPhone}
                placeholder="09..."
                class="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs"
              />
            </div>
            <div>
              <label for="downPayment" class="block text-[11px] font-semibold text-slate-600 mb-1">Downpayment Now (₱):</label>
              <input
                id="downPayment"
                bind:value={partialPaidNow}
                type="number"
                min="0"
                class="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs font-mono font-bold"
              />
            </div>
          </div>
        </div>
      {/if}

      <!-- Print Receipt Option -->
      <label class="flex items-center gap-2 cursor-pointer pt-1 text-xs font-semibold text-slate-700">
        <input
          type="checkbox"
          bind:checked={printReceipt}
          class="w-4 h-4 rounded text-emerald-600 focus:ring-emerald-500 border-slate-300 cursor-pointer"
        />
        <Printer class="w-4 h-4 text-slate-500" />
        <span>Print 58mm Thermal Receipt</span>
      </label>
    </div>

    <!-- Actions -->
    <div class="p-3.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between flex-shrink-0">
      <button
        type="button"
        onclick={onClose}
        class="px-4 py-2.5 text-xs font-bold text-slate-600 hover:text-slate-900 rounded-xl cursor-pointer"
      >
        Cancel (Esc)
      </button>

      <button
        type="button"
        onclick={handleCheckout}
        disabled={!isTenderedSufficient || isSubmitting}
        class="flex items-center gap-2 px-6 py-3 bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs font-extrabold rounded-xl shadow-md transition-all cursor-pointer"
      >
        {#if isSubmitting}
          <Loader2 class="w-4 h-4 animate-spin" />
          <span>Processing...</span>
        {:else}
          <Check class="w-4 h-4" />
          <span>Finish Sale (Enter / F5)</span>
        {/if}
      </button>
    </div>
  </div>
</div>
