import type { Product, CartItem, CustomerDebt, TransactionResult, DebtTransaction } from '../types'
import { supabase, ensureCashierSession } from './supabase'
import { parseScaleBarcode } from './scanner'

const BASE_URL = (import.meta.env.VITE_BACKEND_URL as string) || ''
let isBackendOnline: boolean | null = null

/**
 * Checks if the local FastAPI backend is reachable.
 * If not, falls back to direct Supabase Cloud queries.
 */
async function checkBackendAvailability(): Promise<boolean> {
  if (isBackendOnline !== null) return isBackendOnline
  if (typeof window !== 'undefined' && (window.location.protocol === 'capacitor:' || window.location.protocol === 'file:')) {
    isBackendOnline = false
    return false
  }

  try {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 1200)
    const res = await fetch(`${BASE_URL}/api/products/quick-items`, { signal: controller.signal })
    clearTimeout(timeout)
    isBackendOnline = res.ok
  } catch {
    isBackendOnline = false
  }
  return isBackendOnline
}

export async function fetchQuickItems(): Promise<Product[]> {
  const hasLocal = await checkBackendAvailability()
  if (hasLocal) {
    try {
      const res = await fetch(`${BASE_URL}/api/products/quick-items`)
      if (res.ok) return await res.json()
    } catch {
      isBackendOnline = false
    }
  }

  // Cloud Mode: Direct Supabase query
  await ensureCashierSession()
  let { data, error } = await supabase
    .from('products')
    .select('*')
    .eq('is_quick_item', true)
    .order('name')

  if (error || !data || data.length === 0) {
    // If no explicit quick items set, return first 16 products as quick staples
    const fallback = await supabase
      .from('products')
      .select('*')
      .order('name')
      .limit(16)
    data = fallback.data || []
  }

  return (data || []).map(formatProduct)
}

export async function searchProducts(query: string): Promise<Product[]> {
  if (!query.trim()) return []

  const hasLocal = await checkBackendAvailability()
  if (hasLocal) {
    try {
      const res = await fetch(`${BASE_URL}/api/products/search?q=${encodeURIComponent(query.trim())}`)
      if (res.ok) return await res.json()
    } catch {
      isBackendOnline = false
    }
  }

  // Cloud Mode: Direct Supabase query
  await ensureCashierSession()
  const q = query.trim()
  const { data, error } = await supabase
    .from('products')
    .select('*')
    .or(`name.ilike.%${q}%,category.ilike.%${q}%,barcode.eq.${q},pack_barcode.eq.${q}`)
    .limit(20)

  if (error) {
    console.error('[Supabase] Search error:', error)
    return []
  }
  return (data || []).map(formatProduct)
}

export async function lookupBarcode(barcode: string): Promise<Product> {
  const cleanCode = barcode.trim()
  const hasLocal = await checkBackendAvailability()
  if (hasLocal) {
    try {
      const res = await fetch(`${BASE_URL}/api/products/barcode/${encodeURIComponent(cleanCode)}`)
      if (res.ok) return await res.json()
    } catch {
      isBackendOnline = false
    }
  }

  // Cloud Mode: Direct Supabase query
  await ensureCashierSession()
  const { data, error } = await supabase
    .from('products')
    .select('*')
    .or(`barcode.eq.${cleanCode},pack_barcode.eq.${cleanCode},jar_code.eq.${cleanCode}`)
    .limit(1)

  if (error || !data || data.length === 0) {
    throw new Error(`Product not found for barcode: ${cleanCode}`)
  }

  const prod = formatProduct(data[0])

  // Check if mother-pack barcode or jar refill
  if (prod.pack_barcode === cleanCode && prod.pcs_per_pack && prod.pcs_per_pack > 1) {
    prod.scan_type = 'mother_pack'
    prod.default_qty = prod.pcs_per_pack
    prod.default_price = prod.full_pack_price || (prod.selling_price * prod.pcs_per_pack)
    prod.pack_label = `Pack of ${prod.pcs_per_pack}`
  } else if (prod.jar_code === cleanCode && prod.refill_price) {
    prod.scan_type = 'jar_refill'
    prod.default_qty = prod.refill_qty || 1
    prod.default_price = prod.refill_price
    prod.pack_label = `Refill (${prod.default_qty}${prod.unit})`
  }

  return prod
}

export async function smartScan(code: string): Promise<any> {
  const clean = code.trim()

  // 1. Check if scale weight-embedded barcode (e.g. Dahua, Rongta, Toledo, CAS)
  const scaleInfo = parseScaleBarcode(clean)
  if (scaleInfo.isScaleBarcode && scaleInfo.plu && scaleInfo.weightKg !== undefined) {
    await ensureCashierSession()
    const pluNum = parseInt(scaleInfo.plu.replace(/^0+/, '') || '0', 10)

    const { data: products } = await supabase
      .from('products')
      .select('*')
      .or(`plu_code.eq.${pluNum},id.eq.${pluNum},barcode.eq.${scaleInfo.plu}`)
      .limit(1)

    if (products && products.length > 0) {
      const prod = formatProduct(products[0])
      const weight = scaleInfo.weightKg
      const subtotal = Number((weight * prod.selling_price).toFixed(2))

      return {
        scan_type: 'scale_weight',
        product: prod,
        quantity_to_add: weight,
        effective_unit_price: prod.selling_price,
        effective_subtotal: subtotal,
        pack_label: `Scale Weighed (${weight.toFixed(3)}${prod.unit})`,
        message: `Scale Barcode: ${prod.name} (${weight.toFixed(3)}${prod.unit} — ₱${subtotal.toFixed(2)})`
      }
    }
  }

  // 2. Standard Barcode / QR Lookup
  const product = await lookupBarcode(clean)
  return {
    scan_type: product.scan_type || 'unit',
    product,
    quantity_to_add: product.default_qty || 1,
    effective_unit_price: product.default_price || product.selling_price,
    effective_subtotal: product.default_subtotal || (product.default_price || product.selling_price),
    pack_label: product.pack_label || null,
    message: `Scanned: ${product.name}`
  }
}

export async function submitCheckout(payload: {
  items: CartItem[]
  total_amount: number
  payment_method: 'CASH' | 'GCASH' | 'UTANG'
  amount_tendered: number
  print_receipt: boolean
  customer_name?: string
  phone_number?: string
  notes?: string
  amount_paid_now?: number
}): Promise<TransactionResult> {
  const hasLocal = await checkBackendAvailability()
  if (hasLocal) {
    try {
      const res = await fetch(`${BASE_URL}/api/checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (res.ok) return await res.json()
    } catch {
      isBackendOnline = false
    }
  }

  // Cloud Mode: Direct Supabase atomic RPC execution
  await ensureCashierSession()
  const { data, error } = await supabase.rpc('process_checkout', { payload })

  if (error) {
    console.error('[Supabase] Checkout error:', error)
    throw new Error(error.message || 'Checkout failed in cloud database')
  }

  return data as TransactionResult
}

export async function fetchDebtCustomers(search?: string): Promise<CustomerDebt[]> {
  const hasLocal = await checkBackendAvailability()
  if (hasLocal) {
    try {
      const url = search && search.trim()
        ? `${BASE_URL}/api/debts?search=${encodeURIComponent(search.trim())}`
        : `${BASE_URL}/api/debts`
      const res = await fetch(url)
      if (res.ok) return await res.json()
    } catch {
      isBackendOnline = false
    }
  }

  // Cloud Mode: Direct Supabase query
  await ensureCashierSession()
  let query = supabase.from('customer_debts').select('*').order('customer_name')
  if (search && search.trim()) {
    query = query.ilike('customer_name', `%${search.trim()}%`)
  }

  const { data, error } = await query
  if (error) {
    console.error('[Supabase] Debt customers fetch error:', error)
    return []
  }
  return data || []
}

export async function payDebt(debtId: number, paymentAmount: number, notes?: string): Promise<{
  message: string
  customer: CustomerDebt
  payment_amount: number
}> {
  const hasLocal = await checkBackendAvailability()
  if (hasLocal) {
    try {
      const res = await fetch(`${BASE_URL}/api/debts/${debtId}/pay`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ payment_amount: paymentAmount, notes })
      })
      if (res.ok) return await res.json()
    } catch {
      isBackendOnline = false
    }
  }

  // Cloud Mode: Direct Supabase RPC
  await ensureCashierSession()
  const { data, error } = await supabase.rpc('pay_customer_debt', {
    p_debt_id: debtId,
    p_payment_amount: paymentAmount,
    p_notes: notes || null
  })

  if (error) {
    throw new Error(error.message || 'Failed to process debt repayment')
  }
  return data
}

export async function fetchDebtHistory(debtId: number): Promise<{
  customer: CustomerDebt
  history: DebtTransaction[]
}> {
  const hasLocal = await checkBackendAvailability()
  if (hasLocal) {
    try {
      const res = await fetch(`${BASE_URL}/api/debts/${debtId}/history`)
      if (res.ok) return await res.json()
    } catch {
      isBackendOnline = false
    }
  }

  // Cloud Mode: Direct Supabase query
  await ensureCashierSession()
  const { data: customer, error: custErr } = await supabase
    .from('customer_debts')
    .select('*')
    .eq('id', debtId)
    .single()

  if (custErr || !customer) {
    throw new Error('Customer debt record not found')
  }

  const { data: history, error: histErr } = await supabase
    .from('debt_transactions')
    .select('*')
    .eq('debt_id', debtId)
    .order('created_at', { ascending: false })

  if (histErr) {
    throw new Error('Failed to fetch debt history')
  }

  return { customer, history: history || [] }
}

export async function registerDebtCustomer(payload: {
  customer_name: string
  amount_charged?: number
  phone_number?: string
  notes?: string
}): Promise<CustomerDebt> {
  const hasLocal = await checkBackendAvailability()
  if (hasLocal) {
    try {
      const res = await fetch(`${BASE_URL}/api/debts/charge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_name: payload.customer_name,
          amount_charged: payload.amount_charged ?? 0,
          phone_number: payload.phone_number,
          notes: payload.notes
        })
      })
      if (res.ok) return await res.json()
    } catch {
      isBackendOnline = false
    }
  }

  // Cloud Mode: Direct Supabase insert
  await ensureCashierSession()
  const { data, error } = await supabase
    .from('customer_debts')
    .insert({
      customer_name: payload.customer_name.trim(),
      total_debt: payload.amount_charged ?? 0,
      phone_number: payload.phone_number?.trim() || null,
      notes: payload.notes?.trim() || null
    })
    .select()
    .single()

  if (error) {
    throw new Error(error.message || 'Failed to register customer debt account')
  }
  return data
}

export async function submitGCashTransaction(payload: {
  transaction_type: string
  flow_type: string
  input_amount: number
  principal_amount: number
  fee: number
  total_collected: number
  reference_number?: string
  mobile_number?: string
  receipt_image?: string
  gcash_timestamp?: string
}): Promise<any> {
  const hasLocal = await checkBackendAvailability()
  if (hasLocal) {
    try {
      const res = await fetch(`${BASE_URL}/api/gcash/transact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (res.ok) return await res.json()
    } catch {
      isBackendOnline = false
    }
  }

  // Cloud Mode: Direct Supabase RPC
  await ensureCashierSession()
  const { data, error } = await supabase.rpc('record_gcash_transaction', { payload })
  if (error) {
    throw new Error(error.message || 'Failed to record GCash transaction in cloud')
  }
  return data
}

export async function printReceipt(receiptText: string): Promise<{ success: boolean; message: string }> {
  const hasLocal = await checkBackendAvailability()
  if (hasLocal) {
    try {
      const res = await fetch(`${BASE_URL}/api/printer/print-receipt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ receipt_text: receiptText })
      })
      if (res.ok) return await res.json()
    } catch {
      // Ignore and fallback
    }
  }

  // In standalone tablet mode: can trigger native browser print or return success
  if (typeof window !== 'undefined' && window.print) {
    // Return receipt text confirmation
    return { success: true, message: 'Receipt rendered for display / printing.' }
  }
  return { success: true, message: 'Receipt ready.' }
}

export async function fetchDailyReport(): Promise<any> {
  const hasLocal = await checkBackendAvailability()
  if (hasLocal) {
    try {
      const res = await fetch(`${BASE_URL}/api/reports/daily`)
      if (res.ok) return await res.json()
    } catch {
      isBackendOnline = false
    }
  }

  // Cloud Mode: Aggregate today's transactions from Supabase
  await ensureCashierSession()
  const todayStart = new Date()
  todayStart.setHours(0, 0, 0, 0)

  const { data: txns, error } = await supabase
    .from('transactions')
    .select('*')
    .gte('created_at', todayStart.toISOString())

  if (error) {
    console.error('[Supabase] Daily report error:', error)
    return null
  }

  let totalSales = 0
  let cashSales = 0
  let gcashSales = 0
  let utangSales = 0
  let totalProfit = 0

  for (const t of txns || []) {
    const amt = Number(t.total_amount) || 0
    const cost = Number(t.total_cost) || 0
    totalSales += amt
    totalProfit += (amt - cost)

    if (t.payment_method === 'CASH') cashSales += amt
    else if (t.payment_method === 'GCASH') gcashSales += amt
    else if (t.payment_method === 'UTANG') utangSales += amt
  }

  return {
    today_sales: totalSales,
    total_transactions: (txns || []).length,
    cash_sales: cashSales,
    gcash_sales: gcashSales,
    utang_sales: utangSales,
    total_profit: totalProfit,
    date: new Date().toLocaleDateString('en-PH', { dateStyle: 'medium' })
  }
}

/**
 * Normalizes Supabase products to matching frontend types.
 */
function formatProduct(raw: any): Product {
  return {
    id: Number(raw.id),
    name: raw.name || '',
    barcode: raw.barcode || null,
    pack_barcode: raw.pack_barcode || null,
    jar_code: raw.jar_code || null,
    cost_price: Number(raw.cost_price) || 0,
    selling_price: Number(raw.selling_price) || 0,
    stock_qty: Number(raw.stock_qty) || 0,
    low_stock_threshold: Number(raw.low_stock_threshold) || 5,
    unit: raw.unit || 'pc',
    is_quick_item: Boolean(raw.is_quick_item),
    quick_button_color: raw.quick_button_color || '#3b82f6',
    category: raw.category || 'General',
    pcs_per_pack: raw.pcs_per_pack ? Number(raw.pcs_per_pack) : 1,
    bulk_cost_price: raw.bulk_cost_price ? Number(raw.bulk_cost_price) : null,
    full_pack_price: raw.full_pack_price ? Number(raw.full_pack_price) : null,
    half_dozen_price: raw.half_dozen_price ? Number(raw.half_dozen_price) : null,
    dozen_price: raw.dozen_price ? Number(raw.dozen_price) : null,
    plu_code: raw.plu_code ? Number(raw.plu_code) : null,
    freezer_section: raw.freezer_section || 'Frozen Main',
    refill_price: raw.refill_price ? Number(raw.refill_price) : null,
    refill_qty: raw.refill_qty ? Number(raw.refill_qty) : 1.0,
    is_low_stock: (Number(raw.stock_qty) || 0) <= (Number(raw.low_stock_threshold) || 5)
  }
}
