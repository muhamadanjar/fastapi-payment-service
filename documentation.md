# Payment Service Step-by-Step Guide

Dokumen ini adalah panduan utama implementasi dan operasional project.
Semua alur inti (setup DB, konfigurasi gateway, urutan API, callback webhook, admin operations) disatukan di sini.

---

## 1) Tujuan Sistem

Sistem ini menangani:

- katalog produk
- transaksi checkout
- pemilihan metode bayar
- integrasi multi-gateway (Midtrans/Xendit)
- validasi voucher
- callback webhook gateway
- reporting, analytics, dan admin configuration

---

## 2) Persiapan Environment

1. Siapkan environment variables database.
2. Jalankan migrasi.
3. Jalankan service.

```bash
alembic upgrade head
uvicorn app.main:app --reload --port=9080
```

Base URL default lokal:

- API internal: `http://localhost:9080/api`
- Webhook callback publik: `http://localhost:9080/webhook`

---

## 3) Urutan Setup Data (Wajib)

Ikuti urutan ini agar runtime payment tidak gagal.

### Step 3.1 - Buat Applications

Isi tabel `applications` terlebih dahulu (setiap client app punya `app_key`, `app_secret`, `callback_url`).

### Step 3.2 - Master Payment Gateways

Isi tabel `payment_gateways`:

- `gateway_code`: `midtrans`, `xendit`, dst
- `priority`: semakin kecil semakin diprioritaskan
- `is_active`: aktif/nonaktif gateway
- `supported_methods`: metode yang didukung

### Step 3.3 - Credentials per App per Gateway

Isi tabel `payment_gateway_credentials`:

- relasi `application_id` + `gateway_id`
- `api_key`/`api_secret`/`client_key`
- `webhook_secret`
- `is_active`

Catatan:

- Satu app bisa punya lebih dari satu gateway (primary + fallback).
- Credential app A dan app B tidak boleh dicampur.

### Step 3.4 - Master Payment Methods

Isi tabel `payment_methods`:

- `method_code`, `method_name`, `method_type`
- `admin_fee` dan `admin_fee_type`
- `is_active`

### Step 3.5 - Mapping Method ke Gateway

Isi tabel `payment_method_gateways`:

- `payment_method_id`
- `gateway_id`
- `gateway_method_code` (kode bisa beda per gateway)
- `processing_time_minutes`
- `is_active`

Ini kunci untuk fallback multi-gateway.

### Step 3.6 - Seed Produk dan Voucher

Isi:

- `product_categories`, `products`
- `vouchers`, `voucher_conditions`, `voucher_eligible_users` (opsional)

---

## 4) Alur Runtime Inti (End-to-End)

### Flow A - Catalog & Product

1. Create product: `POST /api/products`
2. List products: `GET /api/products`
3. Detail product: `GET /api/products/{id}`
4. Update product: `PUT /api/products/{id}`
5. Soft delete product: `DELETE /api/products/{id}`
6. List categories: `GET /api/products/categories`

### Flow B - Checkout dan Pembayaran

1. Buat transaksi: `POST /api/transactions`
2. Ambil metode bayar tersedia: `GET /api/payment-methods`
3. Hitung fee: `POST /api/payment-methods/{id}/calculate-fee`
4. Pilih metode bayar: `POST /api/transactions/{id}/pay`
5. Cek status: `GET /api/transactions/{id}/status`
6. Jika perlu kirim ulang instruksi: `POST /api/transactions/{id}/resend-instructions`
7. Ambil invoice: `GET /api/transactions/{id}/invoice`
8. Lihat timeline audit: `GET /api/transactions/{id}/timeline`

### Flow C - Voucher

1. Validasi voucher: `POST /api/vouchers/validate`
2. Claim voucher: `POST /api/vouchers/{id}/claim`
3. List voucher user: `GET /api/vouchers/my-vouchers`
4. List voucher public: `GET /api/vouchers/public`

---

## 5) Webhook Gateway (Kritis)

### Endpoint Callback

- `POST /webhook/payment/{gateway_code}`
- `POST /webhook/test`

### Endpoint Management Webhook

- `GET /api/webhooks/logs`
- `POST /api/webhooks/{id}/retry`

### Validasi Signature

#### Midtrans

Validasi:

`SHA512(order_id + status_code + gross_amount + server_key)`

Kecocokan dibandingkan dengan header/payload signature.

#### Xendit

Validasi:

- header `x-callback-token` harus sama dengan `webhook_secret`.

### Behavior Callback

Saat callback valid diterima:

1. cari gateway dari `gateway_code`
2. cari transaksi (`invoice_number` / `transaction_code` / `payment_reference`)
3. simpan payload ke `payment_gateway_callbacks`
4. mapping status gateway ke status transaksi internal
5. update `transactions`
6. tulis `transaction_logs`

Jika signature invalid:

- callback tetap dicatat
- transaksi tidak diubah
- response unauthorized

---

## 6) Daftar Endpoint API

### 6.1 Products

- `POST /api/products`
- `GET /api/products`
- `GET /api/products/{id}`
- `PUT /api/products/{id}`
- `DELETE /api/products/{id}`
- `GET /api/products/categories`

### 6.2 Transactions

- `POST /api/transactions`
- `GET /api/transactions`
- `GET /api/transactions/{id}`
- `POST /api/transactions/{id}/pay`
- `GET /api/transactions/{id}/status`
- `POST /api/transactions/{id}/cancel`
- `POST /api/transactions/{id}/refund`
- `GET /api/transactions/{id}/invoice`
- `POST /api/transactions/{id}/resend-instructions`
- `GET /api/transactions/{id}/timeline`

### 6.3 Payment Methods

- `GET /api/payment-methods`
- `GET /api/payment-methods/{id}`
- `POST /api/payment-methods/{id}/calculate-fee`

### 6.4 Vouchers

- `POST /api/vouchers/validate`
- `GET /api/vouchers/my-vouchers`
- `POST /api/vouchers/{id}/claim`
- `GET /api/vouchers/public`
- `POST /api/vouchers`
- `PUT /api/vouchers/{id}`
- `POST /api/vouchers/{id}/conditions`
- `GET /api/vouchers/{id}/eligible-users`

### 6.5 Webhooks

- `POST /webhook/payment/{gateway_code}`
- `POST /webhook/test`
- `GET /api/webhooks/logs`
- `POST /api/webhooks/{id}/retry`

### 6.6 Reports & Analytics

- `GET /api/reports/transactions`
- `GET /api/reports/revenue`
- `GET /api/reports/vouchers`
- `GET /api/reports/payment-methods`
- `GET /api/analytics/dashboard`
- `GET /api/analytics/user-behavior`

### 6.7 Admin / Configuration

- `GET /api/admin/applications`
- `PUT /api/admin/applications/{id}`
- `POST /api/admin/applications/{id}/regenerate-keys`
- `GET /api/admin/gateways`
- `POST /api/admin/gateways/{id}/credentials`
- `PUT /api/admin/gateways/{id}/toggle`
- `GET /api/admin/gateway-requests`
- `POST /api/admin/transactions/{id}/force-status`
- `GET /api/admin/callbacks`
- `POST /api/admin/vouchers/{id}/assign-users`
- `GET /api/admin/health`
- `GET /api/admin/reconciliation`

### 6.8 Utilities

- `GET /api/banks`
- `POST /api/notifications/send`
- `GET /api/fees/calculate`

---

## 7) Operasional Gateway (Checklist)

Sebelum go-live:

1. pastikan `payment_gateways.is_active = true` untuk gateway target
2. pastikan credential app aktif (`payment_gateway_credentials.is_active = true`)
3. pastikan mapping method ke gateway aktif (`payment_method_gateways.is_active = true`)
4. pastikan webhook URL sudah terdaftar di dashboard gateway:
   - `.../webhook/payment/midtrans`
   - `.../webhook/payment/xendit`
5. test callback via `POST /webhook/test`
6. monitor callback di `GET /api/webhooks/logs`

Fallback rule:

- pilih gateway berdasarkan `priority` paling kecil yang aktif dan punya credential aktif untuk app tersebut.

---

## 8) Error Handling Contract

Gunakan format error konsisten:

```json
{
  "success": false,
  "error_code": "SOME_ERROR_CODE",
  "message": "Human readable message",
  "details": {}
}
```

Contoh error umum:

- signature invalid pada webhook
- gateway/credential tidak ditemukan
- transaksi tidak ditemukan
- payload tidak lengkap

---

## 9) Hal yang Harus Dihindari

- Jangan proses callback tanpa validasi signature/token.
- Jangan hard-delete produk (gunakan soft delete via `is_active=false`).
- Jangan menyimpan credential gateway di source code.
- Jangan pakai satu credential untuk banyak aplikasi.

---

## 10) Ringkasan Implementasi Bertahap (Recommended)

1. Setup DB + migrasi
2. Seed applications
3. Seed gateways + credentials + method mappings
4. Aktifkan product + voucher flows
5. Aktifkan checkout + pay flow
6. Uji callback webhook end-to-end
7. Aktifkan admin monitoring + reports
8. Hardening (idempotency callback, rate limit, observability)

