import uvicorn
from yfinance_wrapper.api import app


def main():
    print("YFinance Wrapper Starting Up!")
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()