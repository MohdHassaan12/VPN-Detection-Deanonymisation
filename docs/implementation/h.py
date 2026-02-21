import xgboost as xgb
from sklearn.metrics import accuracy_score

def train_intent_classifier(X_train, y_train, X_test, y_test):
    model = xgb.XGBClassifier(
        n_estimators=300, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, eval_metric='logloss'
    )
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    print("Accuracy:", accuracy_score(y_test, preds))
    return model
