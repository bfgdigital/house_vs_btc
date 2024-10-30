import streamlit as st

def show_references():

    

    st.title('Data Sources & References')
    
    st.write("""
    This page provides detailed information about the data sources used in the analysis, 
    as well as links to the original code and data.
    """)

    # Market Data Sources
    st.header('Market Data Sources')
    
    st.subheader('Property Market Data')
    st.markdown("""
    - **Australian Housing Market Data**: [ABS Total Value of Dwellings Report](https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/total-value-dwellings/jun-quarter-2024)
        - Primary source for housing price data
        - Data file: `643201.xlsx`
    - **Property Market Capitalization**: [CoreLogic Research News](https://www.corelogic.com.au/news-research/news/2024/australian-property-market-reaches-$11-trillion-as-national-price-growth-slows)
        - Used for total market value comparisons
    """)

    st.subheader('Comparative Market Data')
    st.markdown("""
    - **Gold Market Capitalization**: [8MarketCap](https://8marketcap.com)
    - **Bitcoin Price History**: [Yahoo Finance BTC-AUD](https://finance.yahoo.com/quote/BTC-AUD/history?p=BTC-AUD)
    """)

    # Code Repository
    st.header('Source Code')
    st.markdown("""
    The complete source code and data files for this analysis are available on GitHub:
    
    📁 [Housing vs BTC Analysis Repository](https://github.com/bfgdigital/housing-vs-btc)
    
    The repository includes:
    - Source code for all analyses
    - Data processing scripts
    - Visualization code
    - Raw data files
    """)

    # Data Files
    st.header('Data Files')
    st.markdown("""
    The primary data file used in this analysis is:
    
    - `643201.xlsx`: Contains the ABS housing market data
        - Source: Australian Bureau of Statistics
        - Updated quarterly
        - Contains mean residential dwelling prices by state/territory
    """)

    # Additional Information
    st.header('Usage and Citation')
    st.markdown("""
    When using or referencing this analysis, please cite both this tool and the original data sources listed above. 
    The analysis code is available under the repository's license terms.
    
    For questions about the data or analysis, please open an issue in the GitHub repository.
    """)

if __name__ == "__main__":
    st.set_page_config(page_title='Data Sources & References', layout="centered") 
    show_references()