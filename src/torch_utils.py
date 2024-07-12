import torch
import torchvision
from full_dataset import SiameseDataset
from torch.utils.data import DataLoader
import torchvision.transforms.v2 as T
import torchvision.transforms.v2.functional as TF
import matplotlib.pyplot as plt
import numpy as np
import random


def save_checkpoint(state, filename):
    print("=> Saving checkpoint")
    torch.save(state, filename)


# TODO -- research tuning models from a checkpoint
def load_checkpoint(checkpoint, model):
    print("=> Loading checkpoint")
    model.load_state_dict(checkpoint["state_dict"])


def get_loaders(
    patch_sz,
    batch_size,
    num_workers=4,
    pin_memory=True,
    transforms=None,
    split=0.9,
):
    full_ds = SiameseDataset(patch_sz=patch_sz, transform=transforms)
    num_train = int(len(full_ds) * split)
    train_ds, val_ds = torch.utils.data.random_split(
        full_ds,
        [num_train, len(full_ds) - num_train],
    )

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        num_workers=num_workers,  # TODO look up 'workers'
        pin_memory=pin_memory,  # TODO look up pin memory
        shuffle=True,
    )

    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        num_workers=num_workers,
        pin_memory=pin_memory,
        shuffle=False,
    )

    return {"train": train_loader, "val": val_loader}


# keep separate
def get_even_loaders(
    patch_sz,
    batch_size,
    num_workers=4,
    pin_memory=True,
    transforms=None,
    split=0.9,
):
    full_ds = SiameseDataset(patch_sz=patch_sz, transform=transforms)
    damaged_ds = [x for x in full_ds if x[4] == 1]
    undamaged_ds = [x for x in full_ds if x[4] == 0]
    undamaged_ds = torch.utils.data.Subset(undamaged_ds, range(len(damaged_ds)))
    full_ds = torch.utils.data.ConcatDataset([damaged_ds, undamaged_ds])
    num_train = int(len(full_ds) * split)
    train_ds, val_ds = torch.utils.data.random_split(
        full_ds,
        [num_train, len(full_ds) - num_train],
    )

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        num_workers=num_workers,  # TODO look up 'workers'
        pin_memory=pin_memory,  # TODO look up pin memory
        shuffle=True,
    )

    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        num_workers=num_workers,
        pin_memory=pin_memory,
        shuffle=False,
    )

    return {"train": train_loader, "val": val_loader}


def dice_score(loader, model, device="cuda"):
    """
    simplistic accuracy checker
    """

    num_correct = 0
    num_pixels = 0
    dice_score = 0
    model.eval()

    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            y = y.to(device).unsqueeze(1)
            preds = torch.sigmoid(model(x))
            preds = (preds > 0.5).float()
            num_correct += (preds == y).sum()
            num_pixels += torch.numel(preds)
            dice_score += (2 * (preds * y).sum()) / ((preds + y).sum() + 1e-8)

    print(f"Got {num_correct}/{num_pixels} with acc {num_correct/num_pixels*100:.3f}")
    print(f"Dice score: {dice_score/len(loader)}")
    model.train()


def save_predictions_as_imgs(loader, model, folder="saved_images/", device="cuda"):
    model.eval()
    for idx, (x, y) in enumerate(loader):
        x = x.to(device)
        with torch.no_grad():
            preds = torch.sigmoid(model(x))
            preds = (preds > 0.5).float()
            torchvision.utils.save_image(preds, f"{folder}/{idx}_pred.png")
            torchvision.utils.save_image(y.unsqueeze(1), f"{folder}/{idx}_real.png")

    model.train()


def imshow(imgs, title=None):
    """Plot tensors as images"""
    if not isinstance(imgs, list):
        imgs = [imgs]
    fig, axs = plt.subplots(ncols=len(imgs), squeeze=False)
    for i, img in enumerate(imgs):
        img = img.detach()
        img = TF.to_pil_image(img)
        axs[0, i].imshow(np.asarray(img))
        axs[0, i].set(xticklabels=[], yticklabels=[], xticks=[], yticks=[])
        if title is not None:
            plt.title(title)
    plt.ioff()
    plt.show()


# from https://www.learnpytorch.io/04_pytorch_custom_datasets/#78-plot-the-loss-curves-of-model-0
def plot_loss_curves(results):
    """Plots training curves of a results dictionary.

    Args:
        results (dict): dictionary containing list of values, e.g.
            {"train_loss": [...],
             "train_acc": [...],
             "val_loss": [...],
             "val_acc": [...]}
    """

    # Get the loss values of the results dictionary (training and test)
    loss = results["train_loss"]
    test_loss = results["val_loss"]

    # Get the accuracy values of the results dictionary (training and test)
    accuracy = results["train_acc"]
    test_accuracy = results["val_acc"]

    # Figure out how many epochs there were
    epochs = range(len(results["train_loss"]))

    # Setup a plot
    plt.figure(figsize=(15, 7))

    # Plot loss
    plt.subplot(1, 2, 1)
    plt.plot(epochs, loss, label="train_loss")
    plt.plot(epochs, test_loss, label="val_loss")
    plt.title("Loss")
    plt.xlabel("Epochs")
    plt.legend()

    # Plot accuracy
    plt.subplot(1, 2, 2)
    plt.plot(epochs, accuracy, label="train_accuracy")
    plt.plot(epochs, test_accuracy, label="val_accuracy")
    plt.title("Accuracy")
    plt.xlabel("Epochs")
    plt.legend()

    plt.show()


if __name__ == "__main__":
    pass
