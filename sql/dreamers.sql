-- 1. Total number of customers
SELECT COUNT(*) AS total_customers
FROM dreamers.customers;


-- 2. Total number of products
SELECT COUNT(*) AS total_products
FROM dreamers.products;


-- 3. Total number of invoices
SELECT COUNT(*) AS total_invoices
FROM dreamers.invoices;


-- 4. Total quantity of products sold
SELECT SUM("Quantity") AS total_quantity_sold
FROM dreamers.invoice_items;


-- 5. Number of customers in each country
SELECT "Country", COUNT(*) AS total_customers
FROM dreamers.customers
GROUP BY "Country"
ORDER BY total_customers DESC;


-- 6. Average product price
SELECT ROUND(AVG("UnitPrice"), 2) AS average_product_price
FROM dreamers.products;


-- 7. Ten most expensive products
SELECT "StockCode", "Description", "UnitPrice"
FROM dreamers.products
ORDER BY "UnitPrice" DESC
LIMIT 10;


-- 8. Ten customers with the most invoices
SELECT "CustomerID", COUNT(*) AS total_invoices
FROM dreamers.invoices
GROUP BY "CustomerID"
ORDER BY total_invoices DESC
LIMIT 10;


-- 9. Ten products with the highest quantity sold
SELECT p."StockCode", p."Description", SUM(i."Quantity") AS total_quantity
FROM dreamers.invoice_items AS i
JOIN dreamers.products AS p
    ON i."StockCode" = p."StockCode"
GROUP BY p."StockCode", p."Description"
ORDER BY total_quantity DESC
LIMIT 10;


-- 10. Ten invoices with the highest sales value
SELECT i."InvoiceNo",
       ROUND(SUM(i."Quantity" * p."UnitPrice"), 2) AS total_sales
FROM dreamers.invoice_items AS i
JOIN dreamers.products AS p
    ON i."StockCode" = p."StockCode"
GROUP BY i."InvoiceNo"
ORDER BY total_sales DESC
LIMIT 10;
