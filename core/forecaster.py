import json
import numpy as np
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.arima.model import ARIMA


# =====================================================
#  Forecaster
# =====================================================
class Forecaster:
    def __init__(self, indicator, df, file_config="config.json"):
        self.indicator = indicator
        self.df = df.copy()
        self.model  = None
        self.load_config(file_config)
        
    def load_config(self, path):
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
            cfg    = config.get("forecast", {})
                    
    def predictions(self):
        df = self.df
        method = self.indicator.get("ind_t", "RF")
        params = self.indicator.get("ind_p", [])        
        self.n_estimators = params[0]
        self.max_depth    = params[1]
        self.n_lags       = params[2]
        
        y  = df["Close"]

        # build features for ML model
        X, Y = [], []
        for i in range(self.n_lags, len(y)):
            X.append(y.iloc[i-self.n_lags:i])
            Y.append(y.iloc[i])
        X = np.array(X)
        Y = np.array(Y)

        # supervised machine learning methods
        if method == "LR":
            model = LinearRegression()
        elif method == "DT":
            model = DecisionTreeRegressor(max_depth=self.max_depth)
        elif method == "RF":
            model = RandomForestRegressor(n_estimators=self.n_estimators, max_depth=self.max_depth, random_state=0)
        elif method == "GB":
            model = GradientBoostingRegressor(n_estimators=self.n_estimators, max_depth=self.max_depth)
        elif method == "ET":
            model = ExtraTreesRegressor(n_estimators=self.n_estimators, max_depth=self.max_depth)
        elif method == "KNN":
            model = KNeighborsRegressor(n_neighbors=self.max_depth)
        model.fit(X, Y)
        self.model = model
                
        # statistical methods
        #if method == "ARIMA":
        #    p = 1
        #    d = 1
        #    q = 1
        #    model = ARIMA(Y, order=(p, d, q))
        #    model = model.fit()
        #self.model = model

        # predictions
        y_hat = model.predict(X)
        
        # add to dataframe
        df["Predicted_Close"] = np.nan
        df.loc[df.index[self.n_lags:], "Predicted_Close"] = y_hat
        return df
    
    def predict_next(self):
        if self.model is None:
            raise ValueError("No existing model.")
        last_Y = self.df["Close"].iloc[-self.n_lags:].values.reshape(1, -1)               
        y_hat  = self.model.predict(last_Y)[0]
        return y_hat