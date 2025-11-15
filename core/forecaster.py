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
            
    def build_features(self, y):
        X, Y = [], []
        for i in range(self.n_lags, len(y)):
            X.append(y.iloc[i-self.n_lags:i])
            Y.append(y.iloc[i])
        return np.array(X), np.array(Y)
                
    def predictions(self):
        df = self.df.copy()
        y  = df["Close"]
        
        method = self.indicator.get("ind_t", "RF")
        params = self.indicator.get("ind_p", [50, 5, 5])
        if method not in self.MODELS:
                raise ValueError(f"Unknown forecasting method: {method}.")
        
        # supervised machine learning methods    
        if method != "ARIMA":
            self.n_estimators, self.max_depth, self.n_lags = params
            
            # build features for ML models:
            X, Y = self.build_features(y)
            
            # train data and test data
            X_train, Y_train = X[:self.N], Y[:self.N]
            X_test, Y_test   = X[self.N:], Y[self.N:]
            
            # define method and trainning
            model = self.MODELS[method](params)
            model.fit(X_train, Y_train)
            
            # predictions
            y_hat = model.predict(X_test)

        # statistical methods
        elif method == "ARIMA":
            # AR order, differencing order, MA order
            p, d, q = params
            
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning)
                warnings.filterwarnings("ignore", category=FutureWarning)
                self.n_lags = 0
                y_train, y_test = y.iloc[:self.N], y.iloc[self.N:]
                
                # model class and trainning
                model = ARIMA(y_train, order=(p, d, q), enforce_stationarity=False, enforce_invertibility=False).fit()
                
                #y_history = list(y_train.values)
                y_hat = []
                for k in range(len(y_test)):
                    # predictions
                    y_pred = model.forecast().iloc[0]
                    y_hat.append(y_pred)
                    #y_history.append(y_test.iloc[k])
                    model = model.append([y_test.iloc[k]], refit=False)
            y_hat = np.asarray(y_hat).ravel()
                
        # save model            
        self.model = model
        
        # add to dataframe
        pred = np.full(len(df), np.nan)
        pred[self.N+self.n_lags: self.N+self.n_lags+len(y_hat)] = y_hat
        df["Predicted_Close"] = pred
        return df
    
    def predict_next(self):
        if self.model is None:
            raise ValueError("No existing model.")
        method = self.indicator.get("ind_t")
        
        if method == "ARIMA":
            y_hat  = float(self.model.forecast().iloc[0])
        else:
            last_Y = self.df["Close"].iloc[-self.n_lags:].values.reshape(1, -1)               
            y_hat  = self.model.predict(last_Y)[0]
        return y_hat
    
    MODELS = {
        "RF": lambda params: RandomForestRegressor(n_estimators=params[0], max_depth=params[1], random_state=0),
        "RT": lambda params: RandomTreesEmbedding(n_estimators=params[0], max_depth=params[1]),
        "ET": lambda params: ExtraTreesRegressor(n_estimators=params[0], max_depth=params[1]),
        "GB": lambda params: GradientBoostingRegressor(n_estimators=params[0], max_depth=params[1]),
        "KN": lambda params: KNeighborsRegressor(n_neighbors=params[1]),
        "LR": lambda params: LinearRegression(),
        "RR": lambda params: Ridge(alpha=1.0),
        "ARIMA": lambda params: None
    }