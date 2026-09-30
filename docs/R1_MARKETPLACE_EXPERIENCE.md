# R1 & R1.1 — Pre-Login Marketplace Experience & Acquisition Hierarchy

**Product:** Yara Care (Family App)  
**Scope:** Phase 3.5 — MVP Release Preparation (R1 Extension & R1.1 UX Polish)  
**Status:** Approved Architecture & Implementation  

---

## 1. Overview & Purpose

R1 has been extended and refined (R1.1) to provide an unauthenticated **Marketplace Discovery Experience** within the Family App.
A user can install the Family App before purchasing hardware or an active subscription and explore:
1. What the Yara care ecosystem is (Discovery).
2. The available hardware packages (Marketplace):
   - **Yara Hub** (Standalone tabletop appliance)
   - **Yara Care** (Yara Hub + Smart Pill Box)
   - **Yara Care Plus** (Yara Hub + Smart Pill Box + Health Wearable)
3. Factual capabilities and included devices for each package (Product Detail).
4. **Hierarchical Acquisition Model (R1.1):**
   - **Level 1 — روش دریافت دستگاه (Primary Choice):**
     - **خرید دستگاه (Buy):** Outright hardware ownership + Yara Care service subscription.
     - **اجاره دستگاه (Rent):** Time-limited hardware usage without purchase.
   - **Level 2 — Conditional Controls:**
     - When **خرید دستگاه** is selected:
       - **🎁 ۳ ماه اشتراک رایگان:** Prominent promotional callout highlighting 3 months of complimentary software, calling, and care services with device purchase.
       - **نوع اشتراک خدمات پس از دوره رایگان:** Choice between `اشتراک ماهانه` and `اشتراک سالانه` (with 2-month discount).
     - When **اجاره دستگاه** is selected:
       - **مدت زمان اجاره دستگاه:** Chips for `۱ ماه`, `۳ ماه`, `۶ ماه`, and `۱۲ ماه`.
5. **Clear Price Breakdown (Strictly Below Controls):**
   - Eliminates card overlap defects with clean vertical flex flow.
   - For Buy: Device price + Subscription tier price + Free gift banner + Initial payment.
   - For Rent: Rental duration + Total rental amount.
   - Displayed in natural Persian numerals (`toPersianDigits`) and Tomans.
6. **Consistent Navigation & Header:**
   - Unified `BrandLockup` and `بازگشت` (Back) button across Marketplace and Product Detail screens in RTL.


---

## 2. Architectural Boundaries & Future Work

### Presentation-Only Experience
This implementation provides the pre-login UI/UX exploration layer. It is **not** an e-commerce backend.
- **No Backend Domain Models:** No Django models, tables, migrations, or marketplace endpoints were created.
- **No Pricing / Checkout API:** Pricing is calculated via a typed local catalog provider (`LocalPricingProvider`).
- **No Fake Domain State:** Browsing and configuring does not write to cart, orders, or database state.
- **Authentication Boundary:** Browsing and price calculation require zero authentication. The final action ("ادامه و ثبت سفارش") routes the user to Login/Signup, ready for when a future transactional checkout pipeline is introduced.

### Replaceable Visual Asset System
Professional product photography and final hardware renders are intentionally deferred to a later visual/branding phase.
- An asset renderer abstraction (`ProductAsset`) provides controlled, theme-aligned vector illustrations for each product and accessory.
- When official hardware photography is produced, it can be dropped into `apps/family/src/marketplace/assets.tsx` without modifying product cards, detail views, or pricing logic.

### Future Work
The following items remain planned for future post-MVP roadmap phases:
1. Authoritative Backend Marketplace Catalog & Pricing API.
2. Checkout, Cart, and Payment Gateway integration for physical goods.
3. Formal Rental Agreements & Contract management.
4. Order lifecycle & shipment tracking.
