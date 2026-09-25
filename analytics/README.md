# Module 2 — Analytics & Machine Learning Pipeline

## Overview
This module implements an end-to-end data science workflow on the Titanic dataset, spanning exploratory data analysis, leak-free preprocessing, multi-model evaluation, hyperparameter optimization, regression diagnostics, and pipeline serialization.

---

## Part A: Exploratory Data Analysis & Cleaning Summary
* **Dataset Offline Fallback**: Dataset loaded once via Seaborn and saved locally as `titanic.csv` for standalone reproducibility.
* **Missing Value Threshold Rule**:
  * `embarked` (< 5% missing): Dropped missing rows.
  * `age` (5%–30% missing): Imputed using median strategy.
  * `deck` (> 70% missing): Dropped column due to high sparsity.
* **Univariate & Outlier Analysis**: Outliers identified using the 1.5 * IQR rule. Passenger fare exhibits strong right skew (Mean > Median > Mode).
* **Multivariate Visual Story**: Documented across 4 core visualizations in `01_eda.ipynb`, saved in `plots/`.

---

## Part B: Predictive Modeling Summary & Results

### 1. Leak-Free Preprocessing Architecture
* **Stratified Train/Test Split**: 80/20 split stratified on `survived` to preserve class ratios (61.7% non-survivors vs. 38.3% survivors).
* **Pipeline Structure**: Scikit-Learn `ColumnTransformer` wrapping median imputation and `StandardScaler` for numeric columns (`pclass`, `age`, `sibsp`, `parch`), and one-hot encoding for categorical columns (`sex`, `embarked`).
* **Data Leakage Prevention**: Transformers were fit exclusively on `X_train` and applied in transform-only mode to `X_test`.

### 2. Imbalance Handling Comparison (Logistic Regression)
* **Baseline (No Handling)**: Accuracy: 0.8090 | Precision: 0.7833 | Recall: 0.6912 | F1: 0.7344 | ROC-AUC: 0.8610
* **`class_weight='balanced'`**: Accuracy: 0.7921 | Precision: 0.7183 | Recall: 0.7500 | F1: 0.7338 | ROC-AUC: 0.8612
* **SMOTE Oversampling**: Accuracy: 0.7978 | Precision: 0.7353 | Recall: 0.7353 | F1: 0.7353 | ROC-AUC: 0.8667
* **Conclusion**: SMOTE applied strictly inside the training fold balanced precision and recall equally (0.7353) with the highest ROC-AUC (0.8667).

### 3. Hyperparameter Tuning & Out-of-Bag (OOB) Evaluation
* **Estimator**: `RandomForestClassifier(oob_score=True, random_state=42)`
* **Optimal Hyperparameters**: `max_depth=10`, `max_features=None`, `n_estimators=200`
* **Validation Scores**: 5-Fold CV Accuracy: **0.8256** | OOB Score: **0.8326** | Holdout Test Accuracy: **0.8315**

### 4. Regression Side-Task (Predicting Fare)
* **Model**: Multivariate Linear Regression
* **Metrics**: MAE: **20.7778** | RMSE: **30.4516** | R²: **0.4008** | Adjusted R²: **0.3651**
* **Heteroscedasticity Conclusion**: The residual plot exhibits a widening fan/funnel shape, confirming non-constant variance (heteroscedasticity) driven by luxury ticket outliers.

### 5. Master Model Comparison Table

| Model Type | Model Name | Accuracy | Precision | Recall | F1-Score | ROC-AUC | MAE | RMSE | R² | Adj R² |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Classification | Logistic Regression | 0.8090 | 0.7833 | 0.6912 | 0.7344 | 0.8610 | — | — | — | — |
| Classification | Decision Tree | 0.7697 | 0.6901 | 0.7206 | 0.7050 | 0.7541 | — | — | — | — |
| Classification | Random Forest (Tuned) | 0.8315 | 0.7937 | 0.7353 | 0.7634 | 0.8645 | — | — | — | — |
| Regression | Multivariate Linear Reg | — | — | — | — | — | 20.7778 | 30.4516 | 0.4008 | 0.3651 |

### 6. Deployment Recommendation
Deploy the **Tuned Random Forest** model. It achieves the highest **Accuracy (83.15%)** and **F1-Score (0.7634)**, with balanced **Precision (0.7937)** and **Recall (0.7353)** on holdout test data. Its ensemble structure effectively models non-linear interactions across passenger class, age, and fare without the variance instability seen in the individual decision tree.

### 7. Serialized Artifact Verification
The full pipeline was saved via `joblib.dump` to `models/best_titanic_pipeline.joblib`. End-to-end functionality was confirmed by reloading with `joblib.load` and generating predictions on raw, unpreprocessed records containing missing values.