from fastai.vision.all import *

if __name__ == '__main__':
    # Step 1: Set up the path to your dataset
    path = Path(r'E:\plantnet_300K\images_train')  # Update this with the actual path to your dataset

    # Step 2: Load the data from folders, resize the images, and apply basic augmentations
    dls = ImageDataLoaders.from_folder(
        path, 
        valid_pct=0.2,  # Split 20% of data for validation
        item_tfms=Resize(224),  # Resize images to 224x224 for ResNet input
        batch_tfms=aug_transforms(mult=2)  # Apply random transformations for augmentation
    )

    # Step 3: Load a pre-trained ResNet34 model for transfer learning and specify accuracy as the metric
    learn = vision_learner(dls, resnet34, metrics=accuracy)

    # Step 4: Find the optimal learning rate
    learn.lr_find()

    # Step 5: Fine-tune the model using the found learning rate
    learn.fine_tune(4, base_lr=1e-3)  # Fine-tune for 4 epochs with the given learning rate

    # Step 6: Evaluate the model's results on the validation set
    learn.show_results()

    # Step 7: Optionally, unfreeze the model and fine-tune all layers with differential learning rates
    learn.unfreeze()
    learn.fit_one_cycle(4, lr_max=slice(1e-6, 1e-3))

    # Step 8: Save the trained model to a file
    learn.export(r'E:\plantnet_300K\images_train\plant_classifier.pkl')

    # Step 9: Load the saved model and make predictions on new images
    learn_inf = load_learner('plant_classifier.pkl')

    # Example prediction on a new image
    img = PILImage.create(r'E:\plantnet_300K\images_test\1355868\0b0e0be9f73598118994979b15400d0608ff1fa3.jpg')
    pred, pred_idx, probs = learn_inf.predict(img)
    print(f'Prediction: {pred}; Probability: {probs[pred_idx]:.4f}')
