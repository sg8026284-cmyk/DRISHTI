import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

def train_and_export():
    np.random.seed(42)
    n_samples = 6000

    # 6 Geotechnical Features
    rainfall = np.random.uniform(0, 130, n_samples)          # mm/hr
    moisture = np.random.uniform(10, 100, n_samples)         # %
    slope = np.random.uniform(5, 60, n_samples)              # degrees
    displacement = np.random.uniform(0, 18, n_samples)       # mm
    land_cover = np.random.choice([1, 2, 3], size=n_samples) # 1: Forest, 2: Barren, 3: Built-up
    river_prox = np.random.uniform(20, 1200, n_samples)      # meters

    cover_weight = np.where(land_cover == 1, 0.4, np.where(land_cover == 2, 1.2, 1.0))
    river_weight = np.clip(1.0 - (river_prox / 1000.0), 0.0, 1.0)

    # Physics Geotechnical Instability Equation
    z = (
        0.038 * rainfall +
        0.030 * moisture +
        0.048 * slope +
        0.280 * displacement +
        0.850 * cover_weight +
        1.100 * river_weight -
        6.2
    )
    prob = 1 / (1 + np.exp(-z))

    labels = []
    for p in prob:
        if p < 0.25:
            labels.append(0) # Low
        elif p < 0.55:
            labels.append(1) # Medium
        elif p < 0.80:
            labels.append(2) # High
        else:
            labels.append(3) # Critical

    X = np.column_stack([rainfall, moisture, slope, displacement, land_cover, river_prox])
    y = np.array(labels)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = RandomForestClassifier(n_estimators=150, max_depth=12, random_state=42)
    model.fit(X_scaled, y)

    joblib.dump(model, 'landslide_model.pkl')
    joblib.dump(scaler, 'scaler.pkl')
    print("[SUCCESS] DRISTI AI: 6-Factor Landslide Model & Scaler compiled successfully.")

if __name__ == '__main__':
    train_and_export()