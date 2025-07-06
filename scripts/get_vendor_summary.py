# importing libraries
import sqlite3
import pandas as pd
# logging setup
import logging
from ingestion_db import ingest_db

logging.basicConfig(
    filename="logs/get_vendor_summary.log",
    level=logging.DEBUG,
    format="%(asctime)s -%(levelname)s -%(message)s",
    filemode="a"
)
# This function merges multiple tables to generate vendor-level summary.
def create_vendor_summary(conn):
    vendor_sales_summary = pd.read_sql_query(
        """
        WITH Freightsummary AS (
            SELECT 
                VendorNumber, 
                SUM(Freight) AS FreightCost 
            FROM vendor_invoice 
            GROUP BY VendorNumber
        ),
        purchasesummary AS (
            SELECT 
                p.VendorNumber, 
                p.VendorName,
                p.Description,
                p.Brand, 
                p.PurchasePrice, 
                pp.Volume, 
                pp.Price AS ActualPrice, 
                SUM(p.Quantity) AS TotalPurchaseQuantity,
                SUM(p.Dollars) AS TotalPurchaseDollars 
            FROM purchases p 
            JOIN purchase_prices pp ON p.Brand = pp.Brand 
            WHERE p.PurchasePrice > 0
            GROUP BY p.VendorNumber, p.VendorName, p.Brand, p.PurchasePrice, pp.Volume, pp.Price
        ),
        salessummary AS (
            SELECT 
                VendorNo, 
                Brand, 
                SUM(SalesDollars) AS TotalSalesDollars, 
                SUM(SalesPrice) AS TotalSalesPrice, 
                SUM(SalesQuantity) AS TotalSalesQuantity, 
                SUM(ExciseTax) AS TotalExciseTax 
            FROM sales 
            GROUP BY VendorNo, Brand
        )

        SELECT
            ps.VendorNumber,
            ps.VendorName,
            ps.Brand,
            ps.Description,
            ps.PurchasePrice,
            ps.ActualPrice,
            ps.Volume,
            ps.TotalPurchaseQuantity,
            ps.TotalPurchaseDollars,
            ss.TotalSalesQuantity,
            ss.TotalSalesDollars,
            ss.TotalSalesPrice,
            ss.TotalExciseTax,
            fs.FreightCost
        FROM purchasesummary ps 
        LEFT JOIN salessummary ss 
            ON ps.VendorNumber = ss.VendorNo AND ps.Brand = ss.Brand
        LEFT JOIN Freightsummary fs 
            ON ps.VendorNumber = fs.VendorNumber
        ORDER BY ps.TotalPurchaseDollars DESC
        """,
        conn
    )
    return vendor_sales_summary
# This function will clean the data
def clean_data(vendor_sales_summary):
    # change data type to float
    vendor_sales_summary['Volume'] = pd.to_numeric(vendor_sales_summary['Volume'], errors='coerce')

    # fill misisng value with zero
    vendor_sales_summary.fillna(0, inplace=True)

    # remove spaces from categorical columns
    vendor_sales_summary ['VendorName'] = vendor_sales_summary['VendorName'].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()
    vendor_sales_summary ['Description'] = vendor_sales_summary['Description'].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()

    # create new columns for better analysis
    vendor_sales_summary['gross_profit'] = vendor_sales_summary['TotalSalesDollars']- vendor_sales_summary['TotalPurchaseDollars']
    vendor_sales_summary['profit_margin'] = vendor_sales_summary['gross_profit'] /  vendor_sales_summary['TotalSalesDollars'] * 100
    vendor_sales_summary['stock_turnover'] = vendor_sales_summary['TotalSalesQuantity'] / vendor_sales_summary['TotalPurchaseQuantity']
    vendor_sales_summary['sales_purchase_ratio'] = vendor_sales_summary['TotalSalesDollars'] /  vendor_sales_summary['TotalPurchaseDollars']

    #df.fillna(0, inplace=True)
    return  vendor_sales_summary

if __name__== '__main__':
    # create database connection
    conn = sqlite3.connect('inventory.db')
    logging.info('Create Vendor Summary Table.....')
    summary_df = create_vendor_summary(conn)
    logging.info(summary_df.head())
    # data cleaning
    logging.info('cleaning data....')
    clean_df = clean_data(summary_df)
    logging.info(clean_df.head())
    # data ingesting
    logging.info('Ingesting Data')
    ingest_db(clean_df,'vendor_sales_summary', conn)
    logging.info('Completed')
     
