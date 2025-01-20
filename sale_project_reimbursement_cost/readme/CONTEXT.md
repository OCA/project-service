In businesses, especially those in services or consulting, where expenses may be incurred on behalf of a client but later need to be reimbursed by the client, Odoo’s functionality for `Re-Invoice Expenses` products (without using the hr_expenses module) lacks visibility of this information in the project dashboard.

With this module, two sections are added to the project dashboard:

- **Provisions**: Values invoiced to the client in advance to cover any necessary expenses. This section displays the analytic entries generated from customer invoices for specific products.
- **Reimbursements cost:** Values generated from vendor bills that need to be charged to the client. Using Odoo’s functionality, these are the sales order lines automatically created from a vendor bill when the product is configured as `Re-Invoice Expenses`.