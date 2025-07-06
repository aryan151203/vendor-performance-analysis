## Importing libraries
import pandas as pd
import os

## Connect with sqlite
from sqlalchemy import create_engine
engine = create_engine('sqlite:///inventory.db')

# Create logs directory 
os.makedirs("logs", exist_ok=True)
#Used to track events during script execution.
import logging
import time
logging.basicConfig(
    filename = "logs/ingestion.db.log",
    level = logging.DEBUG,
    format = "%(asctime)s -%(levelname)s -%(message)s",
#Appends to log file instead of overwriting.    
    filemode = "a"
)

## Extract the csv files from zip file
import zipfile
# open zipfile into the current directory
zip_ref = zipfile.ZipFile('data.zip')
#Extracts all files inside data.zip into the current directory.
zip_ref.extractall()
#Close the zip file after extraction.
zip_ref.close()
# Using def to define a function name ingest_db.
def ingest_db(df,table_name,engine):
    '''This function will ingest the datafrma into database table'''
#Takes a DataFrame df and writes it to the database as table_name.
#if_exists='replace': Deletes the existing table and replaces it.
#index=False: Does not store DataFrame index as a column.    
    df.to_sql(table_name, con=engine , if_exists = "replace", index = False )
# Using def to define a function name load raw dat.
def load_raw_data():
    ''' This function will load  the csvs as dataframe and ingest into db'''
# Captures the current time at the start of execution to measure total runtime.    
    start = time.time()
# Loops over every file name inside the data/ directory.        
    for file in os.listdir('data'):
# Filters only files that contain .csv in their names.        
        if'.csv' in file:
# Read the csv file into pandas DataFrame           
           df = pd.read_csv('data/'+file)
# Ingesting the file into Database          
           logging.info(f'Ingesting {file} in db')
# Calls the ingest_db() function to save the DataFrame to a database.
# file[:-4] removes the .csv extension to use as the table name.           
           ingest_db(df,file[:-4],engine)
# Captures the end time, calculates how long the process took (in minutes).           
    end = time.time()
    total_time = (end - start)/60
    logging.info('--------Ingestion complete--------') 
# showing how much time will it take.
    logging.info(f'\n Total Time Taken: {total_time:.2f} in minutes')   
if __name__== '__main__':
# function calling.  
    load_raw_data()