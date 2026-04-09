# Payment Service API Documentation

## 📋 Table of Contents

1. [Product Management APIs](#product-management-apis)
2. [Transaction APIs](#transaction-apis)
3. [Payment Method APIs](#payment-method-apis)
4. [Voucher APIs](#voucher-apis)
5. [Webhook APIs](#webhook-apis)
6. [Reporting & Analytics APIs](#reporting--analytics-apis)
7. [Admin/Configuration APIs](#adminconfiguration-apis)



## 📦 Product Management APIs

### 4. `POST /api/products`
**Kegunaan:** Create produk baru  
**Untuk:** Aplikasi register produk yang bisa dijual  
**Input:** product_code, name, price, category_id, stock  
**Output:** product_id, product_details  
**Use Case:** E-commerce tambah produk baru

### 5. `GET /api/products`
**Kegunaan:** List semua produk  
**Untuk:** Tampilkan katalog produk  
**Query Params:** page, limit, category_id, search, is_active  
**Output:** List products dengan pagination  
**Use Case:** Display produk di checkout page

### 6. `GET /api/products/{id}`
**Kegunaan:** Detail produk spesifik  
**Untuk:** Lihat info lengkap satu produk  
**Output:** Product details (name, price, stock, metadata)  
**Use Case:** User klik detail produk

### 7. `PUT /api/products/{id}`
**Kegunaan:** Update produk  
**Untuk:** Edit harga, stok, atau info produk  
**Input:** Fields to update (price, stock, is_active, etc)  
**Output:** Updated product details  
**Use Case:** Admin ubah harga produk

### 8. `DELETE /api/products/{id}`
**Kegunaan:** Soft delete produk  
**Untuk:** Non-aktifkan produk (set is_active = false)  
**Output:** Success message  
**Use Case:** Produk discontinued

### 9. `GET /api/product-categories`
**Kegunaan:** List kategori produk  
**Untuk:** Filter produk by category  
**Output:** List categories  
**Use Case:** Filter produk di UI

---

## 💳 Transaction APIs

### 10. `POST /api/transactions`
**Kegunaan:** Create transaksi baru (checkout)  
**Untuk:** User checkout produk  
**Input:** user_id, products[], voucher_code (optional)  
**Output:** transaction_id, available_payment_methods, total_amount  
**Use Case:** User klik "Checkout" di cart

### 11. `GET /api/transactions/{id}`
**Kegunaan:** Detail transaksi  
**Untuk:** Lihat info lengkap transaksi  
**Output:** Transaction details, items, payment info, status  
**Use Case:** User lihat invoice/receipt

### 12. `GET /api/transactions`
**Kegunaan:** List transaksi  
**Untuk:** History transaksi user atau aplikasi  
**Query Params:** user_id, status, date_from, date_to, page, limit  
**Output:** List transactions dengan pagination  
**Use Case:** User lihat "Order History"

### 13. `POST /api/transactions/{id}/pay`
**Kegunaan:** Pilih metode pembayaran & generate payment instruction  
**Untuk:** User pilih cara bayar (VA/e-wallet/QRIS)  
**Input:** payment_method_id  
**Output:** payment_details (VA number, QR code, payment_url, expired_at)  
**Use Case:** User pilih "BCA Virtual Account"

### 14. `GET /api/transactions/{id}/status`
**Kegunaan:** Cek status pembayaran  
**Untuk:** Real-time check apakah sudah dibayar  
**Output:** Current status, paid_at (if paid)  
**Use Case:** Polling untuk update status payment

### 15. `POST /api/transactions/{id}/cancel`
**Kegunaan:** Cancel transaksi  
**Untuk:** User batalkan transaksi sebelum bayar  
**Input:** reason (optional)  
**Output:** Updated transaction status  
**Use Case:** User klik "Cancel Order"

### 16. `POST /api/transactions/{id}/refund`
**Kegunaan:** Request refund transaksi  
**Untuk:** Kembalikan uang ke customer  
**Input:** refund_amount, reason, notes  
**Output:** refund_id, refund_details  
**Use Case:** Customer return barang rusak

### 17. `GET /api/transactions/{id}/invoice`
**Kegunaan:** Download invoice PDF  
**Untuk:** Generate invoice untuk customer  
**Output:** PDF file atau invoice_url  
**Use Case:** User download invoice untuk bukti bayar

---

## 💰 Payment Method APIs

### 18. `GET /api/payment-methods`
**Kegunaan:** List metode pembayaran available  
**Untuk:** Tampilkan opsi pembayaran ke user  
**Query Params:** type (va/e_wallet/qris/credit_card)  
**Output:** List payment methods dengan admin fee  
**Use Case:** Display "Pilih Metode Pembayaran"

### 19. `GET /api/payment-methods/{id}`
**Kegunaan:** Detail metode pembayaran  
**Untuk:** Info lengkap satu payment method  
**Output:** Method details, admin_fee, processing_time, instructions  
**Use Case:** User klik info icon di payment method

### 20. `POST /api/payment-methods/{id}/calculate-fee`
**Kegunaan:** Hitung admin fee untuk amount tertentu  
**Untuk:** Preview total sebelum pilih metode  
**Input:** amount  
**Output:** admin_fee, total_with_fee  
**Use Case:** Show "Total jika pakai GoPay: Rp 612.000"

---

## 🎟️ Voucher APIs

### 21. `POST /api/vouchers/validate`
**Kegunaan:** Validasi kode voucher  
**Untuk:** Check voucher valid & bisa dipakai  
**Input:** voucher_code, user_id, transaction_amount  
**Output:** is_valid, discount_amount, voucher_details, error_message  
**Use Case:** User input kode voucher di checkout

### 22. `GET /api/vouchers/my-vouchers`
**Kegunaan:** List voucher yang user miliki  
**Untuk:** Tampilkan "Voucher Saya" page  
**Query Params:** user_id, is_claimed, is_expired  
**Output:** List eligible vouchers untuk user ini  
**Use Case:** User buka tab "Voucher Saya"

### 23. `POST /api/vouchers/{id}/claim`
**Kegunaan:** Claim voucher yang tersedia  
**Untuk:** User aktifkan voucher yang dapat  
**Input:** user_id  
**Output:** Claimed voucher details  
**Use Case:** User klik "Claim Voucher" dari notifikasi

### 24. `GET /api/vouchers/public`
**Kegunaan:** List public vouchers yang available  
**Untuk:** Discovery vouchers yang bisa dipakai siapa saja  
**Output:** List public vouchers  
**Use Case:** Display "Promo Hari Ini"

### 25. `POST /api/vouchers` *(Admin)*
**Kegunaan:** Create voucher baru  
**Untuk:** Admin/marketing buat campaign voucher  
**Input:** voucher_code, discount_type, value, conditions[], validity  
**Output:** voucher_id, voucher_details  
**Use Case:** Marketing buat "RAMADAN50"

### 26. `PUT /api/vouchers/{id}` *(Admin)*
**Kegunaan:** Update voucher  
**Untuk:** Edit voucher config (extend validity, change quota)  
**Input:** Fields to update  
**Output:** Updated voucher  
**Use Case:** Extend expiry date voucher

### 27. `POST /api/vouchers/{id}/conditions` *(Admin)*
**Kegunaan:** Add kondisi ke voucher  
**Untuk:** Set syarat dapat/pakai voucher  
**Input:** condition_type, operator, condition_value  
**Output:** Condition added  
**Use Case:** Set "min 10 transaksi"

### 28. `GET /api/vouchers/{id}/eligible-users` *(Admin)*
**Kegunaan:** List users yang eligible untuk voucher  
**Untuk:** Analytics & monitoring voucher distribution  
**Output:** List users + eligibility status  
**Use Case:** Marketing lihat berapa user dapat voucher

---

## 🔔 Webhook APIs

### 29. `POST /webhook/payment/{gateway_code}`
**Kegunaan:** Receive callback dari payment gateway  
**Untuk:** Gateway notify payment service saat ada update  
**Input:** Gateway-specific payload + signature  
**Output:** 200 OK (acknowledgment)  
**Use Case:** Midtrans kirim notif payment success

### 30. `POST /webhook/test` *(Admin)*
**Kegunaan:** Test webhook ke client app  
**Untuk:** Verify webhook configuration  
**Input:** application_id, event_type, test_payload  
**Output:** Webhook response  
**Use Case:** Test apakah callback_url client working

### 31. `GET /api/webhooks/logs`
**Kegunaan:** List webhook delivery logs  
**Untuk:** Monitor webhook success/failure rate  
**Query Params:** application_id, is_success, date_from, date_to  
**Output:** List webhook logs  
**Use Case:** Debug kenapa webhook ke client app failed

### 32. `POST /api/webhooks/{id}/retry`
**Kegunaan:** Manual retry failed webhook  
**Untuk:** Retry kirim webhook yang gagal  
**Output:** Retry result  
**Use Case:** Webhook failed karena client app down, retry setelah up

---

## 📊 Reporting & Analytics APIs

### 33. `GET /api/reports/transactions`
**Kegunaan:** Transaction report  
**Untuk:** Financial report & reconciliation  
**Query Params:** date_from, date_to, status, payment_method, format (json/csv/pdf)  
**Output:** Transaction summary & details  
**Use Case:** Finance team download daily transaction report

### 34. `GET /api/reports/revenue`
**Kegunaan:** Revenue report  
**Untuk:** Analytics pendapatan  
**Query Params:** date_from, date_to, group_by (day/week/month)  
**Output:** Revenue breakdown  
**Use Case:** Dashboard "Revenue This Month"

### 35. `GET /api/reports/vouchers`
**Kegunaan:** Voucher usage report  
**Untuk:** Campaign effectiveness analysis  
**Query Params:** voucher_id, date_from, date_to  
**Output:** Usage stats (claim rate, conversion rate, discount given)  
**Use Case:** Marketing evaluate voucher ROI

### 36. `GET /api/reports/payment-methods`
**Kegunaan:** Payment method distribution  
**Untuk:** Analytics metode pembayaran populer  
**Query Params:** date_from, date_to  
**Output:** Payment method usage breakdown  
**Use Case:** "80% user pakai VA, 15% e-wallet"

### 37. `GET /api/analytics/dashboard`
**Kegunaan:** Dashboard summary  
**Untuk:** Real-time business metrics  
**Output:** Total transactions, revenue, success rate, pending payments  
**Use Case:** Admin dashboard homepage

### 38. `GET /api/analytics/user-behavior`
**Kegunaan:** User behavior analytics  
**Untuk:** Understand user journey  
**Query Params:** user_id, date_from, date_to  
**Output:** Transaction patterns, average order value, favorite payment method  
**Use Case:** Personalization & targeting

---

## ⚙️ Admin/Configuration APIs

### 39. `GET /api/admin/applications`
**Kegunaan:** List registered applications  
**Untuk:** Manage client apps  
**Output:** List applications  
**Use Case:** Admin lihat semua apps yang terdaftar

### 40. `PUT /api/admin/applications/{id}`
**Kegunaan:** Update application config  
**Untuk:** Update callback_url, status, etc  
**Input:** Fields to update  
**Output:** Updated application  
**Use Case:** Client app ganti callback_url

### 41. `POST /api/admin/applications/{id}/regenerate-keys`
**Kegunaan:** Generate ulang app_key & app_secret  
**Untuk:** Security - rotate credentials  
**Output:** New app_key, app_secret  
**Use Case:** Credentials compromised, need new keys

### 42. `GET /api/admin/gateways`
**Kegunaan:** List payment gateways  
**Untuk:** Manage gateway integrations  
**Output:** List gateways (Midtrans, Xendit, etc)  
**Use Case:** Admin monitoring gateway status

### 43. `POST /api/admin/gateways/{id}/credentials`
**Kegunaan:** Set gateway credentials untuk aplikasi  
**Untuk:** Configure gateway per app  
**Input:** application_id, api_key, api_secret, webhook_secret  
**Output:** Credentials saved  
**Use Case:** Setup Midtrans untuk app baru

### 44. `PUT /api/admin/gateways/{id}/toggle`
**Kegunaan:** Enable/disable gateway  
**Untuk:** Maintenance atau switch gateway  
**Input:** is_active  
**Output:** Updated status  
**Use Case:** Midtrans maintenance, switch to Xendit

### 45. `GET /api/admin/gateway-requests`
**Kegunaan:** List semua request ke gateway  
**Untuk:** Debugging & monitoring gateway communication  
**Query Params:** gateway_id, request_type, is_success, date_from, date_to  
**Output:** List gateway requests + responses  
**Use Case:** Debug kenapa payment creation failed

### 46. `POST /api/admin/transactions/{id}/force-status`
**Kegunaan:** Manual update transaction status  
**Untuk:** Emergency - fix status yang salah  
**Input:** new_status, reason  
**Output:** Updated transaction  
**Use Case:** Gateway callback missed, manual set to paid

### 47. `GET /api/admin/callbacks`
**Kegunaan:** List gateway callbacks  
**Untuk:** Monitor & debug callbacks dari gateway  
**Query Params:** gateway_id, is_processed, is_signature_valid  
**Output:** List callbacks  
**Use Case:** Debug signature validation issues

### 48. `POST /api/admin/vouchers/{id}/assign-users`
**Kegunaan:** Bulk assign voucher ke users  
**Untuk:** Targeted campaign  
**Input:** user_ids[], expires_at  
**Output:** Assignment result  
**Use Case:** Marketing kasih voucher ke 1000 VIP users

### 49. `GET /api/admin/health`
**Kegunaan:** System health check  
**Untuk:** Monitoring system status  
**Output:** Database status, gateway connectivity, queue status  
**Use Case:** DevOps monitoring

### 50. `GET /api/admin/reconciliation`
**Kegunaan:** Reconciliation report  
**Untuk:** Match internal records vs gateway settlements  
**Query Params:** date, gateway_id  
**Output:** Matched/unmatched transactions  
**Use Case:** Finance reconcile daily settlements

---

## 🔍 Additional Utility APIs

### 51. `GET /api/banks`
**Kegunaan:** List supported banks  
**Untuk:** Display bank options untuk Virtual Account  
**Output:** List banks dengan logo & codes  
**Use Case:** User pilih bank untuk VA

### 52. `POST /api/notifications/send`
**Kegunaan:** Send notification ke user  
**Untuk:** Custom notification (payment reminder, promo)  
**Input:** user_id, type, title, message  
**Output:** Notification sent  
**Use Case:** Reminder "Transaksi akan expire 1 jam lagi"

### 53. `GET /api/fees/calculate`
**Kegunaan:** Calculate total fees  
**Untuk:** Preview total dengan berbagai payment methods  
**Input:** amount, payment_method_ids[]  
**Output:** Breakdown fees per method  
**Use Case:** Compare "Bayar pakai apa yang paling murah?"

### 54. `POST /api/transactions/{id}/resend-instructions`
**Kegunaan:** Resend payment instructions  
**Untuk:** User lupa/kehilangan VA number  
**Output:** Payment instructions via email/SMS  
**Use Case:** User klik "Kirim ulang instruksi pembayaran"

### 55. `GET /api/transactions/{id}/timeline`
**Kegunaan:** Transaction activity timeline  
**Untuk:** Audit trail user-friendly  
**Output:** Chronological events (created, paid, refunded, etc)  
**Use Case:** Customer service trace transaction history

---

## 📝 Summary by User Type

### **For End Users (via Client App):**
- Create transaction, pay, check status, cancel
- Use vouchers, see payment instructions
- View transaction history

### **For Client App Developers:**
- Authentication, product CRUD
- Transaction management
- Webhook handling
- Voucher integration

### **For Admins/Finance:**
- Reports & analytics
- Reconciliation
- Gateway monitoring
- Manual interventions

### **For Marketing:**
- Voucher creation & management
- Campaign analytics
- User targeting

### **For DevOps:**
- Health checks
- Webhook logs
- Gateway status
- System monitoring

---

## 🔐 Authentication & Authorization

**Header Required for All APIs (except webhooks):**
```
Authorization: Bearer {access_token}
X-App-Key: {app_key}
```

**Rate Limiting:**
- Public APIs: 1000 requests/hour per app
- Admin APIs: 10000 requests/hour
- Webhook: Unlimited (from whitelisted IPs)

**Error Response Format:**
```json
{
  "success": false,
  "error_code": "INVALID_VOUCHER",
  "message": "Voucher code not found or expired",
  "details": {...}
}
```