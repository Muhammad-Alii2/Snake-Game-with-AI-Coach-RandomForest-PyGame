import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib
import warnings

def MLTrainer():
    # Suppress future warnings from sklearn
    warnings.filterwarnings("ignore", category=FutureWarning, module="sklearn")

    # Load the collected data
    data = pd.read_csv(r"..\Required Files\game_data.csv")

    # Prepare the data for training
    X = data[["head_x", "head_y", "xdirection", "ydirection", "food_x", "food_y"]]
    y = data["collision"]

    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=99)

    # Train a RandomForestClassifier
    model = RandomForestClassifier(n_estimators=100, random_state=99)
    model.fit(X_train, y_train)

    # Save the trained model
    joblib.dump(model, r"..\Output Files\snake_ai_model.pkl")
