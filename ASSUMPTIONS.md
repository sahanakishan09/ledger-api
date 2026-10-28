# Architectural Assumptions & Design Decisions

This document outlines the distributed systems trade-offs, financial invariants, and operational edge cases considered during the development of the Transaction Ledger API.

---

### 1. Balance Cache vs. Transaction Stream (Ground Truth)
- **The Trade-Off:** Storing an explicit `balance` column on an `accounts` table alongside a `transactions` table creates a potential "dual-source-of-truth" drift if updates fall out of sync.
- **Architectural Choice:** 
  - The immutable, append-only `transactions` log is the **sole canonical source of truth**.
  - The `accounts.balance` column is treated strictly as an **atomic, materialized read-cache** to eliminate $O(N)$ table scans on high-frequency balance reads.
  - **Audit Invariant:** The system maintains the continuous accounting invariant:
    $$\text{account.balance} \equiv \sum \text{Credits} - \sum \text{Debits}$$
    Any failure in writing either record results in a complete database-level rollback.

---

### 2. Concurrency Control & Double-Spending Prevention
- **The Risk:** In standard read-then-write workflows, parallel HTTP requests can read the same starting balance simultaneously, allowing an account with $100 to execute two concurrent $70 debits (double-spend vulnerability).
- **Architectural Choice:**
  - The engine uses **pessimistic row-level locking** (`SELECT ... FOR UPDATE`) on the account record inside the database transaction before checking balances or applying deductions.
  - Concurrent requests for the same account are serialized at the database engine level, guaranteeing consistent evaluations.

---

### 3. Deadlock Prevention in Bilateral Transfers
- **The Risk:** When money is transferred between Account A and Account B concurrently with a reverse transfer from Account B to Account A, acquiring row locks in execution order (`A -> B` and `B -> A`) causes circular wait deadlocks.
- **Architectural Choice:**
  - Before acquiring locks, account UUIDs are sorted deterministically:
    $$\text{Lock Order} = [\min(A, B), \max(A, B)]$$
  - Both transactions request locks in the identical order, eliminating circular wait conditions at the database level.

---

### 4. Monetary Precision & Storage
- **The Risk:** Binary floating-point representation (IEEE-754) introduces cumulative rounding anomalies (e.g., `0.1 + 0.2 = 0.30000000000000004`).
- **Architectural Choice:**
  - All currency values are validated to two decimal places and persisted using PostgreSQL's arbitrary-precision `NUMERIC(14, 2)`.
  - Python processes these values using the standard library `decimal.Decimal` module rather than standard floats.

---

### 5. Idempotency & Reference ID Scoping
- **Requirement Analysis:** Requirement 2 specifies that `reference_id` must be unique per account, but may be reused across different accounts.
- **Architectural Choice:**
  - Enforced via a composite database index: `UNIQUE(account_id, reference_id)`.
  - For bilateral transfers (Bonus requirement), atomic records are created on each ledger using derived unique reference keys (`${reference_id}_DEBIT` and `${reference_id}_CREDIT`), preventing partial re-runs while maintaining end-to-end reconciliation trails.

---

### 6. Immutability & Auditing Standards
- **Compliance Model:** Under financial compliance standards (e.g., SOX, GAAP), ledger entries cannot be overwritten or deleted.
- **Architectural Choice:**
  - The API exposes **no `PUT`, `PATCH`, or `DELETE` endpoints** for transactions.
  - Once written, transactions can only be corrected by posting offsetting adjustment entries (a compensating credit or debit).

---

### 7. HTTP Status Code Conventions
- `200 OK`: Successful retrieval or transfer operation.
- `201 Created`: Successful resource creation (Account, Transaction).
- `400 Bad Request`: Malformed request payloads or invalid parameter types.
- `404 Not Found`: Account ID does not exist in the database.
- `409 Conflict`: Duplicate transaction attempt with an existing `reference_id` on the target account.
- `422 Unprocessable Entity`: Business invariant violations (e.g., overdraft/insufficient balance, attempt to transfer between identical accounts, or negative amounts).