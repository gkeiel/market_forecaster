import json, warnings
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.ensemble import RandomTreesEmbedding
from sklearn.neighbors import KNeighborsRegressor
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import Ridge
from statsmodels.tsa.arima.model import ARIMA


# =====================================================
#  Forecaster
# =====================================================
class Forecaster:
    def __init__(self, indicator, df, file_config="config/config.json"):
        self.indicator = indicator
        self.df = df.copy()
        self.model  = None
        self.load_config(file_config)
        
    def load_config(self, path):
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
            self.N = config.get("N_train", 100)
                    
    def predictions(self):
        df = self.df
        method = self.indicator.get("ind_t", "RF")
        params = self.indicator.get("ind_p", [50, 5, 5])
        y  = df["Close"]
        
        # supervised machine learning methods    
        if method != "ARIMA":
            self.n_estimators, self.max_depth, self.n_lags = params
            
            # build features for ML model:
            X, Y = [], []
            for i in range(self.n_lags, len(y)):
                X.append(y.iloc[i-self.n_lags:i])
                Y.append(y.iloc[i])
            X, Y= np.array(X), np.array(Y)
            
            # train data and test data
            X_train, Y_train = X[:self.N], Y[:self.N]
            X_test, Y_test   = X[self.N:], Y[self.N:]
            
            # method and trainning
            if method == "RF":
                model = RandomForestRegressor(n_estimators=self.n_estimators, max_depth=self.max_depth, random_state=0)
            elif method == "ET":
                model = ExtraTreesRegressor(n_estimators=self.n_estimators, max_depth=self.max_depth)
            elif method == "GB":
                model = GradientBoostingRegressor(n_estimators=self.n_estimators, max_depth=self.max_depth)
            elif method == "RTE":
                model = RandomTreesEmbedding(n_estimators=self.n_estimators, max_depth=self.max_depth)
            elif method == "KNN":
                model = KNeighborsRegressor(n_neighbors=self.max_depth)
            elif method == "LR":
                model = LinearRegression()
            elif method == "RR":
                model = Ridge(alpha=1.0)
            model.fit(X_train, Y_train)
            
            # predictions
            y_hat = model.predict(X_test)

        # statistical methods
        elif method == "ARIMA":
            p, d, q = params
            
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning)
                warnings.filterwarnings("ignore", category=FutureWarning)
                self.n_lags = 0
                y_train, y_test = y.iloc[:self.N], y.iloc[self.N:]
                
                # model class and trainning
                model = ARIMA(y_train, order=(p, d, q), enforce_stationarity=False, enforce_invertibility=False).fit()
                
                y_history = list(y_train.values)
                y_hat = []
                for k in range(len(y_test)):
                    # predictions
                    y_pred = model.forecast(steps=1).iloc[0]
                    y_hat.append(y_pred)
                    y_history.append(y_test.iloc[k])
                    model = model.append([y_test.iloc[k]], refit=False)
            y_hat = np.asarray(y_hat).ravel()
                
        # save model            
        self.model = model
        
        # add to dataframe
        df["Predicted_Close"] = np.nan
        df.loc[df.index[self.N+self.n_lags:], "Predicted_Close"] = y_hat
        return df
    
    def predict_next(self):
        if self.model is None:
            raise ValueError("No existing model.")
        method = self.indicator.get("ind_t")
        
        if method == "ARIMA":
            y_hat  = float(self.model.forecast(steps=1).iloc[0])
        else:
            last_Y = self.df["Close"].iloc[-self.n_lags:].values.reshape(1, -1)               
            y_hat  = self.model.predict(last_Y)[0]
        return y_hat