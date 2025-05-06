# Kola technologies internship assesment


## Overview
The **Purchase Request Customization** module for Odoo enhances the purchasing process by introducing features like multi-vendor support, bid management, automatic purchase order generation from the winning bid, and custom user access rules. This module is my assessment solution for the kola technologies internship.

### Key Features:
1. **Multi-Vendor RFQ Handling**: Enables RFQs to be sent to multiple vendors for quotes and manages them independently.
2. **Bid Selection**: Allows vendors to place bids, automatically selecting the lowest bid as the winner.
3. **Purchase Order Generation**: Automatically creates purchase orders from the winning bid.
4. **Role-based Access Control**: Configures user access to purchase requests based on roles (e.g., User, Manager, Procurement).
5. **Parent-Child RFQ Relationship**: Supports hierarchical RFQ relationships, where a parent RFQ can generate multiple child RFQs for different vendors.

---

## Installation

To install the **Purchase Request Customization** module:

1. **Install via Odoo Apps**:
   - Navigate to the Odoo Apps menu.
   - Search for **RFQ_enhanced**.
   - Click **Install**.

2. **Configure Security Groups**:
   - The module requires security groups such as "RFQ Customization / User", "RFQ Customization / Manager", and "RFQ Customization / Procurement" to be assigned to the respective users.
   - You can assign groups through **Settings > Users & Companies > Users**.


---

## Models

### 1. **Purchase Order (`purchase.order`)**
The core model for managing RFQs. Custom fields and methods enhance the purchase order lifecycle.
- **vendor_ids**: A Many2many field linking vendors to the RFQ.
- **bid_ids**: A One2many field storing all bids related to the RFQ.
- **winning_bid_id**: A Many2one field that links the winning bid to the RFQ.
- **is_multi_vendor_rfq**: A Boolean field to indicate if the RFQ is for multiple vendors.
- **purchase_request_id**: A Many2one field linking the RFQ to the corresponding purchase request.
- **parent_rfq_id**: A Many2one field linking the RFQ to a parent RFQ, if applicable.

### 2. **Purchase Bid (`purchase.bid`)**
A model for managing vendor bids related to the RFQ.
- **sequence**: A unique identifier for each bid.
- **purchase_order_id**: A Many2one field linking the bid to a purchase order (RFQ).
- **vendor_id**: A Many2one field linking the bid to a vendor.
- **bid_amount**: The amount of the bid.
- **bid_date**: The date when the bid was placed.
- **state**: A selection field that tracks the status of the bid (`draft`, `submitted`, `selected`, `rejected`).

---

## Key Methods

### 1. **Purchase Order Methods**
- **_onchange_vendor_ids**: Automatically sets the `is_multi_vendor_rfq` field based on the number of vendors selected.
- **action_send_to_multiple_vendors**: Creates separate RFQs for each selected vendor. This method copies the original RFQ and assigns it to the respective vendor.
- **select_winning_bid**: Selects the lowest valid bid as the winning bid and creates a purchase order based on the winning bid.

### 2. **Purchase Bid Methods**
- **create**: Automatically generates a unique bid reference number (`sequence`) when a new bid is created.
- **_check_bid_amount**: Ensures that the bid amount is greater than zero. If not, raises a validation error.
- **action_submit**: Changes the bid status to 'submitted'.
- **action_select**: Marks the bid as 'selected' and assigns it as the winning bid on the RFQ.
- **action_reject**: Marks the bid as 'rejected'.

---

## Access Control & Security Rules

### Security Groups:
- **RFQ Customization / User**: Basic access to purchase requests, can only view their own requests.
- **RFQ Customization / Manager**: Can access purchase requests within their department.
- **RFQ Customization / Procurement**: Can access all purchase requests.

### Access Control Rules:
- **User Rule**: Users can only see their own purchase requests (`domain_force=[('create_uid', '=', user.id)]`).
- **Manager Rule**: Managers can view requests from their department (`domain_force=[('department_id', '=', user.department_id.id)]`).
- **Procurement Rule**: Procurement users have access to all purchase requests (`domain_force=[(1, '=', 1)]`).

---
