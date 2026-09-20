<script lang="ts">
  import type { Product } from '../types'
  import {
    Drumstick,
    Package,
    Sparkles,
    Snowflake,
    GlassWater,
    Scale,
    ShieldCheck
  } from 'lucide-svelte'

  interface Props {
    quickItems: Product[]
    onSelectProduct: (product: Product, quantity?: number, price?: number, label?: string | null) => void
    onRequestWeightModal: (product: Product) => void
    onOpenGCash?: (type: 'GCASH_IN' | 'GCASH_OUT') => void
  }

  let { quickItems, onSelectProduct, onRequestWeightModal }: Props = $props()

  let activeTab = $state<'poultry' | 'hotdogs' | 'ice' | 'drinks' | 'all'>('poultry')
  let multiplier = $state(1)

  // ─── 1. POULTRY & CUTS (By Weight / PLU) ──────────────────────────
  const poultryItems = [
    { id: 91001, plu: 1, name: 'Chicken Feet / Adidas', price: 160, unit: 'kg', icon: '🐾', color: 'bg-red-50 border-red-300 text-red-950', badge: 'PLU 1 • ₱160/kg' },
    { id: 91002, plu: 2, name: 'Chicken Gizzard / Balun-balunan', price: 190, unit: 'kg', icon: '🍗', color: 'bg-rose-50 border-rose-300 text-rose-950', badge: 'PLU 2 • ₱190/kg' },
    { id: 91003, plu: 3, name: 'Chicken Liver / Atay', price: 180, unit: 'kg', icon: '🥩', color: 'bg-red-100 border-red-400 text-red-950', badge: 'PLU 3 • ₱180/kg' },
    { id: 91004, plu: 4, name: 'Chicken Wings / Pakpak', price: 230, unit: 'kg', icon: '🍗', color: 'bg-orange-50 border-orange-300 text-orange-950', badge: 'PLU 4 • ₱230/kg' },
    { id: 91005, plu: 5, name: 'Whole Dressed Chicken', price: 190, unit: 'kg', icon: '🐔', color: 'bg-amber-50 border-amber-300 text-amber-950', badge: 'PLU 5 • ₱190/kg' },
    { id: 91006, plu: 6, name: 'Chicken Breast Fillet', price: 250, unit: 'kg', icon: '🥩', color: 'bg-orange-100 border-orange-400 text-orange-950', badge: 'PLU 6 • ₱250/kg' },
    { id: 91007, plu: 7, name: 'Pork Liempo (Belly Cut)', price: 340, unit: 'kg', icon: '🥓', color: 'bg-rose-50 border-rose-400 text-rose-950', badge: 'PLU 7 • ₱340/kg' },
    { id: 91008, plu: 8, name: 'Pork Chops (Bone-in)', price: 320, unit: 'kg', icon: '🥩', color: 'bg-red-50 border-red-300 text-red-950', badge: 'PLU 8 • ₱320/kg' }
  ]

  // ─── 2. TJ HOTDOGS & PROCESSED PACKS ──────────────────────────────
  const hotdogItems = [
    { id: 91011, name: 'TJ Hotdog Jumbo (1kg Pack)', price: 210, unit: 'pack', icon: '🌭', color: 'bg-red-500 text-white border-red-600', badge: 'TJ 1kg Jumbo' },
    { id: 91012, name: 'TJ Hotdog Regular (500g)', price: 115, unit: 'pack', icon: '🌭', color: 'bg-red-100 border-red-400 text-red-900', badge: 'TJ 500g' },
    { id: 91013, name: 'TJ Cheesedog Jumbo (1kg)', price: 220, unit: 'pack', icon: '🧀', color: 'bg-amber-100 border-amber-400 text-amber-950', badge: 'TJ Cheese 1kg' },
    { id: 91014, name: 'TJ Hotdog Classic (250g)', price: 65, unit: 'pack', icon: '🌭', color: 'bg-red-50 border-red-300 text-red-900', badge: 'TJ 250g' },
    { id: 91015, name: 'Purefoods Sweet Tocino 450g', price: 125, unit: 'pack', icon: '🥓', color: 'bg-pink-50 border-pink-300 text-pink-950', badge: '450g Pack' },
    { id: 91016, name: 'Vigan Garlic Longganisa 12s', price: 110, unit: 'pack', icon: '🧄', color: 'bg-purple-50 border-purple-300 text-purple-950', badge: '12 pcs Pack' },
    { id: 91017, name: 'Pork & Shrimp Siomai 20s', price: 140, unit: 'pack', icon: '🥟', color: 'bg-emerald-50 border-emerald-300 text-emerald-950', badge: '20s Tray' },
    { id: 91018, name: 'Shoestring French Fries 1kg', price: 165, unit: 'pack', icon: '🍟', color: 'bg-yellow-50 border-yellow-300 text-yellow-950', badge: '1kg Bag' }
  ]

  // ─── 3. SANITARY ICE FREEZER (Separate Freezer for Sanitation) ─────
  const iceItems = [
    { id: 91021, name: 'Sanitary Purified Tube Ice (1kg)', price: 20, unit: 'bag', icon: '🧊', color: 'bg-cyan-50 border-cyan-300 text-cyan-950', badge: '₱20 • 1kg Bag' },
    { id: 91022, name: 'Sanitary Tube Ice Block (2kg)', price: 35, unit: 'bag', icon: '🧊', color: 'bg-sky-50 border-sky-300 text-sky-950', badge: '₱35 • 2kg Bag' },
    { id: 91023, name: 'Thermal Foil Insulation Bag', price: 35, unit: 'pc', icon: '🛍️', color: 'bg-slate-100 border-slate-300 text-slate-800', badge: '3-Hr Cold Pouch' }
  ]

  // ─── 4. CHILLED EXOTIC & REFRESHING DRINKS ────────────────────────
  const drinkItems = [
    { id: 91031, name: 'Japanese Ramune Soda (Original)', price: 85, unit: 'bottle', icon: '🍾', color: 'bg-sky-50 border-sky-300 text-sky-950', badge: 'Japan Marble' },
    { id: 91032, name: 'Korean Chilsung Cider 250ml', price: 45, unit: 'can', icon: '🥤', color: 'bg-emerald-50 border-emerald-300 text-emerald-950', badge: 'Korea Cider' },
    { id: 91033, name: 'Calpis Sparkling Soda 350ml', price: 65, unit: 'can', icon: '🥛', color: 'bg-blue-50 border-blue-300 text-blue-950', badge: 'Japan Soda' },
    { id: 91034, name: 'Dr Pepper Cherry 355ml', price: 60, unit: 'can', icon: '🍒', color: 'bg-red-50 border-red-300 text-red-950', badge: 'US Soda' },
    { id: 91035, name: 'A&W Aged Vanilla Cream Soda', price: 60, unit: 'can', icon: '🍦', color: 'bg-amber-50 border-amber-300 text-amber-950', badge: 'US Soda' },
    { id: 91036, name: 'ChaTraMue Thai Milk Tea Can', price: 75, unit: 'can', icon: '🧋', color: 'bg-orange-50 border-orange-300 text-orange-950', badge: 'Thai Street' },
    { id: 91037, name: 'UCC Black Cold Coffee 185g', price: 70, unit: 'can', icon: '☕', color: 'bg-slate-100 border-slate-300 text-slate-900', badge: 'Japan Cold Brew' },
    { id: 91038, name: 'Basil Seed Drink with Mango 290ml', price: 65, unit: 'bottle', icon: '🥭', color: 'bg-yellow-50 border-yellow-300 text-yellow-950', badge: 'Glass Bottle' },
    { id: 91039, name: 'Pocari Sweat Ion Water 500ml', price: 50, unit: 'bottle', icon: '💧', color: 'bg-cyan-50 border-cyan-300 text-cyan-950', badge: 'Chilled 500ml' }
  ]

  function handleGenericAdd(item: { id: number; plu?: number; name: string; price: number; unit: string; badge?: string }) {
    // Exact match in inventory if registered, otherwise fallback to item
    const existing = quickItems.find(p => p.name.trim().toLowerCase() === item.name.trim().toLowerCase())

    const productToAdd: Product = existing || {
      id: item.id,
      name: item.name,
      selling_price: item.price,
      cost_price: Number((item.price * 0.82).toFixed(2)),
      stock_qty: 100,
      low_stock_threshold: 5,
      unit: item.unit,
      is_quick_item: true,
      quick_button_color: '#06b6d4',
      category: item.unit === 'kg' ? 'Poultry & Cuts' : 'Cold Storage',
      plu_code: item.plu
    }

    if (item.unit === 'kg') {
      onRequestWeightModal(productToAdd)
    } else {
      onSelectProduct(productToAdd, multiplier, item.price, item.badge)
      multiplier = 1
    }
  }

  function handleCustomAdd(prod: Product) {
    if (['kg', 'l', 'g'].includes(prod.unit.toLowerCase())) {
      onRequestWeightModal(prod)
    } else {
      onSelectProduct(prod, multiplier)
      multiplier = 1
    }
  }
</script>

<div class="flex flex-col h-full bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
  <!-- Tabs & Multiplier Header -->
  <div class="p-3 bg-slate-50/80 border-b border-slate-200 flex flex-wrap items-center justify-between gap-2">
    <!-- Category Tabs -->
    <div class="flex items-center gap-1 bg-slate-200/70 p-1 rounded-xl text-xs font-semibold overflow-x-auto">
      <button
        type="button"
        onclick={() => activeTab = 'poultry'}
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all cursor-pointer whitespace-nowrap {activeTab === 'poultry' ? 'bg-white text-red-900 shadow-xs font-bold' : 'text-slate-600 hover:text-slate-900'}"
      >
        <Drumstick class="w-3.5 h-3.5 text-red-600" />
        <span>🍗 Poultry & Cuts (kg)</span>
      </button>

      <button
        type="button"
        onclick={() => activeTab = 'hotdogs'}
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all cursor-pointer whitespace-nowrap {activeTab === 'hotdogs' ? 'bg-white text-red-900 shadow-xs font-bold' : 'text-slate-600 hover:text-slate-900'}"
      >
        <Package class="w-3.5 h-3.5 text-amber-600" />
        <span>🌭 TJ Hotdogs & Packs</span>
      </button>

      <button
        type="button"
        onclick={() => activeTab = 'ice'}
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all cursor-pointer whitespace-nowrap {activeTab === 'ice' ? 'bg-cyan-600 text-white shadow-xs font-bold' : 'text-slate-600 hover:text-slate-900'}"
      >
        <Snowflake class="w-3.5 h-3.5 {activeTab === 'ice' ? 'text-white' : 'text-cyan-600'}" />
        <span>🧊 Ice Freezer (Sanitary)</span>
      </button>

      <button
        type="button"
        onclick={() => activeTab = 'drinks'}
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all cursor-pointer whitespace-nowrap {activeTab === 'drinks' ? 'bg-white text-blue-900 shadow-xs font-bold' : 'text-slate-600 hover:text-slate-900'}"
      >
        <GlassWater class="w-3.5 h-3.5 text-blue-600" />
        <span>🥤 Chilled Drinks</span>
      </button>

      <button
        type="button"
        onclick={() => activeTab = 'all'}
        class="flex items-center gap-1 px-2.5 py-1.5 rounded-lg transition-all cursor-pointer whitespace-nowrap {activeTab === 'all' ? 'bg-white text-slate-900 shadow-xs font-bold' : 'text-slate-500 hover:text-slate-900'}"
      >
        <Sparkles class="w-3.5 h-3.5 text-indigo-500" />
        <span>Catalog ({quickItems.length})</span>
      </button>
    </div>

    <!-- Multiplier Bar -->
    <div class="flex items-center gap-1 bg-white border border-slate-200 px-2 py-1 rounded-xl shadow-2xs">
      <span class="text-[11px] font-bold text-slate-500 mr-1">Qty:</span>
      {#each [1, 2, 3, 5, 10] as num}
        <button
          type="button"
          onclick={() => multiplier = num}
          class="px-2 py-0.5 rounded-md text-xs font-bold font-mono transition-all cursor-pointer {multiplier === num ? 'bg-cyan-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-100'}"
        >
          {num}x
        </button>
      {/each}
    </div>
  </div>

  <!-- Sanitary Ice Notice Banner when Ice tab is active -->
  {#if activeTab === 'ice'}
    <div class="px-4 py-2 bg-cyan-50 border-b border-cyan-200 flex items-center justify-between text-xs text-cyan-900">
      <div class="flex items-center gap-2 font-semibold">
        <ShieldCheck class="w-4 h-4 text-cyan-600 shrink-0" />
        <span>Sanitary Food-Grade Ice: Stored in a dedicated clean freezer isolated from raw meats.</span>
      </div>
      <span class="text-[10px] font-bold uppercase tracking-wider bg-cyan-200/60 px-2 py-0.5 rounded-md text-cyan-800">
        Sanitation Compliant
      </span>
    </div>
  {/if}

  <!-- Scale Reminder Banner when Poultry tab is active -->
  {#if activeTab === 'poultry'}
    <div class="px-4 py-2 bg-amber-50/70 border-b border-amber-200 flex items-center justify-between text-xs text-amber-900">
      <div class="flex items-center gap-2 font-medium">
        <Scale class="w-4 h-4 text-amber-600 shrink-0" />
        <span>Dahua Scale Barcode Ready: Scan weight label stickers (03..., 21...) or click any cut to enter kilograms.</span>
      </div>
      <span class="text-[10px] font-bold uppercase tracking-wider bg-amber-200/60 px-2 py-0.5 rounded-md text-amber-800">
        Weighed per kg
      </span>
    </div>
  {/if}

  <!-- Tiles Grid -->
  <div class="p-3 flex-1 overflow-y-auto min-h-0">
    <!-- 1. POULTRY & CUTS -->
    {#if activeTab === 'poultry'}
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        {#each poultryItems as item (item.id)}
          <button
            type="button"
            onclick={() => handleGenericAdd(item)}
            class="flex flex-col items-start justify-between p-3 rounded-xl border text-left transition-all hover:scale-[1.02] active:scale-95 shadow-2xs cursor-pointer min-h-[92px] {item.color}"
          >
            <div class="w-full flex items-center justify-between">
              <span class="text-xl leading-none">{item.icon}</span>
              <span class="text-[10px] font-bold font-mono px-1.5 py-0.5 rounded-md bg-white/80 border border-current shadow-2xs">
                {item.badge}
              </span>
            </div>
            <div class="mt-2 w-full">
              <span class="text-xs font-bold line-clamp-1 block leading-tight">{item.name}</span>
              <div class="flex items-center justify-between mt-1">
                <span class="text-xs font-extrabold font-mono">₱{item.price.toFixed(2)}/kg</span>
                <span class="text-[9px] uppercase font-bold tracking-wider text-slate-500">Tap to Weigh</span>
              </div>
            </div>
          </button>
        {/each}
      </div>

    <!-- 2. TJ HOTDOGS & PACKS -->
    {:else if activeTab === 'hotdogs'}
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        {#each hotdogItems as item (item.id)}
          <button
            type="button"
            onclick={() => handleGenericAdd(item)}
            class="flex flex-col items-start justify-between p-3 rounded-xl border text-left transition-all hover:scale-[1.02] active:scale-95 shadow-2xs cursor-pointer min-h-[92px] {item.color}"
          >
            <div class="w-full flex items-center justify-between">
              <span class="text-xl leading-none">{item.icon}</span>
              <span class="text-[10px] font-bold font-mono px-1.5 py-0.5 rounded-md bg-white/90 text-slate-900 border border-slate-200 shadow-2xs">
                {item.badge}
              </span>
            </div>
            <div class="mt-2 w-full">
              <span class="text-xs font-bold line-clamp-1 block leading-tight">{item.name}</span>
              <span class="text-sm font-extrabold font-mono mt-0.5 block">₱{item.price.toFixed(2)}</span>
            </div>
          </button>
        {/each}
      </div>

    <!-- 3. SANITARY ICE FREEZER -->
    {:else if activeTab === 'ice'}
      <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {#each iceItems as item (item.id)}
          <button
            type="button"
            onclick={() => handleGenericAdd(item)}
            class="flex flex-col items-start justify-between p-4 rounded-2xl border text-left transition-all hover:scale-[1.02] active:scale-95 shadow-2xs cursor-pointer min-h-[110px] {item.color}"
          >
            <div class="w-full flex items-center justify-between">
              <span class="text-3xl leading-none">{item.icon}</span>
              <span class="text-xs font-bold font-mono px-2 py-0.5 rounded-lg bg-white/90 text-cyan-950 border border-cyan-200 shadow-2xs">
                {item.badge}
              </span>
            </div>
            <div class="mt-3 w-full">
              <span class="text-sm font-bold block leading-tight">{item.name}</span>
              <span class="text-base font-black font-mono mt-1 text-cyan-800 block">₱{item.price.toFixed(2)}</span>
            </div>
          </button>
        {/each}
      </div>

    <!-- 4. CHILLED EXOTIC DRINKS -->
    {:else if activeTab === 'drinks'}
      <div class="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
        {#each drinkItems as item (item.id)}
          <button
            type="button"
            onclick={() => handleGenericAdd(item)}
            class="flex flex-col items-start justify-between p-3 rounded-xl border text-left transition-all hover:scale-[1.02] active:scale-95 shadow-2xs cursor-pointer min-h-[92px] {item.color}"
          >
            <div class="w-full flex items-center justify-between">
              <span class="text-xl leading-none">{item.icon}</span>
              <span class="text-[10px] font-bold font-mono px-1.5 py-0.5 rounded-md bg-white/90 text-slate-800 border border-slate-200 shadow-2xs">
                {item.badge}
              </span>
            </div>
            <div class="mt-2 w-full">
              <span class="text-xs font-bold line-clamp-1 block leading-tight">{item.name}</span>
              <span class="text-sm font-extrabold font-mono mt-0.5 text-blue-900 block">₱{item.price.toFixed(2)}</span>
            </div>
          </button>
        {/each}
      </div>

    <!-- 5. ALL QUICK ITEMS (DATABASE CATALOG) -->
    {:else}
      {#if quickItems.length === 0}
        <div class="h-48 flex flex-col items-center justify-center text-slate-400 text-xs">
          <Package class="w-8 h-8 mb-2 opacity-50" />
          <span>No additional quick items registered.</span>
        </div>
      {:else}
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
          {#each quickItems as prod (prod.id)}
            <button
              type="button"
              onclick={() => handleCustomAdd(prod)}
              class="flex flex-col items-start justify-between p-3 rounded-xl border border-slate-200 bg-white hover:border-cyan-400 hover:bg-cyan-50/30 text-left transition-all hover:scale-[1.02] active:scale-95 shadow-2xs cursor-pointer min-h-[92px]"
            >
              <div class="w-full flex items-center justify-between">
                <span class="w-3 h-3 rounded-full" style="background-color: {prod.quick_button_color || '#06b6d4'}"></span>
                <span class="text-[10px] font-mono font-bold text-slate-400">
                  {prod.plu_code ? `PLU ${prod.plu_code}` : prod.unit}
                </span>
              </div>
              <div class="mt-2 w-full">
                <span class="text-xs font-bold text-slate-800 line-clamp-1 block leading-tight">{prod.name}</span>
                <span class="text-xs font-extrabold font-mono text-cyan-700 mt-0.5 block">
                  ₱{prod.selling_price.toFixed(2)}{prod.unit === 'kg' ? '/kg' : ''}
                </span>
              </div>
            </button>
          {/each}
        </div>
      {/if}
    {/if}
  </div>
</div>
