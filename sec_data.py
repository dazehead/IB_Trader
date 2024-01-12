import requests
import pandas as pd

"""floats are different from the floats on SEC and Company Profile on IB will have to figure out why"""

class SEC_Data:
    """A class for connecting to EDGAR the SEC's API"""
    def __init__(self, tickers_to_search):
        """Initializing resources for API"""
        self.headers = {'User-Agent': "dazetrading0880@gmail.com"}
        self.tickers_to_search = tickers_to_search
        self.cik_list = []
        self.company_float_list = []
        self.get_cik_data()
        self.get_company_float()

    # CIK request
    def get_cik_data(self):
        """Function to retrieve CIK number for tickers"""
        # retrives CIK data as a DataFrame and correctly formats number for further API requests
        company_tickers = requests.get("https://www.sec.gov/files/company_tickers.json", headers=self.headers)
        company_data = pd.DataFrame.from_dict(company_tickers.json(),orient='index')
        company_data['cik_str'] = company_data['cik_str'].astype(str).str.zfill(10)

        # Pair tickers with CIK numbers and apend onto a list
        for ticker in self.tickers_to_search:
            ticker_match = company_data[company_data['ticker'] == ticker]
            self.cik_list.append(ticker_match['cik_str'][0])

    def get_filing_data(self):
        """Gets company specific filing metadeta"""
        for cik in self.cik_list:
            company_meta_data = requests.get(f"https://data.sec.gov/submissions/CIK{cik}.json", headers=self.headers)
            all_forms = pd.DataFrame.from_dict(company_meta_data.json()['filings']['recent'])

        return all_forms

    def get_company_float(self):
        """used to retrieve financial data from statments"""
        # need to verify dates is the most recent
        float_list = []
        for i, cik in enumerate(self.cik_list):
            company_facts = requests.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json", headers=self.headers)
            #print(company_facts.json()['facts']['dei'].keys())

            try:
                float_list.append(company_facts.json()['facts']['dei']['EntityPublicFloat']['units']['USD'][-1]['val'])
            except KeyError:
                print(f"{self.tickers_to_search[i]} Does not have an EntityPublicFloat")
                float_list.append(0)

        self.company_float_list = [[x, y] for x, y in zip(self.tickers_to_search, float_list)]
