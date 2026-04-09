# Payment Service

## Development
### Migrate
```bash
alembic upgrade head
```

### Make Migration
```bash
alembic revision --autogenerate -m "update database"
```

### Run Server
```bash
uvicorn app.main:app --reload --port=9080
```

## Database Tables

This section explains each database table and its purpose in the payment service system.

### product_categories
Used to categorize products. Stores category names, descriptions, and timestamps for creation and updates. Products can be linked to categories for better organization.

### products
Stores information about individual products available for purchase. Includes product code, name, price, stock, currency, and metadata. Linked to product categories and applications.

### payment_methods
Defines available payment methods such as virtual accounts, e-wallets, credit cards, etc. Includes provider information, admin fees, and activation status.

### payment_gateways
Configures payment gateway providers like Midtrans, Xendit, etc. Stores gateway details, base URLs, sandbox mode settings, and supported methods.

### payment_gateway_credentials
Stores credentials for payment gateways per application. Includes merchant IDs, API keys, secrets, and client keys required for gateway integration.

### transactions
Records payment transactions. Includes transaction details like amounts, status, payment methods, gateways, vouchers, and timestamps. Tracks the entire payment lifecycle.

### transaction_items
Details the items within a transaction. Links transactions to products, storing quantities, unit prices, and subtotals for each item purchased.

### vouchers
Manages discount vouchers. Includes voucher codes, types (public/private), discount values, usage limits, validity periods, and applicable products.

### voucher_conditions
Defines conditions for voucher usage, such as minimum amounts, specific products, or user segments. Ensures vouchers are applied only when criteria are met.

### voucher_eligible_users
Manages which users are eligible for specific vouchers. Controls access to private or targeted voucher campaigns.