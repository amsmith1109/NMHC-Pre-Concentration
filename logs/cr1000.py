import requests
import pandas as pd
import time
import schedule

# Ignoring a FutureWarning from pandas when converting the html table to a dataframe
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

class CR1000:
    def __init__(self, address, filename):
        self.address = address
        self.filename = filename
        self.last_row = self.read_last_row()
        self.columns = self.last_row.keys()

    def read_last_row(self):
        with open(self.filename, 'r'):
            last_row = pd.read_csv(self.filename).tail(1).reset_index()
        return last_row[last_row.keys()[1:]]

    def append_csv(self, row):         
        if row is None:
            print('Nothing to record.')
            return
        try:
            with open(self.filename, "a") as f:  # Open file in append mode
                data_string = row.iloc[[0]].to_csv(index=False, header=False).strip() + '\n'
                f.write(data_string)  # Write data to file
        except:
            print(f'Failed to update file. {time.strftime("%Y-%m-%d %H:%M:%S")}')

    def grab_data(self):
        r = requests.get(self.address)
        data = pd.read_html(r.text)
        row = data[0][self.columns]
        return row

    def push_data(self):
        row = self.grab_data()
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        if row[met_station.columns[0]][0] != self.last_row[met_station.columns[0]][0]:
            self.append_csv(row)
            print(f'{row}')
        else:
            print(f'Nothing new to save {current_time}.')

    def logger(self, delay=1):
        self.push_data()
        schedule.every(delay).minutes.do(self.push_data)
        while True:
            schedule.run_pending()
            time.sleep(delay*10)

if __name__ == '__main__':
    '''
    The address calls the CR1000 and queries which information will be saved elsewhere.
    In this file it asks for the last record from the "Weather" table.
    
    The filename is the address where the CSV file is saved. I'm using the Google Drive app
    for Windows, with the file saved to my lab group's shared drive. Saving it this way will
    automatically update the file on google drive.
    '''
    address = 'http://131.252.124.156/?command=TableDisplay&table=Weather&records=1'
    filename = 'G:/Shared drives/Rice Lab Data/SRTC met data.csv'
    columns = [0, 2, 3, 4, 5] # picks out specific columns
    met_station = CR1000(address, filename)
    met_station.logger()

