<script lang="ts">
  import { cart } from '../lib/cart.svelte'
  import { sound } from '../lib/sound'
  import { onMount } from 'svelte'
  import { fetchDailyReport } from '../lib/api'
  import {
    Store,
    Clock,
    PauseCircle,
    Volume2,
    VolumeX,
    HelpCircle,
    BookOpen,
    RefreshCw
  } from 'lucide-svelte'

  interface Props {
    onOpenParked: () => void
    onOpenShortcuts: () => void
    onOpenGCash: () => void
    onOpenUtang: () => void
  }

  let { onOpenParked, onOpenShortcuts, onOpenGCash, onOpenUtang }: Props = $props()

  let currentTime = $state('')
  let drawerCash = $state<number | null>(null)
  let isRefreshingDrawer = $state(false)
  let soundEnabled = $state(sound.enabled)

  function toggleSound() {
    sound.enabled = !sound.enabled
    soundEnabled = sound.enabled
    if (soundEnabled) {
      sound.playBeep('scan')
    }
  }

  function updateClock() {
    const now = new Date()
    currentTime = now.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    })
  }

  async function loadDrawer() {
    isRefreshingDrawer = true
    try {
      const data = await fetchDailyReport()
      if (data && data.cash_in_drawer !== undefined) {
        drawerCash = data.cash_in_drawer
      }
    } catch (e) {
      // quiet fail
    } finally {
      isRefreshingDrawer = false
    }
  }

  onMount(() => {
    updateClock()
    const timer = setInterval(updateClock, 1000)
    loadDrawer()
    const drawerTimer = setInterval(loadDrawer, 30000)
    return () => {
      clearInterval(timer)
      clearInterval(drawerTimer)
    }
  })
</script>

<header class="bg-white border-b border-slate-200 px-3 sm:px-4 py-2 flex flex-wrap items-center justify-between gap-2 shadow-xs z-10 select-none flex-shrink-0">
  <!-- Brand & Status -->
  <div class="flex items-center gap-2.5">
    <div class="w-9 h-9 rounded-xl bg-cyan-600 text-white flex items-center justify-center font-bold shadow-xs flex-shrink-0">
      <Store class="w-5 h-5" />
    </div>
    <div>
      <div class="flex items-center gap-1.5 flex-wrap">
        <h1 class="text-sm font-extrabold text-slate-900 tracking-tight leading-none">Coldcut POS</h1>
        <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-cyan-50 text-cyan-800 border border-cyan-200">
          <span class="w-1.5 h-1.5 rounded-full bg-cyan-500 animate-pulse"></span>
          DAHUA SCALE READY
        </span>
      </div>
      <p class="text-[11px] text-slate-500 font-medium mt-0.5 hidden sm:block">Poultry, Frozen Cuts, Ice & Chilled Drinks</p>
    </div>
  </div>

  <!-- Center: Live Clock & Cash in Drawer -->
  <div class="hidden lg:flex items-center gap-3 text-xs">
    <div class="flex items-center gap-1.5 px-2.5 py-1 bg-slate-50 border border-slate-200 rounded-lg text-slate-700 font-medium">
      <Clock class="w-3.5 h-3.5 text-slate-400" />
      <span>{currentTime}</span>
    </div>

    {#if drawerCash !== null}
      <button
        type="button"
        onclick={loadDrawer}
        class="flex items-center gap-1.5 px-2.5 py-1 bg-amber-50 hover:bg-amber-100 border border-amber-200 rounded-lg text-amber-800 font-bold cursor-pointer transition-colors"
        title="Click to refresh cash drawer total"
      >
        <span>💵 Drawer: ₱{drawerCash.toFixed(2)}</span>
        <RefreshCw class="w-3 h-3 text-amber-600 {isRefreshingDrawer ? 'animate-spin' : ''}" />
      </button>
    {/if}
  </div>

  <!-- Right Actions -->
  <div class="flex items-center gap-1.5 sm:gap-2">
    <!-- Sound Toggle -->
    <button
      type="button"
      onclick={toggleSound}
      class="p-2 rounded-lg border transition-all cursor-pointer {soundEnabled ? 'text-slate-600 bg-slate-50 border-slate-200 hover:bg-slate-100' : 'text-slate-400 bg-slate-100 border-slate-200'}"
      title={soundEnabled ? 'Scanner Beep Sound: ON (Click to mute)' : 'Scanner Beep Sound: MUTED (Click to unmute)'}
    >
      {#if soundEnabled}
        <Volume2 class="w-4 h-4 text-emerald-600" />
      {:else}
        <VolumeX class="w-4 h-4 text-slate-400" />
      {/if}
    </button>

    <!-- Utang Ledger Button -->
    <button
      type="button"
      onclick={onOpenUtang}
      class="flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 text-xs font-bold text-amber-800 bg-amber-50 hover:bg-amber-100 border border-amber-200 rounded-lg transition-all shadow-2xs cursor-pointer"
      title="Customer Utang Ledger & Repayments (F7)"
    >
      <BookOpen class="w-4 h-4 text-amber-600" />
      <span class="hidden sm:inline">Utang Ledger</span>
      <kbd class="text-[9px] bg-amber-200/70 px-1 py-0.2 rounded font-mono font-bold">F7</kbd>
    </button>

    <!-- Parked Carts Button -->
    <button
      type="button"
      onclick={onOpenParked}
      class="relative flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 text-xs font-semibold rounded-lg border transition-all cursor-pointer {cart.parkedCarts.length > 0 ? 'bg-amber-50 border-amber-300 text-amber-800 hover:bg-amber-100' : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'}"
      title="Park / Hold Carts (F4)"
    >
      <PauseCircle class="w-4 h-4 {cart.parkedCarts.length > 0 ? 'text-amber-600' : 'text-slate-400'}" />
      <span class="hidden sm:inline">Hold</span>
      <kbd class="text-[9px] bg-slate-200 px-1 py-0.2 rounded font-mono font-bold">F4</kbd>
      {#if cart.parkedCarts.length > 0}
        <span class="w-4.5 h-4.5 rounded-full bg-amber-500 text-white font-bold text-[10px] flex items-center justify-center">
          {cart.parkedCarts.length}
        </span>
      {/if}
    </button>

    <!-- Shortcuts Help -->
    <button
      type="button"
      onclick={onOpenShortcuts}
      class="p-1.5 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-all cursor-pointer"
      title="Keyboard Shortcuts"
    >
      <HelpCircle class="w-4 h-4" />
    </button>

    <!-- Admin Link -->
    <a
      href="/admin"
      target="_blank"
      class="flex items-center gap-1 px-2.5 sm:px-3 py-1.5 text-xs font-bold text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-lg hover:bg-indigo-100 transition-all cursor-pointer"
    >
      <span>Admin</span>
    </a>
  </div>
</header>
