```
-- ================================================================
-- GATEWAY CONFIGURATION: XENDIT & MIDTRANS
-- Step-by-step setup untuk menggunakan multiple payment gateways
-- ================================================================

-- ================================================================
-- STEP 1: Register Payment Gateway (Master Data)
-- Table: payment_gateways
-- ================================================================
-- Ini adalah MASTER DATA gateway yang tersedia di system
-- Setup sekali saja, berlaku untuk semua aplikasi

INSERT INTO payment_gateways (
    id, 
    gateway_code, 
    gateway_name, 
    gateway_type, 
    base_url, 
    is_active, 
    is_sandbox, 
    priority, 
    supported_methods
) VALUES 
-- MIDTRANS Configuration
(
    'gw-001',
    'midtrans',
    'Midtrans',
    'aggregator',
    'https://api.midtrans.com',  -- Production
    TRUE,
    FALSE,  -- Production mode
    1,  -- Priority 1 (highest)
    '["virtual_account", "e_wallet", "credit_card", "qris", "retail"]'
),
-- MIDTRANS Sandbox (for testing)
(
    'gw-001-sandbox',
    'midtrans_sandbox',
    'Midtrans Sandbox',
    'aggregator',
    'https://api.sandbox.midtrans.com',  -- Sandbox
    TRUE,
    TRUE,  -- Sandbox mode
    99,  -- Low priority (for testing only)
    '["virtual_account", "e_wallet", "credit_card", "qris", "retail"]'
),
-- XENDIT Configuration
(
    'gw-002',
    'xendit',
    'Xendit',
    'aggregator',
    'https://api.xendit.co',  -- Production
    TRUE,
    FALSE,  -- Production mode
    2,  -- Priority 2 (fallback if Midtrans down)
    '["virtual_account", "e_wallet", "credit_card", "qris", "retail"]'
),
-- XENDIT Sandbox (for testing)
(
    'gw-002-sandbox',
    'xendit_sandbox',
    'Xendit Sandbox',
    'aggregator',
    'https://api.xendit.co',  -- Same URL but different API key
    TRUE,
    TRUE,  -- Sandbox mode
    98,  -- Low priority (for testing only)
    '["virtual_account", "e_wallet", "qris"]'
);


-- ================================================================
-- STEP 2: Set Credentials per Application
-- Table: payment_gateway_credentials
-- ================================================================
-- Setiap APLIKASI punya credentials BERBEDA untuk setiap gateway
-- Satu app bisa pakai multiple gateways

-- Example: E-Commerce App menggunakan MIDTRANS
INSERT INTO payment_gateway_credentials (
    id,
    application_id,
    gateway_id,
    merchant_id,
    api_key,
    api_secret,
    client_key,
    webhook_secret,
    additional_config,
    is_active
) VALUES (
    'cred-001',
    'app-001',  -- E-Commerce App
    'gw-001',   -- Midtrans Production
    'G123456789',  -- Merchant ID dari Midtrans Dashboard
    'SB-Mid-server-abc123xyz',  -- Server Key
    NULL,  -- Midtrans tidak pakai api_secret
    'SB-Mid-client-abc123xyz',  -- Client Key (for frontend)
    'midtrans_webhook_secret_xyz',  -- Untuk validasi webhook
    JSON_OBJECT(
        'enable_3ds', TRUE,
        'enable_savecard', FALSE,
        'custom_field1', 'ecommerce_store',
        'notification_url', 'https://payment-service.com/webhook/payment/midtrans',
        'finish_url', 'https://ecommerce.com/payment/finish',
        'error_url', 'https://ecommerce.com/payment/error'
    ),
    TRUE
);

-- Example: E-Commerce App juga pakai XENDIT (as fallback)
INSERT INTO payment_gateway_credentials (
    id,
    application_id,
    gateway_id,
    merchant_id,
    api_key,
    api_secret,
    client_key,
    webhook_secret,
    additional_config,
    is_active
) VALUES (
    'cred-002',
    'app-001',  -- Same E-Commerce App
    'gw-002',   -- Xendit Production
    NULL,  -- Xendit tidak pakai merchant_id
    'xnd_production_abc123xyz',  -- API Key (Secret Key)
    NULL,  -- Xendit API key adalah secret key
    'xnd_public_abc123xyz',  -- Public Key (for frontend)
    'xendit_webhook_token_xyz',  -- Verification Token
    JSON_OBJECT(
        'callback_virtual_account_id', 'https://payment-service.com/webhook/payment/xendit',
        'callback_ewallet_id', 'https://payment-service.com/webhook/payment/xendit',
        'success_redirect_url', 'https://ecommerce.com/payment/success',
        'failure_redirect_url', 'https://ecommerce.com/payment/failure'
    ),
    TRUE
);

-- Example: Food Delivery App menggunakan MIDTRANS SANDBOX (for testing)
INSERT INTO payment_gateway_credentials (
    id,
    application_id,
    gateway_id,
    merchant_id,
    api_key,
    api_secret,
    client_key,
    webhook_secret,
    additional_config,
    is_active
) VALUES (
    'cred-003',
    'app-002',  -- Food Delivery App
    'gw-001-sandbox',  -- Midtrans Sandbox
    'G987654321',
    'SB-Mid-server-sandbox123',
    NULL,
    'SB-Mid-client-sandbox123',
    'midtrans_webhook_secret_sandbox',
    JSON_OBJECT(
        'enable_3ds', FALSE,
        'notification_url', 'https://payment-service.com/webhook/payment/midtrans'
    ),
    TRUE
);


-- ================================================================
-- STEP 3: Map Payment Methods to Gateways
-- Table: payment_method_gateways
-- ================================================================
-- Definisikan payment method mana yang didukung gateway mana
-- Satu payment method bisa didukung multiple gateways

-- BCA Virtual Account - supported by MIDTRANS
INSERT INTO payment_method_gateways (
    id,
    payment_method_id,
    gateway_id,
    gateway_method_code,
    is_active,
    processing_time_minutes
) VALUES (
    'pmg-001',
    'pm-001',  -- BCA VA
    'gw-001',  -- Midtrans
    'bca_va',  -- Kode method di Midtrans
    TRUE,
    1440  -- 24 hours
);

-- BCA Virtual Account - also supported by XENDIT (fallback)
INSERT INTO payment_method_gateways (
    id,
    payment_method_id,
    gateway_id,
    gateway_method_code,
    is_active,
    processing_time_minutes
) VALUES (
    'pmg-002',
    'pm-001',  -- BCA VA
    'gw-002',  -- Xendit
    'BCA',  -- Kode method di Xendit (beda format!)
    TRUE,
    1440  -- 24 hours
);

-- Mandiri Virtual Account - MIDTRANS
INSERT INTO payment_method_gateways (
    id,
    payment_method_id,
    gateway_id,
    gateway_method_code,
    is_active,
    processing_time_minutes
) VALUES (
    'pmg-003',
    'pm-002',  -- Mandiri VA
    'gw-001',  -- Midtrans
    'echannel',  -- Kode method di Midtrans untuk Mandiri
    TRUE,
    1440
);

-- Mandiri Virtual Account - XENDIT
INSERT INTO payment_method_gateways (
    id,
    payment_method_id,
    gateway_id,
    gateway_method_code,
    is_active,
    processing_time_minutes
) VALUES (
    'pmg-004',
    'pm-002',  -- Mandiri VA
    'gw-002',  -- Xendit
    'MANDIRI',  -- Kode method di Xendit
    TRUE,
    1440
);

-- GoPay - MIDTRANS (Midtrans punya GoPay)
INSERT INTO payment_method_gateways (
    id,
    payment_method_id,
    gateway_id,
    gateway_method_code,
    is_active,
    processing_time_minutes
) VALUES (
    'pmg-005',
    'pm-003',  -- GoPay
    'gw-001',  -- Midtrans
    'gopay',
    TRUE,
    15  -- 15 minutes
);

-- OVO - XENDIT (Xendit punya OVO, Midtrans tidak)
INSERT INTO payment_method_gateways (
    id,
    payment_method_id,
    gateway_id,
    gateway_method_code,
    is_active,
    processing_time_minutes
) VALUES (
    'pmg-006',
    'pm-004',  -- OVO
    'gw-002',  -- Xendit only
    'ID_OVO',
    TRUE,
    15  -- 15 minutes
);

-- QRIS - MIDTRANS
INSERT INTO payment_method_gateways (
    id,
    payment_method_id,
    gateway_id,
    gateway_method_code,
    is_active,
    processing_time_minutes
) VALUES (
    'pmg-007',
    'pm-005',  -- QRIS
    'gw-001',  -- Midtrans
    'qris',
    TRUE,
    15
);

-- QRIS - XENDIT
INSERT INTO payment_method_gateways (
    id,
    payment_method_id,
    gateway_id,
    gateway_method_code,
    is_active,
    processing_time_minutes
) VALUES (
    'pmg-008',
    'pm-005',  -- QRIS
    'gw-002',  -- Xendit
    'ID_QRIS',
    TRUE,
    15
);

-- Credit Card - MIDTRANS
INSERT INTO payment_method_gateways (
    id,
    payment_method_id,
    gateway_id,
    gateway_method_code,
    is_active,
    processing_time_minutes
) VALUES (
    'pmg-009',
    'pm-006',  -- Credit Card
    'gw-001',  -- Midtrans
    'credit_card',
    TRUE,
    5
);

-- Credit Card - XENDIT
INSERT INTO payment_method_gateways (
    id,
    payment_method_id,
    gateway_id,
    gateway_method_code,
    is_active,
    processing_time_minutes
) VALUES (
    'pmg-010',
    'pm-006',  -- Credit Card
    'gw-002',  -- Xendit
    'CREDIT_CARD',
    TRUE,
    5
);


-- ================================================================
-- CONFIGURATION SUMMARY
-- ================================================================

/*
┌─────────────────────────────────────────────────────────────┐
│ TABLE USAGE SUMMARY                                         │
└─────────────────────────────────────────────────────────────┘

1. payment_gateways
   Purpose: Master data gateway yang tersedia
   Insert: Sekali saja per gateway
   Contains: URL, priority, supported methods
   Example: Midtrans, Xendit, Doku, iPaymu
   
2. payment_gateway_credentials  
   Purpose: Credentials per aplikasi per gateway
   Insert: Per app per gateway
   Contains: API keys, secrets, webhook tokens
   Example: 
   - App "E-commerce" → Midtrans credentials
   - App "E-commerce" → Xendit credentials (fallback)
   - App "Food Delivery" → Midtrans credentials (different keys!)
   
3. payment_method_gateways
   Purpose: Mapping method ↔ gateway
   Insert: Per payment method per gateway
   Contains: Gateway-specific method codes
   Example:
   - BCA VA → Midtrans (code: "bca_va")
   - BCA VA → Xendit (code: "BCA")
   - GoPay → Midtrans only
   - OVO → Xendit only
*/

-- ================================================================
-- QUERY EXAMPLES: How to Get Configuration
-- ================================================================

-- Example 1: Get all gateways available for an app
SELECT 
    pg.*,
    pgc.api_key,
    pgc.is_active as credential_active
FROM payment_gateways pg
INNER JOIN payment_gateway_credentials pgc 
    ON pg.id = pgc.gateway_id
WHERE pgc.application_id = 'app-001'
    AND pg.is_active = TRUE
    AND pgc.is_active = TRUE
ORDER BY pg.priority ASC;

-- Example 2: Get gateway for specific payment method
-- (When user selects BCA VA)
SELECT 
    pm.method_name,
    pg.gateway_name,
    pg.base_url,
    pmg.gateway_method_code,
    pgc.api_key,
    pgc.client_key,
    pgc.webhook_secret
FROM payment_methods pm
INNER JOIN payment_method_gateways pmg 
    ON pm.id = pmg.payment_method_id
INNER JOIN payment_gateways pg 
    ON pmg.gateway_id = pg.id
INNER JOIN payment_gateway_credentials pgc 
    ON pg.id = pgc.gateway_id
WHERE pm.id = 'pm-001'  -- BCA VA
    AND pgc.application_id = 'app-001'  -- E-commerce App
    AND pm.is_active = TRUE
    AND pmg.is_active = TRUE
    AND pg.is_active = TRUE
    AND pgc.is_active = TRUE
ORDER BY pg.priority ASC
LIMIT 1;  -- Get highest priority gateway

-- Example 3: Get all payment methods available via specific gateway
SELECT 
    pm.*,
    pmg.gateway_method_code,
    pg.gateway_name
FROM payment_methods pm
INNER JOIN payment_method_gateways pmg 
    ON pm.id = pmg.payment_method_id
INNER JOIN payment_gateways pg 
    ON pmg.gateway_id = pg.id
WHERE pg.gateway_code = 'midtrans'
    AND pm.is_active = TRUE
    AND pmg.is_active = TRUE;

-- Example 4: Check if app has multiple gateways (for fallback)
SELECT 
    a.app_name,
    pg.gateway_name,
    pg.priority,
    pgc.is_active,
    pg.is_sandbox
FROM applications a
INNER JOIN payment_gateway_credentials pgc 
    ON a.id = pgc.application_id
INNER JOIN payment_gateways pg 
    ON pgc.gateway_id = pg.id
WHERE a.id = 'app-001'
ORDER BY pg.priority ASC;


-- ================================================================
-- REAL WORLD CONFIG EXAMPLE
-- ================================================================

-- Scenario: E-commerce setup dengan Midtrans & Xendit

-- 1. Master Gateway (Already exists in system)
-- ✓ Midtrans Production (priority 1)
-- ✓ Xendit Production (priority 2)

-- 2. E-commerce Credentials
-- ✓ Midtrans: Merchant G123456789, Server Key: SB-Mid-server-xxx
-- ✓ Xendit: API Key: xnd_production_xxx

-- 3. Payment Methods Support
-- BCA VA: Midtrans (primary), Xendit (fallback)
-- Mandiri VA: Midtrans (primary), Xendit (fallback)
-- GoPay: Midtrans only
-- OVO: Xendit only
-- QRIS: Both
-- Credit Card: Both

-- 4. Runtime Logic (in application code)
-- Step 1: User pilih BCA VA
-- Step 2: Query gateway berdasarkan priority
-- Step 3: Try Midtrans first (priority 1)
-- Step 4: If Midtrans fails/down → Fallback to Xendit (priority 2)
-- Step 5: Create payment dengan gateway terpilih

-- ================================================================
-- SWITCHING GATEWAY (ON THE FLY)
-- ================================================================

-- Scenario 1: Midtrans maintenance, switch semua ke Xendit
UPDATE payment_gateways 
SET is_active = FALSE 
WHERE gateway_code = 'midtrans';

-- Sekarang semua request otomatis pakai Xendit (priority 2)

-- Scenario 2: Disable gateway untuk app tertentu saja
UPDATE payment_gateway_credentials
SET is_active = FALSE
WHERE application_id = 'app-001' 
    AND gateway_id = 'gw-001';

-- App-001 tidak bisa pakai Midtrans, otomatis pakai Xendit

-- Scenario 3: Change gateway priority
UPDATE payment_gateways 
SET priority = 1 
WHERE gateway_code = 'xendit';

UPDATE payment_gateways 
SET priority = 2 
WHERE gateway_code = 'midtrans';

-- Xendit jadi primary, Midtrans jadi fallback


-- ================================================================
-- ADDITIONAL CONFIG: Webhook Validation
-- ================================================================

-- Ketika gateway kirim callback, validate dengan webhook_secret

-- Example untuk Midtrans:
-- Signature = SHA512(order_id + status_code + gross_amount + server_key)

-- Example untuk Xendit:
-- Validation: x-callback-token header === webhook_secret

-- Simpan di additional_config untuk dokumentasi:
UPDATE payment_gateway_credentials
SET additional_config = JSON_SET(
    additional_config,
    '$.signature_method', 'SHA512',
    '$.signature_fields', '["order_id", "status_code", "gross_amount", "server_key"]',
    '$.webhook_validation', 'signature_comparison'
)
WHERE gateway_id = 'gw-001';  -- Midtrans

UPDATE payment_gateway_credentials
SET additional_config = JSON_SET(
    additional_config,
    '$.signature_method', 'token_comparison',
    '$.webhook_header', 'x-callback-token',
    '$.webhook_validation', 'token_match'
)
WHERE gateway_id = 'gw-002';  -- Xendit

```