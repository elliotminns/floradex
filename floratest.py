from fastai.vision.all import *

if __name__ == '__main__':
    # Step 9: Load the saved model and make predictions on new images
    learn_inf = load_learner(r"E:\plantnet_300K\images_train\1355868\plant_classifier.pkl")

    # Example prediction on a new image
    img = PILImage.create(r'C:\Users\Elliot\Desktop\download.jpg')
    pred, pred_idx, probs = learn_inf.predict(img)
    print(f'Prediction: {pred}; Probability: {probs[pred_idx]:.4f}')
