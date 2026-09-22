<script lang="ts">
  import type { TransactionResult } from '../types'
  import { printReceipt } from '../lib/api'
  import { sound } from '../lib/sound'
  import { CheckCircle2, Printer, ArrowRight, X, Copy, Check } from 'lucide-svelte'
  import { onMount } from 'svelte'

  interface Props {
    transaction: TransactionResult
    onClose: () => void
  }

  let { transaction, onClose }: Props = $props()

  let isPrinting = $state(false)
  let printStatus = $state('')
  let copied = $state(false)

  function formatReceipt(): string {
    const LINE_WIDTH = 32
    const center = (s: string) => s.length >= LINE_WIDTH ? s : ' '.repeat(Math.floor((LINE_WIDTH - s.length) / 2)) + s
    const twoCol = (left: string, right: string) => {
      const space = LINE_WIDTH - left.length - right.length
      return space > 0 ? left + ' '.repeat(space) + right : `${left} ${right}`
    }

    const lines: string[] = [
      center("COLDCUT & SARI-SARI POS"),
      center("Official POS Receipt"),
      "-".repeat(LINE_WIDTH),
      twoCol("Receipt #:", transaction.receipt_number),
      twoCol("Date:", new Date(transaction.created_at).toLocaleDateString()),
      twoCol("Time:", new Date(transaction.created_at).toLocaleTimeString()),
      "-".repeat(LINE_WIDTH)
    ]

    for (const item of transaction.items) {
      lines.push(twoCol(
        `${item.quantity}${item.unit === 'pc' ? 'x' : item.unit} ${item.product_name.substring(0, 16)}`,
        `P${item.subtotal.toFixed(2)}`
      ))
    }

    lines.push("-".repeat(LINE_WIDTH))
    lines.push(twoCol("TOTAL AMOUNT:", `P${transaction.total_amount.toFixed(2)}`))
    lines.push(twoCol("Payment Method:", transaction.payment_method))
    const changeVal = transaction.change ?? transaction.change_amount ?? 0
    lines.push(twoCol("CHANGE (SUKLI):", `P${changeVal.toFixed(2)}`))

    if (transaction.customer_name) {
      lines.push(twoCol("Customer:", transaction.customer_name))
    }

    lines.push("=".repeat(LINE_WIDTH))
    lines.push(center("Salamat po sa pagbili!"))
    lines.push(center("Please come again."))

    return lines.join("\n")
  }

  async function handlePrint() {
    isPrinting = true
    printStatus = ''
    try {
      const text = formatReceipt()
      const res = await printReceipt(text)
      printStatus = res.message || 'Receipt sent to 58mm printer!'
    } catch (e: any) {
      printStatus = 'Printer offline or not connected'
    } finally {
      isPrinting = false
    }
  }

  async function handleCopyReceipt() {
    try {
      await navigator.clipboard.writeText(formatReceipt())
      copied = true
      setTimeout(() => {
        copied = false
      }, 2000)
    } catch {
      // fallback
    }
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Enter' || e.key === 'Escape') {
      e.preventDefault()
      onClose()
    }
  }

  onMount(() => {
    sound.playBeep('success')
  })
</script>

<div
  class="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4 z-50 animate-in fade-in duration-150 select-none"
  onkeydown={handleKeyDown}
  role="dialog"
  aria-modal="true"
  tabindex="-1"
>
  <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-md overflow-hidden flex flex-col max-h-[95vh]">
    <!-- Success Banner -->
    <div class="p-5 bg-emerald-600 text-white text-center flex flex-col items-center flex-shrink-0">
      <CheckCircle2 class="w-11 h-11 text-emerald-200 mb-1.5" />
      <h2 class="text-xl font-black tracking-tight">Sale Completed!</h2>
      <p class="text-xs text-emerald-100 font-mono mt-0.5">Receipt #{transaction.receipt_number}</p>

      <!-- Change Banner -->
      <div class="mt-3.5 w-full bg-emerald-700/80 rounded-xl p-3 border border-emerald-500/50 flex items-baseline justify-between">
        <span class="text-xs font-bold uppercase tracking-wider text-emerald-100">Sukli (Change):</span>
        <span class="text-3xl font-black font-mono">₱{(transaction.change ?? transaction.change_amount ?? 0).toFixed(2)}</span>
      </div>
    </div>

    <!-- 58mm Thermal Preview -->
    <div class="p-4 bg-slate-50 border-y border-slate-200 flex-1 overflow-y-auto max-h-56">
      <div class="bg-white p-3 border border-slate-300 rounded-xl shadow-2xs font-mono text-[11px] leading-tight text-slate-800 whitespace-pre">
        {formatReceipt()}
      </div>
      {#if printStatus}
        <p class="text-[11px] font-bold text-center mt-2 {printStatus.includes('offline') ? 'text-amber-700' : 'text-emerald-700'}">
          {printStatus}
        </p>
      {/if}
    </div>

    <!-- Actions -->
    <div class="p-3.5 bg-white flex flex-col gap-2 flex-shrink-0">
      <div class="flex items-center gap-2">
        <button
          type="button"
          onclick={handlePrint}
          disabled={isPrinting}
          class="flex-1 flex items-center justify-center gap-1.5 py-2.5 bg-slate-100 hover:bg-slate-200 active:bg-slate-300 text-slate-800 text-xs font-bold rounded-xl transition-all cursor-pointer"
        >
          <Printer class="w-4 h-4 text-slate-600" />
          <span>{isPrinting ? 'Printing...' : 'Print 58mm'}</span>
        </button>

        <button
          type="button"
          onclick={handleCopyReceipt}
          class="flex items-center justify-center gap-1.5 px-4 py-2.5 bg-slate-100 hover:bg-slate-200 active:bg-slate-300 text-slate-800 text-xs font-bold rounded-xl transition-all cursor-pointer"
          title="Copy receipt for SMS or messenger"
        >
          {#if copied}
            <Check class="w-4 h-4 text-emerald-600" />
            <span class="text-emerald-700">Copied!</span>
          {:else}
            <Copy class="w-4 h-4 text-slate-600" />
            <span>Copy Text</span>
          {/if}
        </button>
      </div>

      <!-- Primary Next Customer CTA -->
      <button
        type="button"
        onclick={onClose}
        class="w-full py-3 bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white text-xs font-black rounded-xl shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer"
      >
        <span>Next Customer / Bagong Sukli (Enter)</span>
        <ArrowRight class="w-4 h-4" />
      </button>
    </div>
  </div>
</div>
