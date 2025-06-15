import librosa
import numpy as np
import joblib

modelo = joblib.load('app/modelo_estres.joblib')
scaler = joblib.load('app/scaler_estres.joblib')

def predecir_estres(audio_path):
    y, sr = librosa.load(audio_path, duration=9)
    rms = np.mean(librosa.feature.rms(y=y))
    pitch = np.mean(librosa.yin(y, fmin=50, fmax=300, sr=sr))
    mfccs = np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).T, axis=0)
    features = [rms, pitch] + list(mfccs)
    scaled = scaler.transform([features])
    pred = modelo.predict(scaled)
    return "Estresado" if pred[0] == 1 else "No estresado"
